"""
byceps.announce.handlers.news
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Announce news events.

:Copyright: 2014-2023 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

from functools import wraps

from ...events.news import NewsItemPublished
from ...services.webhooks.models import OutgoingWebhook
from ...util.jobqueue import enqueue_at

from ..helpers import call_webhook, matches_selectors
from ..text_assembly import news


def apply_selectors(handler):
    @wraps(handler)
    def wrapper(event: NewsItemPublished, webhook: OutgoingWebhook):
        channel_id = str(event.channel_id)
        if not matches_selectors(event, webhook, 'channel_id', channel_id):
            return

        handler(event, webhook)

    return wrapper


@apply_selectors
def announce_news_item_published(
    event: NewsItemPublished, webhook: OutgoingWebhook
) -> None:
    """Announce that a news item has been published."""
    text = news.assemble_text_for_news_item_published(event)

    if event.published_at > event.occurred_at:
        # Schedule job to announce later.
        enqueue_at(event.published_at, call_webhook, webhook, text)
    else:
        # Announce now.
        call_webhook(webhook, text)
