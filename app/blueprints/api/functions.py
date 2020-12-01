import jwt
import os
import base64
from cryptography.fernet import Fernet

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

