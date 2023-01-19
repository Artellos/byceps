"""
byceps.services.authentication.api.models
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright: 2014-2023 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID

from ....typing import UserID

from ...authorization.models import PermissionID


@dataclass(frozen=True)
class ApiToken:
    id: UUID
    created_at: datetime
    creator_id: UserID
    token: str
    permissions: frozenset[PermissionID]
    description: Optional[str]
    suspended: bool
