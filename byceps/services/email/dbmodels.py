"""
byceps.services.email.dbmodels
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright: 2014-2023 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

from __future__ import annotations

from byceps.database import db
from byceps.typing import BrandID
from byceps.util.instances import ReprBuilder


class DbEmailConfig(db.Model):
    """An e-mail configuration."""

    __tablename__ = 'email_configs'

    brand_id = db.Column(
        db.UnicodeText, db.ForeignKey('brands.id'), primary_key=True
    )
    sender_address = db.Column(db.UnicodeText, nullable=False)
    sender_name = db.Column(db.UnicodeText, nullable=True)
    contact_address = db.Column(db.UnicodeText, nullable=True)

    def __init__(
        self,
        brand_id: BrandID,
        sender_address: str,
        *,
        sender_name: str | None = None,
        contact_address: str | None = None,
    ) -> None:
        self.brand_id = brand_id
        self.sender_address = sender_address
        self.sender_name = sender_name
        self.contact_address = contact_address

    def __repr__(self) -> str:
        return ReprBuilder(self).add_with_lookup('brand_id').build()
