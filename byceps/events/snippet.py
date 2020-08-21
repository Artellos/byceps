"""
byceps.events.snippet
~~~~~~~~~~~~~~~~~~~~~

:Copyright: 2006-2020 Jochen Kupperschmidt
:License: Modified BSD, see LICENSE for details.
"""

from dataclasses import dataclass

from ..services.snippet.transfer.models import (
    Scope,
    SnippetID,
    SnippetVersionID,
)

from .base import _BaseEvent


@dataclass(frozen=True)
class _SnippetEvent(_BaseEvent):
    snippet_id: SnippetID
    scope: Scope
    snippet_name: str


@dataclass(frozen=True)
class SnippetCreated(_SnippetEvent):
    snippet_version_id: SnippetVersionID


@dataclass(frozen=True)
class SnippetUpdated(_SnippetEvent):
    snippet_version_id: SnippetVersionID


@dataclass(frozen=True)
class SnippetDeleted(_SnippetEvent):
    pass
