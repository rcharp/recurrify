import pprint
import requests
from sqlalchemy import exists, and_
from app import shopify_api as shopify
from .functions import rest_call, graphql_query
from flask import (
    Blueprint, render_template, current_app, request, redirect, session, flash, url_for)
from flask_login import logout_user, current_user

from app.blueprints.user.models.user import User
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
    r = url_for("shopify.finalize", _external=True, _scheme='https')

    permission_url = s.create_permission_url(
        scope, r)

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
    result = rest_call(shop_url, 'shop', token, 'get')

    # Get the shop owner's email
    shopify_id = result.json()['shop']['id'] if 'shop' in result.json() and 'id' in result.json()['shop'] else None
    email = result.json()['shop']['email'] if 'shop' in result.json() and 'email' in result.json()['shop'] else None

    if db.session.query(exists().where(and_(Shop.shopify_id == shopify_id, Shop.user_id is not None))).scalar():
        flash('There is already an account for this store. Please login or use a different store.', 'error')

        # TODO: remove this code
        s = Shop.query.filter(Shop.shopify_id == shopify_id).scalar()
        s.delete()
        # return redirect(url_for('user.login'))

    # Add the shop to the database
    shop = Shop(url=shop_url, shopify_id=shopify_id, token=token)
    shop.save()

    # Set the session
    session['shopify_url'] = shop_url
    session['shopify_email'] = email
    session['shopify_token'] = token
    session['shopify_id'] = shopify_id
    session['shop_id'] = shop.shop_id

    # Logout the user if they're logged in
    if current_user.is_authenticated:
        logout_user()

    # The user already exists in the database, so have them login
    if db.session.query(exists().where(User.email == email)).scalar():
        return redirect(url_for('user.login'))

    return redirect(url_for('user.signup'))
