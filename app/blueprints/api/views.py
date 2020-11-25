from flask import Blueprint, render_template, json, flash, request, redirect, url_for, jsonify
from app.extensions import csrf

api = Blueprint('api', __name__, template_folder='templates')


@api.route('/api', methods=['GET', 'POST'])
@csrf.exempt
def filter(status):
    return jsonify({'success': 'Success!'})
