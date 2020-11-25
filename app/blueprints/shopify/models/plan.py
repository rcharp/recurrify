from sqlalchemy import or_, exists
import string
import random

from lib.util_sqlalchemy import ResourceMixin, AwareDateTime
from app.extensions import db


class Plan(ResourceMixin, db.Model):
    __tablename__ = 'plans'

    # Objects.
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), unique=False, index=True, nullable=True)
    tag = db.Column(db.String(255), unique=False, index=True, nullable=True)
    limit = db.Column(db.Integer, unique=False, index=True, nullable=True)
    price = db.Column(db.Integer, unique=False, index=True, nullable=True)

    def __init__(self, **kwargs):
        # Call Flask-SQLAlchemy's constructor.
        super(Plan, self).__init__(**kwargs)
        # self.plan_id = Plan.generate_id()

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    @classmethod
    def generate_id(cls, size=8):
        # Generate a random 8-character id
        chars = string.digits
        result = int(''.join(random.choice(chars) for _ in range(size)))

        # Check to make sure there isn't already that id in the database
        if not db.session.query(exists().where(cls.id == result)).scalar():
            return result
        else:
            Plan.generate_id()

    @classmethod
    def find_by_id(cls, identity):
        """
        Find an email by its message id.

        :param identity: Email or username
        :type identity: str
        :return: User instance
        """
        return Plan.query.filter(
            (Plan.id == identity).first())

    @classmethod
    def search(cls, query):
        """
        Search a resource by 1 or more fields.

        :param query: Search query
        :type query: str
        :return: SQLAlchemy filter
        """
        if not query:
            return ''

        search_query = '%{0}%'.format(query)
        search_chain = (Plan.id.ilike(search_query))

        return or_(*search_chain)

    @classmethod
    def bulk_delete(cls, ids):
        """
        Override the general bulk_delete method because we need to delete them
        one at a time while also deleting them on Stripe.

        :param ids: Plan of ids to be deleted
        :type ids: plan
        :return: int
        """
        delete_count = 0

        for id in ids:
            plan = Plan.query.get(id)

            if plan is None:
                continue

            plan.delete()

            delete_count += 1

        return delete_count
