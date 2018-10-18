"""
byceps.blueprints.authentication.views
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright: 2006-2018 Jochen Kupperschmidt
:License: Modified BSD, see LICENSE for details.
"""

from flask import abort, current_app, g, request, url_for

from ...config import get_site_mode, get_user_registration_enabled
from ...services.authentication.exceptions import AuthenticationFailed
from ...services.authentication import service as authentication_service
from ...services.authentication.password import service as password_service
from ...services.authentication.password import \
    reset_service as password_reset_service
from ...services.authentication.session.models.current_user import CurrentUser
from ...services.authentication.session import service as session_service
from ...services.authorization import service as authorization_service
from ...services.terms import consent_service as terms_consent_service, \
    version_service as terms_version_service
from ...services.user import event_service as user_event_service
from ...services.user import service as user_service
from ...services.user_avatar import service as user_avatar_service
from ...services.verification_token import service as verification_token_service
from ...typing import UserID
from ...util.framework.blueprint import create_blueprint
from ...util.framework.flash import flash_error, flash_notice, flash_success
from ...util.framework.templating import templated
from ...util.views import redirect_to, respond_no_content

from ..authorization.registry import permission_registry
from ..core_admin.authorization import AdminPermission

from .forms import LoginForm, RequestPasswordResetForm, ResetPasswordForm, \
    UpdatePasswordForm
from . import session as user_session


blueprint = create_blueprint('authentication', __name__)


# -------------------------------------------------------------------- #
# current user


@blueprint.before_app_request
def before_request():
    is_admin_mode = _is_admin_mode()

    g.current_user = _get_current_user(is_admin_mode)


def _get_current_user(is_admin_mode: bool) -> CurrentUser:
    user = user_session.get_user()

    if user is None:
        return CurrentUser.create_anonymous()

    is_anonymous = False
    avatar_url = user_avatar_service.get_avatar_url_for_user(user.id)
    permissions = _get_permissions_for_user(user.id)

    if is_admin_mode and not _has_admin_access(permissions):
        # The user lacks the admin access permission which is
        # required to enter the admin area.
        return CurrentUser.create_anonymous()

    return CurrentUser(user, is_anonymous, avatar_url, permissions)


# -------------------------------------------------------------------- #
# log in/out


@blueprint.route('/login')
@templated
def login_form():
    """Show login form."""
    logged_in = g.current_user.is_active
    if logged_in:
        flash_notice('Du bist bereits als Benutzer "{}" angemeldet.',
                     g.current_user.screen_name)

    form = LoginForm()
    user_registration_enabled = get_user_registration_enabled()

    return {
        'logged_in': logged_in,
        'form': form,
        'user_registration_enabled': user_registration_enabled,
    }


@blueprint.route('/login', methods=['POST'])
@respond_no_content
def login():
    """Allow the user to authenticate with e-mail address and password."""
    if g.current_user.is_active:
        return

    form = LoginForm(request.form)

    screen_name = form.screen_name.data
    password = form.password.data
    permanent = form.permanent.data
    if not all([screen_name, password]):
        abort(403)

    try:
        user = authentication_service.authenticate(screen_name, password)
    except AuthenticationFailed:
        abort(403)

    in_admin_mode = _is_admin_mode()

    if in_admin_mode:
        permissions = _get_permissions_for_user(user.id)
        if not _has_admin_access(permissions):
            # The user lacks the admin access permission which is required
            # to enter the admin area.
            abort(403)

    if not in_admin_mode:
        terms_version = terms_version_service.find_current_version(g.brand_id)

        if not terms_version:
            raise Exception(
                'No terms of service defined for brand "{}", denying login.'
                .format(g.brand_id))

        if not terms_consent_service.has_user_accepted_version(user.id,
                                                               terms_version.id):
            verification_token = verification_token_service \
                .find_or_create_for_terms_consent(user.id)
            consent_form_url = url_for('terms.consent_form',
                                       version_id=terms_version.id,
                                       token=verification_token.token)
            flash_notice(
                'Bitte <a href="{}">akzeptiere zunächst die aktuellen AGB</a>.',
                consent_form_url, text_is_safe=True)
            return

    # Authorization succeeded.

    session_token = session_service.find_session_token_for_user(user.id)
    if session_token is None:
        current_app.logger.error(
            'No session token found for user %s on attempted login.', user)
        abort(500)

    _create_login_event(user.id)

    user_session.start(user.id, session_token.token, permanent=permanent)
    flash_success('Erfolgreich eingeloggt als {}.', user.screen_name)


