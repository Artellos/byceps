"""
:Copyright: 2014-2023 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from flask import Flask
from moneyed import EUR
import pytest

from byceps.services.authz import authz_service
from byceps.services.authz.models import PermissionID, Role, RoleID
from byceps.services.board import board_service
from byceps.services.board.models import Board, BoardID
from byceps.services.brand import brand_service
from byceps.services.brand.models import Brand, BrandID
from byceps.services.email import email_config_service
from byceps.services.email.models import EmailConfig
from byceps.services.language import language_service
from byceps.services.news import news_channel_service
from byceps.services.news.models import NewsChannel, NewsChannelID
from byceps.services.party.models import Party
from byceps.services.shop.article.models import Article
from byceps.services.shop.order import order_sequence_service
from byceps.services.shop.order.models.number import (
    OrderNumberSequence,
    OrderNumberSequenceID,
)
from byceps.services.shop.order.models.order import Orderer
from byceps.services.shop.shop import shop_service
from byceps.services.shop.shop.models import Shop, ShopID
from byceps.services.shop.storefront import storefront_service
from byceps.services.shop.storefront.models import (
    Storefront,
    StorefrontID,
)
from byceps.services.site.models import Site, SiteID
from byceps.services.ticketing import ticket_category_service
from byceps.services.ticketing.models.ticket import TicketCategory
from byceps.services.user.models.user import User
from byceps.typing import PartyID, UserID

from tests.helpers import (
    create_admin_app,
    create_party,
    create_role_with_permissions_assigned,
    create_site,
    create_site_app,
    create_user,
    generate_token,
    http_client,
)
from tests.helpers.shop import create_article, create_orderer

from .database import set_up_database, tear_down_database  # noqa: F401


_CONFIG_PATH_DATA_KEY = 'PATH_DATA'


@pytest.fixture(scope='session')
def make_admin_app(data_path: Path):
    """Provide the admin web application."""

    def _wrapper(**config_overrides: Any) -> Flask:
        if _CONFIG_PATH_DATA_KEY not in config_overrides:
            config_overrides[_CONFIG_PATH_DATA_KEY] = data_path
        return create_admin_app(config_overrides)

    return _wrapper


@pytest.fixture(scope='session')
def admin_app(make_admin_app) -> Iterator[Flask]:
    """Provide the admin web application."""
    app = make_admin_app()
    with app.app_context():
        tear_down_database()
        set_up_database()

        for code in 'en', 'de':
            language_service.create_language(code)

        authz_service.create_role(RoleID('board_user'), 'Board User')

        yield app


@pytest.fixture(scope='session')
def make_site_app(admin_app, data_path):
    """Provide a site web application."""

    def _wrapper(site_id: SiteID, **config_overrides: dict[str, Any]) -> Flask:
        if _CONFIG_PATH_DATA_KEY not in config_overrides:
            config_overrides[_CONFIG_PATH_DATA_KEY] = data_path
        return create_site_app(site_id, config_overrides)

    return _wrapper


@pytest.fixture(scope='session')
def site_app(make_site_app, site: Site) -> Flask:
    """Provide a site web application."""
    app = make_site_app(site.id)
    with app.app_context():
        return app


@pytest.fixture(scope='session')
def data_path() -> Path:
    with TemporaryDirectory() as d:
        return Path(d)


@pytest.fixture(scope='package')
def make_client():
    """Provide a test HTTP client against the application."""

    def _wrapper(app: Flask, *, user_id: UserID | None = None):
        with http_client(app, user_id=user_id) as client:
            return client

    return _wrapper


@pytest.fixture(scope='session')
def make_role(admin_app: Flask):
    def _wrapper() -> Role:
        role_id = generate_token()
        return authz_service.create_role(role_id, role_id).unwrap()

    return _wrapper


@pytest.fixture(scope='session')
def make_user(admin_app: Flask):
    def _wrapper(*args, **kwargs) -> User:
        return create_user(*args, **kwargs)

    return _wrapper


@pytest.fixture(scope='session')
def make_admin(make_user):
    def _wrapper(permission_id_strs: set[str], *args, **kwargs) -> User:
        admin = make_user(*args, **kwargs)

        # Create role.
        role_id = RoleID(f'admin_{generate_token()}')
        permission_ids = [PermissionID(p_id) for p_id in permission_id_strs]
        create_role_with_permissions_assigned(role_id, permission_ids)

        # Assign role to user.
        authz_service.assign_role_to_user(role_id, admin)

        return admin

    return _wrapper


@pytest.fixture(scope='session')
def admin_user(make_admin) -> User:
    permission_ids = {'admin.access'}
    return make_admin(permission_ids, screen_name='Admin')


@pytest.fixture(scope='session')
def user(make_user) -> User:
    return make_user('User')


@pytest.fixture(scope='session')
def uninitialized_user(make_user) -> User:
    return make_user('UninitializedUser', initialized=False)


@pytest.fixture(scope='session')
def suspended_user(make_user) -> User:
    return make_user('SuspendedUser', suspended=True)


@pytest.fixture(scope='session')
def deleted_user(make_user) -> User:
    return make_user('DeletedUser', deleted=True)


@pytest.fixture(scope='session')
def make_email_config(admin_app: Flask):
    def _wrapper(
        brand_id: BrandID,
        *,
        sender_address: str | None = None,
        sender_name: str | None = None,
        contact_address: str | None = None,
    ) -> EmailConfig:
        if sender_address is None:
            sender_address = f'{generate_token()}@domain.example'

        email_config_service.set_config(
            brand_id,
            sender_address,
            sender_name=sender_name,
            contact_address=contact_address,
        )

        return email_config_service.get_config(brand_id)

    return _wrapper


@pytest.fixture(scope='session')
def email_config(make_email_config, brand: Brand) -> EmailConfig:
    return make_email_config(
        brand.id,
        sender_address='noreply@acmecon.test',
        sender_name='ACME Entertainment Convention',
        contact_address='help@acmecon.test',
    )


@pytest.fixture(scope='session')
def site(email_config: EmailConfig, party: Party, board: Board) -> Site:
    return create_site(
        SiteID('acmecon-2014-website'),
        party.brand_id,
        title='ACMECon 2014 website',
        server_name='www.acmecon.test',
        party_id=party.id,
        board_id=board.id,
    )


@pytest.fixture(scope='session')
def make_brand(admin_app: Flask):
    def _wrapper(
        brand_id: BrandID | None = None, title: str | None = None
    ) -> Brand:
        if brand_id is None:
            brand_id = BrandID(generate_token())

        if title is None:
            title = brand_id

        return brand_service.create_brand(brand_id, title)

    return _wrapper


@pytest.fixture(scope='session')
def brand(make_brand) -> Brand:
    return make_brand('acmecon', 'ACME Entertainment Convention')


@pytest.fixture(scope='session')
def make_party(admin_app: Flask):
    def _wrapper(*args, **kwargs) -> Party:
        return create_party(*args, **kwargs)

    return _wrapper


@pytest.fixture(scope='session')
def party(make_party, brand: Brand) -> Party:
    return make_party(brand.id, title='ACMECon 2014')


@pytest.fixture(scope='session')
def make_ticket_category(admin_app: Flask):
    def _wrapper(party_id: PartyID, title: str) -> TicketCategory:
        return ticket_category_service.create_category(party_id, title)

    return _wrapper


@pytest.fixture(scope='session')
def board(brand: Brand) -> Board:
    board_id = BoardID(generate_token())
    return board_service.create_board(brand, board_id)


@pytest.fixture()
def make_news_channel():
    def _wrapper(
        brand: Brand,
        channel_id: NewsChannelID | None = None,
        *,
        announcement_site_id: SiteID | None = None,
    ) -> NewsChannel:
        if channel_id is None:
            channel_id = NewsChannelID(generate_token())

        return news_channel_service.create_channel(
            brand, channel_id, announcement_site_id=announcement_site_id
        )

    return _wrapper


@pytest.fixture(scope='session')
def make_shop(admin_app: Flask):
    def _wrapper(
        brand_id: BrandID,
        *,
        shop_id: ShopID | None = None,
        title: str | None = None,
    ) -> Shop:
        if shop_id is None:
            shop_id = ShopID(generate_token())

        if title is None:
            title = shop_id

        return shop_service.create_shop(shop_id, brand_id, title, EUR)

    return _wrapper


@pytest.fixture(scope='session')
def make_order_number_sequence():
    def _wrapper(
        shop_id: ShopID,
        *,
        prefix: str | None = None,
        value: int | None = None,
    ) -> OrderNumberSequence:
        if prefix is None:
            prefix = f'{generate_token()}-O'

        return order_sequence_service.create_order_number_sequence(
            shop_id, prefix, value=value
        ).unwrap()

    return _wrapper


@pytest.fixture(scope='session')
def make_storefront():
    def _wrapper(
        shop_id: ShopID, order_number_sequence_id: OrderNumberSequenceID
    ) -> Storefront:
        storefront_id = StorefrontID(generate_token())
        return storefront_service.create_storefront(
            storefront_id, shop_id, order_number_sequence_id, closed=False
        )

    return _wrapper


@pytest.fixture(scope='session')
def make_article():
    def _wrapper(shop_id: ShopID, **kwargs) -> Article:
        return create_article(shop_id, **kwargs)

    return _wrapper


@pytest.fixture(scope='session')
def make_orderer():
    def _wrapper(user: User) -> Orderer:
        return create_orderer(user)

    return _wrapper
