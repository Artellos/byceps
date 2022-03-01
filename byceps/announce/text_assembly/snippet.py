"""
byceps.announce.text_assembly.snippet
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Announce snippet events.

:Copyright: 2014-2022 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

from flask_babel import gettext, lazy_gettext

from ...events.snippet import SnippetCreated, SnippetDeleted, SnippetUpdated
from ...services.snippet.transfer.models import Scope, SnippetType

from ._helpers import get_screen_name_or_fallback, with_locale


@with_locale
def assemble_text_for_snippet_created(event: SnippetCreated) -> str:
    editor_screen_name = get_screen_name_or_fallback(
        event.initiator_screen_name
    )

    return gettext(
        '%(editor_screen_name)s has created snippet %(snippet_type)s "%(snippet_name)s" in scope "%(scope)s".',
        editor_screen_name=editor_screen_name,
        snippet_type=_get_snippet_type_label(event.snippet_type),
        snippet_name=event.snippet_name,
        scope=_get_scope_label(event.scope),
    )


@with_locale
def assemble_text_for_snippet_updated(event: SnippetUpdated) -> str:
    editor_screen_name = get_screen_name_or_fallback(
        event.initiator_screen_name
    )

    return gettext(
        '%(editor_screen_name)s has updated snippet %(snippet_type)s "%(snippet_name)s" in scope "%(scope)s".',
        editor_screen_name=editor_screen_name,
        snippet_type=_get_snippet_type_label(event.snippet_type),
        snippet_name=event.snippet_name,
        scope=_get_scope_label(event.scope),
    )


@with_locale
def assemble_text_for_snippet_deleted(event: SnippetDeleted) -> str:
    initiator_screen_name = get_screen_name_or_fallback(
        event.initiator_screen_name
    )

    return gettext(
        '%(initiator_screen_name)s has deleted snippet "%(snippet_name)s" in scope "%(scope)s".',
        initiator_screen_name=initiator_screen_name,
        snippet_name=event.snippet_name,
        scope=_get_scope_label(event.scope),
    )


# helpers


_SNIPPET_TYPE_LABELS = {
    SnippetType.document: lazy_gettext('document'),
    SnippetType.fragment: lazy_gettext('fragment'),
}


def _get_snippet_type_label(snippet_type: SnippetType) -> str:
    """Return label for snippet type."""
    return _SNIPPET_TYPE_LABELS.get(snippet_type, '?')


def _get_scope_label(scope: Scope) -> str:
    return scope.type_ + '/' + scope.name
