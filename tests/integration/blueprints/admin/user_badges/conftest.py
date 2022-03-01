"""
:Copyright: 2014-2022 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

import pytest

from byceps.services.user_badge import badge_service

from tests.helpers import log_in_user


@pytest.fixture(scope='package')
def user_badge_admin(make_admin):
    permission_ids = {
        'admin.access',
        'user_badge.award',
        'user_badge.create',
        'user_badge.update',
        'user_badge.view',
    }
    admin = make_admin('UserBadgeAdmin', permission_ids)
    log_in_user(admin.id)
    return admin


@pytest.fixture(scope='package')
def user_badge_admin_client(make_client, admin_app, user_badge_admin):
    return make_client(admin_app, user_id=user_badge_admin.id)


@pytest.fixture(scope='module')
def badge():
    slug = 'badge-of-beauty'
    label = 'Badge of Beauty'
    image_filename = 'sooo-beautiful.svg'

    badge = badge_service.create_badge(slug, label, image_filename)

    yield badge

    badge_service.delete_badge(badge.id)
