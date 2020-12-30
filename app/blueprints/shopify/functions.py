import json
import pprint

import requests
from flask import current_app
from flask_login import current_user
from app.extensions import db
from sqlalchemy import exists, and_
from app.blueprints.shopify.models.product import SyncedProduct, Product
from app.blueprints.shopify.models.shop import Shop
from app.blueprints.shopify.models.sync import Sync
from app.blueprints.shopify.models.plan import Plan


def sync_all_products(s):
    if s is None or not s.active:
        return None

    try:
        source = Shop.query.filter(Shop.shop_id == s.source_id).scalar()
        destination = Shop.query.filter(Shop.shop_id == s.destination_id).scalar()
        if source is None or destination is None:
            return None

        # Get the product ids of the synced products from the source store
        synced_products = SyncedProduct.query.with_entities(SyncedProduct.source_product_id, SyncedProduct.destination_product_id).filter(SyncedProduct.sync_id == s.sync_id).all()
        source_product_ids = [str(x.source_product_id) for x in synced_products]
        destination_product_ids = [str(x.destination_product_id) for x in synced_products]

        # Get the source products for those ids
        source_products = get_all_products(source, True, ids=','.join(source_product_ids))

        print("Source products ids are:")
        print(','.join(source_product_ids))
        print("Source Products are:")
        pprint.pprint(source_products)

        # Get the products that are currently synced to the destination store
        vendor = source.url.replace('.myshopify.com', '')
        destination_products = get_all_products(destination, True, vendor=vendor, ids=','.join(destination_product_ids))

        print("Destination products are:")
        pprint.pprint(destination_products)

        # for product in source_products:
        #     sync_or_create_product(destination.shop_id, product, destination_products)

        return True

    except Exception as e:
        from app.blueprints.base.functions import print_traceback
        print_traceback(e)
        return False


def sync_or_create_product(destination_id, source_product, destination_products):
    try:
        # If destination store already has this product update it
        destination_product = next((x for x in destination_products if 'tags' in x and current_app.config.get("APP_NAME") + '-' + str(source_product['id']) in x['tags']), None)

        if destination_product is not None:
            try:
                update_product(destination_id, destination_product['id'], source_product)
                return destination_product['id']
            except Exception as e:
                from app.blueprints.base.functions import print_traceback
                print_traceback(e)
                return -1

        # Otherwise create it in the destination store
        else:
            return create_product(destination_id, source_product)

    except Exception as e:
        from app.blueprints.base.functions import print_traceback
        print_traceback(e)
        return None


def update_sync(sync_id, product_ids):
    try:
        count = 0
        sync = Sync.query.filter(Sync.sync_id == sync_id).scalar()
        if sync is None or not sync.active:
            return -1

        # Get the source store and destination store
        source = Shop.query.filter(Shop.shop_id == sync.source_id).scalar()
        destination = Shop.query.filter(Shop.shop_id == sync.destination_id).scalar()

        if source is None or destination is None:
            return -1

        # Get the products that are currently synced to the destination store
        vendor = source.url.replace('.myshopify.com', '')
        destination_products = get_all_products(destination, True, vendor=vendor)

        # Create the newly synced products
        for product_id in product_ids:
            try:
                # Add the product to the synced product table, if it doesn't already exist
                if not db.session.query(exists().where(SyncedProduct.source_product_id == product_id)).scalar():
                    p = SyncedProduct(product_id, None, current_user.id, source.shop_id, sync_id)
                    p.save()

                # Either sync or create the product in the destination store
                from app.blueprints.base.tasks import sync_product
                sync_product.delay(source.shop_id, destination.shop_id, product_id, destination_products)

                count += 1
            except Exception as e:
                from app.blueprints.base.functions import print_traceback
                print_traceback(e)

        # Delete the syncs that no longer exist
        from app.blueprints.base.tasks import delete_syncs

        # Get all existing synced products for this particular sync
        synced_products = SyncedProduct.query.filter(SyncedProduct.sync_id == sync_id).all()

        # Delete the unsynced products from the database
        ids_to_delete = [x.id for x in synced_products if str(x.source_product_id) not in product_ids]
        SyncedProduct.bulk_delete(ids_to_delete)

        # Delete the unsynced products from the destination store
        products_to_delete = [x.destination_product_id for x in synced_products if str(x.source_product_id) not in product_ids]
        delete_syncs.delay(destination.token, destination.url, products_to_delete)

        return count

    except Exception as e:
        from app.blueprints.base.functions import print_traceback
        print_traceback(e)
        return -1


def update_product(shop_id, destination_product_id, data):
    shop = Shop.query.filter(Shop.shop_id == shop_id).scalar()
    if shop is None:
        return

    token = shop.token
    url = shop.url

    if token is None or url is None:
        return None

    try:
        # Update the variants to not include variant IDs; overwriting the variant ID will throw an error
        if 'variants' in data and data['variants'] is not None:
            for variant in data['variants']:
                del variant['id']

        # Update the existing product
        result = rest_call(url, 'products', token, 'put', destination_product_id, data=data)

        # print("Update result is:")
        # pprint.pprint(result.json())

        if result.status_code < 400:
            r = result.json()
            if 'product' in r and 'id' in r['product']:
                return r['product']['id']
            elif 'errors' in r:
                return -1
        return None
    except Exception as e:
        from app.blueprints.base.functions import print_traceback
        print_traceback(e)
        return None


