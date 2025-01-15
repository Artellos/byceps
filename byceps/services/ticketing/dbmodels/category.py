"""
byceps.services.ticketing.dbmodels.category
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright: 2014-2025 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

from sqlalchemy.orm import Mapped, mapped_column

from byceps.database import db
from byceps.services.party.models import PartyID
from byceps.services.ticketing.models.ticket import TicketCategoryID
from byceps.util.instances import ReprBuilder


class DbTicketCategory(db.Model):
    """A ticket category."""

    __tablename__ = 'ticket_categories'
    __table_args__ = (db.UniqueConstraint('party_id', 'title'),)

    id: Mapped[TicketCategoryID] = mapped_column(db.Uuid, primary_key=True)
    party_id: Mapped[PartyID] = mapped_column(
        db.UnicodeText, db.ForeignKey('parties.id'), index=True
    )
    title: Mapped[str] = mapped_column(db.UnicodeText)

    def __init__(
        self, category_id: TicketCategoryID, party_id: PartyID, title: str
    ) -> None:
        self.id = category_id
        self.party_id = party_id
        self.title = title

    def __repr__(self) -> str:
        return (
            ReprBuilder(self)
            .add('id', str(self.id))
            .add('party', self.party_id)
            .add_with_lookup('title')
            .build()
        )
