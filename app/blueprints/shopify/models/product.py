from sqlalchemy import or_, exists
import string
import random

from lib.util_sqlalchemy import ResourceMixin, AwareDateTime
from app.extensions import db


class SyncedProduct(ResourceMixin, db.Model):
    __tablename__ = 'products'

    # Objects.
    id = db.Column(db.Integer, primary_key=True)
    source_product_id = db.Column(db.BigInteger, unique=False, index=True, nullable=False)
    destination_product_id = db.Column(db.BigInteger, unique=False, index=True, nullable=True)

    # Relationships.
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', onupdate='CASCADE', ondelete='CASCADE'),
                        index=True, nullable=True, primary_key=False, unique=False)
    shop_id = db.Column(db.BigInteger, db.ForeignKey('shops.shop_id', onupdate='CASCADE', ondelete='CASCADE'),
                        index=True, nullable=True, primary_key=False, unique=False)
    sync_id = db.Column(db.BigInteger, db.ForeignKey('syncs.sync_id', onupdate='CASCADE', ondelete='CASCADE'),
                        index=True, nullable=True, primary_key=False, unique=False)

    def __init__(self, source_product_id, destination_product_id, user_id, shop_id, sync_id, **kwargs):
        # Call Flask-SQLAlchemy's constructor.
        super(SyncedProduct, self).__init__(**kwargs)
        self.source_product_id = source_product_id
        self.destination_product_id = destination_product_id
        self.user_id = user_id
        self.shop_id = shop_id
        self.sync_id = sync_id

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
            SyncedProduct.generate_id()

    @classmethod
    def find_by_id(cls, identity):
        """
        Find an email by its message id.

        :param identity: Email or username
        :type identity: str
        :return: User instance
        """
        return SyncedProduct.query.filter(
            (SyncedProduct.id == identity).first())

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
        search_chain = (SyncedProduct.id.ilike(search_query))

        return or_(*search_chain)

    @classmethod
    def bulk_delete(cls, ids):
        """
        Override the general bulk_delete method because we need to delete them
        one at a time while also deleting them on Stripe.

        :param ids: Product of ids to be deleted
        :type ids: product
        :return: int
        """
        delete_count = 0

        for id in ids:
            product = SyncedProduct.query.get(id)

            if product is None:
                continue

            product.delete()

            delete_count += 1

        return delete_count


class Product:

    tags = ''

    def __init__(self, product):
        self.description = product['body_html']
        self.title = product['title']
        self.created = product['created_at']
        self.product_id = product['id']
        self.images = product['images']
        self.options = product['options']
        self.variants = product['variants']