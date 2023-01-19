"""
byceps.services.user.dbmodels.log
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright: 2014-2023 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

from datetime import datetime

from ....database import db, generate_uuid
from ....typing import UserID
from ....util.instances import ReprBuilder

from ..models.log import UserLogEntryData


class DbUserLogEntry(db.Model):
    """A log entry regarding a user."""

    __tablename__ = 'user_log_entries'

    id = db.Column(db.Uuid, default=generate_uuid, primary_key=True)
    occurred_at = db.Column(db.DateTime, nullable=False)
    event_type = db.Column(db.UnicodeText, index=True, nullable=False)
    user_id = db.Column(
        db.Uuid, db.ForeignKey('users.id'), index=True, nullable=False
    )
    data = db.Column(db.JSONB)

    def __init__(
        self,
        occurred_at: datetime,
        event_type: str,
        user_id: UserID,
        data: UserLogEntryData,
    ) -> None:
        self.occurred_at = occurred_at
        self.event_type = event_type
        self.user_id = user_id
        self.data = data

    def __repr__(self) -> str:
        return (
            ReprBuilder(self)
            .add_custom(repr(self.event_type))
            .add_with_lookup('user_id')
            .add_with_lookup('data')
            .build()
        )
