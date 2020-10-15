from flask import (
    Blueprint,
    redirect,
    request,
    flash,
    Markup,
    url_for,
    render_template,
    current_app,
    json,
    jsonify,
    session)
from flask_login import (
    login_required,
    login_user,
    current_user,
    logout_user)

import time
import random
import requests
from operator import attrgetter
from flask_cors import cross_origin

from lib.safe_next_url import safe_next_url
from app.blueprints.user.decorators import anonymous_required
from app.blueprints.user.models.user import User, Domain
from app.blueprints.user.forms import (
    LoginForm,
    LoginFormAnon,
    BeginPasswordResetForm,
    PasswordResetForm,
    SignupForm,
    SignupFormAnon,
    WelcomeForm,
    UpdateCredentials)

from app.extensions import cache, csrf, timeout, db
from importlib import import_module
from sqlalchemy import or_, and_, exists, inspect, func
from app.blueprints.base.models.feedback import Feedback
from app.blueprints.base.models.status import Status
from app.blueprints.base.models.vote import Vote
from app.blueprints.base.models.comment import Comment
from app.blueprints.base.functions import is_admin

user = Blueprint('user', __name__, template_folder='templates')
use_username = False


# Login and Credentials -------------------------------------------------------------------
@user.route('/login', methods=['GET', 'POST'])
@user.route('/login', subdomain='<subdomain>', methods=['GET', 'POST'])
@anonymous_required()
@csrf.exempt
def login(subdomain=None):

    if subdomain:
        # form = LoginForm(next=request.args.get('next'))
        form = LoginForm(next=request.referrer)

        if form.validate_on_submit():

            u = User.find_by_identity(request.form.get('identity'))

            if u and u.is_active() and u.authenticated(password=request.form.get('password')):
                if login_user(u, remember=True) and u.is_active():

                    if current_user.role == 'admin':
                        return redirect(url_for('admin.dashboard'))

                    u.update_activity_tracking(request.remote_addr)

                    next_url = request.form.get('next')
                    # next_url = request.referrer

                    if next_url == url_for('user.login', subdomain=subdomain) or next_url == '' or next_url is None:
                        next_url = url_for('user.dashboard', subdomain=subdomain)

                    if next_url:
                        return redirect(safe_next_url(next_url), code=307)

                else:
                    flash('This account has been disabled.', 'error')
            else:
                flash('Your username/email or password is incorrect.', 'error')

        else:
            if len(form.errors) > 0:
                print(form.errors)

        return render_template('user/login.html', subdomain=subdomain, form=form)
    else:
        form = LoginFormAnon(next=request.args.get('next'))

        if form.validate_on_submit():
            u = User.find_by_identity(request.form.get('identity'))

            if u and u.is_active() and u.authenticated(password=request.form.get('password')):

                # If the user doesn't have a company, make them sign up for one
                subdomain = request.form.get('domain')

                # Check if the entered domain exists
                if subdomain:
                    if not db.session.query(exists().where(func.lower(Domain.name) == subdomain.lower())).scalar():
                        flash(Markup("That domain wasn't found. Please try again or <a href='" + url_for('user.signup') + "'><span class='text-indigo-700'><u>create a new company</span></u></a>."),
                              category='error')
                        return render_template('user/login.html', form=form)

                if login_user(u, remember=True) and u.is_active():
                    if current_user.role == 'admin':
                        return redirect(url_for('admin.dashboard'))

                    u.update_activity_tracking(request.remote_addr)

                    next_url = request.form.get('next')

                    if next_url == url_for('user.login') or next_url == '' or next_url is None:

                        # If they entered a domain in the form, take them there after login
                        if subdomain:
                            next_url = url_for('user.dashboard', subdomain=subdomain)
                        else:

                            # If not, and they have a domain, take them to that dashboard
                            if u.domain:
                                next_url = url_for('user.dashboard', subdomain=u.domain)
                            # Otherwise, take them to their settings page.
                            else:
                                next_url = url_for('user.settings')

                    if next_url:
                        return redirect(safe_next_url(next_url), code=307)

                    if current_user.role == 'admin':
                        return redirect(url_for('admin.dashboard'))
                else:
                    flash('This account has been disabled.', 'error')
            else:
                flash('Your username/email or password is incorrect.', 'error')

        else:
            if len(form.errors) > 0:
                print(form.errors)

        return render_template('user/login.html', form=form)


