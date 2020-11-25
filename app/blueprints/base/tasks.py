from app.app import create_celery_app
import time

celery = create_celery_app()


@celery.task()
def encrypt_string(plaintext):
    from app.blueprints.base.encryption import encrypt_string
    return encrypt_string(plaintext)
