"""
byceps.services.shop.order.order_command_service
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright: 2014-2024 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import delete
import structlog

from byceps.database import db
from byceps.events.shop import ShopOrderCanceledEvent, ShopOrderPaidEvent
from byceps.services.shop.article import article_service
from byceps.services.shop.article.models import ArticleType
from byceps.services.ticketing.models.ticket import TicketCategoryID
from byceps.services.user import user_service
from byceps.services.user.models.user import User
from byceps.util.result import Err, Ok, Result

from . import (
    order_action_service,
    order_domain_service,
    order_log_service,
    order_payment_service,
)
from .actions import (
    ticket as ticket_actions,
    ticket_bundle as ticket_bundle_actions,
)
from .dbmodels.line_item import DbLineItem
from .dbmodels.log import DbOrderLogEntry
from .dbmodels.order import DbOrder
from .errors import OrderAlreadyCanceledError, OrderAlreadyMarkedAsPaidError
from .models.log import OrderLogEntry
from .models.order import LineItemID, Order, OrderID, PaymentState
from .models.payment import AdditionalPaymentData
from .order_helper_service import to_order, _is_paid


log = structlog.get_logger()


def add_note(order: Order, author: User, text: str) -> None:
    """Add a note to the order."""
    log_entry = order_domain_service.add_note(order, author, text)

    db_log_entry = order_log_service.to_db_entry(log_entry)
    db.session.add(db_log_entry)
    db.session.commit()


def set_shipped_flag(order: Order, initiator: User) -> Result[None, str]:
    """Mark the order as shipped."""
    set_shipped_flag_result = order_domain_service.set_shipped_flag(
        order, initiator
    )

    if set_shipped_flag_result.is_err():
        return Err(set_shipped_flag_result.unwrap_err())

    log_entry = set_shipped_flag_result.unwrap()

    _persist_shipped_flag(log_entry, log_entry.occurred_at)

    return Ok(None)


def unset_shipped_flag(order: Order, initiator: User) -> Result[None, str]:
    """Mark the order as not shipped."""
    unset_shipped_flag_result = order_domain_service.unset_shipped_flag(
        order, initiator
    )

    if unset_shipped_flag_result.is_err():
        return Err(unset_shipped_flag_result.unwrap_err())

    log_entry = unset_shipped_flag_result.unwrap()

    _persist_shipped_flag(log_entry, None)

    return Ok(None)


def _persist_shipped_flag(
    log_entry: OrderLogEntry, processed_at: datetime | None
) -> None:
    db_order = _get_order_entity(log_entry.order_id)

    db_log_entry = order_log_service.to_db_entry(log_entry)
    db.session.add(db_log_entry)

    db_order.processed_at = processed_at

    db.session.commit()


def cancel_order(
    order_id: OrderID, initiator: User, reason: str
) -> Result[tuple[Order, ShopOrderCanceledEvent], OrderAlreadyCanceledError]:
    """Cancel the order.

    Reserved quantities of articles from that order are made available
    again.
    """
    db_order = _get_order_entity(order_id)

    orderer_user = user_service.get_user(db_order.placed_by_id)
    order = to_order(db_order, orderer_user)

    occurred_at = datetime.utcnow()

    cancel_order_result = order_domain_service.cancel_order(
        order,
        orderer_user,
        occurred_at,
        reason,
        initiator,
    )
    if cancel_order_result.is_err():
        return Err(cancel_order_result.unwrap_err())

    event, log_entry = cancel_order_result.unwrap()

    payment_state_to = (
        PaymentState.canceled_after_paid
        if _is_paid(db_order)
        else PaymentState.canceled_before_paid
    )

    _update_payment_state(db_order, payment_state_to, occurred_at, initiator)
    db_order.cancellation_reason = reason

    db_log_entry = order_log_service.to_db_entry(log_entry)
    db.session.add(db_log_entry)

    # Make the reserved quantity of articles available again.
    for db_line_item in db_order.line_items:
        article_service.increase_quantity(
            db_line_item.article.id, db_line_item.quantity, commit=False
        )

    db.session.commit()

    canceled_order = to_order(db_order, orderer_user)

    if payment_state_to == PaymentState.canceled_after_paid:
        _execute_article_revocation_actions(canceled_order, initiator)

    log.info('Order canceled', shop_order_canceled_event=event)

    return Ok((canceled_order, event))


def mark_order_as_paid(
    order_id: OrderID,
    payment_method: str,
    initiator: User,
    *,
    additional_payment_data: AdditionalPaymentData | None = None,
) -> Result[tuple[Order, ShopOrderPaidEvent], OrderAlreadyMarkedAsPaidError]:
    """Mark the order as paid."""
    db_order = _get_order_entity(order_id)

    orderer_user = user_service.get_user(db_order.placed_by_id)
    order = to_order(db_order, orderer_user)

    occurred_at = datetime.utcnow()

    order_payment_service.add_payment(
        order,
        occurred_at,
        payment_method,
        order.total_amount,
        initiator,
        additional_payment_data if additional_payment_data is not None else {},
    )

    mark_order_as_paid_result = order_domain_service.mark_order_as_paid(
        order,
        orderer_user,
        occurred_at,
        payment_method,
        additional_payment_data,
        initiator,
    )
    if mark_order_as_paid_result.is_err():
        return Err(mark_order_as_paid_result.unwrap_err())

    event, log_entry = mark_order_as_paid_result.unwrap()

    db_order.payment_method = payment_method
    _update_payment_state(db_order, PaymentState.paid, occurred_at, initiator)

    db_log_entry = order_log_service.to_db_entry(log_entry)
    db.session.add(db_log_entry)

    db.session.commit()

    paid_order = to_order(db_order, orderer_user)

    _execute_article_creation_actions(paid_order, initiator)

    log.info('Order paid', shop_order_paid_event=event)

    return Ok((paid_order, event))


def _update_payment_state(
    db_order: DbOrder,
    state: PaymentState,
    updated_at: datetime,
    initiator: User,
) -> None:
    db_order.payment_state = state
    db_order.payment_state_updated_at = updated_at
    db_order.payment_state_updated_by_id = initiator.id


def _execute_article_creation_actions(order: Order, initiator: User) -> None:
    # based on article type
    for line_item in order.line_items:
        if line_item.article_type in (
            ArticleType.ticket,
            ArticleType.ticket_bundle,
        ):
            article = article_service.get_article(line_item.article_id)

            ticket_category_id = TicketCategoryID(
                UUID(str(article.type_params['ticket_category_id']))
            )

            if line_item.article_type == ArticleType.ticket:
                ticket_actions.create_tickets(
                    order,
                    line_item,
                    ticket_category_id,
                    initiator,
                )
            elif line_item.article_type == ArticleType.ticket_bundle:
                ticket_quantity_per_bundle = int(
                    article.type_params['ticket_quantity']
                )
                ticket_bundle_actions.create_ticket_bundles(
                    order,
                    line_item,
                    ticket_category_id,
                    ticket_quantity_per_bundle,
                    initiator,
                )

    # based on order action registered for article number
    order_action_service.execute_creation_actions(order, initiator)


def _execute_article_revocation_actions(order: Order, initiator: User) -> None:
    # based on article type
    for line_item in order.line_items:
        if line_item.article_type == ArticleType.ticket:
            ticket_actions.revoke_tickets(order, line_item, initiator)
        elif line_item.article_type == ArticleType.ticket_bundle:
            ticket_bundle_actions.revoke_ticket_bundles(
                order, line_item, initiator
            )

    # based on order action registered for article number
    order_action_service.execute_revocation_actions(order, initiator)


def update_line_item_processing_result(
    line_item_id: LineItemID, data: dict[str, Any]
) -> None:
    """Update the line item's processing result data."""
    db_line_item = db.session.get(DbLineItem, line_item_id)

    if db_line_item is None:
        raise ValueError(f'Unknown line item ID "{line_item_id}"')

    db_line_item.processing_result = data
    db_line_item.processed_at = datetime.utcnow()
    db.session.commit()


def delete_order(order: Order) -> None:
    """Delete an order."""
    order_payment_service.delete_payments_for_order(order.id)

    db.session.execute(delete(DbOrderLogEntry).filter_by(order_id=order.id))
    db.session.execute(
        delete(DbLineItem).filter_by(order_number=order.order_number)
    )
    db.session.execute(delete(DbOrder).filter_by(id=order.id))
    db.session.commit()

    log.info('Order deleted', order_number=order.order_number)


def _get_order_entity(order_id: OrderID) -> DbOrder:
    """Return the order database entity with that id, or raise an
    exception.
    """
    db_order = db.session.get(DbOrder, order_id)

    if db_order is None:
        raise ValueError(f'Unknown order ID "{order_id}"')

    return db_order