'''
Signup to post feedback in an existing domain
'''


@user.route('/signup', methods=['GET', 'POST'])
@user.route('/signup', subdomain='<subdomain>', methods=['GET', 'POST'])
@anonymous_required()
@csrf.exempt
def signup(subdomain=None):
    from app.blueprints.base.functions import print_traceback
    if subdomain:
        form = SignupForm()

        try:
            if form.validate_on_submit():
                if db.session.query(exists().where(User.email == request.form.get('email'))).scalar():
                    flash('There is already an account with this email. Please login.', 'error')
                    return redirect(url_for('user.login', subdomain=subdomain))

                u = User()

                form.populate_obj(u)
                u.password = User.encrypt_password(request.form.get('password'))
                u.role = 'member'
                u.save()

                if login_user(u):
                    from app.blueprints.user.tasks import send_creator_welcome_email
                    # from app.blueprints.contact.mailerlite import create_subscriber

                    send_member_welcome_email.delay(current_user.email, subdomain)
                    # create_subscriber(current_user.email)

                    flash("You've successfully signed up!", 'success')
                    return redirect(url_for('user.dashboard', subdomain=subdomain))
        except Exception as e:
            print_traceback(e)

        return render_template('user/signup.html', subdomain=subdomain, form=form)
    else:
        form = SignupFormAnon()

        try:
            if form.validate_on_submit():
                if db.session.query(exists().where(User.email == request.form.get('email'))).scalar():
                    flash('There is already an account with this email. Please login.', 'error')

                    u = User.query.filter(User.email == request.form.get('email')).scalar()
                    if u.domain is not None:
                        return redirect(url_for('user.login', subdomain=u.domain))
                    return redirect(url_for('user.login'))

                subdomain = request.form.get('domain').replace(' ', '')

                if db.session.query(exists().where(func.lower(Domain.name) == subdomain.lower())).scalar():
                    flash('That domain is already in use. Please try another.', 'error')
                    return render_template('user/signup.html', form=form)

                u = User()

                form.populate_obj(u)
                u.password = User.encrypt_password(request.form.get('password'))
                u.role = 'creator'
                
                # Save the user to the database
                u.save()

                if login_user(u):
                    from app.blueprints.user.tasks import send_creator_welcome_email
                    # from app.blueprints.contact.mailerlite import create_subscriber

                    send_creator_welcome_email.delay(current_user.email)
                    # create_subscriber(current_user.email)

                    # Create the domain from the form, as well as the heroku subdomain
                    from app.blueprints.base.functions import create_domain
                    from app.blueprints.base.tasks import populate_domain, create_heroku_subdomain

                    # Create the domain in the database
                    d = create_domain(u, form.domain.data, form.company.data)

                    # Populate the domain with a private key
                    populate_domain.delay(d)

                    # Create the Heroku and Cloudflare subdomains
                    create_heroku_subdomain.delay(form.domain.data)

                    # Log the user in
                    flash("You've successfully signed up!", 'success')
                    return redirect(url_for('user.start', subdomain=subdomain))
        except Exception as e:
            print_traceback(e)

        return render_template('user/signup.html', form=form)


@user.route('/logout')
@user.route('/logout', subdomain='<subdomain>')
@login_required
def logout(subdomain=None):
    if subdomain:
        logout_user()
        # next = request.referrer
        flash('You have been logged out.', 'success')
        return redirect(url_for('user.dashboard', subdomain=subdomain))
    else:
        logout_user()
        flash('You have been logged out.', 'success')
        return redirect(url_for('user.login'))


