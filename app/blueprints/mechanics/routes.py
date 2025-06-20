"""Mechanic blueprint routes for registration, authentication, and mechanic management."""
from app.utils.decorators import mechanic_required, token_required
from .schemas import mechanic_schema, mechanics_schema, mechanic_customer_view_schema, mechanic_customer_view_schema_many
from flask import request, jsonify
from marshmallow import ValidationError
from sqlalchemy import select
from app.models import Mechanic, db
from . import mechanics_bp
from app.extensions import limiter, cache

# Create a mechanic


@mechanics_bp.route('/', methods=['POST'])
@limiter.limit("5 per minute; 50 per day")
def create_mechanic():
    """Create a new mechanic account."""
    try:
        mechanic_data = mechanic_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400

    query = select(Mechanic).where(Mechanic.email == mechanic_data['email'])
    existing_mechanic = db.session.execute(query).scalars().all()
    if existing_mechanic:
        return jsonify({'error': 'Mechanic already exists'}), 400

    hashed_password = Mechanic.hash_password(mechanic_data['password'])
    mechanic_data['password'] = hashed_password

    new_mechanic = Mechanic(**mechanic_data)
    db.session.add(new_mechanic)
    db.session.commit()
    return mechanic_schema.jsonify(new_mechanic), 201


# Get all mechanics (RBAC: Mechanic only)
@mechanics_bp.route('/', methods=['GET'])
@token_required
@cache.cached(timeout=30)
def get_mechanics(current_user_id, current_user_role):
    """Get a paginated list of mechanics."""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
    except ValueError:
        return jsonify({'error': 'Page and per_page must be integers'}), 400

    if page < 1 or per_page < 1:
        return jsonify({'error': 'Page and per_page must be positive integers'}), 400

    query = select(Mechanic)
    pagination = db.paginate(query, page=page, per_page=per_page)
    mechanics = pagination.items

    if not mechanics:
        return jsonify({'message': 'No mechanics found'}), 404

    if current_user_role == 'mechanic':
        mechanics = mechanic_customer_view_schema_many.dump(mechanics)
    elif current_user_role == 'customer':
        mechanics = mechanic_customer_view_schema_many.dump(mechanics)
    else:
        return jsonify({'error': 'Access denied'}), 403

    return jsonify({
        'mechanics': mechanics,
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': pagination.page,
        'has_next': pagination.has_next,
        'has_prev': pagination.has_prev
    }), 200


# Get a mechanic by ID (RBAC: Mechanic only)
@mechanics_bp.route('/<int:mechanic_id>', methods=['GET'])
@token_required
@cache.cached(timeout=30)
def get_mechanic_by_id(current_user_id, mechanic_id, current_user_role):
    """Get mechanic details by ID."""
    mechanic = db.session.get(Mechanic, mechanic_id)

    if not mechanic:
        return jsonify({'error': 'Mechanic not found'}), 404

    if current_user_role == 'mechanic':
        return mechanic_schema.jsonify(mechanic), 200
    elif current_user_role == 'customer':
        mechanic_data = mechanic_customer_view_schema.dump(mechanic)
        return jsonify(mechanic_data), 200
    else:
        return jsonify({'error': 'Access denied'}), 403


# Update a mechanic
@mechanics_bp.route('/<int:mechanic_id>', methods=['PUT'])
@mechanic_required
@limiter.limit('5 per minute; 50 per day')
def update_mechanic(current_user_id, current_user_role, mechanic_id):
    """Update mechanic details."""
    mechanic = db.session.get(Mechanic, mechanic_id)
    if not mechanic:
        return jsonify({'error': 'Mechanic not found'}), 404
    try:
        mechanic_data = mechanic_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400

    for key, value in mechanic_data.items():
        setattr(mechanic, key, value)

    db.session.commit()
    return mechanic_schema.jsonify(mechanic), 200


# Partial update a mechanic (RBAC: Mechanic only)
@mechanics_bp.route('/<int:mechanic_id>', methods=['PATCH'])
@mechanic_required
@limiter.limit('5 per minute; 50 per day')
def partial_update_mechanic(current_user_id, current_user_role, mechanic_id):
    """Partially update mechanic details."""
    mechanic = db.session.get(Mechanic, mechanic_id)
    if not mechanic:
        return jsonify({'error': 'Mechanic not found'}), 404
    try:
        mechanic_data = mechanic_schema.load(request.json, partial=True)
    except ValidationError as e:
        return jsonify(e.messages), 400
    for key, value in mechanic_data.items():
        setattr(mechanic, key, value)
    db.session.commit()
    return mechanic_schema.jsonify(mechanic), 200

# Delete a mechanic (RBAC: Mechanic only)


@mechanics_bp.route('/<int:mechanic_id>', methods=['DELETE'])
@mechanic_required
@limiter.limit('5 per minute; 50 per day')
def delete_mechanic(current_user_id, current_user_role, mechanic_id):
    """Delete a mechanic by ID."""
    mechanic = db.session.get(Mechanic, mechanic_id)
    if not mechanic:
        return jsonify({'error': 'Mechanic not found'}), 404

    db.session.delete(mechanic)
    db.session.commit()
    return jsonify({'message': f'Mechanic: ID: {mechanic.id} Name: {mechanic.name} deleted successfully'}), 200


# GET mechanics sorted by the number of service tickets
@mechanics_bp.route('/popular', methods=['GET'])
@token_required
@cache.cached(timeout=60)
def get_popular_mechanics(current_user_id, current_user_role):
    """Get mechanics sorted by the number of service tickets."""
    query = select(Mechanic)
    mechanics = db.session.execute(query).scalars().all()

    mechanics.sort(key=lambda m: len(m.service_tickets), reverse=True)

    if current_user_role == 'mechanic':
        return jsonify(mechanics_schema.dump(mechanics)), 200
    elif current_user_role == 'customer':
        mechanic_data = mechanic_customer_view_schema.dump(
            mechanics, many=True)
        return jsonify(mechanic_data), 200
    else:
        return jsonify({'error': 'Access denied'}), 403

# Get mechanics by name or email


@mechanics_bp.route('/search', methods=['GET'])
@token_required
def search_mechanics(current_user_id, current_user_role):
    """Search mechanics by name or email."""
    name = request.args.get('name')
    email = request.args.get('email')
    query = select(Mechanic)

    if not name and not email:
        return ({'error': 'Most provide a search parameter(name or email)'}), 400

    if name:
        query = query.where(Mechanic.name.ilike(f'%{name}%'))
    if email:
        query = query.where(Mechanic.email.ilike(f'%{email}%'))

    mechanics = db.session.execute(query).scalars().all()

    if current_user_role == 'mechanic':
        return jsonify(mechanics_schema.dump(mechanics)), 200
    elif current_user_role == 'customer':
        return jsonify(mechanic_customer_view_schema.dump(mechanics)), 200
    else:
        return jsonify({'error': 'Must be logged in to search mechanics'}), 403

    return jsonify(mechanics), 200
