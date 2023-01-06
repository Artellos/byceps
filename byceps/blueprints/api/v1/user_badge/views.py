"""
byceps.blueprints.api.v1.user_badge.views
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright: 2014-2023 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

from flask import abort, request
from pydantic import ValidationError

from .....services.user import user_service
from .....services.user_badge import (
    user_badge_awarding_service,
    user_badge_service,
)
from .....signals import user_badge as user_badge_signals
from .....util.framework.blueprint import create_blueprint
from .....util.views import respond_no_content

from ...decorators import api_token_required

from .models import AwardBadgeToUserRequest


blueprint = create_blueprint('user_badge_api', __name__)


@blueprint.post('/awardings')
@api_token_required
@respond_no_content
def award_badge_to_user():
    """Award the badge to a user."""
    if not request.is_json:
        abort(415)

    try:
        req = AwardBadgeToUserRequest.parse_obj(request.get_json())
    except ValidationError as e:
        abort(400, e.json())

    badge = user_badge_service.find_badge_by_slug(req.badge_slug)
    if not badge:
        abort(400, 'Badge slug unknown')

    user = user_service.find_user(req.user_id)
    if not user:
        abort(400, 'User ID unknown')

    initiator = user_service.find_user(req.initiator_id)
    if not initiator:
        abort(400, 'Initiator ID unknown')

    _, event = user_badge_awarding_service.award_badge_to_user(
        badge.id, user.id, initiator_id=initiator.id
    )

    user_badge_signals.user_badge_awarded.send(None, event=event)
