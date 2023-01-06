"""
byceps.services.newsletter.types
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright: 2014-2023 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

from enum import Enum


SubscriptionState = Enum('SubscriptionState', ['requested', 'declined'])
