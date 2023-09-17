"""
byceps.services.webhooks.dbmodels
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright: 2014-2023 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

from __future__ import annotations

from typing import Any, Optional, TYPE_CHECKING
from uuid import UUID

from sqlalchemy.orm import Mapped, mapped_column


if TYPE_CHECKING:
    hybrid_property = property
else:
    from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.ext.mutable import MutableDict, MutableList

from byceps.database import db
from byceps.util.uuid import generate_uuid4

from .models import EventFilters


class DbOutgoingWebhook(db.Model):
    """An outgoing webhook configuration."""

    __tablename__ = 'outgoing_webhooks'

    id: Mapped[UUID] = mapped_column(
        db.Uuid, default=generate_uuid4, primary_key=True
    )
    _event_types: Mapped[list[str]] = mapped_column(
        'event_types', MutableList.as_mutable(db.JSONB)
    )
    event_filters: Mapped[Optional[Any]] = mapped_column(  # noqa: UP007
        MutableDict.as_mutable(db.JSONB)
    )
    format: Mapped[str] = mapped_column(db.UnicodeText)
    text_prefix: Mapped[Optional[str]] = mapped_column(  # noqa: UP007
        db.UnicodeText
    )
    extra_fields: Mapped[Optional[Any]] = mapped_column(  # noqa: UP007
        MutableDict.as_mutable(db.JSONB)
    )
    url: Mapped[str] = mapped_column(db.UnicodeText)
    description: Mapped[Optional[str]] = mapped_column(  # noqa: UP007
        db.UnicodeText
    )
    enabled: Mapped[bool]

    def __init__(
        self,
        event_types: set[str],
        event_filters: EventFilters,
        format: str,
        url: str,
        enabled: bool,
        *,
        text_prefix: str | None = None,
        extra_fields: dict[str, Any] | None = None,
        description: str | None = None,
    ) -> None:
        self.event_types = event_types
        self.event_filters = event_filters
        self.format = format
        self.text_prefix = text_prefix
        self.extra_fields = extra_fields
        self.url = url
        self.description = description
        self.enabled = enabled

    @hybrid_property
    def event_types(self) -> set[str]:
        return set(self._event_types)

    @event_types.setter
    def event_types(self, event_types: set[str]) -> None:
        self._event_types = list(event_types)
