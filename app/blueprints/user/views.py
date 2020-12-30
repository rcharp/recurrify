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
import pprint
from operator import attrgetter
from flask_cors import cross_origin
from flask_paginate import Pagination, get_page_args
from lib.safe_next_url import safe_next_url
from app.blueprints.user.decorators import anonymous_required
from app.blueprints.shopify.functions import get_all_products, update_sync, get_product_count, get_product_by_id
from app.blueprints.user.models.user import User
from app.blueprints.base.functions import get_pagination
from app.blueprints.shopify.models.shop import Shop
from app.blueprints.shopify.models.sync import Sync
from app.blueprints.shopify.models.product import SyncedProduct
from app.blueprints.shopify.models.plan import Plan
from app.blueprints.user.forms import (
    LoginForm,
    LoginFormExistingStore,
    BeginPasswordResetForm,
    PasswordResetForm,
    SignupFormDestinationStore,
    SignupFormSourceStore,
    WelcomeForm,
    UpdateCredentials)

from app.extensions import cache, csrf, timeout, db
from importlib import import_module
from sqlalchemy import or_, and_, exists, inspect, func
from app.blueprints.base.functions import is_admin

user = Blueprint('user', __name__, template_folder='templates')
use_username = False


"""
User
"""


# Login and Credentials -------------------------------------------------------------------
@user.route('/login', methods=['GET', 'POST'])
@anonymous_required()
@csrf.exempt
def login():

    # This is when setting up a destination store, and the user already has an account with a source store
    if 'shopify_url' in session and session['shopify_url'] is not None and 'shopify_email' in session and session['shopify_email'] is not None:
        form = LoginFormExistingStore()
        form.url.data = session['shopify_url']
        form.identity.data = session['shopify_email']

        if form.validate_on_submit():
            u = User.find_by_identity(request.form.get('identity'))

            if u and u.is_active() and u.authenticated(password=request.form.get('password')):

                if login_user(u, remember=True) and u.is_active():

                    u.update_activity_tracking(request.remote_addr)

                    next_url = request.form.get('next')

                    if next_url == url_for('user.login') or next_url == '' or next_url is None:
                        # Take them to the settings page
                        next_url = url_for('user.start', shop_url=session['shopify_url'])

                    if next_url:
                        return redirect(safe_next_url(next_url), code=307)
                else:
                    flash('This account has been disabled.', 'error')
            else:
                flash('Your username/email or password is incorrect.', 'error')

        else:
            if len(form.errors) > 0:
                print(form.errors)

        return render_template('user/login_existing_store.html', form=form, url=session['shopify_url'])
    else:
        form = LoginForm(next=request.args.get('next'))

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
                        next_url = url_for('user.dashboard')

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
@anonymous_required()
@csrf.exempt
def signup():
    from app.blueprints.base.functions import print_traceback
    form = SignupFormSourceStore()

    # Populate the form
    if 'shopify_url' in session and 'shopify_email' in session:
        form.url.data = session['shopify_url']
        form.email.data = session['shopify_email']

    try:
        if form.validate_on_submit():
            if db.session.query(exists().where(User.email == request.form.get('email'))).scalar():
                flash(Markup("There is already an account using this email. Please use another or <a href='" + url_for(
                    'user.login') + "'><span class='text-indigo-700'><u>login</span></u></a>."), category='error')
                return redirect(url_for('user.signup'))

            u = User()

            form.populate_obj(u)
            u.password = User.encrypt_password(request.form.get('password'))
            u.role = 'owner'

            # Save the user to the database
            u.save()

            if login_user(u):

                # Set the shop's user id to the current user
                if 'shopify_id' in session and session['shopify_id'] is not None:
                    shop = Shop.query.filter(Shop.shopify_id == session['shopify_id']).scalar()
                    if shop is not None:
                        shop.user_id = u.id
                        shop.save()

                        flash("You've successfully signed up!", 'success')
                        return redirect(url_for('user.start', shop_url=shop.url))

                # from app.blueprints.user.tasks import send_owner_welcome_email
                # from app.blueprints.contact.mailerlite import create_subscriber

                # send_owner_welcome_email.delay(current_user.email)
                # create_subscriber(current_user.email)

                # Log the user in
                flash("You've successfully signed up!", 'success')
                return redirect(url_for('user.dashboard'))
            else:
                # Delete the shop from the database
                if 'shopify_id' in session and session['shopify_id'] is not None:
                    shop = Shop.query.filter(Shop.shopify_id == session['shopify_id']).scalar()
                    if shop is not None:
                        shop.delete()
    except Exception as e:
        # Delete the shop from the database
        if 'shopify_id' in session and session['shopify_id'] is not None:
            shop = Shop.query.filter(Shop.shopify_id == session['shopify_id']).scalar()
            if shop is not None:
                shop.delete()
        print_traceback(e)

    return render_template('user/signup.html', form=form)


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


"""
Pages
"""


