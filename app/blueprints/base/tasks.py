from app.app import create_celery_app
from app.blueprints.user.models.domain import Domain
from app.blueprints.base.models.feedback import Feedback
import time

celery = create_celery_app()


@celery.task()
def populate_domain(domain_id):
    from app.blueprints.base.functions import generate_private_key, print_traceback

    try:
        d = Domain.query.filter(Domain.domain_id == domain_id).scalar()
        d.private_key = generate_private_key()
        d.save()

        return True
    except Exception as e:
        print_traceback(e)
        return False


@celery.task()
def create_heroku_subdomain(subdomain):
    # Create the subdomain in Heroku
    from app.blueprints.base.dns.heroku import create_subdomain
    return create_subdomain(subdomain)


@celery.task()
def encrypt_string(plaintext):
    from app.blueprints.base.encryption import encrypt_string
    return encrypt_string(plaintext)


@celery.task()
def format_comments(feedback_id, user_id):
    from app.blueprints.base.functions import format_comments
    from app.blueprints.base.models.comment import Comment
    from app.blueprints.user.models.user import User

    is_admin = False

    if user_id:
        user = User.query.filter(User.id == user_id).scalar()

        f = Feedback.query.filter(Feedback.feedback_id == feedback_id).scalar()
        if f is not None:
            d = Domain.query.filter(Domain.domain_id == f.domain_id).scalar()

            if d is not None:
                is_admin = (user.domain_id == d.domain_id)
    else:
        user = None
    comments = Comment.query.filter(Comment.feedback_id == feedback_id).all()

    return format_comments(comments, user, is_admin)


@celery.task()
def delete_demo_feedback(feedback_id):
    f = Feedback.query.filter(Feedback.feedback_id == feedback_id).scalar()
    time.sleep(10)
    f.delete()
