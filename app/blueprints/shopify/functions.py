import json
import pprint

import requests
from flask import current_app

from app.blueprints.shopify.models.product import Product
from app.blueprints.shopify.models.shop import Shop


def sync_products(s):
    if s is None:
        return None

    source = Shop.query.filter(Shop.shop_id == s.source_id).scalar()
    destination = Shop.query.filter(Shop.shop_id == s.destination_id).scalar()
    if source is None or destination is None:
        return None

    try:
        vendor = source.url.replace('.myshopify.com', '')
        source_products = get_all_products(source, True)
        synced_products = get_all_products(destination, True, vendor=vendor)
        pprint.pprint(synced_products)
        for product in source_products:
            sync_or_create(product, destination)

        return True
    except Exception as e:
        from app.blueprints.base.functions import print_traceback
        print_traceback(e)
        return False


def sync_or_create(product, destination):
    # Store already has this product, so update it
    p = get_product_by_id(destination, product['id'], True, True)
    if p is not None:
        update_product(destination, product)
    else:
        product.update({'tags': ['recurrify-' + str(product['id'])]})
        create_product(destination, product)

    return


def update_product(shop, data):
    token = shop.token
    url = shop.url

    if token is None or url is None:
        return None

    try:
        print("Updating: " + str(data['id']))
        # Update the existing product
        result = rest_call(url, 'products', token, 'put', data['id'], data=data)
        return result
    except Exception as e:
        from app.blueprints.base.functions import print_traceback
        print_traceback(e)
        return None


def create_product(shop, data):
    token = shop.token
    url = shop.url

    if token is None or url is None:
        return None

    try:
        result = rest_call(url, 'products', token, 'post', data=data)
        return result
    except Exception as e:
        from app.blueprints.base.functions import print_traceback
        print_traceback(e)
        return None


def get_all_products(shop, return_json=False, vendor=None):
    products = list()

    if shop is None:
        return None

    token = shop.token
    url = shop.url

    if token is None or url is None:
        return None

    # Only return the products originating from the specified vendor
    if vendor is not None:
        result = rest_call(url, 'products', token, 'get', vendor=vendor)
    else:
        result = rest_call(url, 'products', token, 'get')

    if result is not None and 'products' in result:
        if return_json:
            for p in result['products']:
                products.append(p)
        else:
            for p in result['products']:
                product = Product(p)
                products.append(product)

    if not return_json:
        products.sort(key=lambda x: x.created, reverse=True)
    else:
        products.sort(key=lambda x: x['created_at'], reverse=True)
    return products


def get_product_by_id(shop, product_id, synced=False, return_json=False):

    if shop is None:
        return None

    token = shop.token
    url = shop.url

    if token is None or url is None:
        return None

    if synced:
        kwargs = {'tags': 'hello'}
        result = rest_call(url, 'products', token, 'get', str(product_id), **kwargs)
    else:
        result = rest_call(url, 'products', token, 'get', str(product_id))

    if result is not None and 'product' in result and result['product'] is not None:
        if not return_json:
            product = Product(result['product'])
        else:
            product = result['product']
        return product

    return None


"""
Queries
"""


def rest_call(shop_url, api, token, method, *args, data=None, vendor=None, **kwargs):
    api_version = current_app.config.get('SHOPIFY_API_VERSION')
    url = 'https://' + shop_url + '/admin/api/' + api_version + '/' + api

    for arg in args:
        if arg is not None:
            url += '/' + arg

    # Append json to the end of the rest call
    url += '.json?'

    if vendor:
        url += 'vendor=' + vendor

    for k,v in kwargs.items():
        url += k + '=' + v

    headers = {
        "X-Shopify-Access-Token": token,
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    if method == 'put':
        r = requests.put(url, headers=headers, json={'product': data})
    elif method == 'post':
        r = requests.post(url, headers=headers, json={'product': data})
    else:
        r = requests.get(url, headers=headers)

    # print("URL")
    # print(url)
    # print("method")
    # print(method)
    # print("R code")
    # print(r.status_code)
    # print("R json")
    # print(r.json())
    # print("----------------------------")

    result = r.json()
    if 'Not Found' in result.values():
        result = None

    return result


def construct_query(query, parameters):
    from app.blueprints.base.functions import print_traceback
    try:
        if not isinstance(parameters, dict):
            return None

        # Handle a dictionary of query parameters
        for k, v in parameters.items():
            query = str(k) + ' {\n'
            if isinstance(v, list):
                for item in v:
                    if isinstance(item, dict):
                        query += construct_query(query, item)
                    else:
                        query += str(item) + '\n'
            elif isinstance(v, dict):
                query += construct_query(query, v)
            else:
                query += str(v) + '\n}\n'
    except Exception as e:
        print_traceback(e)
        pass

    # Return the query string
    return query


def graphql_query(shop_url, token, parameters=None):
    from app.blueprints.base.functions import print_traceback
    try:
        api_version = current_app.config.get('SHOPIFY_API_VERSION')
        url = 'https://' + shop_url + '/admin/api/' + api_version + '/graphql.json'

        headers = {
            "X-Shopify-Access-Token": token,
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

        q = construct_query("", parameters)

        if q is not None:
            query = str('{\n' + q + '}\n}')
            print(query)

            r = requests.post(url, json={'query': query}, headers=headers)
            result = json.dumps(json.loads(r.text), indent=3)
            print(result)

            return result
        return None
    except Exception as e:
        print_traceback(e)
        return None