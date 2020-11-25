from functools import wraps
from typing import List
import logging

import re
import hmac
import base64
import hashlib
from flask import request, abort, current_app


def generate_install_redirect_url(shop: str, scopes: List, nonce: str, access_mode: List):
    SHOPIFY_API_KEY = current_app.config['SHOPIFY_API_KEY']
    INSTALL_REDIRECT_URL = current_app.config['INSTALL_REDIRECT_URL']

    scopes_string = ','.join(scopes)
    access_mode_string = ','.join(access_mode)
    redirect_url = "https://" + shop + "/admin/oauth/authorize?client_id=" + SHOPIFY_API_KEY + "&scope=" + scopes_string + "&redirect_uri=" + INSTALL_REDIRECT_URL + "&state=" + nonce + "&grant_options[]=" + access_mode_string
    return redirect_url


def generate_post_install_redirect_url(shop: str):
    APP_NAME = current_app.config['APP_NAME']
    redirect_url = "https://" + shop + "/admin/apps/" + APP_NAME
    return redirect_url


def verify_web_call(f):
    @wraps(f)
    def wrapper(*args, **kwargs) -> bool:
        get_args = request.args
        hmac = get_args.get('hmac')
        sorted(get_args)
        data = '&'.join([f'{key}={value}' for key, value in get_args.items() if key != 'hmac']).encode('utf-8')
        if not verify_hmac(data, hmac):
            logging.error(f"HMAC could not be verified: \n\thmac {hmac}\n\tdata {data}")
            abort(400)

        shop = get_args.get('shop')
        if shop and not is_valid_shop(shop):
            logging.error(f"Shop name received is invalid: \n\tshop {shop}")
            abort(401)
        return f(*args, **kwargs)

    return wrapper


def verify_webhook_call(f):
    @wraps(f)
    def wrapper(*args, **kwargs) -> bool:
        encoded_hmac = request.headers.get('X-Shopify-Hmac-Sha256')
        hmac = base64.b64decode(encoded_hmac).hex()

        data = request.get_data()
        if not verify_hmac(data, hmac):
            logging.error(f"HMAC could not be verified: \n\thmac {hmac}\n\tdata {data}")
            abort(401)
        return f(*args, **kwargs)

    return wrapper


def verify_hmac(data: bytes, orig_hmac: str):
    SHOPIFY_SECRET = current_app.config['SHOPIFY_SECRET']
    new_hmac = hmac.new(
        SHOPIFY_SECRET.encode('utf-8'),
        data,
        hashlib.sha256
    )
    return new_hmac.hexdigest() == orig_hmac


def is_valid_shop(shop: str) -> bool:
    # Shopify docs give regex with protocol required, but shop never includes protocol
    shopname_regex = r'[a-zA-Z0-9][a-zA-Z0-9\-]*\.myshopify\.com[\/]?'
    return re.match(shopname_regex, shop)


def scopes():
    return ["read_products",
            "write_products",
            "read_script_tags",
            "write_script_tags",
            "read_customers",
            "write_customers",
            "read_orders",
            "write_orders",
            "read_all_orders",
            "read_inventory",
            "read_analytics",
            "read_price_rules",
            "write_price_rules",
            "read_discounts",
            "write_discounts",
            "read_shopify_payments_payouts",
            "read_shopify_payments_disputes"]
