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
from app.blueprints.user.models.domain import Domain
from app.blueprints.base.models.feedback import Feedback
from app.blueprints.base.models.comment import Comment
from app.blueprints.base.models.status import Status
from app.blueprints.base.models.vote import Vote


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
    if not db.session.query(exists().where(Domain.private_key == enc)).scalar():
        return enc
    else:
        generate_private_key()


# Domains ###################################################
def create_domain(user, domain, company):
    d = Domain()
    d.domain_id = generate_id(Domain, 8)
    d.name = domain
    d.company = company.title()
    d.user_id = user.id
    d.admin_email = user.email
    d.save()

    user.domain_id = d.domain_id
    user.domain = domain
    user.save()

    return d.domain_id


# Feedback ###################################################
def create_feedback(user, domain, email, title, description):
    try:
        d = Domain.query.filter(Domain.name == domain).scalar()
        s = Status.query.filter(Status.name == 'In Backlog').scalar()

        feedback_id = generate_id(Feedback, size=8)

        f = Feedback()
        f.title = title
        f.feedback_id = feedback_id
        f.description = description
        f.domain_id = d.domain_id
        f.domain = d.name
        f.status = s.name
        f.status_id = s.status_id

        if not d.requires_approval:
            f.approved = True

        if user is not None:
            f.user_id = user.id
            f.username = user.username
            f.fullname = user.name
            f.email = user.email
            f.save()

            add_vote(f, user.id)
        else:
            user = create_anon_user(email, domain)

            f.email = email
            f.user_id = user.id
            f.save()

            add_vote(f, user.id, email)

        return f
    except Exception as e:
        print_traceback(e)
        return None


def update_feedback(feedback_id, domain, title, description, status_id):
    try:
        s = Status.query.filter(Status.status_id == status_id).scalar()

        f = Feedback.query.filter(and_(Feedback.domain == domain, Feedback.feedback_id == feedback_id)).scalar()
        f.title = title
        f.description = description
        f.status = s.name
        f.status_id = s.status_id
        f.save()

        return f
    except Exception as e:
        print_traceback(e)
        return None


def get_new_feedback(current_user):
    if current_user.is_authenticated:
        if current_user.domain and current_user.role == 'creator':
            u = Domain.query.filter(Domain.name == current_user.domain).scalar()
            if u is not None:
                return Feedback.query.filter(and_(Feedback.domain_id == u.domain_id, Feedback.approved.is_(False))).all()

    return list()

# Comments ################################################
def add_comment(feedback_id, content, domain_id, user_id, email, parent_id, created_by_user):
    try:
        print(email)
        print(domain_id)

        c = Comment()
        c.comment_id = generate_id(Comment)
        c.feedback_id = feedback_id
        c.comment = content
        c.domain_id = domain_id

        # Set the parent
        if parent_id:
            parent = Comment.query.filter(Comment.comment_id == parent_id).scalar()
            if parent is not None:
                c.parent_id = parent.id

        if user_id is not None:
            c.user_id = user_id

            if created_by_user:
                u = User.query.filter(User.id == user_id).scalar()
                if u is not None:
                    c.fullname = u.name
        elif email is not None:
            d = Domain.query.filter(Domain.domain_id == domain_id).scalar()
            if d is not None:
                u = create_anon_user(email, d.name)
                c.user_id = u.id
                c.email = email

        c.save()

        return True
    except Exception as e:
        print_traceback(e)
    return False


def update_comment(c, content):
    try:

        # Update the comment
        c.comment = content
        c.save()

        return True
    except Exception as e:
        print_traceback(e)
    return False


def format_comments(comments, current_user, is_admin):
    try:
        comment_list = list()

        for comment in comments:
            c = dict()
            created_date = get_year_date_string(comment.created_on)
            created_by_user = True if (current_user is not None and current_user.is_authenticated and comment.user_id == current_user.id) else False
            created_by_admin = True if (current_user is not None and current_user.is_authenticated and created_by_user and current_user.role == 'creator') else False
            parent_id = next(iter([p.comment_id for p in comments if p.id == comment.parent_id]), None)
            name = comment.fullname if comment.fullname else comment.email if is_admin else 'An anonymous user'
            c.update({'id': comment.comment_id,
                      'content': comment.comment,
                      'fullname': name,
                      'parent': parent_id,
                      'creator': comment.user_id,
                      'created_by_current_user': created_by_user,
                      'created_by_admin': created_by_admin,
                      'created': created_date})

            comment_list.append(c)
        return comment_list
    except Exception as e:
        print_traceback(e)
        return None


# Votes ###################################################
def add_vote(f, user_id, email=None):
    try:
        v = Vote()
        v.feedback_id = f.feedback_id
        v.vote_id = generate_id(Vote)
        v.domain_id = f.domain_id

        if user_id is not None:
            v.user_id = user_id
        else:
            u = create_anon_user(email, f.domain)
            v.email = email
            v.user_id = u.id

        v.save()

        f.votes += 1
        f.save()

        return v
    except Exception as e:
        print_traceback(e)
        return None


def remove_vote(f, vote):
    try:
        vote.delete()

        f.votes -= 1
        f.save()
    except Exception as e:
        print_traceback(e)
        return None


# Admin ###################################################
def is_admin(current_user, subdomain):
    return current_user.is_authenticated and current_user.domain == subdomain and current_user.role == 'creator'


# Users ###################################################
def create_anon_user(email, domain):
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

        try:
            # Send them a password reset email
            send_temp_password_email.delay(email, password, domain.title())
        except Exception as e:
            print_traceback(e)
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
    d = Domain.query.filter(Domain.domain_id == domain_id).scalar()
    from app.blueprints.base.encryption import decrypt_string
    return decrypt_string(d.private_key)


def set_inactive(current_user):
    current_user.domain = None
    current_user.domain_id = None
    current_user.active = False
    current_user.save()


# Other ###################################################
def print_traceback(e):
    traceback.print_tb(e.__traceback__)
    print(e)