def create_product(shop_id, data):
    shop = Shop.query.filter(Shop.shop_id == shop_id).scalar()
    if shop is None:
        return

    token = shop.token
    url = shop.url

    if token is None or url is None:
        return None

    try:
        result = rest_call(url, 'products', token, 'post', data=data)

        # print("Create result is:")
        # pprint.pprint(result.json())

        if result.status_code < 400:
            r = result.json()
            if 'product' in r and 'id' in r['product']:
                return r['product']['id']
            elif 'errors' in r:
                return -1
        return None
    except Exception as e:
        from app.blueprints.base.functions import print_traceback
        print_traceback(e)
        return None


def delete_product(token, url, product_id):

    if token is None or url is None:
        return None

    try:
        result = rest_call(url, 'products', token, 'delete', product_id)
        if result.status_code == 200:
            return True
        return False
    except Exception as e:
        from app.blueprints.base.functions import print_traceback
        print_traceback(e)
        return False


def get_all_products(shop, return_json=False, vendor=None, **kwargs):
    products = list()

    if shop is None:
        return None

    token = shop.token
    url = shop.url

    if token is None or url is None:
        return None

    # Only return the products originating from the specified vendor
    result = rest_call(url, 'products', token, 'get', vendor=vendor, **kwargs)

    if result.json() is not None and 'products' in result.json():
        if return_json:
            for p in result.json()['products']:
                products.append(p)
        else:
            for p in result.json()['products']:
                product = Product(p)
                products.append(product)

    if not return_json:
        products.sort(key=lambda x: x.created, reverse=True)
    else:
        products.sort(key=lambda x: x['created_at'], reverse=True)
    return products


def get_product_count(shop):

    if shop is None:
        return None

    token = shop.token
    url = shop.url

    if token is None or url is None:
        return None

    # Return the product count
    result = rest_call(url, 'products', token, 'get', 'count')

    if result.json() is not None:
        return result.json()

    return 0


# Unused method
def get_synced_products(sync_id):
    if sync_id is None:
        return None

    s = Sync.query.filter(Sync.sync_id == sync_id).scalar()
    if s is None:
        return None

    source = Shop.query.filter(Shop.shop_id == s.source_id).scalar()
    if source is None:
        return None

    products = get_all_products(source)
    return products


def get_product_by_id(shop, product_id, return_json=False):

    if shop is None:
        return None

    token = shop.token
    url = shop.url

    if token is None or url is None:
        return None

    result = rest_call(url, 'products', token, 'get', str(product_id))

    if result.json() is not None and 'product' in result.json() and result.json()['product'] is not None:
        if not return_json:
            product = Product(result.json()['product'])
        else:
            product = result.json()['product']
        return product

    return None


# Adds the source product's id to the tag, so it can be identified for a sync
def add_source_tag(source_product, product_id):
    source_product.update({'tags': [current_app.config.get("APP_NAME") + '-' + str(product_id)]})

"""
Queries
"""


# The base rest call that returns data from Shopify's API
def rest_call(shop_url, api, token, method, *args, data=None, vendor=None, **kwargs):
    api_version = current_app.config.get('SHOPIFY_API_VERSION')
    url = 'https://' + shop_url + '/admin/api/' + api_version + '/' + api

    for arg in args:
        if arg is not None:
            url += '/' + str(arg)

    # Append json to the end of the rest call
    url += '.json?'

    if vendor is not None:
        url += '&vendor=' + str(vendor)

    if kwargs is not None:
        for k, v in kwargs.items():
            if isinstance(v, list):
                url += '&' + str(k) + '=' + ','.join(v)
            elif isinstance(v, dict):
                if 'ids' in v:
                    ids = v['ids']
                    url += '&' + k + '=' + ','.join(list(ids))
            else:
                url += '&' + str(k) + '=' + str(v)

    print("REST call url: ")
    print(url)
    headers = {
        "X-Shopify-Access-Token": token,
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    if method == 'put':
        r = requests.put(url, headers=headers, json={'product': data})
    elif method == 'post':
        r = requests.post(url, headers=headers, json={'product': data})
    elif method == 'delete':
        r = requests.delete(url, headers=headers)
    else:
        r = requests.get(url, headers=headers)

    # print(method)
    # pprint.pprint(r.json())
    # print("URL")
    # print(url)
    # print("method")
    # print(method)
    # print("R code")
    # print(r.status_code)
    # print("R json")
    # print(r.json())
    # print("----------------------------")

    result = r
    if 'Not Found' in result.json().values():
        result = None

    return result


# Unused, constructs the GraphQL query.
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


# Unused, calls the constructed GraphQL query
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