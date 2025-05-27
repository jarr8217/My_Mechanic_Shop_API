from flask import Blueprint, request, jsonify
from werkzeug.security import check_password_hash
from app.models import Customer
from app.utils.util import encode_token

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        credentials = request.json
        email = credentials.get('email')
        password = credentials.get('password')
    except KeyError:
        return jsonify({'message': 'Invalid request format'}), 400

    if not email or not password:
        return jsonify({'error': 'Email and password are required'}), 400

    customer = Customer.query.filter_by(email=email).first()

    if not customer or not check_password_hash(customer.password, password):
        return jsonify({'error': 'Invalid email or password'}), 400

    token = encode_token(customer.id)

    return jsonify({
        'token': token,
        'user': {
            'id': customer.id,
            'email': customer.email,
        }
    }), 200
