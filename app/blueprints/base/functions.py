import string
import random
import pytz
import names
import traceback
from datetime import datetime as dt
from app.extensions import db
from sqlalchemy import exists, and_
from app.blueprints.page.date import get_year_date_string
from app.blueprints.user.models.user import User


# Pagination
def get_pagination(products, offset, page):
    pagination = products[page * offset - offset:page * offset]
    start = page * offset - offset + 1
    finish = len(products) if len(products) < start + offset - 1 else start + offset - 1
    pages = int(len(products) / offset) + 1 if len(products) % offset != 0 else int(len(products) / offset)

    return start, finish, pagination, pages


# Generations ###################################################
def generate_id(table, size=8):
    # Generate a random 8-digit id
    chars = string.digits
    id = int(''.join(random.choice(chars) for _ in range(size)))

    # Check to make sure there isn't already that id in the database
    if not db.session.query(exists().where(table.id == id)).scalar():
        return id
    else:
        generate_id(table)


def generate_alphanumeric_id(table, size=8):
    # Generate a random 8-character alphanumeric id
    chars = string.digits + string.ascii_lowercase + string.ascii_uppercase
    id = ''.join(random.choice(chars) for _ in range(size))

    # Check to make sure there isn't already that id in the database
    if not db.session.query(exists().where(table.id == id)).scalar():
        return id
    else:
        generate_id(table)


def generate_temp_password(size=15):
    # Generate a random 15-character temporary password
    chars = string.digits + string.ascii_lowercase + string.ascii_uppercase
    return ''.join(random.choice(chars) for _ in range(size))


def generate_private_key(size=16):
    from app.blueprints.base.encryption import encrypt_string

    # Generate a random 16-character alphanumeric id
    chars = string.digits + string.ascii_lowercase + string.ascii_uppercase
    id = ''.join(random.choice(chars) for _ in range(size))

    # Encrypt the private key
    enc = encrypt_string(id)

    # Check to make sure there isn't already that id in the database
    if not db.session.query(exists().where(User.private_key == enc)).scalar():
        return enc
    else:
        generate_private_key()


# Admin ###################################################
def is_admin(current_user):
    return current_user.is_authenticated and current_user.role == 'creator'


# Users ###################################################
def create_anon_user(email):
    from app.blueprints.user.models.user import User
    from app.blueprints.user.tasks import send_temp_password_email

    if not db.session.query(exists().where(User.email == email)).scalar():
        password = generate_temp_password()
        u = User()
        u.email = email
        u.user_id = generate_id(User)
        u.role = 'member'
        u.password = User.encrypt_password(password)
        u.save()
    else:
        u = User.query.filter(User.email == email).scalar()
    return u


def populate_signup(request, user):
    user.created_on = dt.now().replace(tzinfo=pytz.utc)
    user.updated_on = dt.now().replace(tzinfo=pytz.utc)
    user.role = request.form['role']
    user.is_active = True
    user.name = request.form['name']
    user.email = request.form['email']


def generate_name():
    return names.get_first_name()


def get_private_key(domain_id, user_id):
    # d = Domain.query.filter(Domain.domain_id == domain_id).scalar()
    from app.blueprints.base.encryption import decrypt_string
    return decrypt_string(User.private_key)


def set_inactive(current_user):
    current_user.domain = None
    current_user.domain_id = None
    current_user.active = False
    current_user.save()


# Other ###################################################
def print_traceback(e):
    traceback.print_tb(e.__traceback__)
    print(e)
