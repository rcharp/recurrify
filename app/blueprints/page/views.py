from flask import Blueprint, render_template, flash
from app.extensions import cache, timeout
from config import settings
import uuid
from app.extensions import db, csrf
from flask import redirect, url_for, request, current_app
from flask_login import current_user, login_required
import requests
import ast
import json
import traceback
from sqlalchemy import and_, exists, text
from importlib import import_module
import os
import random
from flask_cors import cross_origin
from app.blueprints.shopify.decorators import shopify_auth_required

# from app.blueprints.shopify import helpers
# from app.blueprints.shopify.shopify_client import ShopifyStoreClient
#
# from app.blueprints.shopify.config import WEBHOOK_APP_UNINSTALL_URL

page = Blueprint('page', __name__, template_folder='templates')


# ACCESS_TOKEN = None
# NONCE = None
# ACCESS_MODE = []  # Defaults to offline access mode if left blank or omitted. https://shopify.dev/concepts/about-apis/authentication#api-access-modes
# SCOPES = ['write_script_tags']  # https://shopify.dev/docs/admin-api/access-scopes


@page.route('/', methods=['GET', 'POST'])
@cross_origin()
def home():
    if current_user.is_authenticated:
        return redirect(url_for('user.settings'))

    return render_template('page/index.html', plans=settings.STRIPE_PLANS)


# @page.route('/', methods=['GET'])
# @shopify_auth_required
# def index():
#     return render_template('shopify/index.html')


# @page.route('/', methods=['GET'])
# @helpers.verify_web_call
# def shopify_index():
#     shop = request.args.get('shop')
#     global ACCESS_TOKEN, NONCE
#
#     if ACCESS_TOKEN:
#         return render_template('welcome.html', shop=shop)
#
#     # The NONCE is a single-use random value we send to Shopify so we know the next call from Shopify is valid (see #shopify_redirect)
#     #   https://en.wikipedia.org/wiki/Cryptographic_nonce
#     NONCE = uuid.uuid4().hex
#     redirect_url = helpers.generate_install_redirect_url(shop=shop, scopes=SCOPES, nonce=NONCE, access_mode=ACCESS_MODE)
#     return shopify_redirect(redirect_url, code=302)
#
#
# @page.route('/auth/callback', methods=['GET'])
# @helpers.verify_web_call
# def shopify_redirect():
#     state = request.args.get('state')
#     global NONCE, ACCESS_TOKEN
#
#     # Shopify passes our NONCE, created in #home, as the `state` parameter, we need to ensure it matches!
#     if state != NONCE:
#         return "Invalid `state` received", 400
#     NONCE = None
#
#     # Ok, NONCE matches, we can get rid of it now (a nonce, by definition, should only be used once)
#     # Using the `code` received from Shopify we can now generate an access token that is specific to the specified `shop` with the
#     #   ACCESS_MODE and SCOPES we asked for in #shopify_redirect
#     shop = request.args.get('shop')
#     code = request.args.get('code')
#     ACCESS_TOKEN = ShopifyStoreClient.authenticate(shop=shop, code=code)
#
#     # We have an access token! Now let's register a webhook so Shopify will notify us if/when the app gets uninstalled
#     # NOTE This webhook will call the #app_uninstalled function defined below
#     shopify_client = ShopifyStoreClient(shop=shop, access_token=ACCESS_TOKEN)
#     shopify_client.create_webook(address=WEBHOOK_APP_UNINSTALL_URL, topic="app/uninstalled")
#
#     redirect_url = helpers.generate_post_install_redirect_url(shop=shop)
#     return shopify_redirect(redirect_url, code=302)
#
#
# @page.route('/app_uninstalled', methods=['POST'])
# @helpers.verify_webhook_call
# def app_uninstalled():
#     # https://shopify.dev/docs/admin-api/rest/reference/events/webhook?api[version]=2020-04
#     # Someone uninstalled your app, clean up anything you need to
#     # NOTE the shop ACCESS_TOKEN is now void!
#     global ACCESS_TOKEN
#     ACCESS_TOKEN = None
#
#     webhook_topic = request.headers.get('X-Shopify-Topic')
#     webhook_payload = request.get_json()
#     # logging.error(f"webhook call received {webhook_topic}:\n{json.dumps(webhook_payload, indent=4)}")
#
#     return "OK"
#
#
# @page.route('/data_removal_request', methods=['POST'])
# @helpers.verify_webhook_call
# def data_removal_request():
#     # https://shopify.dev/tutorials/add-gdpr-webhooks-to-your-app
#     # Clear all personal information you may have stored about the specified shop
#     return "OK"


@page.route('/terms')
@cross_origin()
def terms():
    return render_template('page/terms.html')


@page.route('/privacy')
@cross_origin()
def privacy():
    return render_template('page/privacy.html')

# @page.route('/index')
# @cross_origin()
# def index():
#     return render_template('page/index.html', plans=settings.STRIPE_PLANS)