@user.route('/account/begin_password_reset', methods=['GET', 'POST'])
@anonymous_required()
def begin_password_reset():
    form = BeginPasswordResetForm()

    if form.validate_on_submit():
        u = User.initialize_password_reset(request.form.get('identity'))

        flash('An email has been sent to {0}.'.format(u.email), 'success')
        return redirect(url_for('user.login'))

    return render_template('user/begin_password_reset.html', form=form)


@user.route('/account/password_reset', methods=['GET', 'POST'])
@anonymous_required()
def password_reset():
    form = PasswordResetForm(reset_token=request.args.get('reset_token'))

    if form.validate_on_submit():
        u = User.deserialize_token(request.form.get('reset_token'))

        if u is None:
            flash('Your reset token has expired or was tampered with.',
                  'error')
            return redirect(url_for('user.begin_password_reset'))

        form.populate_obj(u)
        u.password = User.encrypt_password(request.form.get('password'))
        u.save()

        if login_user(u):
            flash('Your password has been reset.', 'success')
            return redirect(url_for('user.settings'))

    return render_template('user/password_reset.html', form=form)


@user.route('/start', methods=['GET', 'POST'])
@user.route('/start/<subdomain>', methods=['GET', 'POST'])
@login_required
def start(subdomain=None):
    if not current_user.is_authenticated:
        return redirect(url_for('user.login'))

    if not current_user.domain == subdomain:
        return redirect(url_for('user.settings'))

    domain = Domain.query.filter(Domain.name == current_user.domain).scalar()
    return render_template('user/start.html', current_user=current_user, domain=domain, subdomain=subdomain)


@user.route('/settings/update_credentials', methods=['GET', 'POST'])
@user.route('/settings/update_credentials', subdomain='<subdomain>', methods=['GET', 'POST'])
@login_required
def update_credentials(subdomain=None):
    form = UpdateCredentials(current_user, uid=current_user.id)

    if form.validate_on_submit():
        name = request.form.get('name', '')
        username = request.form.get('username', '')
        new_password = request.form.get('password', '')
        current_user.email = request.form.get('email')

        if new_password:
            current_user.password = User.encrypt_password(new_password)

        current_user.name = name
        current_user.username = username
        current_user.save()

        flash('Your credentials have been updated.', 'success')
        return redirect(url_for('user.settings', subdomain=subdomain))

    return render_template('user/update_credentials.html', form=form, subdomain=subdomain)


@user.route('/dashboard', methods=['GET','POST'])
@user.route('/dashboard', subdomain='<subdomain>', methods=['GET','POST'])
@csrf.exempt
@cross_origin()
def dashboard(subdomain=None):
    demo = False
    from app.blueprints.base.functions import get_new_feedback
    new_feedback = get_new_feedback(current_user)

    if subdomain:
        from app.blueprints.api.functions import site_exists
        # if not site_exists(subdomain):
        #     return redirect(url_for('user.settings'))

        if subdomain == 'demo':
            demo = True
            d = Domain.query.filter(Domain.name == 'demo').scalar()
        else:
            d = Domain.query.filter(Domain.name == subdomain).scalar()

        if d is not None:
            if is_admin(current_user, d.name):
                feedbacks = Feedback.query.filter(and_(Feedback.domain_id == d.domain_id, Feedback.approved.is_(True), Feedback.status_id != 5964768)).all()
            else:
                feedbacks = Feedback.query.filter(and_(Feedback.domain_id == d.domain_id, Feedback.approved.is_(True))).all()

            if current_user.is_authenticated:
                votes = Vote.query.filter(and_(Vote.user_id == current_user.id, Vote.domain_id == d.domain_id)).all()
            else:
                votes = None

            statuses = Status.query.all()

            for f in feedbacks:
                f.votes = int(f.votes)
                f.comments = int(f.comments)

            feedbacks.sort(key=lambda x: x.created_on, reverse=True)
            return render_template('user/dashboard.html',
                                   current_user=current_user,
                                   feedbacks=feedbacks,
                                   new_feedback=new_feedback,
                                   statuses=statuses,
                                   domain=d,
                                   demo=demo,
                                   subdomain=subdomain,
                                   votes=votes,
                                   admin=is_admin(current_user, d.name),
                                   use_username=use_username)
        return redirect(url_for('user.settings', subdomain=subdomain))
    else:
        subdomain = 'demo'
        demo = True

        d = Domain.query.filter(Domain.name == subdomain).scalar()
        feedbacks = Feedback.query.all()
        statuses = Status.query.all()

        for f in feedbacks:
            f.votes = int(f.votes)

        feedbacks.sort(key=lambda x: x.created_on, reverse=True)
        return render_template('user/dashboard.html',
                               current_user=current_user,
                               feedbacks=feedbacks,
                               statuses=statuses,
                               domain=d,
                               subdomain=subdomain,
                               demo=demo,
                               admin=is_admin(current_user, d.name),
                               use_username=use_username)