@user.route('/dashboard/', methods=['GET', 'POST'])
@user.route('/dashboard/<int:page>', methods=['GET', 'POST'])
@csrf.exempt
@cross_origin()
def dashboard(page=1):
    shop = Shop.query.filter(Shop.user_id == current_user.id).scalar()

    products = get_all_products(shop)

    # How many products per page
    offset = 20
    page_start, page_finish, pagination, total_pages = get_pagination(products, offset, page)
    prev_page, next_page = page - 1, page + 1

    # Print the list
    # pprint.pprint(products)

    return render_template('user/dashboard.html', current_user=current_user, total=len(products),
                           products=pagination, start=page_start, finish=page_finish,
                           total_pages=total_pages, page=page, prev=prev_page, next=next_page)


@user.route('/start', methods=['GET', 'POST'])
@user.route('/start/<shop_url>', methods=['GET', 'POST'])
@login_required
def start(shop_url):
    if not current_user.is_authenticated:
        return redirect(url_for('user.login'))

    shop = Shop.query.filter(Shop.url == shop_url).scalar()
    if shop is None:
        return redirect(url_for('user.dashboard'))

    pending = Sync.query.filter(and_(Sync.destination_url == shop_url, Sync.active.is_(False))).all()
    plans = Plan.query.all()

    return render_template('user/start.html', current_user=current_user, shop_id=shop.shop_id, pending=pending, plans=plans)


# Settings -------------------------------------------------------------------
@user.route('/settings', methods=['GET', 'POST'])
@login_required
@csrf.exempt
def settings():
    shop = Shop.query.filter(Shop.user_id == current_user.id).scalar()

    if shop is None:
        return redirect(url_for('user.logout'))
    destinations = [x.destination_url for x in Sync.query.filter(Sync.user_id == current_user.id)]
    return render_template('user/settings.html', current_user=current_user, shop=shop, destinations=destinations)


"""
Syncing
"""


@user.route('/sync/', methods=['GET', 'POST'])
@user.route('/sync/<sync_id>', methods=['GET', 'POST'])
@csrf.exempt
@cross_origin()
def sync(sync_id=None):
    if sync_id is not None:
        s = Sync.query.filter(Sync.sync_id == sync_id).scalar()
        if s is None:
            return redirect(url_for('user.dashboard'))

        source = Shop.query.filter(Shop.shop_id == s.source_id).scalar()
        destination = Shop.query.filter(Shop.shop_id == s.destination_id).scalar()

        if source is None or destination is None:
            return redirect(url_for('user.dashboard'))

        products = get_all_products(source)
        # products = products * 10
        synced_product_ids = [str(x.source_product_id) for x in SyncedProduct.query.filter(SyncedProduct.sync_id == sync_id)]

        # Get the plan limit
        p = Plan.query.filter(Plan.id == s.plan_id).scalar()
        limit = p.limit if p is not None and p.limit is not None else 3

        return render_template('user/sync.html', sync=s, source=source, destination=destination, products=products,
                               product_ids=synced_product_ids, limit=limit)
    else:
        shop = Shop.query.filter(Shop.user_id == current_user.id).scalar()
        plans = Plan.query.all()
        return render_template('user/create_sync.html', shop=shop, plans=plans)


@user.route('/create_sync', methods=['GET', 'POST'])
@login_required
def create_sync():
    if not current_user.is_authenticated:
        return redirect(url_for('user.login'))
    if request.method == 'POST':
        if 'shop_id' in request.form:
            s = Shop.query.filter(Shop.shop_id == request.form['shop_id']).scalar()
            if s is not None:
                # They're on the start page
                if 'store_type' in request.form:
                    # They're setting it up as a destination store
                    if request.form['store_type'] == 'destination':
                        t = Sync.query.filter(Sync.destination_url == request.form['source_url']).scalar()
                        if t is not None:
                            t.destination_url = s.url
                            t.destination_id = s.shop_id
                            t.save()

                            flash(Markup("You're successfully synced with " + request.form['source_url'] + "."),
                                  category='success')
                            return redirect(url_for('user.syncs'))
                        else:
                            flash("There was an error.", "error")
                            return redirect(url_for('user.settings'))

                    # They're setting it up as a source store
                    s.source = True
                    s.save()
                    flash(Markup("You've successfully set up your store to sync with others. Click \"Sync a new store!\" "
                                 "above to sell your products on another store."), category='success')

                # They're on the sync page
                else:
                    # Create a new sync
                    if 'destination_url' and 'plan_id' in request.form:
                        destination_url = request.form['destination_url']

                        if db.session.query(exists().where(and_(Sync.source_id == s.shop_id, Sync.destination_url == destination_url))).scalar():
                            flash(Markup("There is already an existing sync with " + destination_url + ". Please go to stores above to see syncs."), category='error')
                            return redirect(url_for('user.dashboard'))

                        plan = request.form['plan_id']

                        # Get the associated plan
                        p = Plan.query.filter(Plan.tag == plan).scalar()

                        if p is None:
                            flash(Markup("There was an error. Please try again."), category='error')
                            return redirect(url_for('user.dashboard'))

                        # Create the sync
                        t = Sync()
                        t.source_id = s.shop_id
                        t.source_url = s.url
                        t.destination_url = destination_url
                        t.plan = p.tag
                        t.plan_id = p.id
                        t.user_id = current_user.id

                        t.save()

                        flash(Markup("You've initiated a sync with " + destination_url + ". That store owner needs to install " + current_app.config.get('APP_NAME') + " to complete the sync."),
                              category='success')
                        return redirect(url_for('user.dashboard', store_id=s.shop_id))
                    flash(Markup("There was an error. Please try again."), category='error')
            else:
                flash(Markup("That store couldn't be found. Please try again."), category='error')
    return redirect(url_for('user.dashboard'))


