import json
import pprint

import requests
from flask import current_app
from flask_login import current_user

from app.blueprints.shopify.models.product import SyncedProduct, Product
from app.blueprints.shopify.models.shop import Shop
from app.blueprints.shopify.models.sync import Sync


def sync_all_products(s):
    if s is None:
        return None

    try:
        source = Shop.query.filter(Shop.shop_id == s.source_id).scalar()
        destination = Shop.query.filter(Shop.shop_id == s.destination_id).scalar()
        if source is None or destination is None:
            return None

        # Get the product ids of the synced products from the source store
        synced_products = SyncedProduct.query.with_entities(SyncedProduct.source_product_id, SyncedProduct.destination_product_id).filter(SyncedProduct.sync_id == s.sync_id).all()
        source_product_ids = [x.source_product_id for x in synced_products]
        destination_product_ids = [x.destination_product_id for x in synced_products]

        # Get the source products for those ids
        source_products = get_all_products(source, True, kwargs={'ids': source_product_ids})

        # Get the products that are currently synced to the destination store
        vendor = source.url.replace('.myshopify.com', '')
        destination_products = get_all_products(destination, True, vendor=vendor, kwargs={'ids': destination_product_ids})

        for product in source_products:
            sync_or_create(destination, product, destination_products)

        return True

    except Exception as e:
        from app.blueprints.base.functions import print_traceback
        print_traceback(e)
        return False


def sync_or_create(destination, product, destination_products):
    try:
        # Destination store already has this product, so update it
        destination_product = next(x for x in destination_products if 'tags' in x and 'recurrify-' + str(product['id']) in x['tags'])
        if destination_product is not None:
            update_product(destination, product)

        # Otherwise create it in the destination store
        else:
            product.update({'tags': ['recurrify-' + str(product['id'])]})
            create_product(destination, product)

        return True
    except Exception as e:
        from app.blueprints.base.functions import print_traceback
        print_traceback(e)
        return False


def update_sync(sync_id, product_ids):
    try:
        count = 0
        sync = Sync.query.filter(Sync.sync_id == sync_id).scalar()
        if sync is None:
            return -1

        # Get the source store and destination store
        source = Shop.query.filter(Shop.shop_id == sync.source_id).scalar()
        destination = Shop.query.filter(Shop.shop_id == sync.destination_id).scalar()

        if source is None or destination is None:
            return -1

        # Get all existing synced products for this particular sync
        s = SyncedProduct.query.with_entities(SyncedProduct.id, SyncedProduct.source_product_id).filter(SyncedProduct.sync_id == sync_id).all()

        # Delete the product syncs that no longer exist
        ids_to_delete = [x.id for x in s if x.source_product_id not in product_ids]
        SyncedProduct.bulk_delete(ids_to_delete)

        # Create the synced products
        for product_id in product_ids:

            # Get the product from the source store via its id
            product = get_product_by_id(source, product_id, return_json=True)

            # Add the identifying tag for the destination store
            product.update({'tags': ['recurrify-' + str(product['id'])]})

            # Create the product in the destination store
            #TODO: sync or create to avoid duplicating creation of products
            destination_product_id = create_product(destination, product)
            if destination_product_id is not None:
                p = SyncedProduct(product_id, destination_product_id, current_user.id, source.shop_id, sync_id)
                p.save()

                count += 1

        return count

    except Exception as e:
        from app.blueprints.base.functions import print_traceback
        print_traceback(e)
        return -1


def update_product(shop, data):
    token = shop.token
    url = shop.url

    if token is None or url is None:
        return None

    try:
        print("Updating: " + str(data['id']))
        # Update the existing product
        result = rest_call(url, 'products', token, 'put', data['id'], data=data)
        return result.json()
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

        if result.status_code < 400:
            r = result.json()
            if 'product' in r and 'id' in r['product']:
                return r['product']['id']
        return None
    except Exception as e:
        from app.blueprints.base.functions import print_traceback
        print_traceback(e)
        return None


def get_all_products(shop, return_json=False, vendor=None, **kwargs):
    products = list()

    if shop is None:
        return None

    token = shop.token
    url = shop.url

    if token is None or url is None:
        return None

    # Only return the products originating from the specified vendor
    result = rest_call(url, 'products', token, 'get', vendor=vendor, kwargs=kwargs)

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


def get_synced_products(sync_id):
    if sync_id is None:
        return None

    s = Sync.query.filter(Sync.sync_id == sync_id).scalar()
    if s is None:
        return None

    source = Shop.query.filter(Shop.shop_id == s.source_id).scalar()
    if source is None:
        return None

    product_ids = [str(x.source_product_id) for x in SyncedProduct.query.filter(SyncedProduct.sync_id == sync_id)]

    if len(product_ids) > 0:
        products = get_all_products(source, kwargs={'ids': product_ids})
    else:
        products = get_all_products(source)

    # print(products)
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

    if result.json() is not None and 'product' in result.json() and result.json()['product'] is not None:
        if not return_json:
            product = Product(result.json()['product'])
        else:
            product = result.json()['product']
        return product

    return None


"""
Queries
"""


def rest_call(shop_url, api, token, method, *args, data=None, vendor=None, kwargs=None):
    api_version = current_app.config.get('SHOPIFY_API_VERSION')
    url = 'https://' + shop_url + '/admin/api/' + api_version + '/' + api

    for arg in args:
        if arg is not None:
            url += '/' + arg

    # Append json to the end of the rest call
    url += '.json?'

    if vendor is not None:
        url += 'vendor=' + vendor

    if kwargs is not None:
        for k, v in kwargs.items():
            if isinstance(v, list):
                url += k + '=' + ','.join(v)
            elif isinstance(v, dict):
                if 'ids' in v:
                    ids = v['ids']
                    url += k + '=' + ','.join(list(ids))
            else:
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

    result = r#.json()
    if 'Not Found' in result.json().values():
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