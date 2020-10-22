import logging
import pytz
from logging.handlers import SMTPHandler
import os
import uuid
import json
import stripe
import datetime
import random
from sqlalchemy import inspect
from werkzeug.contrib.fixers import ProxyFix
from flask import Flask, render_template, url_for, flash, redirect, request
from celery import Celery
from itsdangerous import URLSafeTimedSerializer
from flask_compress import Compress
from app.blueprints.admin import admin
from app.blueprints.page import page
from app.blueprints.contact import contact
from app.blueprints.user import user
from app.blueprints.shopify import shopify_bp
from app.blueprints.base import base
from app.blueprints.api import api
from app.blueprints.api.functions import deserialize_token
from app.blueprints.billing import billing
from app.blueprints.user.models.user import User
from app.blueprints.errors import errors
from app.blueprints.page.date import get_year_date_string, get_datetime_from_string, get_dt_string, is_date, format_datetime, format_datetime_string
from app.blueprints.billing.template_processors import (
  format_currency,
  current_year
)
from app.extensions import (
    debug_toolbar,
    mail,
    csrf,
    db,
    login_manager,
    cache,
    cors,
)


CELERY_TASK_LIST = [
    'app.blueprints.base.tasks',
    'app.blueprints.contact.tasks',
    'app.blueprints.user.tasks',
    'app.blueprints.billing.tasks'
]


def create_celery_app(app=None):
    """
    Create a new Celery object and tie together the Celery config to the app's
    config. Wrap all tasks in the context of the application.

    :param app: Flask app
    :return: Celery app
    """
    app = app or create_app()
    celery = Celery(broker=app.config.get('CELERY_BROKER_URL'), include=CELERY_TASK_LIST)
    celery.conf.update(app.config)
    celery.conf.beat_schedule = app.config.get('CELERYBEAT_SCHEDULE')
    TaskBase = celery.Task

    class ContextTask(TaskBase):
        abstract = True

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)

    celery.Task = ContextTask
    return celery


def create_app(settings_override=None):
    """
    Create a Flask application using the app factory pattern.

    :param settings_override: Override settings
    :return: Flask app
    """
    app = Flask(__name__, instance_relative_config=True)

    app.config.from_object('config.settings')
    app.config.from_pyfile('settings.py', silent=True)

    if os.environ.get('PRODUCTION') == 'Development':
        # Set the app server name
        app.config['SERVER_NAME'] = 'localhost:5000'
        app.config['REMEMBER_COOKIE_DOMAIN'] = '.localhost:5000'
    # else:
        # Set the app server name
        # app.config['SERVER_NAME'] = 'recurrify.io'
        # app.config['REMEMBER_COOKIE_DOMAIN'] = '.recurrify.io'

    # Keeps the app from crashing on reload
    app.config['SQLALCHEMY_POOL_RECYCLE'] = 499
    app.config['SQLALCHEMY_POOL_TIMEOUT'] = 120
    app.static_folder = 'static'
    app.static_url_path = '/static'

    # CORS
    app.config['CORS_HEADERS'] = 'Content-Type'

    if settings_override:
        app.config.update(settings_override)

    stripe.api_key = app.config.get('STRIPE_KEY')
    stripe.api_version = '2018-02-28'

    middleware(app)
    error_templates(app)
    exception_handler(app)
    app.register_blueprint(admin)
    app.register_blueprint(page)
    app.register_blueprint(contact)
    app.register_blueprint(user)
    app.register_blueprint(shopify_bp)
    app.register_blueprint(base)
    app.register_blueprint(api)
    app.register_blueprint(billing)
    app.register_blueprint(errors)
    app.register_error_handler(404, page_not_found)
    app.register_error_handler(500, internal_error)
    template_processors(app)
    extensions(app)
    authentication(app, User)

    # Compress Flask app
    COMPRESS_MIMETYPES = ['text/html' 'text/css', 'application/json']
    COMPRESS_LEVEL = 6
    COMPRESS_MIN_SIZE = 500
    Compress(app)

    # @app.before_request
    # def before_request():
    #     if not request.is_secure and os.environ.get('PRODUCTION') == 'true':
    #         url = request.url.replace("http://", "https://", 1)
    #         code = 301
    #         return shopify_redirect(url, code=code)

    @app.errorhandler(500)
    def error_502(e):
        return render_template('errors/500.html')

    @app.errorhandler(404)
    def error_404(e):
        return render_template('errors/404.html')

    @app.errorhandler(502)
    def error_502(e):
        return render_template('errors/500.html')

    return app


