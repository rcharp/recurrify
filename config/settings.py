from datetime import timedelta
import os
from celery.schedules import crontab

PRODUCTION = os.environ.get('PRODUCTION', None)

SERVER_NAME = os.environ.get('SERVER_NAME', None)
SITE_NAME = os.environ.get('SITE_NAME', None)
APP_NAME = os.environ.get('APP_NAME', None)
REMEMBER_COOKIE_DOMAIN = os.environ.get('REMEMBER_COOKIE_DOMAIN', None)
HEROKU_APP_NAME = os.environ.get('HEROKU_APP_NAME', None)

DEBUG = True
LOG_LEVEL = 'DEBUG'  # CRITICAL / ERROR / WARNING / INFO / DEBUG

SECRET_KEY = os.environ.get('SECRET_KEY', None)
CRYPTO_KEY = os.environ.get('CRYPTO_KEY', None)
PASSWORD = os.environ.get('PASSWORD', None)

# Shopify
SHOPIFY_API_KEY = os.environ.get('SHOPIFY_API_KEY', None)
SHOPIFY_SHARED_SECRET = os.environ.get('SHOPIFY_SHARED_SECRET', None)
SHOPIFY_SHOP_ID = os.environ.get('SHOPIFY_SHOP_ID', None)
SHOPIFY_API_VERSION = os.environ.get('SHOPIFY_API_VERSION', None)
SHOPIFY_SHOP_URL = os.environ.get('SHOPIFY_SHOP_URL', None)
SERVER_HOSTNAME = "recurrify.io"
SERVER_BASE_URL = "https://" + SERVER_HOSTNAME + "/shopify"
INSTALL_REDIRECT_URL = SERVER_BASE_URL + "/shopify/finalize"
WEBHOOK_APP_UNINSTALL_URL = "https://" + SERVER_HOSTNAME + "/auth/callback"

# Flask-Mail.
MAIL_USERNAME = os.environ.get('MAIL_USERNAME', None)
MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', None)
MAIL_DEFAULT_SENDER = os.environ.get('MAIL_USERNAME', None)
MAIL_SERVER = os.environ.get('MAIL_SERVER', None)
MAIL_PORT = os.environ.get('MAIL_PORT', None)
MAIL_USE_TLS = False
MAIL_USE_SSL = True

CARD_NAME = ''
CARD_NUMBER = ''
CARD_MONTH = ''
CARD_YEAR = ''
CARD_CVV = ''

# Cache
CACHE_TYPE = 'redis'
CACHE_REDIS_HOST = os.environ.get('REDIS_HOST', None)
CACHE_REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD', None)
CACHE_DEFAULT_TIMEOUT = os.environ.get('DEFAULT_TIMEOUT', None)
CACHE_REDIS_PORT = os.environ.get('REDIS_PORT', None)
CACHE_REDIS_URL = os.environ.get('REDIS_URL', None)

# Celery Heartbeat.
BROKER_HEARTBEAT = 10
BROKER_HEARTBEAT_CHECKRATE = 2

# Celery.
CLOUDAMQP_URL = os.environ.get('CLOUDAMQP_URL', None)
REDIS_URL = os.environ.get('REDIS_URL', None)
REDBEAT_REDIS_URL = os.environ.get('REDIS_URL', None)

CELERY_BROKER_URL = os.environ.get('REDIS_URL', None)
CELERY_BROKER_HEARTBEAT = 10
CELERY_BROKER_HEARTBEAT_CHECKRATE = 2
CELERY_RESULT_BACKEND = os.environ.get('REDIS_URL', None)
CELERY_REDIS_URL = os.environ.get('REDIS_URL', None)
CELERY_REDIS_HOST = os.environ.get('REDIS_HOST', None)
CELERY_REDIS_PORT = os.environ.get('REDIS_PORT', None)
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_RESULT_EXPIRES = 300
CELERY_REDIS_MAX_CONNECTIONS = 20
CELERY_TASK_FREQUENCY = 2  # How often (in minutes) to run this task
CELERYBEAT_SCHEDULE = {
    'test': {
        'task': 'app.blueprints.base.tasks.test',
        'schedule': timedelta(hours=12)
        # 'schedule': crontab(minute=0, hour="*/12") # every 12 hours
        # 'schedule': crontab(minute="*/1") # every minute
        # 'schedule': crontab(minute="*/5") # every 5 minutes
        # 'schedule': crontab(hour=0, minute=0) # every night at midnight, GMT
    },
}

