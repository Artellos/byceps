"""
:Copyright: 2014-2023 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

from byceps.services.orga import orga_service


def test_flag_changes(brand, admin_user, user):
    assert not is_orga_for_brand(user.id, brand.id)

    orga_service.add_orga_flag(user.id, brand.id, admin_user)

    assert is_orga_for_brand(user.id, brand.id)

    orga_service.remove_orga_flag(user.id, brand.id, admin_user)

    assert not is_orga_for_brand(user.id, brand.id)


def is_orga_for_brand(user_id, brand_id) -> bool:
    return orga_service.find_orga_flag(user_id, brand_id) is not None
