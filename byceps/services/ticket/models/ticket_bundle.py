# -*- coding: utf-8 -*-

"""
byceps.services.ticket.models.ticket_bundle
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright: 2006-2016 Jochen Kupperschmidt
:License: Modified BSD, see LICENSE for details.
"""

from datetime import datetime

from ....database import db, generate_uuid
from ....util.instances import ReprBuilder

from ...seating.models.category import Category
from ...user.models.user import User


class TicketBundle(db.Model):
    """A set of tickets of the same category and with with a common
    owner, seat manager, and user manager, respectively.
    """
    __tablename__ = 'ticket_bundles'

    id = db.Column(db.Uuid, default=generate_uuid, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    ticket_category_id = db.Column(db.Uuid, db.ForeignKey('seat_categories.id'), index=True, nullable=False)
    ticket_category = db.relationship(Category)
    ticket_quantity = db.Column(db.Integer, nullable=False)
    owned_by_id = db.Column(db.Uuid, db.ForeignKey('users.id'), index=True, nullable=False)
    owned_by = db.relationship(User, foreign_keys=[owned_by_id])
    seats_managed_by_id = db.Column(db.Uuid, db.ForeignKey('users.id'), index=True, nullable=True)
    seats_managed_by = db.relationship(User, foreign_keys=[seats_managed_by_id])
    users_managed_by_id = db.Column(db.Uuid, db.ForeignKey('users.id'), index=True, nullable=True)
    users_managed_by = db.relationship(User, foreign_keys=[users_managed_by_id])

    def __init__(self, ticket_category_id, owned_by):
        self.ticket_category_id = ticket_category_id
        self.owned_by = owned_by

    def __repr__(self):
        return ReprBuilder(self) \
            .add('id', str(self.id)) \
            .add('party', self.category.party_id) \
            .add('category', self.category.title) \
            .add_with_lookup('ticket_quantity') \
            .build()