@user.route('/activate_sync', methods=['GET', 'POST'])
@login_required
def activate_sync():
    try:
        if request.method == 'POST':
            if 'sync_id' in request.form and 'shop_id' in request.form and 'activate' in request.form:
                sync_id = request.form['sync_id']
                shop_id = request.form['shop_id']
                activate = request.form['activate']

                s = Sync.query.filter(Sync.sync_id == sync_id).scalar()
                if s is not None:
                    s.destination_id = shop_id
                    s.active = True if activate == 'true' else False
                    s.save()

                return jsonify({'success': 'Success'})
        return jsonify({'error': 'Error'})
    except Exception as e:
        return jsonify({'error': 'Error'})


@user.route('/submit_sync', methods=['GET', 'POST'])
@login_required
def submit_sync():
    try:
        if request.method == 'POST':
            if 'sync_id' in request.form:
                product_ids = list()
                sync_id = request.form['sync_id']

                # Get the checked products from the page
                if 'product[]' in request.form:
                    product_ids = request.form.getlist('product[]')

                # Get the count
                count = update_sync(sync_id, product_ids)

                if count >= 0:
                    return jsonify({'success': 'Success', 'count': count})
                return jsonify({'error': 'Error'})
    except Exception as e:
        from app.blueprints.base.functions import print_traceback
        print_traceback(e)

        flash("There was an error.", 'error')
    return redirect(url_for('user.dashboard'))


@user.route('/sync_all_products', methods=['GET', 'POST'])
@login_required
def sync_all_products():
    try:
        if request.method == 'POST':
            if 'sync_id' in request.form:
                sync_id = request.form['sync_id']

                s = Sync.query.filter(Sync.sync_id == sync_id).scalar()

                from app.blueprints.shopify.functions import sync_all_products
                success = sync_all_products(s)

                if success:
                    return jsonify({'success': 'Success'})
        return jsonify({'error': 'Error'})
    except Exception as e:
        from app.blueprints.base.functions import print_traceback
        print_traceback(e)
        return jsonify({'error': 'Error'})


"""
Stores and Products
"""


@user.route('/syncs/', methods=['GET', 'POST'])
@csrf.exempt
@cross_origin()
def syncs():
    sources = Shop.query.filter(and_(Shop.user_id == current_user.id, Shop.source.is_(True))).all()
    destinations = Sync.query.filter(Sync.user_id == current_user.id).all()
    plans = Plan.query.all()
    product_counts = [{'id': x.shop_id, 'count': get_product_count(x)['count']} for x in sources]
    sync_counts = [{'id': x.sync_id, 'count': SyncedProduct.query.filter(SyncedProduct.sync_id == x.sync_id).count()} for x in destinations]
    return render_template('user/syncs.html', plans=plans,
                           sources=sources,
                           destinations=destinations,
                           sync_counts=sync_counts,
                           product_counts=product_counts)


@user.route('/product/<product_id>', methods=['GET', 'POST'])
@csrf.exempt
@cross_origin()
def product(product_id):
    from itertools import chain

    shop = Shop.query.filter(Shop.user_id == current_user.id).scalar()
    p = get_product_by_id(shop, product_id, return_json=True)

    if p is None:
        flash("Product not found", 'error')
        return redirect(url_for('user.dashboard'))

    syncs = [x.sync_id for x in SyncedProduct.query.filter(SyncedProduct.source_product_id == p['id'])]
    store_names = list(
        chain.from_iterable([[x.destination_url for x in Sync.query.filter(Sync.sync_id == y)] for y in syncs]))

    return render_template('user/product.html', current_user=current_user, product=p, stores=store_names)


@user.route('/dashboard/<s>', methods=['GET', 'POST'])
@csrf.exempt
@cross_origin()
def sort_products(s):
    shop = Shop.query.filter(Shop.user_id == current_user.id).scalar()
    products = get_all_products(shop)

    # Print the list
    # pprint.pprint(products)

    if s == 'alphabetical':
        products.sort(key=lambda x: x.title)
    else:
        products.sort(key=lambda x: x.created, reverse=True)

    return render_template('user/dashboard.html', current_user=current_user, s=s, products=products)


# Actions -------------------------------------------------------------------
@user.route('/get_private_key', methods=['GET', 'POST'])
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
@user.route('/contact', methods=['GET', 'POST'])
@csrf.exempt
def contact():
    if request.method == 'POST':
        from app.blueprints.user.tasks import send_contact_us_email
        send_contact_us_email.delay(request.form['email'], request.form['message'])

        flash('Thanks for your email! You can expect a response shortly.', 'success')
        return redirect(url_for('user.contact'))
    return render_template('user/contact.html', current_user=current_user)
