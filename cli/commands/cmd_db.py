import click
import random
from cli.commands.data import (
    statuses,
    generate_comments,
    generate_feedback
)
from sqlalchemy_utils import database_exists, create_database
from app.app import create_app
from app.extensions import db
from app.blueprints.base.functions import generate_id, generate_name, generate_private_key
from app.blueprints.user.models.user import User
from app.blueprints.user.models.domain import Domain
from app.blueprints.base.models.status import Status
from app.blueprints.base.models.feedback import Feedback
from app.blueprints.base.models.vote import Vote
from app.blueprints.base.models.comment import Comment

# Create an app context for the database connection.
app = create_app()
db.app = app


@click.group()
def cli():
    """ Run PostgreSQL related tasks. """
    pass


@click.command()
@click.option('--with-testdb/--no-with-testdb', default=False,
              help='Create a test db too?')
def init(with_testdb):
    """
    Initialize the database.

    :param with_testdb: Create a test database
    :return: None
    """
    db.drop_all()

    db.create_all()

    if with_testdb:
        db_uri = '{0}_test'.format(app.config['SQLALCHEMY_DATABASE_URI'])

        if not database_exists(db_uri):
            create_database(db_uri)


@click.command()
def seed_users():
    """
    Seed the database with an initial user.

    :return: User instance
    """
    if User.find_by_identity(app.config['SEED_ADMIN_EMAIL']) is not None:
        return None

    admin = {
        'role': 'admin',
        'email': app.config['SEED_ADMIN_EMAIL'],
        'username': app.config['SEED_ADMIN_USERNAME'],
        'password': app.config['SEED_ADMIN_PASSWORD'],
        'name': 'Admin'
    }

    feedback = {
        'role': 'creator',
        'email': app.config['SEED_MEMBER_EMAIL'],
        'username': app.config['SEED_MEMBER_USERNAME'],
        'password': app.config['SEED_ADMIN_PASSWORD'],
        'domain': 'feedback',
        'name': 'Ricky'
    }

    demo = {
        'role': 'creator',
        'email': 'demo@recurrify.io',
        'username': 'demo',
        'password': app.config['SEED_ADMIN_PASSWORD'],
        'domain': 'demo',
        'name': 'Demo User'
    }

    User(**feedback).save()
    User(**demo).save()

    return User(**admin).save()


@click.command()
def seed_status():
    for status in statuses():
        params = {
            'status_id': generate_id(Status),
            'name': status['name'],
            'color': status['color']
        }

        Status(**params).save()

    return


@click.command()
def seed_domains():
    from app.blueprints.base.encryption import encrypt_string
    d = User.query.filter(User.domain == 'demo').scalar()
    d_id = generate_id(Domain, 8)
    demo = {
        'domain_id': d_id,
        'name': 'demo',
        'company': 'Demo',
        'admin_email': d.email,
        'user_id': d.id,
        'private_key': encrypt_string(generate_private_key())
    }

    u = User.query.filter(User.domain == 'feedback').scalar()
    u_id = generate_id(Domain, 8)
    feedback = {
        'domain_id': u_id,
        'name': 'feedback',
        'company': 'Recurrify',
        'admin_email': u.email,
        'user_id': u.id,
        'private_key': encrypt_string(generate_private_key())
    }

    Domain(**demo).save()
    d.domain_id = d_id
    d.save()

    Domain(**feedback).save()
    u.domain_id = u_id
    u.save()


@click.command()
def seed_feedback():

    s = list(Status.query.all())
    feedback = generate_feedback()

    d = Domain.query.filter(Domain.name == 'demo').scalar()
    demo_user = User.query.filter(User.username == 'demo').scalar()

    # w = Domain.query.filter(Domain.name == 'recurrify').scalar()
    # recurrify_user = User.query.filter(User.username == 'ricky').scalar()

    for x in range(1, 31):
        status = random.choice(s)
        f = random.choice(feedback)
        params = {
            'user_id': demo_user.id,
            'feedback_id': generate_id(Feedback),
            'title': f['title'],
            'email': demo_user.email,
            'username': demo_user.username,
            'fullname': generate_name(),
            'description': f['description'],
            'votes': random.randint(10, 1000),
            # 'comments': random.randint(1, 500),
            'status_id': status.status_id,
            'status': status.name,
            'domain': d.name,
            'domain_id': d.domain_id
        }

        Feedback(**params).save()

    # for x in range(1, 11):
    #     status = random.choice(s)
    #     params = {
    #         'user_id': 1,
    #         'feedback_id': generate_id(Feedback),
    #         'title': random.choice(titles()),
    #         'email': recurrify_user.email,
    #         'username': recurrify_user.username,
    #         'fullname': generate_name(),
    #         'description': random.choice(descriptions()),
    #         'votes': random.randint(10, 1000),
    #         'comments': random.randint(1, 500),
    #         'status_id': status.status_id,
    #         'status': status.name,
    #         'domain': w.name,
    #         'domain_id': w.domain_id
    #     }
    #
    #     Feedback(**params).save()

    return


@click.command()
def seed_comments():
    d = Domain.query.filter(Domain.name == 'demo').scalar()
    # demo_user = User.query.filter(User.username == 'demo').scalar()
    feedback = Feedback.query.order_by(Feedback.created_on.desc()).limit(10).all()
    comments = generate_comments()

    for f in feedback:
        for x in range(random.randint(1, 21)):
            c = Comment()
            # c.user_id = demo_user.id
            c.comment_id = generate_id(Comment)
            c.fullname = generate_name()
            c.comment = random.choice(comments)
            c.feedback_id = f.feedback_id
            c.domain_id = d.domain_id
            c.save()

            f.comments += 1
        f.save()

    return


@click.command()
@click.option('--with-testdb/--no-with-testdb', default=False,
              help='Create a test db too?')
@click.pass_context
def reset(ctx, with_testdb):
    """
    Init and seed_users automatically.

    :param with_testdb: Create a test database
    :return: None
    """
    ctx.invoke(init, with_testdb=with_testdb)
    ctx.invoke(seed_users)
    ctx.invoke(seed_domains)
    ctx.invoke(seed_status)
    ctx.invoke(seed_feedback)
    ctx.invoke(seed_comments)

    return None


@click.command()
def backup():
    """
    Backup the db.
    :return: None
    """
    # from flask.alchemydumps import AlchemyDumps
    #
    # alchemydumps = AlchemyDumps(app, db)
    #
    # return alchemydumps.create()
    return None


cli.add_command(init)
cli.add_command(seed_users)
cli.add_command(reset)