@user.route('/dashboard/<domain>', methods=['GET','POST'])
@csrf.exempt
@cross_origin()
def dashboard_redirect(domain):
    return redirect(url_for('user.dashboard', subdomain=domain))


@user.route('/dashboard', methods=['GET','POST'])
@csrf.exempt
@cross_origin()
def demo():
    return redirect(url_for('user.dashboard', subdomain='demo'))


# Feedback -------------------------------------------------------------------
'''
View feedback details
'''


@user.route('/feedback/<feedback_id>', methods=['GET','POST'])
@user.route('/feedback/<feedback_id>', subdomain='<subdomain>', methods=['GET','POST'])
@csrf.exempt
@cross_origin()
def feedback(feedback_id, subdomain):
    from app.blueprints.base.functions import get_new_feedback
    new_feedback = get_new_feedback(current_user)

    demo = False
    if subdomain == 'demo':
        demo = True

    f = Feedback.query.filter(Feedback.feedback_id == feedback_id).scalar()
    d = Domain.query.filter(Domain.name == subdomain).scalar()

    # If the feedback isn't approved yet, only let creators view it
    if not f.approved:
        if not is_admin(current_user, subdomain):
            return redirect(url_for('user.dashboard', subdomain=subdomain))

    # Redirect if feedback no longer exists
    if f is None:
        return redirect(url_for('user.dashboard', subdomain=subdomain))

    # Determine whether the current user voted on the feedback or not
    if current_user.is_authenticated:
        voted = db.session.query(exists().where(and_(Vote.feedback_id == feedback_id, Vote.user_id == current_user.id))).scalar()
    else:
        voted = False

    votes = len(Vote.query.filter(Vote.feedback_id == feedback_id).all())
    comments = len(Comment.query.filter(Comment.feedback_id == feedback_id).all())

    # Get the statuses
    statuses = Status.query.all()
    return render_template('user/view_feedback.html',
                           current_user=current_user,
                           feedback=f,
                           domain=d,
                           vote_count=votes,
                           comment_count=comments,
                           statuses=statuses,
                           subdomain=subdomain,
                           voted=voted,
                           demo=demo,
                           new_feedback=new_feedback,
                           use_username=use_username)


'''
Add feedback to the list
'''