def page_not_found(e):
    return render_template('errors/404.html'), 404


def internal_error(e):
    return render_template('errors/500.html'), 500


def extensions(app):
    """
    Register 0 or more extensions (mutates the app passed in).

    :param app: Flask application instance
    :return: None
    """
    debug_toolbar.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)
    cache.init_app(app, config={'CACHE_TYPE': 'redis'})
    cors(app, support_credentials=True, resources={r"/*": {"origins": "*"}})

    return None


def template_processors(app):
    """
    Register 0 or more custom template processors (mutates the app passed in).

    :param app: Flask application instance
    :return: App jinja environment
    """
    app.jinja_env.filters['format_currency'] = format_currency
    app.jinja_env.filters['pretty_date_filter'] = pretty_date_filter
    app.jinja_env.filters['datetime_filter'] = datetime_filter
    app.jinja_env.filters['short_date_filter'] = short_date_filter
    app.jinja_env.filters['list_filter'] = list_filter
    app.jinja_env.filters['dict_filter'] = dict_filter
    app.jinja_env.filters['today_filter'] = today_filter
    app.jinja_env.filters['site_name_filter'] = site_name_filter
    app.jinja_env.filters['site_url_filter'] = site_url_filter
    app.jinja_env.filters['site_version_filter'] = site_version_filter
    app.jinja_env.filters['site_color_filter'] = site_color_filter
    app.jinja_env.filters['shuffle_filter'] = shuffle_filter
    app.jinja_env.filters['percent_filter'] = percent_filter
    app.jinja_env.filters['default_profile_image_url'] = default_profile_image_url
    app.jinja_env.filters['any_votes_filter'] = any_votes_filter
    app.jinja_env.filters['initial_filter'] = initial_filter
    app.jinja_env.filters['deserialize_private_key'] = deserialize_private_key
    app.jinja_env.globals.update(current_year=current_year)

    return app.jinja_env


def authentication(app, user_model):
    """
    Initialize the Flask-Login extension (mutates the app passed in).

    :param app: Flask application instance
    :param user_model: Model that contains the authentication information
    :type user_model: SQLAlchemy model
    :return: None
    """
    login_manager.login_view = 'user.login'

    @login_manager.user_loader
    def load_user(uid):
        return user_model.query.get(uid)

    #@login_manager.token_loader
    def load_token(token):
        duration = app.config['REMEMBER_COOKIE_DURATION'].total_seconds()
        max = 999999999999
        serializer = URLSafeTimedSerializer(app.secret_key)

        data = serializer.loads(token, max_age=max)
        user_uid = data[0]

        return user_model.query.get(user_uid)


def middleware(app):
    """
    Register 0 or more middleware (mutates the app passed in).

    :param app: Flask application instance
    :return: None
    """
    # Swap request.remote_addr with the real IP address even if behind a proxy.
    app.wsgi_app = ProxyFix(app.wsgi_app)

    return None


def error_templates(app):
    """
    Register 0 or more custom error pages (mutates the app passed in).

    :param app: Flask application instance
    :return: None
    """

    def render_status(status):
        """
         Render a custom template for a specific status.
           Source: http://stackoverflow.com/a/30108946

         :param status: Status as a written name
         :type status: str
         :return: None
         """
        # Get the status code from the status, default to a 500 so that we
        # catch all types of errors and treat them as a 500.
        code = getattr(status, 'code', 500)
        return render_template('errors/{0}.html'.format(code)), code

    for error in [404, 500]:
        app.errorhandler(error)(render_status)

    return None


