import os
from simplecrypt import encrypt, decrypt


def encrypt_string(plaintext):
    key = os.environ.get('SECRET_KEY')
    ciphertext = encrypt(key, plaintext)
    return ciphertext


def decrypt_string(cipher):
    key = os.environ.get('SECRET_KEY')
    plaintext = decrypt(key, cipher).decode('utf-8')
    return plaintext