def _create_login_event(user_id: UserID) -> None:
    data = {
        'ip_address': request.remote_addr,
    }

    user_event_service.create_event('user-logged-in', user_id, data)


@blueprint.route('/logout', methods=['POST'])
@respond_no_content
def logout():
    """Log out user by deleting the corresponding cookie."""
    user_session.end()
    flash_success('Erfolgreich ausgeloggt.')


# -------------------------------------------------------------------- #
# password update


@blueprint.route('/password/update')
@templated
def password_update_form(erroneous_form=None):
    """Show a form to update the current user's password."""
    _get_current_user_or_404()

    form = erroneous_form if erroneous_form else UpdatePasswordForm()

    return {'form': form}


@blueprint.route('/password', methods=['POST'])
def password_update():
    """Update the current user's password."""
    user = _get_current_user_or_404()

    form = UpdatePasswordForm(request.form)

    if not form.validate():
        return password_update_form(form)

    password = form.new_password.data

    password_service.update_password_hash(user.id, password, user.id)

    flash_success('Das Passwort wurde geändert.')
    return redirect_to('.login_form')


# -------------------------------------------------------------------- #
# password reset


@blueprint.route('/password/reset/request')
@templated
def request_password_reset_form(erroneous_form=None):
    """Show a form to request a password reset."""
    form = erroneous_form if erroneous_form else RequestPasswordResetForm()

    return {'form': form}


@blueprint.route('/password/reset/request', methods=['POST'])
def request_password_reset():
    """Request a password reset."""
    form = RequestPasswordResetForm(request.form)
    if not form.validate():
        return request_password_reset_form(form)

    screen_name = form.screen_name.data.strip()
    user = user_service.find_user_by_screen_name(screen_name)

    if user is None:
        flash_error('Der Benutzername "{}" ist unbekannt.', screen_name)
        return request_password_reset_form(form)

    if not user.enabled:
        flash_error('Die E-Mail-Adresse für das Benutzerkonto "{}" wurde '
                    'noch nicht bestätigt.', screen_name)
        return redirect_to('user.request_email_address_confirmation_email')

    password_reset_service.prepare_password_reset(user, g.brand_id)

    flash_success(
        'Ein Link zum Setzen eines neuen Passworts für den Benutzernamen "{}" '
        'wurde an die hinterlegte E-Mail-Adresse versendet.',
        user.screen_name)
    return request_password_reset_form()


@blueprint.route('/password/reset/token/<uuid:token>')
@templated
def password_reset_form(token, erroneous_form=None):
    """Show a form to reset the current user's password."""
    verification_token = verification_token_service \
        .find_for_password_reset_by_token(token)

    _verify_password_reset_token(verification_token)

    form = erroneous_form if erroneous_form else ResetPasswordForm()

    return {
        'form': form,
        'token': token,
    }


@blueprint.route('/password/reset/token/<uuid:token>', methods=['POST'])
def password_reset(token):
    """Reset the current user's password."""
    verification_token = verification_token_service \
        .find_for_password_reset_by_token(token)

    _verify_password_reset_token(verification_token)

    form = ResetPasswordForm(request.form)
    if not form.validate():
        return password_reset_form(token, form)

    password = form.new_password.data

    password_reset_service.reset_password(verification_token, password)

    flash_success('Das Passwort wurde geändert.')
    return redirect_to('.login_form')


def _verify_password_reset_token(verification_token):
    if verification_token is None or verification_token.is_expired:
        flash_error('Es wurde kein gültiges Token angegeben. '
                    'Ein Token ist nur 24 Stunden lang gültig.')
        abort(404)


# -------------------------------------------------------------------- #
# helpers


def _get_current_user_or_404():
    user = g.current_user
    if not user.is_active:
        abort(404)

    return user


def _get_permissions_for_user(user_id):
    permission_ids = authorization_service.get_permission_ids_for_user(user_id)
    return permission_registry.get_enum_members(permission_ids)


def _has_admin_access(permissions):
    """Return `True` if the permissions include administrator access."""
    return AdminPermission.access in permissions


def _is_admin_mode():
    return get_site_mode().is_admin()
