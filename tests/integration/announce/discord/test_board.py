"""
:Copyright: 2014-2022 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

import pytest

import byceps.announce.connections  # Connect signal handlers.
from byceps.events.board import BoardPostingCreated, BoardTopicCreated
from byceps.services.board import (
    board_category_command_service,
    board_posting_command_service,
    board_topic_command_service,
)
from byceps.services.webhooks import webhook_service
from byceps.signals import board as board_signals

from .helpers import assert_request, mocked_webhook_receiver


WEBHOOK_URL = 'https://webhoooks.test/board'


def test_announce_topic_created(
    webhook_settings, admin_app, board, topic, creator
):
    expected_url = f'https://website.test/board/topics/{topic.id}'
    expected_content = (
        '[Forum] RocketRandy hat das Thema '
        '"Cannot connect to the party network :(" erstellt: '
        f'<{expected_url}>'
    )

    event = BoardTopicCreated(
        occurred_at=topic.created_at,
        initiator_id=creator.id,
        initiator_screen_name=creator.screen_name,
        board_id=board.id,
        topic_id=topic.id,
        topic_creator_id=creator.id,
        topic_creator_screen_name=creator.screen_name,
        topic_title=topic.title,
        url=expected_url,
    )

    with mocked_webhook_receiver(WEBHOOK_URL) as mock:
        board_signals.topic_created.send(None, event=event)

    assert_request(mock, expected_content)


def test_announce_posting_created(
    webhook_settings, admin_app, board, posting, creator
):
    expected_url = f'https://website.test/board/postings/{posting.id}'
    expected_content = (
        '[Forum] RocketRandy hat auf das Thema '
        '"Cannot connect to the party network :(" geantwortet: '
        f'<{expected_url}>'
    )

    event = BoardPostingCreated(
        occurred_at=posting.created_at,
        initiator_id=creator.id,
        initiator_screen_name=creator.screen_name,
        board_id=board.id,
        posting_creator_id=creator.id,
        posting_creator_screen_name=creator.screen_name,
        posting_id=posting.id,
        topic_id=posting.topic.id,
        topic_title=posting.topic.title,
        topic_muted=posting.topic.muted,
        url=expected_url,
    )

    with mocked_webhook_receiver(WEBHOOK_URL) as mock:
        board_signals.posting_created.send(None, event=event)

    assert_request(mock, expected_content)


# helpers


@pytest.fixture(scope='module')
def webhook_settings(board):
    board_ids = [str(board.id), 'totally-different-id']
    format = 'discord'
    text_prefix = '[Forum] '
    url = WEBHOOK_URL
    enabled = True

    webhooks = [
        webhook_service.create_outgoing_webhook(
            # event_types
            {
                'board-posting-created',
                'board-topic-created',
            },
            # event_filters
            {
                'board-posting-created': {'board_id': [board_id]},
                'board-topic-created': {'board_id': [board_id]},
            },
            format,
            url,
            enabled,
            text_prefix=text_prefix,
        )
        for board_id in board_ids
    ]

    yield

    for webhook in webhooks:
        webhook_service.delete_outgoing_webhook(webhook.id)


@pytest.fixture(scope='module')
def creator(make_user):
    return make_user('RocketRandy')


@pytest.fixture(scope='module')
def category(board):
    slug = 'support'
    title = 'Support'
    description = 'How can I help you, dear Sir/Madam?'

    return board_category_command_service.create_category(
        board.id, slug, title, description
    )


@pytest.fixture(scope='module')
def topic(category, creator):
    title = 'Cannot connect to the party network :('
    body = 'I think I did not receive an IP address via DHCP. BUT WHY?!'

    topic, _ = board_topic_command_service.create_topic(
        category.id, creator.id, title, body
    )

    return topic


@pytest.fixture(scope='module')
def posting(topic, creator):
    posting, _ = board_posting_command_service.create_posting(
        topic.id, creator.id, 'This is nice and all, but check out my website!'
    )

    return posting