@user.route('/add_feedback', methods=['POST'])
@user.route('/add_feedback', subdomain='<subdomain>', methods=['POST'])
@csrf.exempt
@cross_origin()
def add_feedback(subdomain=None):
    if subdomain:
        # If there is no user, redirect them to the login for this domain
        # if not current_user.is_authenticated:
            # return redirect(url_for('user.login', subdomain=subdomain))

        if request.method == 'POST':
            try:
                title = request.form['title']
                description = request.form['description']
                email = request.form['email'] if 'email' in request.form else ''

                from app.blueprints.base.functions import create_feedback

                if current_user.is_authenticated:
                    f = create_feedback(current_user, subdomain, None, title, description)

                    # Delete demo feedback after 60 seconds
                    if subdomain == 'demo':
                        from app.blueprints.base.tasks import delete_demo_feedback
                        delete_demo_feedback.delay(f.feedback_id)
                else:
                    f = create_feedback(None, subdomain, email, title, description)

                    # Delete demo feedback after 60 seconds
                    if subdomain == 'demo':
                        from app.blueprints.base.tasks import delete_demo_feedback
                        delete_demo_feedback.delay(f.feedback_id)

                return redirect(url_for('user.dashboard', subdomain=subdomain))
            except Exception:
                flash("Uh oh, something went wrong!", "error")
                return redirect(url_for('user.dashboard', subdomain=subdomain))

        return render_template('user/add_feedback.html', current_user=current_user, subdomain=subdomain)
    else:
        if request.method == 'POST':
            try:
                title = request.form['title']
                description = request.form['description']
                email = request.form['email'] if 'email' in request.form else None

                from app.blueprints.base.functions import create_feedback

                if current_user.is_authenticated:
                    f = create_feedback(current_user, 'demo', None, title, description)
                else:
                    f = create_feedback(None, 'demo', email, title, description)

                from app.blueprints.base.tasks import delete_demo_feedback
                delete_demo_feedback.delay(f.feedback_id)

                return redirect(url_for('user.dashboard'))
            except Exception:
                flash("Uh oh, something went wrong!", "error")
                return redirect(url_for('user.dashboard'))

        return render_template('user/add_feedback.html', current_user=current_user)


'''
Update the feedback
'''


@user.route('/update_feedback', subdomain='<subdomain>', methods=['POST'])
@csrf.exempt
@cross_origin()
def update_feedback(subdomain=None):
    if request.method == 'POST':
        try:
            feedback_id = request.form['feedback_id']
            title = request.form['title']
            description = request.form['description']
            status_id = request.form['status']

            from app.blueprints.base.functions import update_feedback
            if update_feedback(feedback_id, subdomain, title, description, status_id) is not None:
                return redirect(url_for('user.feedback', feedback_id=feedback_id, subdomain=subdomain))

            flash("Uh oh, something went wrong!", "error")
            return redirect(url_for('user.dashboard', subdomain=subdomain))
        except Exception:
            flash("Uh oh, something went wrong!", "error")
            return redirect(url_for('user.dashboard', subdomain=subdomain))

    return render_template('user/add_feedback.html', current_user=current_user, subdomain=subdomain)


'''
Delete the feedback
'''


@user.route('/delete_feedback/<feedback_id>', subdomain='<subdomain>', methods=['GET'])
@csrf.exempt
@cross_origin()
def delete_feedback(feedback_id, subdomain=None):
    try:
        f = Feedback.query.filter(Feedback.feedback_id == feedback_id).scalar()
        f.delete()

        return redirect(url_for('user.dashboard', subdomain=subdomain))
    except Exception:
        flash("Uh oh, something went wrong!", "error")
        return redirect(url_for('user.feedback', feedback_id=feedback_id, subdomain=subdomain))


'''
Sort the feedback by newest, oldest, or most votes
'''


@user.route('/dashboard/<s>', methods=['GET', 'POST'])
@user.route('/dashboard/<s>', subdomain='<subdomain>', methods=['GET','POST'])
@csrf.exempt
@cross_origin()
def sort_feedback(s, subdomain=None):
    if subdomain:
        if is_admin(current_user, subdomain):
            feedbacks = Feedback.query.filter(and_(Feedback.domain == subdomain, Feedback.status_id != 5964768)).all()
        else:
            feedbacks = Feedback.query.filter(Feedback.domain == subdomain).all()
        d = Domain.query.filter(Domain.name == subdomain).scalar()
        statuses = Status.query.all()

        if s == 'newest':
            feedbacks.sort(key=lambda x: x.created_on, reverse=True)
        elif s == 'oldest':
            feedbacks.sort(key=lambda x: x.created_on)
        else:
            for f in feedbacks:
                f.votes = int(f.votes)

            feedbacks.sort(key=lambda x: x.votes, reverse=True)

        return render_template('user/dashboard.html', current_user=current_user, feedbacks=feedbacks, statuses=statuses, s=s, domain=d, subdomain=subdomain)
    else:
        feedbacks = Feedback.query.filter(Feedback.domain == 'demo').all()
        d = Domain.query.filter(Domain.name == 'demo').scalar()
        statuses = Status.query.all()

        if s == 'newest':
            feedbacks.sort(key=lambda x: x.created_on, reverse=True)
        elif s == 'oldest':
            feedbacks.sort(key=lambda x: x.created_on)
        else:
            for f in feedbacks:
                f.votes = int(f.votes)

            feedbacks.sort(key=lambda x: x.votes, reverse=True)

        return render_template('user/dashboard.html', current_user=current_user, feedbacks=feedbacks, statuses=statuses, s=s, domain=d, subdomain=demo)


