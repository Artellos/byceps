"""
byceps.services.user.models.user
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright: 2014-2023 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

from __future__ import annotations
from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from typing import Any, NewType, Optional
from uuid import UUID

from ....typing import UserID


UserAvatarID = NewType('UserAvatarID', UUID)


@dataclass(frozen=True)
class User:
    id: UserID
    screen_name: Optional[str]
    suspended: bool
    deleted: bool
    locale: Optional[str]
    avatar_url: Optional[str]


@dataclass(frozen=True)
class UserEmailAddress:
    address: Optional[str]
    verified: bool


@dataclass(frozen=True)
class UserDetail:
    first_name: Optional[str]
    last_name: Optional[str]
    date_of_birth: Optional[date]
    country: Optional[str]
    zip_code: Optional[str]
    city: Optional[str]
    street: Optional[str]
    phone_number: Optional[str]
    internal_comment: Optional[str]
    extras: dict[str, Any]

    @property
    def full_name(self) -> Optional[str]:
        names = [self.first_name, self.last_name]
        return ' '.join(filter(None, names)) or None


@dataclass(frozen=True)
class UserForAdmin(User):
    created_at: datetime
    initialized: bool
    detail: UserForAdminDetail


@dataclass(frozen=True)
class UserForAdminDetail:
    full_name: Optional[str]


UserStateFilter = Enum(
    'UserStateFilter',
    [
        'none',
        'active',
        'uninitialized',
        'suspended',
        'deleted',
    ],
)
