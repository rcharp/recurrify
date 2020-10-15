from sqlalchemy import or_

from lib.util_sqlalchemy import ResourceMixin, AwareDateTime
from app.extensions import db
from app.blueprints.base.models.feedback import Feedback


class Status(ResourceMixin, db.Model):

    __tablename__ = 'statuses'

    # Objects.
    id = db.Column(db.Integer, primary_key=True)
    status_id = db.Column(db.Integer, unique=True, index=True, nullable=False)
    name = db.Column(db.String(255), unique=False, index=True, nullable=True, server_default='')
    color = db.Column(db.String(255), unique=False, index=True, nullable=True, server_default='')
    description = db.Column(db.UnicodeText, unique=False, index=True, nullable=True, server_default='')

    # Relationships.
    feedback = db.relationship(Feedback, uselist=False, backref='statuses', lazy='subquery',
                           passive_deletes=True)

    def __init__(self, **kwargs):
        # Call Flask-SQLAlchemy's constructor.
        super(Status, self).__init__(**kwargs)

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
        return Status.query.filter(
          (Status.id == identity).first())

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
        search_chain = (Status.id.ilike(search_query))

        return or_(*search_chain)

    @classmethod
    def bulk_delete(cls, ids):
        """
        Override the general bulk_delete method because we need to delete them
        one at a time while also deleting them on Stripe.

        :param ids: Status of ids to be deleted
        :type ids: status
        :return: int
        """
        delete_count = 0

        for id in ids:
            status = Status.query.get(id)

            if status is None:
                continue

            status.delete()

            delete_count += 1

        return delete_count
