"""
byceps.announce.handlers.shop_order
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Announce shop order events.

:Copyright: 2014-2023 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

from ...events.shop import ShopOrderCanceled, ShopOrderPaid, ShopOrderPlaced
from ...services.webhooks.models import OutgoingWebhook

from ..helpers import call_webhook
from ..text_assembly import shop_order


def announce_order_placed(
    event: ShopOrderPlaced, webhook: OutgoingWebhook
) -> None:
    """Announce that an order has been placed."""
    text = shop_order.assemble_text_for_order_placed(event)

    call_webhook(webhook, text)


def announce_order_paid(event: ShopOrderPaid, webhook: OutgoingWebhook) -> None:
    """Announce that an order has been paid."""
    text = shop_order.assemble_text_for_order_paid(event)

    call_webhook(webhook, text)


def announce_order_canceled(
    event: ShopOrderCanceled, webhook: OutgoingWebhook
) -> None:
    """Announce that an order has been canceled."""
    text = shop_order.assemble_text_for_order_canceled(event)

    call_webhook(webhook, text)
