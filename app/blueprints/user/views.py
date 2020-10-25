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
from app.blueprints.user.models.user import User
from app.blueprints.shopify.models.shop import Shop
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
from app.blueprints.base.functions import is_admin

user = Blueprint('user', __name__, template_folder='templates')
use_username = False


# Login and Credentials -------------------------------------------------------------------
@user.route('/login', methods=['GET', 'POST'])
@anonymous_required()
@csrf.exempt
def login():
    form = LoginFormAnon(next=request.args.get('next'))

    if form.validate_on_submit():
        u = User.find_by_identity(request.form.get('identity'))

        if u and u.is_active() and u.authenticated(password=request.form.get('password')):

            if login_user(u, remember=True) and u.is_active():
                if current_user.role == 'admin':
                    return redirect(url_for('admin.dashboard'))

                u.update_activity_tracking(request.remote_addr)

                next_url = request.form.get('next')

                if next_url == url_for('user.login') or next_url == '' or next_url is None:

                    # Take them to the settings page
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
Signup with an account
'''


@user.route('/signup', methods=['GET', 'POST'])
@user.route('/signup/<email>/<url>', methods=['GET', 'POST'])
@anonymous_required()
@csrf.exempt
def signup(email=None, url=None):
    from app.blueprints.base.functions import print_traceback
    form = SignupFormAnon()

    if url is not None:
        form.url.data = url

    if email is not None:
        form.email.data = email

    s = int(request.args.get('shop_id'))
    print(s)

    try:
        if form.validate_on_submit():
            if db.session.query(exists().where(User.email == request.form.get('email'))).scalar():
                flash(Markup("There is already an account using this email. Please use another or <a href='" + url_for('user.login') + "'><span class='text-indigo-700'><u>login</span></u></a>."), category='error')
                return redirect(url_for('user.signup', shop_id=shop_id, email=email, url=url))

            u = User()

            form.populate_obj(u)
            u.password = User.encrypt_password(request.form.get('password'))
            u.role = 'owner'

            # Save the user to the database
            u.save()

            if login_user(u):

                # Set the shop's user id to the current user

                shop = Shop.query.filter(Shop.shop_id == s).scalar()
                print(shop)

                # from app.blueprints.user.tasks import send_owner_welcome_email
                # from app.blueprints.contact.mailerlite import create_subscriber

                # send_owner_welcome_email.delay(current_user.email)
                # create_subscriber(current_user.email)

                # Log the user in
                flash("You've successfully signed up!", 'success')
                return redirect(url_for('user.dashboard'))
    except Exception as e:
        print_traceback(e)

    return render_template('user/signup.html', form=form, email=email, url=url)


@user.route('/logout')
@login_required
def logout():
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
@login_required
def start():
    if not current_user.is_authenticated:
        return redirect(url_for('user.login'))
    return render_template('user/start.html', current_user=current_user)


@user.route('/settings/update_credentials', methods=['GET', 'POST'])
@login_required
def update_credentials():
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
        return redirect(url_for('user.settings'))

    return render_template('user/update_credentials.html', form=form)


@user.route('/dashboard', methods=['GET','POST'])
@csrf.exempt
@cross_origin()
def dashboard():
    return render_template('user/dashboard.html', current_user=current_user)


# Settings -------------------------------------------------------------------
@user.route('/settings', methods=['GET','POST'])
@login_required
@csrf.exempt
def settings():
    return render_template('user/settings.html', current_user=current_user)


# Actions -------------------------------------------------------------------
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
