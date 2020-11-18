from sqlalchemy import or_, exists

from lib.util_sqlalchemy import ResourceMixin, AwareDateTime
from app.extensions import db
import string
import random


class Membership(ResourceMixin, db.Model):

    __tablename__ = 'memberships'

    # Objects.
    id = db.Column(db.Integer, primary_key=True)
    membership_id = db.Column(db.Integer, unique=True, index=True, nullable=False)
    active = db.Column('is_active', db.Boolean(), nullable=False, server_default='1')

    # Relationships.
    shop_id = db.Column(db.BigInteger, db.ForeignKey('shops.shop_id', onupdate='CASCADE', ondelete='CASCADE'),
                           index=True, nullable=True, primary_key=False, unique=False)
    member_id = db.Column(db.Integer, db.ForeignKey('users.id', onupdate='CASCADE', ondelete='CASCADE'),
                        index=True, nullable=True, primary_key=False, unique=False)

    def __init__(self, **kwargs):
        # Call Flask-SQLAlchemy's constructor.
        super(Membership, self).__init__(**kwargs)
        self.membership_id = Membership.generate_id()

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
            Membership.generate_id()

    @classmethod
    def find_by_id(cls, identity):
        """
        Find an email by its message id.

        :param identity: Email or username
        :type identity: str
        :return: User instance
        """
        return Membership.query.filter(
          (Membership.id == identity).first())

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
        search_chain = (Membership.id.ilike(search_query))

        return or_(*search_chain)

    @classmethod
    def bulk_delete(cls, ids):
        """
        Override the general bulk_delete method because we need to delete them
        one at a time while also deleting them on Stripe.

        :param ids: Membership of ids to be deleted
        :type ids: membership
        :return: int
        """
        delete_count = 0

        for id in ids:
            membership = Membership.query.get(id)

            if membership is None:
                continue

            membership.delete()

            delete_count += 1

        return delete_count
