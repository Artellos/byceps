"""
:Copyright: 2014-2023 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

from byceps.config import AppMode


def test_is_admin():
    assert AppMode.admin.is_admin()
    assert not AppMode.admin.is_base()
    assert not AppMode.admin.is_site()


def test_is_base():
    assert not AppMode.base.is_admin()
    assert AppMode.base.is_base()
    assert not AppMode.base.is_site()


def test_is_site():
    assert not AppMode.site.is_admin()
    assert not AppMode.site.is_base()
    assert AppMode.site.is_site()
