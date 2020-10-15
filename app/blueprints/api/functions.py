import jwt
import requests
import os
import base64
from flask import current_app
from simplecrypt import encrypt, decrypt
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


def site_exists(domain):
    from app.blueprints.base.functions import print_traceback
    url = 'https://' + domain + '.recurrify.io/dashboard'
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36', }

    try:
        r = requests.post(url, headers=headers, verify=False)
        print(r.status_code)
        if r.status_code < 400:
            return True
    except ConnectionError as c:
        print_traceback(c)
        return False
    except Exception as e:
        print_traceback(e)
        return False
    else:
        return True