@user.route('/feedback_approval', subdomain='<subdomain>', methods=['GET','POST'])
@csrf.exempt
@cross_origin()
def feedback_approval(subdomain=None):
    from app.blueprints.base.functions import get_new_feedback
    new_feedback = get_new_feedback(current_user)

    if not subdomain:
        return redirect(url_for('user.settings'))
    else:
        d = Domain.query.filter(Domain.name == subdomain).scalar()

        if not is_admin(current_user, subdomain):
            return redirect(url_for('user.settings'))

        if d is not None:
            feedbacks = Feedback.query.filter(and_(Feedback.domain_id == d.domain_id, Feedback.approved.is_(False))).all()

            feedbacks.sort(key=lambda x: x.created_on, reverse=True)
            return render_template('user/approval.html',
                                   current_user=current_user,
                                   feedbacks=feedbacks,
                                   domain=d,
                                   subdomain=subdomain,
                                   new_feedback=new_feedback,
                                   use_username=use_username)
        return redirect(url_for('user.settings', subdomain=subdomain))


@user.route('/approve_feedback', methods=['GET', 'POST'])
# @login_required
@csrf.exempt
def approve_feedback():
    try:
        if request.method == 'POST':
            if 'feedback_id' in request.form and 'approve' in request.form:
                feedback_id = request.form['feedback_id']
                approve = True if request.form['approve'] == 'true' else False

                f = Feedback.query.filter(Feedback.feedback_id == feedback_id).scalar()
                d = Domain.query.filter(Domain.domain_id == f.domain_id).scalar
                if approve and f is not None and d is not None and is_admin(current_user, d.name):
                    f.approved = True
                    f.save()
                else:
                    f.delete()

                return jsonify({'success': 'Success'})
        return jsonify({'error': 'Error'})
    except Exception as e:
        return jsonify({'error': 'Error'})

# Comments -------------------------------------------------------------------
'''
Get comments
'''


@user.route('/get_comments', methods=['GET','POST'])
@csrf.exempt
@cross_origin()
def get_comments():
    try:
        if request.method == 'POST':
            from app.blueprints.base.tasks import format_comments
            feedback_id = request.form['feedback_id']
            user_id = request.form['user_id']

            comments = format_comments(feedback_id, user_id)

            return jsonify({'comments': comments})
    except Exception as e:
        return jsonify({'comments': None})


'''
Add a comment
'''


@user.route('/add_comment', methods=['POST'])
@csrf.exempt
@cross_origin()
def add_comment():
    try:
        from app.blueprints.base.functions import add_comment
        if request.method == 'POST':
            if 'feedback_id' in request.form:
                feedback_id = request.form['feedback_id']
                if 'email' in request.form:
                    email = request.form['email']
                    parent_id = request.form['parent']
                    content = request.form['content']
                    created_by_user = True if request.form['created_by_current_user'] == 'true' else False

                    f = Feedback.query.filter(Feedback.feedback_id == feedback_id).scalar()

                    if f is not None:
                        if add_comment(feedback_id, content, f.domain_id, None, email, parent_id, created_by_user):
                            f.comments += 1
                            f.save()
                elif 'user_id' in request.form:
                    user_id = request.form['user_id']
                    parent_id = request.form['parent']
                    content = request.form['content']
                    created_by_user = True if request.form['created_by_current_user'] == 'true' else False

                    f = Feedback.query.filter(Feedback.feedback_id == feedback_id).scalar()

                    if f is not None:
                        if add_comment(feedback_id, content, f.domain_id, user_id, None, parent_id, created_by_user):
                            f.comments += 1
                            f.save()
                    return jsonify({'result': 'Success'})
    except Exception as e:
        return jsonify({'result': 'Error'})


