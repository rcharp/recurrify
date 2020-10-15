from sqlalchemy import or_

from lib.util_sqlalchemy import ResourceMixin, AwareDateTime
from app.extensions import db


class Feedback(ResourceMixin, db.Model):

    __tablename__ = 'feedback'

    # Objects.
    id = db.Column(db.Integer, primary_key=True)
    feedback_id = db.Column(db.Integer, unique=True, index=True, nullable=False)
    title = db.Column(db.String(255), unique=False, index=True, nullable=True, server_default='')
    email = db.Column(db.String(255), unique=False, index=True, nullable=True, server_default='')
    fullname = db.Column(db.String(255), unique=False, index=True, nullable=True, server_default='')
    description = db.Column(db.UnicodeText, unique=False, index=True, nullable=True, server_default='')
    votes = db.Column(db.Integer, unique=False, index=True, nullable=False, server_default='0')
    comments = db.Column(db.Integer, unique=False, index=True, nullable=False, server_default='0')
    status = db.Column(db.String(255), unique=False, index=True, nullable=True, server_default='')
    approved = db.Column('approved', db.Boolean(), nullable=False, server_default='0')

    # Relationships.
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', onupdate='CASCADE', ondelete='CASCADE'),
                           index=True, nullable=True, primary_key=False, unique=False)
    username = db.Column(db.String(255), db.ForeignKey('users.username', onupdate='CASCADE', ondelete='CASCADE'),
                        index=True, nullable=True, primary_key=False, unique=False)
    status_id = db.Column(db.Integer, db.ForeignKey('statuses.status_id', onupdate='CASCADE', ondelete='CASCADE'),
                        index=True, nullable=True, primary_key=False, unique=False)
    domain_id = db.Column(db.BigInteger, db.ForeignKey('domains.domain_id', onupdate='CASCADE', ondelete='CASCADE'),
                          index=True, nullable=True, primary_key=False, unique=False)
    domain = db.Column(db.String(255), db.ForeignKey('domains.name', onupdate='CASCADE', ondelete='CASCADE'),
                          index=True, nullable=True, primary_key=False, unique=False)

    def __init__(self, **kwargs):
        # Call Flask-SQLAlchemy's constructor.
        super(Feedback, self).__init__(**kwargs)

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
        return Feedback.query.filter(
          (Feedback.id == identity).first())

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
        search_chain = (Feedback.id.ilike(search_query))

        return or_(*search_chain)

    @classmethod
    def bulk_delete(cls, ids):
        """
        Override the general bulk_delete method because we need to delete them
        one at a time while also deleting them on Stripe.

        :param ids: Feedback of ids to be deleted
        :type ids: feedback
        :return: int
        """
        delete_count = 0

        for id in ids:
            feedback = Feedback.query.get(id)

            if feedback is None:
                continue

            feedback.delete()

            delete_count += 1

        return delete_count
