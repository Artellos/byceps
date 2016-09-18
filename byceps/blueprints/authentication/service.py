# -*- coding: utf-8 -*-

"""
byceps.blueprints.authentication.service
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright: 2006-2016 Jochen Kupperschmidt
:License: Modified BSD, see LICENSE for details.
"""

from uuid import uuid4

from werkzeug.security import check_password_hash as _check_password_hash, \
    generate_password_hash as _generate_password_hash


PASSWORD_HASH_ITERATIONS = 50000
PASSWORD_HASH_METHOD = 'pbkdf2:sha1:%d' % PASSWORD_HASH_ITERATIONS


def generate_password_hash(password):
    """Generate a salted hash value based on the password."""
    return _generate_password_hash(password, method=PASSWORD_HASH_METHOD)


def update_password_hash(user, password):
    """Update the password hash and set a newly-generated authentication
    token for the user.
    """
    password_hash = generate_password_hash(password)

    user.password_hash = password_hash
    _set_new_auth_token(user)


def _set_new_auth_token(user):
    """Generate and store a new authentication token for the user."""
    user.auth_token = _generate_auth_token()


def _generate_auth_token():
    """Generate an authentication token."""
    return uuid4()


def is_password_valid_for_user(user, password):
    """Return `True` if the password is valid for the user, or `False`
    otherwise.
    """
    return check_password_hash(user.password_hash, password)


def check_password_hash(password_hash, password):
    """Hash the password and return `True` if the result matches the
    given hash, `False` otherwise.
    """
    return (password_hash is not None) \
        and _check_password_hash(password_hash, password)


class AuthenticationFailed(Exception):
    pass


def authenticate(user, password):
    """Try to authenticate the user.

    Return the user object on success, or raise an exception on failure.
    """
    if not is_password_valid_for_user(user, password):
        # Password does not match.
        raise AuthenticationFailed()

    if not user.is_active:
        # User account is disabled.
        raise AuthenticationFailed()

    return user
