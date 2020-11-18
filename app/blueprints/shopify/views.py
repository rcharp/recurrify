import pprint
import requests
from sqlalchemy import exists, and_
from app import shopify_api as shopify
from app.blueprints.api.functions import rest_call, graphql_query
from flask import (
    Blueprint, render_template, current_app, request, redirect, session, flash, url_for)

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

    # Clear the session
    session.clear()

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

    # Get the current shop
    result = rest_call(shop_url, 'shop', token)

    # Get the shop owner's email
    shop_id = result['shop']['id'] if 'shop' in result and 'id' in result['shop'] else None
    email = result['shop']['email'] if 'shop' in result and 'email' in result['shop'] else None

    if db.session.query(exists().where(and_(Shop.shop_id == shop_id, Shop.user_id is not None))).scalar():
        flash('There is already an account for this store. Please login or use a different store.', 'error')
        return redirect(url_for('user.login'))

    # Add the shop to the database
    shop = Shop(shop=shop_url, shop_id=shop_id, token=token)
    db.session.add(shop)
    db.session.commit()

    # Set the session
    session['shopify_url'] = shop_url
    session['shopify_email'] = email
    session['shopify_token'] = token
    session['shopify_id'] = shop_id

    return redirect(url_for('user.signup'))
