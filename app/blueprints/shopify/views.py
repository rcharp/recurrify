import pprint

from app import shopify_api as shopify_client
from flask import (
    Blueprint, render_template, current_app, request, redirect, session,
    url_for)

from app.blueprints.shopify.models.shop import Shop
from .decorators import shopify_auth_required
from .helpers import scopes
from app.extensions import db

shopify_bp = Blueprint('shopify', __name__, template_folder='templates', url_prefix='/shopify')


@shopify_bp.route('/')
@shopify_auth_required
def index():
    """ Render the index page of our application.
    """

    return render_template('shopify/index.html')


@shopify_bp.route('/install')
def install():
    """ Redirect user to permission authorization page.
    """

    shop_url = request.args.get("shop")
    # api_version = '2020-10'

    shopify_client.Session.setup(
        api_key=current_app.config['SHOPIFY_API_KEY'],
        secret=current_app.config['SHOPIFY_SHARED_SECRET'])

    s = shopify_client.Session(shop_url)

    scope = scopes()
    permission_url = s.create_permission_url(
        scope, url_for("shopify.finalize", _external=True, _scheme='https'))

    print(permission_url)

    return render_template('shopify/install.html', permission_url=permission_url)


@shopify_bp.route('/finalize')
def finalize():
    """ Generate shop token and store the shop information.

    """

    shop_url = request.args.get("shop")
    shopify_client.Session.setup(
        api_key=current_app.config['SHOPIFY_API_KEY'],
        secret=current_app.config['SHOPIFY_SHARED_SECRET'])
    shopify_session = shopify_client.Session(shop_url)

    token = shopify_session.request_token(request.args)

    shop = Shop(shop=shop_url, token=token)
    db.session.add(shop)
    db.session.commit()

    session['shopify_url'] = shop_url
    session['shopify_token'] = token
    session['shopify_id'] = shop.id

    return redirect(url_for('shopify.index'))