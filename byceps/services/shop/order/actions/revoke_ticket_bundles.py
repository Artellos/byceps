"""
byceps.services.shop.order.actions.revoke_ticket_bundles
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright: 2014-2023 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

from .....typing import UserID

from ..models.action import ActionParameters
from ..models.order import LineItem, Order

from . import ticket_bundle


def revoke_ticket_bundles(
    order: Order,
    line_item: LineItem,
    initiator_id: UserID,
    parameters: ActionParameters,
) -> None:
    """Revoke all ticket bundles in this order."""
    ticket_bundle.revoke_ticket_bundles(order, line_item, initiator_id)
