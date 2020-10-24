import pprint
import requests
from app import shopify_api as shopify
# import shopify
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

    s = shopify.Session(shop_url, api_version)

    scope = scopes()
    permission_url = s.create_permission_url(
        scope, url_for("shopify.finalize", _external=True, _scheme='https'))

    return render_template('shopify/install.html', permission_url=permission_url)


@shopify_bp.route('/finalize')
def finalize():
    """ Generate shop token and store the shop information.

    """
    shop_url = request.args.get("shop")
    api_version = '2020-10'

    shopify.Session.setup(
        api_key=current_app.config['SHOPIFY_API_KEY'],
        secret=current_app.config['SHOPIFY_SHARED_SECRET'],
        api_version=api_version)

    s = shopify.Session(shop_url, api_version)

    token = s.request_token(request.args)

    # Add the shop to the database
    shop = Shop(shop=shop_url, token=token)
    db.session.add(shop)
    db.session.commit()

    # Get the current shop
    url = 'https://' + shop_url + '/admin/api/' + api_version + '/shop.json'

    headers = {
        "X-Shopify-Access-Token": token,
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        result = r.json()
    else:
        result = {}

    # Get the shop owner's email
    shop_id = result['shop']['id'] if 'shop' in result and 'id' in result['shop'] else None
    email = result['shop']['email'] if 'shop' in result and 'email' in result['shop'] else None

    session['shopify_url'] = shop_url
    session['shopify_token'] = token
    session['shopify_id'] = shop.id

    # return redirect(url_for('shopify.index'))
    return redirect(url_for('user.signup', shop_id=shop_id, email=email))
