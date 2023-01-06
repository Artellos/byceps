"""
:Copyright: 2014-2023 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

from byceps.database import db


def set_up_database() -> None:
    # Learn about all tables to also drop old ones no longer
    # defined in models.
    db.reflect()

    db.drop_all()

    db.create_all()


def tear_down_database() -> None:
    db.session.remove()
    db.drop_all()
