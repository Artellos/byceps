"""
:Copyright: 2014-2022 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

import pytest

import byceps.announce.connections  # Connect signal handlers.  # noqa: F401
from byceps.events.board import (
    BoardPostingCreated,
    BoardPostingHidden,
    BoardPostingUnhidden,
    BoardTopicCreated,
    BoardTopicHidden,
    BoardTopicLocked,
    BoardTopicMoved,
    BoardTopicPinned,
    BoardTopicUnhidden,
    BoardTopicUnlocked,
    BoardTopicUnpinned,
)
from byceps.services.board import (
    board_category_command_service,
    board_posting_command_service,
    board_topic_command_service,
)
from byceps.signals import board as board_signals

from .helpers import assert_submitted_text, mocked_irc_bot, now


def test_announce_topic_created(app, board, topic, creator):
    expected_link = f'http://example.com/board/topics/{topic.id}'
    expected_text = (
        'TheShadow999 hat im "ACME Entertainment Convention"-Forum '
        f'das Thema "Brötchen zum Frühstück" erstellt: {expected_link}'
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
        url=expected_link,
    )

    with mocked_irc_bot() as mock:
        board_signals.topic_created.send(None, event=event)

    assert_submitted_text(mock, expected_text)


def test_announce_topic_hidden(app, board, topic, creator, moderator):
    expected_link = f'http://example.com/board/topics/{topic.id}'
    expected_text = (
        'ElBosso hat im "ACME Entertainment Convention"-Forum das Thema '
        '"Brötchen zum Frühstück" von TheShadow999 '
        f'versteckt: {expected_link}'
    )

    event = BoardTopicHidden(
        occurred_at=now(),
        initiator_id=moderator.id,
        initiator_screen_name=moderator.screen_name,
        board_id=board.id,
        topic_id=topic.id,
        topic_creator_id=creator.id,
        topic_creator_screen_name=creator.screen_name,
        topic_title=topic.title,
        moderator_id=moderator.id,
        moderator_screen_name=moderator.screen_name,
        url=expected_link,
    )

    with mocked_irc_bot() as mock:
        board_signals.topic_hidden.send(None, event=event)

    assert_submitted_text(mock, expected_text)


def test_announce_topic_unhidden(app, board, topic, creator, moderator):
    expected_link = f'http://example.com/board/topics/{topic.id}'
    expected_text = (
        'ElBosso hat im "ACME Entertainment Convention"-Forum das Thema '
        '"Brötchen zum Frühstück" von TheShadow999 '
        f'wieder sichtbar gemacht: {expected_link}'
    )

    event = BoardTopicUnhidden(
        occurred_at=now(),
        initiator_id=moderator.id,
        initiator_screen_name=moderator.screen_name,
        board_id=board.id,
        topic_id=topic.id,
        topic_creator_id=creator.id,
        topic_creator_screen_name=creator.screen_name,
        topic_title=topic.title,
        moderator_id=moderator.id,
        moderator_screen_name=moderator.screen_name,
        url=expected_link,
    )

    with mocked_irc_bot() as mock:
        board_signals.topic_unhidden.send(None, event=event)

    assert_submitted_text(mock, expected_text)


def test_announce_topic_locked(app, board, topic, creator, moderator):
    expected_link = f'http://example.com/board/topics/{topic.id}'
    expected_text = (
        'ElBosso hat im "ACME Entertainment Convention"-Forum das Thema '
        '"Brötchen zum Frühstück" von TheShadow999 '
        f'geschlossen: {expected_link}'
    )

    event = BoardTopicLocked(
        occurred_at=now(),
        initiator_id=moderator.id,
        initiator_screen_name=moderator.screen_name,
        board_id=board.id,
        topic_id=topic.id,
        topic_creator_id=creator.id,
        topic_creator_screen_name=creator.screen_name,
        topic_title=topic.title,
        moderator_id=moderator.id,
        moderator_screen_name=moderator.screen_name,
        url=expected_link,
    )

    with mocked_irc_bot() as mock:
        board_signals.topic_locked.send(None, event=event)

    assert_submitted_text(mock, expected_text)


def test_announce_topic_unlocked(app, board, topic, creator, moderator):
    expected_link = f'http://example.com/board/topics/{topic.id}'
    expected_text = (
        'ElBosso hat im "ACME Entertainment Convention"-Forum '
        'das Thema "Brötchen zum Frühstück" von TheShadow999 '
        f'wieder geöffnet: {expected_link}'
    )

    event = BoardTopicUnlocked(
        occurred_at=now(),
        initiator_id=moderator.id,
        initiator_screen_name=moderator.screen_name,
        board_id=board.id,
        topic_id=topic.id,
        topic_creator_id=creator.id,
        topic_creator_screen_name=creator.screen_name,
        topic_title=topic.title,
        moderator_id=moderator.id,
        moderator_screen_name=moderator.screen_name,
        url=expected_link,
    )

    with mocked_irc_bot() as mock:
        board_signals.topic_unlocked.send(None, event=event)

    assert_submitted_text(mock, expected_text)


def test_announce_topic_pinned(app, board, topic, creator, moderator):
    expected_link = f'http://example.com/board/topics/{topic.id}'
    expected_text = (
        'ElBosso hat im "ACME Entertainment Convention"-Forum '
        'das Thema "Brötchen zum Frühstück" von TheShadow999 '
        f'angepinnt: {expected_link}'
    )

    event = BoardTopicPinned(
        occurred_at=now(),
        initiator_id=moderator.id,
        initiator_screen_name=moderator.screen_name,
        board_id=board.id,
        topic_id=topic.id,
        topic_creator_id=creator.id,
        topic_creator_screen_name=creator.screen_name,
        topic_title=topic.title,
        moderator_id=moderator.id,
        moderator_screen_name=moderator.screen_name,
        url=expected_link,
    )

    with mocked_irc_bot() as mock:
        board_signals.topic_pinned.send(None, event=event)

    assert_submitted_text(mock, expected_text)


def test_announce_topic_unpinned(app, board, topic, creator, moderator):
    expected_link = f'http://example.com/board/topics/{topic.id}'
    expected_text = (
        'ElBosso hat im "ACME Entertainment Convention"-Forum '
        'das Thema "Brötchen zum Frühstück" von TheShadow999 '
        f'wieder gelöst: {expected_link}'
    )

    event = BoardTopicUnpinned(
        occurred_at=now(),
        initiator_id=moderator.id,
        initiator_screen_name=moderator.screen_name,
        board_id=board.id,
        topic_id=topic.id,
        topic_creator_id=creator.id,
        topic_creator_screen_name=creator.screen_name,
        topic_title=topic.title,
        moderator_id=moderator.id,
        moderator_screen_name=moderator.screen_name,
        url=expected_link,
    )

    with mocked_irc_bot() as mock:
        board_signals.topic_unpinned.send(None, event=event)

    assert_submitted_text(mock, expected_text)


def test_announce_topic_moved(
    app, board, category, another_category, topic, creator, moderator
):
    expected_link = f'http://example.com/board/topics/{topic.id}'
    expected_text = (
        'ElBosso hat im "ACME Entertainment Convention"-Forum '
        'das Thema "Brötchen zum Frühstück" von TheShadow999 '
        f'aus "Kategorie 1" in "Kategorie 2" verschoben: {expected_link}'
    )

    event = BoardTopicMoved(
        occurred_at=now(),
        initiator_id=moderator.id,
        initiator_screen_name=moderator.screen_name,
        board_id=board.id,
        topic_id=topic.id,
        topic_creator_id=creator.id,
        topic_creator_screen_name=creator.screen_name,
        topic_title=topic.title,
        old_category_id=category.id,
        old_category_title=category.title,
        new_category_id=another_category.id,
        new_category_title=another_category.title,
        moderator_id=moderator.id,
        moderator_screen_name=moderator.screen_name,
        url=expected_link,
    )

    with mocked_irc_bot() as mock:
        board_signals.topic_moved.send(None, event=event)

    assert_submitted_text(mock, expected_text)


def test_announce_posting_created(app, board, posting, creator):
    expected_link = f'http://example.com/board/postings/{posting.id}'
    expected_text = (
        'TheShadow999 hat im "ACME Entertainment Convention"-Forum '
        'auf das Thema "Brötchen zum Frühstück" '
        f'geantwortet: {expected_link}'
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
        url=expected_link,
    )

    with mocked_irc_bot() as mock:
        board_signals.posting_created.send(None, event=event)

    assert_submitted_text(mock, expected_text)


def test_announce_posting_created_on_muted_topic(app, board, posting, creator):
    expected_link = f'http://example.com/board/postings/{posting.id}'

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
        topic_muted=True,
        url=expected_link,
    )

    with mocked_irc_bot() as mock:
        board_signals.posting_created.send(None, event=event)

    assert not mock.called


def test_announce_posting_hidden(app, board, posting, creator, moderator):
    expected_link = f'http://example.com/board/postings/{posting.id}'
    expected_text = (
        'ElBosso hat im "ACME Entertainment Convention"-Forum '
        'eine Antwort von TheShadow999 '
        'im Thema "Brötchen zum Frühstück" '
        f'versteckt: {expected_link}'
    )

    event = BoardPostingHidden(
        occurred_at=now(),
        initiator_id=moderator.id,
        initiator_screen_name=moderator.screen_name,
        board_id=board.id,
        posting_id=posting.id,
        posting_creator_id=creator.id,
        posting_creator_screen_name=creator.screen_name,
        topic_id=posting.topic.id,
        topic_title=posting.topic.title,
        moderator_id=moderator.id,
        moderator_screen_name=moderator.screen_name,
        url=expected_link,
    )

    with mocked_irc_bot() as mock:
        board_signals.posting_hidden.send(None, event=event)

    assert_submitted_text(mock, expected_text)


def test_announce_posting_unhidden(app, board, posting, creator, moderator):
    expected_link = f'http://example.com/board/postings/{posting.id}'
    expected_text = (
        'ElBosso hat im "ACME Entertainment Convention"-Forum '
        'eine Antwort von TheShadow999 '
        'im Thema "Brötchen zum Frühstück" '
        f'wieder sichtbar gemacht: {expected_link}'
    )

    event = BoardPostingUnhidden(
        occurred_at=now(),
        initiator_id=moderator.id,
        initiator_screen_name=moderator.screen_name,
        board_id=board.id,
        posting_id=posting.id,
        posting_creator_id=creator.id,
        posting_creator_screen_name=creator.screen_name,
        topic_id=posting.topic.id,
        topic_title=posting.topic.title,
        moderator_id=moderator.id,
        moderator_screen_name=moderator.screen_name,
        url=expected_link,
    )

    with mocked_irc_bot() as mock:
        board_signals.posting_unhidden.send(None, event=event)

    assert_submitted_text(mock, expected_text)


# helpers


@pytest.fixture(scope='module')
def creator(make_user):
    return make_user('TheShadow999')


@pytest.fixture(scope='module')
def moderator(make_user):
    return make_user('ElBosso')


@pytest.fixture(scope='module')
def category(board):
    return _create_category(board.id, number=1)


@pytest.fixture(scope='module')
def another_category(board):
    return _create_category(board.id, number=2)


@pytest.fixture(scope='module')
def topic(category, creator):
    return _create_topic(
        category.id, creator.id, number=192, title='Brötchen zum Frühstück'
    )


@pytest.fixture(scope='module')
def posting(topic, creator):
    return _create_posting(topic.id, creator.id)


def _create_category(board_id, *, number=1):
    slug = f'category-{number}'
    title = f'Kategorie {number}'
    description = f'Hier geht es um Kategorie {number}'

    return board_category_command_service.create_category(
        board_id, slug, title, description
    )


def _create_topic(category_id, creator_id, *, number=1, title=None):
    if title is None:
        title = f'Thema {number}'
    body = f'Inhalt von Thema {number}'

    topic, _ = board_topic_command_service.create_topic(
        category_id, creator_id, title, body
    )

    return topic


def _create_posting(topic_id, creator_id, *, number=1):
    body = f'Inhalt von Beitrag {number}.'

    posting, event = board_posting_command_service.create_posting(
        topic_id, creator_id, body
    )

    return posting
