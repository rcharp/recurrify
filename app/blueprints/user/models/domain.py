from sqlalchemy import or_
import os
from lib.util_sqlalchemy import ResourceMixin, AwareDateTime
from app.extensions import db
from itsdangerous import URLSafeTimedSerializer, \
    TimedJSONWebSignatureSerializer
from flask import current_app


class Domain(ResourceMixin, db.Model):

    __tablename__ = 'domains'

    # Objects.
    id = db.Column(db.Integer, primary_key=True)
    domain_id = db.Column(db.BigInteger, unique=True, index=True, nullable=False)
    name = db.Column(db.String(255), unique=True, index=True, nullable=True, server_default='')
    company = db.Column(db.String(255), unique=False, index=True, nullable=True, server_default='')
    admin_email = db.Column(db.String(255), unique=False, index=True, nullable=True, server_default='')
    private_key = db.Column(db.LargeBinary, unique=True, nullable=False, server_default='')
    private = db.Column('is_private', db.Boolean(), nullable=False, server_default='0')
    requires_approval = db.Column('requires_approval', db.Boolean(), nullable=False, server_default='1')

    # Relationships.
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', onupdate='CASCADE', ondelete='CASCADE'),
                           index=True, nullable=True, primary_key=False, unique=False)

    def __init__(self, **kwargs):
        # Call Flask-SQLAlchemy's constructor.
        super(Domain, self).__init__(**kwargs)

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    @classmethod
    def find_by_id(cls, identity):
        """
        Find an email by its message id.

        :param identity: Email or username
        :type identity: str
        :return: User instance
        """
        return Domain.query.filter(
          (Domain.id == identity).first())

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
        search_chain = (Domain.id.ilike(search_query))

        return or_(*search_chain)

    @classmethod
    def bulk_delete(cls, ids):
        """
        Override the general bulk_delete method because we need to delete them
        one at a time while also deleting them on Stripe.

        :param ids: Domain of ids to be deleted
        :type ids: domain
        :return: int
        """
        delete_count = 0

        for id in ids:
            domain = Domain.query.get(id)

            if domain is None:
                continue

            domain.delete()

            delete_count += 1

        return delete_count

    # def serialize_token(self, expiration=999999999):
    #     """
    #     Sign and create a token that can be used for things such as resetting
    #     a password or other tasks that involve a one off token.
    #
    #     :param expiration: Seconds until it expires, defaults to 1 hour
    #     :type expiration: int
    #     :return: JSON
    #     """
    #     secret = current_app.config['SECRET_KEY']
    #     from app.blueprints.base.functions import generate_private_key
    #
    #     serializer = TimedJSONWebSignatureSerializer(secret, expiration)
    #     return serializer.dumps({'private_key': generate_private_key()}).decode('utf-8')
    #
    # @classmethod
    # def deserialize_token(cls, token):
    #     """
    #     Obtain a private key from de-serializing a signed token.
    #
    #     :param token: Signed token.
    #     :type token: str
    #     :return: User instance or None
    #     """
    #     secret = TimedJSONWebSignatureSerializer(current_app.config['SECRET_KEY'])
    #     try:
    #         decoded_payload = secret.loads(token)
    #
    #         return decoded_payload.get('private_key')
    #     except Exception as e:
    #         from app.blueprints.base.functions import print_traceback
    #         print_traceback(e)
    #         return None
