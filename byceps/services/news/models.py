"""
byceps.services.news.models
~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright: 2014-2023 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import NewType
from uuid import UUID

from byceps.services.user.models.user import User
from byceps.typing import BrandID, UserID
from byceps.util.result import Result


NewsChannelID = NewType('NewsChannelID', str)


NewsItemID = NewType('NewsItemID', UUID)


NewsItemVersionID = NewType('NewsItemVersionID', UUID)


NewsImageID = NewType('NewsImageID', UUID)


BodyFormat = Enum('BodyFormat', ['html', 'markdown'])


@dataclass(frozen=True)
class NewsChannel:
    id: NewsChannelID
    brand_id: BrandID
    # Should be `SiteID` instead of `str`,
    # but circular imports prevent this.
    announcement_site_id: str | None
    archived: bool


@dataclass(frozen=True)
class NewsImage:
    id: NewsImageID
    created_at: datetime
    creator_id: UserID
    item_id: NewsItemID
    number: int
    filename: str
    url_path: str
    alt_text: str | None
    caption: str | None
    attribution: str | None


@dataclass(frozen=True)
class NewsItem:
    id: NewsItemID
    channel: NewsChannel
    slug: str
    published_at: datetime | None
    published: bool
    title: str
    body: str
    body_format: BodyFormat
    images: list[NewsImage]
    featured_image: NewsImage | None


@dataclass(frozen=True)
class RenderedNewsItem:
    channel: NewsChannel
    slug: str
    published_at: datetime | None
    published: bool
    title: str
    featured_image_html: Result[str | None, str]
    body_html: Result[str, str]


@dataclass(frozen=True)
class NewsHeadline:
    slug: str
    published_at: datetime | None
    published: bool
    title: str


@dataclass(frozen=True)
class NewsTeaser(NewsHeadline):
    featured_image: NewsImage | None


@dataclass(frozen=True)
class AdminListNewsItem:
    id: NewsItemID
    created_at: datetime
    creator: User
    slug: str
    title: str
    image_total: int
    featured_image: NewsImage | None
    published: bool