def exception_handler(app):
    """
    Register 0 or more exception handlers (mutates the app passed in).

    :param app: Flask application instance
    :return: None
    """
    mail_handler = SMTPHandler((app.config.get('MAIL_SERVER'),
                                app.config.get('MAIL_PORT')),
                               app.config.get('MAIL_USERNAME'),
                               [app.config.get('MAIL_USERNAME')],
                               '[Exception handler] A 5xx was thrown',
                               (app.config.get('MAIL_USERNAME'),
                                app.config.get('MAIL_PASSWORD')),
                               secure=())

    mail_handler.setLevel(logging.ERROR)
    mail_handler.setFormatter(logging.Formatter("""
    Time:               %(asctime)s
    Message type:       %(levelname)s


    Message:

    %(message)s
    """))
    app.logger.addHandler(mail_handler)

    return None


def pretty_date_filter(arg):
    time_string = str(arg)

    if is_date(time_string):
        if '.' in time_string:
            time_string = time_string.split('.')[0]
        dt = get_datetime_from_string(time_string)
        return get_dt_string(dt) + ' UTC'

    return arg


def datetime_filter(arg):
    return format_datetime_string(arg)


def short_date_filter(arg):
    time_string = str(arg)

    if is_date(time_string):
        if '.' in time_string:
            time_string = time_string.split('.')[0]
        dt = get_datetime_from_string(time_string)
        return format_datetime(dt)

    return arg


def list_filter(arg):
    return isinstance(arg, list)


def dict_filter(obj):
    return {c.key: getattr(obj, c.key) for c in inspect(obj).mapper.column_attrs}
    #return [x.as_dict() for x in l]


def today_filter(arg):
    return arg - datetime.timedelta(hours=24) <= pytz.utc.localize(datetime.datetime.utcnow())


def site_name_filter(arg):
    from flask import current_app
    return current_app.config.get('SITE_NAME')


def site_version_filter(arg):
    # return 'v1.0'
    return 'Beta'


def site_url_filter(arg):
    from flask import current_app
    return current_app.config.get('SERVER_NAME') # 'recurrify.io'


def site_color_filter(arg):
    return '009fff'


def table_name_filter(arg):
    return arg.replace('_', ' ').title()


def shuffle_filter(arg):
    try:
        random.shuffle(arg)
        return arg
    except Exception as e:
        return arg


def percent_filter(arg):
    return float(100 / len(arg))


def any_votes_filter(arg, k):
    if arg is None:
        return False

    return any(x.feedback_id == k for x in arg)


def deserialize_private_key(arg):
    if arg is not None:
        from app.blueprints.base.encryption import decrypt_string
        return decrypt_string(arg)
    return None


def initial_filter(arg):
    if arg is None:
        return 'W'
    if ' ' in arg:
        initials = list()
        name = arg.split(' ')
        for n in name:
            initials.append(n[0])

        s = ''
        return s.join(initials).upper()
    else:
        return arg[0].upper()


def default_profile_image_url(arg):
    markup = 'https://storage.googleapis.com/indie-hackers.appspot.com/avatars/soVlU13BlpgOX7DVWwfJAy67QA43'
    offerd = 'https://scontent.ftpa1-2.fna.fbcdn.net/v/t1.0-9/23471937_10155779109118398_6528989144266130489_n.jpg?_nc_cat=104&_nc_sid=09cbfe&_nc_ohc=fMD4100xS9wAX8vx9MW&_nc_ht=scontent.ftpa1-2.fna&oh=dc95db0c4dbf170940ac87c45678ccb9&oe=5F09350D'

    return None