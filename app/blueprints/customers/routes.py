from .schemas import customer_schema, customers_schema
from flask import request, jsonify
from marshmallow import ValidationError
from sqlalchemy import func, select
from app.models import Customer, db
from . import customers_bp
from app.extensions import limiter, cache
from app.utils.decorators import token_required, mechanic_required, customer_required
from werkzeug.security import generate_password_hash


# Create a new customer
@customers_bp.route('/', methods=['POST'])
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
@cache.cached(timeout=30)
@mechanic_required
def get_customers(current_user_id, current_user_role):
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 20))
    query = select(Customer)

    pagination = db.paginate(query, page=page, per_page=limit)
    customers = pagination.items

    return jsonify({
        "customers": customers_schema.dump(customers),
        "page": page,
        "per_page": limit,
        "total": pagination.total,
        "pages": pagination.pages
    }), 200

# Get a customer by ID
@customers_bp.route('/<int:customer_id>', methods=['GET'])
@cache.cached(timeout=60)
@token_required
def get_customer(current_user_id, customer_id, current_user_role):
    customer = db.session.get(Customer, customer_id)
    if not customer:
        return jsonify({'error': 'Customer not found'}), 404
    if current_user_role == 'mechanic' or current_user_id == customer_id:
        return customer_schema.jsonify(customer), 200
    return jsonify({'error': 'Unauthorized'}), 403

# Update a customer
@customers_bp.route('/<int:customer_id>', methods=['PUT'])
@limiter.limit('5 per minute; 50 per day')
@customer_required
def update_customer(current_user_id, customer_id, current_user_role):
    customer = db.session.get(Customer, customer_id)
    if not customer:
        return jsonify({'error': 'Customer not found'}), 404
    # Check if the current user is authorized to update the customer. Customer only.
    if current_user_role != 'customer' or current_user_id != customer_id:
        return jsonify({'error': 'Unauthorized attempt to update customer'}), 403

    try:
        customer_data = customer_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400

    for key, value in customer_data.items():
        setattr(customer, key, value)

    db.session.commit()
    return customer_schema.jsonify(customer), 200

# Partial update a customer
@customers_bp.route('/<int:customer_id>', methods=['PATCH'])
@limiter.limit('5 per minute; 50 per day')
@customer_required
def partial_update_customer(current_user_id, customer_id, current_user_role):
    customer = db.session.get(Customer, customer_id)
    if not customer:
        return jsonify({'error': 'Customer not found'}), 404
    # Check if the current user is authorized to update the customer. Customer only.
    if current_user_role != 'customer' or current_user_id != customer_id:
        return jsonify({'error': 'Unauthorized attempt to update customer'}), 403
    try:
        customer_data = customer_schema.load(request.json, partial=True)
    except ValidationError as e:
        return jsonify(e.messages), 400

    for key, value in customer_data.items():
        setattr(customer, key, value)

    db.session.commit()
    return jsonify(customer_schema.dump(customer)), 200

# Delete a customer
@customers_bp.route('/<int:customer_id>', methods=['DELETE'])
@limiter.limit('5 per minute; 50 per day')
@customer_required
def delete_customer(current_user_id, customer_id, current_user_role):
    customer = db.session.get(Customer, customer_id)
    if not customer:
        return jsonify({'error': 'Customer not found'}), 404
    # Check if the current user is authorized to delete the customer. Customer only.
    if current_user_role != 'customer' or current_user_id != customer_id:
        return jsonify({'error': 'Unauthorized attempt to delete customer'}), 403

    db.session.delete(customer)
    db.session.commit()
    return jsonify({'message': f'Customer: {customer_id}, successfully deleted!'}), 200

# Get customers by search criteria
@customers_bp.route('/search', methods=['GET'])
@token_required
def search_customers():
    name = request.args.get('name')
    email = request.args.get('email')
    query = select(Customer)

    if name:
        query = query.where(func.lower(Customer.name).ilike(f'%{name.lower()}%'))
    if email:
        query = query.where(func.lower(Customer.email).ilike(f'%{email.lower()}%'))
    if not name and not email:
        return jsonify({'message': 'Please provide at least one search criteria (name or email)'}), 400

    customers = db.session.execute(query).scalars().all()
    if not customers:
        return jsonify({'message': 'No customers found matching the criteria'}), 404
    
    return jsonify(customers_schema.dump(customers)), 200


