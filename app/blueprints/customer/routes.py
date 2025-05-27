from app.utils.util import encode_token
from .schemas import customer_schema, customers_schema, login_schema
from flask import request, jsonify
from marshmallow import ValidationError
from sqlalchemy import select
from app.models import Customer, db
from . import customers_bp
from app.extensions import limiter, cache
from app.utils.decorators import token_required
from werkzeug.security import generate_password_hash, check_password_hash



# Customer login
@customers_bp.route('/login', methods=['POST'])
@limiter.limit('5 per minute; 50 per day')
def login():
    try:
        credentials = login_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    email = credentials['email']
    password = credentials['password']

    query = select(Customer).where(Customer.email == email)
    customer = db.session.execute(query).scalars().first()

    if not customer or not check_password_hash(customer.password, password):
        return jsonify({'message': 'Invalid email or password'}), 401

    token = encode_token(customer.id)

    response = {
        'status': 'success',
        'message': 'successfully logged in',
        'token': token
    }

    return jsonify(response), 200
# Create a new customer
@customers_bp.route('/', methods=['POST'])
@limiter.limit("3 per minute; 30 per day")
def create_customer():
    try:
        customer_data = customer_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400

    query = select(Customer).where(Customer.email == customer_data['email'], Customer.password == customer_data['password'])
    existing_customer = db.session.execute(query).scalars().all()
    if existing_customer:
        return jsonify({'error': "Email already exists"}), 400

    hashed_password = generate_password_hash(customer_data['password'])

    new_customer = Customer(
        name=customer_data['name'],
        email=customer_data['email'],
        phone=customer_data['phone'],
        password=hashed_password
    )
    db.session.add(new_customer)
    db.session.commit()
    return customer_schema.jsonify(new_customer), 201

# Get all customers
@customers_bp.route('/', methods=['GET'])
@limiter.limit('10 per minute; 200 per day')
@cache.cached(timeout=30)
def get_customers():
    query = select(Customer)
    customers = db.session.execute(query).scalars().all()
    return customers_schema.jsonify(customers), 200

# Get a customer by ID
@customers_bp.route('/<int:customer_id>', methods=['GET'])
@limiter.limit('10 per minute; 200 per day')
@cache.cached(timeout=60)
def get_customer(customer_id):
    customer = db.session.get(Customer, customer_id)
    if not customer:
        return jsonify({'error': 'Customer not found'}), 404
    return customer_schema.jsonify(customer), 200

# Update a customer
@customers_bp.route('/', methods=['PUT'])
@limiter.limit('5 per minute; 50 per day')
@token_required
def update_customer(customer_id):
    customer = db.session.get(Customer, customer_id)
    if not customer:
        return jsonify({'error': 'Customer not found'}), 404
    try:
        customer_data = customer_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400

    for key, value in customer_data.items():
        setattr(customer, key, value)

    db.session.commit()
    return customer_schema.jsonify(customer), 200

# Partial update a customer
@customers_bp.route('/update', methods=['PATCH'])
@limiter.limit('5 per minute; 50 per day')
@token_required
def partial_update_customer(customer_id):
    customer = db.session.get(Customer, customer_id)
    if not customer:
        return jsonify({'error': 'Customer not found'}), 404
    try:
        customer_data = customer_schema.load(request.json, partial=True)
    except ValidationError as e:
        return jsonify(e.messages), 400

    for key, value in customer_data.items():
        setattr(customer, key, value)

    db.session.commit()
    return jsonify(customer_schema.dump(customer)), 200

# Delete a customer
@customers_bp.route('/delete', methods=['DELETE'])
@limiter.limit('5 per minute; 50 per day')
@token_required
def delete_customer(customer_id):
    customer = db.session.get(Customer, customer_id)
    if not customer:
        return jsonify({'error': 'Customer not found'}), 404

    db.session.delete(customer)
    db.session.commit()
    return jsonify({'message': f'Customer: {customer_id}, successfully deleted!'}), 200
