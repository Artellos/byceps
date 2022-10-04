"""
byceps.blueprints.admin.user_badge.views
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright: 2014-2022 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

from flask import abort, g, request
from flask_babel import gettext

from ....services.brand import service as brand_service
from ....services.user import user_service
from ....services.user_badge import (
    user_badge_awarding_service,
    user_badge_service,
)
from ....signals import user_badge as user_badge_signals
from ....util.framework.blueprint import create_blueprint
from ....util.framework.flash import flash_success
from ....util.framework.templating import templated
from ....util.views import permission_required, redirect_to

from .forms import AwardForm, CreateForm, UpdateForm


blueprint = create_blueprint('user_badge_admin', __name__)


# -------------------------------------------------------------------- #
# badges


@blueprint.get('/badges')
@permission_required('user_badge.view')
@templated
def index():
    """List all badges."""
    all_badges = user_badge_service.get_all_badges()

    brands = brand_service.get_all_brands()
    brands_by_id = {brand.id: brand for brand in brands}

    def _find_brand(brand_id):
        if brand_id is None:
            return None

        return brands_by_id[brand_id]

    awarding_counts_by_badge_id = user_badge_awarding_service.count_awardings()

    badges = [
        {
            'id': badge.id,
            'slug': badge.slug,
            'label': badge.label,
            'image_url_path': badge.image_url_path,
            'brand': _find_brand(badge.brand_id),
            'featured': badge.featured,
            'awarding_count': awarding_counts_by_badge_id[badge.id],
        }
        for badge in all_badges
    ]

    return {
        'badges': badges,
    }


@blueprint.get('/badges/<uuid:badge_id>')
@permission_required('user_badge.view')
@templated
def view(badge_id):
    """Show badge details."""
    badge = _get_badge_or_404(badge_id)

    if badge.brand_id:
        brand = brand_service.find_brand(badge.brand_id)
    else:
        brand = None

    awardings = user_badge_awarding_service.get_awardings_of_badge(badge.id)
    recipient_ids = [awarding.user_id for awarding in awardings]
    recipients = user_service.get_users(recipient_ids, include_avatars=True)
    recipients = list(sorted(recipients, key=lambda r: r.screen_name or ''))

    return {
        'badge': badge,
        'brand': brand,
        'recipients': recipients,
    }


@blueprint.get('/create')
@permission_required('user_badge.create')
@templated
def create_form(erroneous_form=None):
    """Show form to create a user badge."""
    form = erroneous_form if erroneous_form else CreateForm()
    _set_brand_ids_on_form(form)

    return {
        'form': form,
    }


@blueprint.post('/badges')
@permission_required('user_badge.create')
def create():
    """Create a user badge."""
    form = CreateForm(request.form)
    _set_brand_ids_on_form(form)

    if not form.validate():
        return create_form(form)

    slug = form.slug.data.strip()
    label = form.label.data.strip()
    description = form.description.data.strip()
    image_filename = form.image_filename.data.strip()
    brand_id = form.brand_id.data
    featured = form.featured.data

    if brand_id:
        brand = brand_service.find_brand(brand_id)
        brand_id = brand.id
    else:
        brand_id = None

    badge = user_badge_service.create_badge(
        slug,
        label,
        image_filename,
        description=description,
        brand_id=brand_id,
        featured=featured,
    )

    flash_success(
        gettext(
            'Badge "%(badge_label)s" has been created.',
            badge_label=badge.label,
        )
    )
    return redirect_to('.index')


@blueprint.get('/badges/<uuid:badge_id>/update')
@permission_required('user_badge.update')
@templated
def update_form(badge_id, erroneous_form=None):
    """Show form to update a badge."""
    badge = _get_badge_or_404(badge_id)

    form = erroneous_form if erroneous_form else UpdateForm(obj=badge)
    _set_brand_ids_on_form(form)

    return {
        'badge': badge,
        'form': form,
    }


@blueprint.post('/badges/<uuid:badge_id>')
@permission_required('user_badge.update')
def update(badge_id):
    """Update a badge."""
    badge = _get_badge_or_404(badge_id)

    form = UpdateForm(request.form)
    _set_brand_ids_on_form(form)
    if not form.validate():
        return update_form(badge.id, form)

    slug = form.slug.data.strip()
    label = form.label.data.strip()
    description = form.description.data.strip()
    image_filename = form.image_filename.data.strip()
    brand_id = form.brand_id.data
    featured = form.featured.data

    badge = user_badge_service.update_badge(
        badge.id, slug, label, description, image_filename, brand_id, featured
    )

    flash_success(
        gettext(
            'Badge "%(badge_label)s" has been updated.',
            badge_label=badge.label,
        )
    )
    return redirect_to('.view', badge_id=badge_id)


def _set_brand_ids_on_form(form):
    brands = brand_service.get_all_brands()
    form.set_brand_choices(brands)


# -------------------------------------------------------------------- #
# awarding


@blueprint.get('/awardings/to/<uuid:user_id>')
@permission_required('user_badge.award')
@templated
def award_form(user_id, erroneous_form=None):
    """Show form to award a badge to a user."""
    user = user_service.find_user(user_id)
    if not user:
        abort(404)

    form = erroneous_form if erroneous_form else AwardForm(user_id=user.id)
    _set_badge_ids_on_form(form)

    return {
        'form': form,
        'user': user,
    }


@blueprint.post('/awardings/to/<uuid:user_id>')
@permission_required('user_badge.award')
def award(user_id):
    """Award a badge to a user."""
    form = AwardForm(request.form)
    _set_badge_ids_on_form(form)

    if not form.validate():
        return award_form(user_id, form)

    badge_id = form.badge_id.data

    user = user_service.find_user(user_id)
    if not user:
        abort(401, 'Unknown user ID')

    badge = user_badge_service.find_badge(badge_id)
    if not badge:
        abort(401, 'Unknown badge ID')

    initiator_id = g.user.id

    _, event = user_badge_awarding_service.award_badge_to_user(
        badge_id, user_id, initiator_id=initiator_id
    )

    flash_success(
        gettext(
            'Badge "%(badge_label)s" has been awarded to %(screen_name)s.',
            badge_label=badge.label,
            screen_name=user.screen_name,
        )
    )

    user_badge_signals.user_badge_awarded.send(None, event=event)

    return redirect_to('user_admin.view', user_id=user.id)


def _set_badge_ids_on_form(form):
    badges = user_badge_service.get_all_badges()
    form.set_badge_choices(badges)


# -------------------------------------------------------------------- #
# helpers


def _get_badge_or_404(badge_id):
    badge = user_badge_service.find_badge(badge_id)

    if badge is None:
        abort(404)

    return badge
