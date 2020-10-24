import pprint
import requests
# from app import shopify_api as shopify_client
import shopify
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
    api_version = '2020-10'

    shopify.Session.setup(
        api_key=current_app.config['SHOPIFY_API_KEY'],
        secret=current_app.config['SHOPIFY_SHARED_SECRET'],
        api_version=api_version)

    s = shopify.Session(shop_url)

    scope = scopes()
    permission_url = s.create_permission_url(
        scope, url_for("shopify.finalize", _external=True, _scheme='https'))

    return render_template('shopify/install.html', permission_url=permission_url)


@shopify_bp.route('/finalize')
def finalize():
    """ Generate shop token and store the shop information.

    """
    shop_url = request.args.get("shop")
    shopify.Session.setup(
        api_key=current_app.config['SHOPIFY_API_KEY'],
        secret=current_app.config['SHOPIFY_SHARED_SECRET'],
        api_version='2020-10')

    shopify_session = shopify.Session(shop_url)

    token = shopify_session.request_token(request.args)

    shop = Shop(shop=shop_url, token=token)
    db.session.add(shop)
    db.session.commit()

    s = shopify.Shop.current()
    print(s)

    # s = shopify_client.Session(shop_url, shopify_session.api_version, token)
    # shopify_client.ShopifyResource.activate_session(s)
    #
    # current_shop = shopify_client.Shop.current()  # Get the current shop
    # print(current_shop)

    # email = s['email'] if 'email' in s else None

    session['shopify_url'] = shop_url
    session['shopify_token'] = token
    session['shopify_id'] = shop.id

    # return redirect(url_for('shopify.index'))
    return redirect(url_for('user.signup', shop_id=shop.id, email=None))
