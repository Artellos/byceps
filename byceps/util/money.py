"""
byceps.util.money
~~~~~~~~~~~~~~~~~

Handle monetary amounts.

:Copyright: 2006-2021 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

from decimal import Decimal

from flask_babel import format_currency


def format_euro_amount(number: Decimal) -> str:
    """Return a locale-specific textual representation of the amount and
    the currency.
    """
    return format_currency(number, 'EUR')
