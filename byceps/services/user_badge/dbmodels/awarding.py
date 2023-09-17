"""
byceps.services.user_badge.dbmodels.awarding
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright: 2014-2023 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Mapped, mapped_column

from byceps.database import db
from byceps.services.user_badge.models import BadgeID
from byceps.typing import UserID


class DbBadgeAwarding(db.Model):
    """The awarding of a badge to a user."""

    __tablename__ = 'user_badge_awardings'

    id: Mapped[UUID] = mapped_column(db.Uuid, primary_key=True)
    badge_id: Mapped[UUID] = mapped_column(
        db.Uuid, db.ForeignKey('user_badges.id')
    )
    awardee_id: Mapped[UUID] = mapped_column(db.Uuid, db.ForeignKey('users.id'))
    awarded_at: Mapped[datetime]

    def __init__(
        self,
        awarding_id: UUID,
        badge_id: BadgeID,
        awardee_id: UserID,
        awarded_at: datetime,
    ) -> None:
        self.id = awarding_id
        self.badge_id = badge_id
        self.awardee_id = awardee_id
        self.awarded_at = awarded_at
