import click
import random
import time
from sqlalchemy_utils import database_exists, create_database
from app.app import create_app
from app.extensions import db
from app.blueprints.base.functions import generate_id, generate_name, generate_private_key
from app.blueprints.user.models.user import User
from app.blueprints.shopify.models.membership import Membership
from app.blueprints.shopify.models.product import Product

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

    owner = {
        'role': 'owner',
        'email': app.config['SEED_OWNER_EMAIL'],
        'username': app.config['SEED_OWNER_USERNAME'],
        'password': app.config['SEED_ADMIN_PASSWORD'],
        'name': 'Ricky Charpentier'
    }

    for x in range(10):
        member = {
            'role': 'member',
            'email': 'user' + str(x) + '@gmail.com',
            'username': 'member' + str(x),
            'password': app.config['SEED_ADMIN_PASSWORD'],
            'name': generate_name()
        }
        User(**member).save()

    return User(**admin).save()


@click.command()
def seed_memberships():

    # Delete all existing memberships
    # User.query.filter(User.role == 'member').delete()

    # Create new memberships
    members = User.query.filter(User.role == 'member').all()

    for member in members:
        time.sleep(1)
        membership = {
            'membership_id': generate_id(Membership),
            'shop_id': app.config['SHOPIFY_SHOP_ID'],
            'member_id': member.id
        }

        Membership(**membership).save()

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

    return None


@click.command()
@click.pass_context
def memberships(ctx):
    """
    Init and seed_users automatically.

    :param with_testdb: Create a test database
    :return: None
    """
    ctx.invoke(seed_memberships)

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
cli.add_command(memberships)