# SQLAlchemy.
SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', None)
SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_USER = os.environ.get('SQLALCHEMY_USER', None)
SQLALCHEMY_DATABASE = os.environ.get('SQLALCHEMY_DATABASE', None)
SQLALCHEMY_HOST = os.environ.get('SQLALCHEMY_HOST', None)
SQLALCHEMY_PASSWORD = os.environ.get('SQLALCHEMY_PASSWORD', None)

# User.
SEED_ADMIN_EMAIL = os.environ.get('SEED_ADMIN_EMAIL', None)
SEED_ADMIN_PASSWORD = os.environ.get('SEED_ADMIN_PASSWORD', None)
SEED_MEMBER_EMAIL = ''
REMEMBER_COOKIE_DURATION = timedelta(days=90)

# Mailgun.
# MAILGUN_LOGIN = os.environ.get('MAILGUN_LOGIN', None)
# MAILGUN_PASSWORD = os.environ.get('MAILGUN_PASSWORD', None)
# MAILGUN_HOST = os.environ.get('MAILGUN_HOST', None)
# MAILGUN_DOMAIN = os.environ.get('MAILGUN_DOMAIN', None)
# MAILGUN_API_KEY = os.environ.get('MAILGUN_API_KEY', None)

# Turn off debug intercepts
DEBUG_TB_INTERCEPT_REDIRECTS = False
DEBUG_TB_ENABLED = False

# Mailerlite
# MAILERLITE_API_KEY = os.environ.get('MAILERLITE_API_KEY', None)

# Billing.
STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY', None)
STRIPE_TEST_SECRET_KEY = os.environ.get('STRIPE_TEST_SECRET_KEY', None)
STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY', None)
STRIPE_TEST_PUBLISHABLE_KEY = os.environ.get('STRIPE_TEST_PUBLISHABLE_KEY', None)
STRIPE_API_VERSION = '2018-02-28'
STRIPE_AUTHORIZATION_LINK = os.environ.get('STRIPE_CONNECT_AUTHORIZE_LINK', None)

# Heroku
HEROKU_API_KEY = os.environ.get('HEROKU_API_KEY', None)
HEROKU_TOKEN = os.environ.get('HEROKU_TOKEN', None)

# Cloudflare
CLOUDFLARE_TOKEN = os.environ.get('CLOUDFLARE_TOKEN', None)

# Change this to the live key when ready to take payments
STRIPE_KEY = STRIPE_SECRET_KEY

STRIPE_PLANS = {
    '0': {
        'id': os.environ.get('STRIPE_ID_FREE', None),
        'name': 'Free',
        'amount': 0000,
        'currency': 'usd',
        'interval': 'month',
        'interval_count': 1,
        'trial_period_days': 0,
        'statement_descriptor': 'FREE',
        'metadata': {}
    },
    '1': {
        'id': os.environ.get('STRIPE_ID_HOBBY', None),
        'name': 'Hobby',
        'amount': 1900,
        'currency': 'usd',
        'interval': 'month',
        'interval_count': 1,
        'trial_period_days': 0,
        'statement_descriptor': 'HOBBY',
        'metadata': {}
    },
    '2': {
        'id': os.environ.get('STRIPE_ID_STARTUP', None),
        'name': 'Startup',
        'amount': 4900,
        'currency': 'usd',
        'interval': 'month',
        'interval_count': 1,
        'trial_period_days': 0,
        'statement_descriptor': 'STARTUP',
        'metadata': {
            'recommended': True
        }
    },
    '3': {
        'id': os.environ.get('STRIPE_ID_BUSINESS', None),
        'name': 'Business',
        'amount': 14900,
        'currency': 'usd',
        'interval': 'month',
        'interval_count': 1,
        'trial_period_days': 0,
        'statement_descriptor': 'BUSINESS',
        'metadata': {}
    },
    '4': {
        'id': 'developer',
        'name': 'Developer',
        'amount': 1,
        'currency': 'usd',
        'interval': 'month',
        'interval_count': 1,
        'trial_period_days': 0,
        'statement_descriptor': 'DEVELOPER',
        'metadata': {}
    }
}
