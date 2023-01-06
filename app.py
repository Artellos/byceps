"""
application instance
~~~~~~~~~~~~~~~~~~~~

:Copyright: 2014-2023 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

from warnings import warn

from byceps.application import create_app
from byceps.database import db
from byceps.services.brand.dbmodels.brand import DbBrand
from byceps.services.party.dbmodels.party import DbParty
from byceps.services.shop.article.dbmodels.article import DbArticle
from byceps.services.shop.order.dbmodels.line_item import DbLineItem
from byceps.services.shop.order.dbmodels.order import DbOrder
from byceps.services.shop.order import order_service
from byceps.services.shop.order.transfer.order import (
    PaymentState as OrderPaymentState,
)
from byceps.services.ticketing.ticket_service import find_ticket_by_code
from byceps.services.user.dbmodels.detail import DbUserDetail
from byceps.services.user.dbmodels.user import DbUser
from byceps.services.user import user_service


app = create_app()


if app.debug and app.config.get('DEBUG_TOOLBAR_ENABLED', False):
    try:
        from flask_debugtoolbar import DebugToolbarExtension
    except ImportError:
        warn(
            'Could not import Flask-DebugToolbar. '
            '`pip install Flask-DebugToolbar` should make it available.'
        )
    else:
        app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
        toolbar = DebugToolbarExtension(app)


@app.shell_context_processor
def extend_shell_context():
    """Provide common objects to make available in the application shell."""
    return {
        'app': app,
        'db': db,
        'DbArticle': DbArticle,
        'DbBrand': DbBrand,
        'find_order_by_order_number': order_service.find_order_by_order_number,
        'DbOrder': DbOrder,
        'DbLineItem': DbLineItem,
        'OrderPaymentState': OrderPaymentState,
        'DbParty': DbParty,
        'find_ticket_by_code': find_ticket_by_code,
        'DbUser': DbUser,
        'DbUserDetail': DbUserDetail,
        'find_db_user_by_screen_name': user_service.find_db_user_by_screen_name,
    }