'''
Update a comment
'''


@user.route('/update_comment', methods=['POST'])
@csrf.exempt
@cross_origin()
def update_comment():
    try:
        from app.blueprints.base.functions import update_comment
        if request.method == 'POST':
            comment_id = request.form['id']
            content = request.form['content']

            c = Comment.query.filter(Comment.comment_id == comment_id).scalar()
            if c is not None:
                update_comment(c, content)

        return jsonify({'result': 'Success'})
    except Exception as e:
        return jsonify({'result': 'Error'})


# Votes -------------------------------------------------------------------
'''
Add or remove a vote
'''


@user.route('/update_vote', subdomain='<subdomain>', methods=['GET','POST'])
@csrf.exempt
@cross_origin()
def update_vote(subdomain=None):
    try:
        if request.method == 'POST':
            if 'feedback_id' in request.form:
                feedback_id = request.form['feedback_id']

                if 'email' in request.form:
                    email = request.form['email']
                    from app.blueprints.base.functions import add_vote

                    f = Feedback.query.filter(Feedback.feedback_id == feedback_id).scalar()

                    if f is not None:
                        add_vote(f, None, email)

                    return jsonify({'success': 'Success'})
                elif 'user_id' in request.form:
                    user_id = request.form['user_id']
                    from app.blueprints.base.functions import add_vote, remove_vote

                    if db.session.query(exists().where(and_(Vote.feedback_id == feedback_id, Vote.user_id == user_id))).scalar():
                        vote = Vote.query.filter(and_(Vote.feedback_id == feedback_id, Vote.user_id == user_id)).scalar()
                        f = Feedback.query.filter(Feedback.feedback_id == feedback_id).scalar()

                        if f is not None:
                            remove_vote(f, vote)
                    else:
                        f = Feedback.query.filter(Feedback.feedback_id == feedback_id).scalar()

                        if f is not None:
                            add_vote(f, user_id)

                    return jsonify({'success': 'Success'})
    except Exception as e:
        from app.blueprints.base.functions import print_traceback
        print_traceback(e)

    return redirect(url_for('user.dashboard', subdomain=subdomain))


# Widgets -------------------------------------------------------------------
@user.route('/widgets', methods=['GET','POST'])
@user.route('/widgets', subdomain='<subdomain>', methods=['GET','POST'])
def widgets(subdomain=None):
    if subdomain:
        return render_template('user/widgets.html', current_user=current_user, subdomain=subdomain)
    else:
        return render_template('user/widgets.html', current_user=current_user)


# Roadmap -------------------------------------------------------------------
@user.route('/roadmap', methods=['GET','POST'])
@user.route('/roadmap', subdomain='<subdomain>', methods=['GET','POST'])
@csrf.exempt
def roadmap(subdomain=None):
    return render_template('user/roadmap.html', current_user=current_user, subdomain=subdomain)


# Settings -------------------------------------------------------------------
@user.route('/settings', methods=['GET','POST'])
@user.route('/settings', subdomain='<subdomain>', methods=['GET','POST'])
@login_required
@csrf.exempt
def settings(subdomain=None):
    from app.blueprints.base.functions import get_new_feedback
    new_feedback = get_new_feedback(current_user)

    if subdomain:
        domain = Domain.query.filter(Domain.user_id == current_user.id).scalar()
        return render_template('user/settings.html', current_user=current_user, domain=domain, subdomain=subdomain, new_feedback=new_feedback)
    else:
        domain = Domain.query.filter(Domain.user_id == current_user.id).scalar()
        return render_template('user/settings.html', current_user=current_user, domain=domain, new_feedback=new_feedback)


