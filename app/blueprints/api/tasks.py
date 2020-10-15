from app.app import create_celery_app, db
from flask import jsonify, make_response

celery = create_celery_app()


@celery.task()
def test():
    return
