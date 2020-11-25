from sqlalchemy import or_

from lib.util_sqlalchemy import ResourceMixin, AwareDateTime
from app.extensions import db


class Shop(ResourceMixin, db.Model):
    __tablename__ = 'shops'

    # Objects.
    id = db.Column(db.Integer, primary_key=True)
    shop_name = db.Column(db.String(255))
    token = db.Column(db.String(255))
    status = db.Column(db.SmallInteger, default=1)

    # Relationships.
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', onupdate='CASCADE', ondelete='CASCADE'),
                        index=True, nullable=True, primary_key=False, unique=False)

    def __init__(self, **kwargs):
        # Call Flask-SQLAlchemy's constructor.
        super(Shop, self).__init__(**kwargs)

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
        return Shop.query.filter(
            (Shop.id == identity).first())

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
        search_chain = (Shop.id.ilike(search_query))

        return or_(*search_chain)

    @classmethod
    def bulk_delete(cls, ids):
        """
        Override the general bulk_delete method because we need to delete them
        one at a time while also deleting them on Stripe.

        :param ids: Shop of ids to be deleted
        :type ids: shop
        :return: int
        """
        delete_count = 0

        for id in ids:
            shop = Shop.query.get(id)

            if shop is None:
                continue

            shop.delete()

            delete_count += 1

        return delete_count
