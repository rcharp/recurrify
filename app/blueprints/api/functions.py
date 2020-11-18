import jwt
import requests
import json
import os
import base64
from flask import current_app
from cryptography.fernet import Fernet
from requests.exceptions import ConnectionError


# Tokens ###########################################
'''
Create a token for the user using JWT
'''


def create_user_token(user, key):
    user = {
        'email': user.email,
        'id': user.id,
        'name': user.name,
    }
    return jwt.encode(user, key, algorithm='HS256')


'''
Decrypt the passed user token using JWT
'''


def decrypt_user_token(token, key):
    return jwt.decode(token, key, verify=True)


'''
Create a general token for plaintext
'''


def serialize_token(plaintext):
    data = {
        'value': plaintext
    }
    return jwt.encode(data, os.environ.get('SECRET_KEY'), algorithm='HS256')


'''
Deserialize a token
'''


def deserialize_token(token):
    return jwt.decode(token, os.environ.get('SECRET_KEY'), algorithms=['HS256'], verify=True)


def encrypt_string(plaintext):
    key = base64.urlsafe_b64encode(bytes(os.environ.get('SECRET_KEY'), 'utf-8'))
    f = Fernet(key)
    encoded = f.encrypt(bytes(plaintext, 'utf-8'))
    return encoded


def decrypt_string(b):
    key = base64.urlsafe_b64encode(bytes(os.environ.get('SECRET_KEY'), 'utf-8'))
    print(key)
    print(type(key))
    f = Fernet(key)
    plaintext = f.decrypt(b)
    return plaintext


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


# noinspection PyBroadException
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


def rest_call(shop_url, api, token):
    api_version = current_app.config.get('SHOPIFY_API_VERSION')
    url = 'https://' + shop_url + '/admin/api/' + api_version + '/' + api + '.json'

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
    return result
