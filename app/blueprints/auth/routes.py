from flask import request, jsonify
from marshmallow import ValidationError
from werkzeug.security import check_password_hash
from app.models import Customer, Mechanic
from app.utils.util import encode_token, encode_mechanic_token
from sqlalchemy import select
from app import db
from . import auth_bp

# Customer login
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

    customer = db.session.execute(select(Customer).where(Customer.email == email)).scalars().first()

    if not customer or not check_password_hash(customer.password, password):
        return jsonify({'error': 'Invalid email or password'}), 400

    token = encode_token(customer.id)

    return jsonify({
        'status': 'Login successful',
        'token': token,
        'user': {
            'id': customer.id,
            'email': customer.email,
            'role': 'customer',
        }
    }), 200

# Mechanic login
@auth_bp.route('/mechanic_login', methods=['POST'])
def mechanic_login():
    try:
        credentials = request.json
        email = credentials.get('email')
        password = credentials.get('password')
    except Exception:
        return jsonify({'message': 'Invalid request format'}), 400

    if not email or not password:
        return jsonify({'error': 'Email and password are required'}), 400
    
    mechanic = db.session.execute(select(Mechanic).where(Mechanic.email == email)).scalars().first() 
    
    if not mechanic or not check_password_hash(mechanic.password, password):
        return jsonify({'error': 'Invalid email or password'}), 400

    token = encode_mechanic_token(mechanic.id)

    return jsonify({
        'token': token,
        'user': {
            'id': mechanic.id,
            'email': mechanic.email,
            'role': 'mechanic',
        }
    }), 200