# Actions -------------------------------------------------------------------
@user.route('/send_invite', subdomain='<subdomain>', methods=['GET','POST'])
@login_required
@csrf.exempt
def send_invite(subdomain=None):
    return redirect(url_for('user.dashboard', subdomain=subdomain))


@user.route('/get_private_key', methods=['GET','POST'])
@csrf.exempt
@cross_origin()
def get_private_key():
    try:
        if request.method == 'POST':
            if 'domain_id' in request.form and 'user_id' in request.form:
                domain_id = request.form['domain_id']
                user_id = request.form['user_id']

                from app.blueprints.base.functions import get_private_key
                key = get_private_key(domain_id, user_id)
                return jsonify({'success': True, 'key': key})
    except Exception as e:
        return jsonify({'success': False})
    return jsonify({'success': False})


@user.route('/check_domain_status', methods=['GET','POST'])
@login_required
@csrf.exempt
@cross_origin()
def check_domain_status():
    try:
        # time.sleep(10)
        if request.method == 'POST':
            if 'subdomain' in request.form and 'user_id' in request.form:
                subdomain = request.form['subdomain']
                user_id = request.form['user_id']

                u = User.query.filter(User.id == user_id).scalar()

                if subdomain == u.domain:
                    try:

                        url = 'https://' + subdomain + '.recurrify.io'

                        r = requests.get(url, verify=False)

                        if r.status_code == 200:
                            r.close()
                            return jsonify({'result': 'Success', 'code': r.status_code})
                        else:
                            r.close()
                            return jsonify({'result': 'Error', 'code': r.status_code})
                    except ConnectionError as c:
                        return jsonify({'result': 'Error'})
        return jsonify({'result': 'Error'})
    except Exception as e:
        from app.blueprints.base.functions import print_traceback
        print_traceback(e)
        return jsonify({'result': 'Error'})


@user.route('/set_domain_privacy', methods=['GET', 'POST'])
# @login_required
@csrf.exempt
def set_domain_privacy():
    try:
        if request.method == 'POST':
            if 'domain_id' in request.form and 'privacy' in request.form:
                domain_id = request.form['domain_id']
                privacy = request.form['privacy']

                d = Domain.query.filter(Domain.domain_id == domain_id).scalar()
                d.private = True if privacy == 'true' else False
                d.save()

                return jsonify({'success': 'Success'})
        return jsonify({'error': 'Error'})
    except Exception as e:
        return jsonify({'error': 'Error'})


@user.route('/set_domain_approval', methods=['GET', 'POST'])
# @login_required
@csrf.exempt
def set_domain_approval():
    try:
        if request.method == 'POST':
            if 'domain_id' in request.form and 'approval' in request.form:
                domain_id = request.form['domain_id']
                approval = request.form['approval']

                d = Domain.query.filter(Domain.domain_id == domain_id).scalar()
                d.requires_approval = True if approval == 'true' else False
                d.save()

                return jsonify({'success': 'Success'})
        return jsonify({'error': 'Error'})
    except Exception as e:
        return jsonify({'error': 'Error'})


# Contact us -------------------------------------------------------------------
@user.route('/contact', methods=['GET','POST'])
@csrf.exempt
def contact():
    if request.method == 'POST':
        from app.blueprints.user.tasks import send_contact_us_email
        send_contact_us_email.delay(request.form['email'], request.form['message'])

        flash('Thanks for your email! You can expect a response shortly.', 'success')
        return redirect(url_for('user.contact'))
    return render_template('user/contact.html', current_user=current_user)


# Testing ----------------------------------------------------------------------
@user.route('/test', methods=['GET','POST'])
@user.route('/test', subdomain='<subdomain>', methods=['GET','POST'])
@login_required
@csrf.exempt
def test(subdomain=None):
    if subdomain:
        domain = Domain.query.filter(Domain.user_id == current_user.id).scalar()
        return render_template('user/test.html', current_user=current_user, domain=domain, subdomain=subdomain)
    else:
        domain = Domain.query.filter(Domain.user_id == current_user.id).scalar()
        return render_template('user/test.html', current_user=current_user, domain=domain)
