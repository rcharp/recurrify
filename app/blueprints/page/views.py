from flask import Blueprint, render_template, flash
from app.extensions import cache, timeout
from config import settings
from app.extensions import db, csrf
from flask import redirect, url_for, request, current_app
from flask_login import current_user, login_required
import requests
import ast
import json
import traceback
from sqlalchemy import and_, exists, text
from importlib import import_module
import os
import random
from flask_cors import cross_origin

page = Blueprint('page', __name__, template_folder='templates')


@page.route('/', methods=['GET', 'POST'])
@page.route('/', subdomain='<subdomain>')
@cross_origin()
def home(subdomain=None):
    if subdomain:
        return redirect(url_for('user.dashboard', subdomain=subdomain))

    if current_user.is_authenticated:
        if subdomain:
            return redirect(url_for('user.dashboard', subdomain=subdomain))
        else:
            return redirect(url_for('user.settings'))

    return render_template('page/index.html', plans=settings.STRIPE_PLANS)


@page.route('/terms')
@cross_origin()
def terms():
    return render_template('page/terms.html')


@page.route('/privacy')
@cross_origin()
def privacy():
    return render_template('page/privacy.html')


@page.route('/index')
@cross_origin()
def index():
    return render_template('page/index.html', plans=settings.STRIPE_PLANS)
