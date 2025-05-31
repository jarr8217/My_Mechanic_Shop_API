from app.utils.decorators import token_required
from .schemas import mechanic_schema, mechanics_schema
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
    try:
        mechanic_data = mechanic_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400

    query = select(Mechanic).where(Mechanic.email == mechanic_data['email'])
    existing_mechanic = db.session.execute(query).scalars().all()
    if existing_mechanic:
        return jsonify({'error': 'Mechanic already exists'}), 400

    new_mechanic = Mechanic(**mechanic_data)
    db.session.add(new_mechanic)
    db.session.commit()
    return jsonify(mechanic_schema.dump(new_mechanic)), 201

#Get all mechanics
@mechanics_bp.route('/', methods=['GET'])
@limiter.limit('10 per minute; 200 per day')
@cache.cached(timeout=30)
def get_mechanics():
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

    return jsonify({
        'mechanics': mechanics_schema.dump(mechanics),
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': pagination.page,
        'has_next': pagination.has_next,
        'has_prev': pagination.has_prev
    }), 200


#Get a mechanic by ID
@mechanics_bp.route('/<int:mechanic_id>', methods=['GET'])
@limiter.limit('10 per minute; 200 per day')
@cache.cached(timeout=30)
@token_required
def get_mechanic_by_id(current_user_id, mechanic_id):
    mechanic = db.session.get(Mechanic, mechanic_id)
    if not mechanic:
        return jsonify({'error': 'Mechanic not found'}), 404
    return jsonify(mechanic_schema.dump(mechanic)), 200

#Update a mechanic
@mechanics_bp.route('/<int:mechanic_id>', methods=['PUT'])
@limiter.limit('5 per minute; 50 per day')
@token_required
def update_mechanic(current_user_id, mechanic_id):
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
    return jsonify(mechanic_schema.dump(mechanic)), 200

#Partial update a mechanic
@mechanics_bp.route('/<int:mechanic_id>', methods=['PATCH'])
@limiter.limit('5 per minute; 50 per day')
@token_required
def partial_update_mechanic(current_user_id,mechanic_id):
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
    return jsonify(mechanic_schema.dump(mechanic)), 200

#Delete a mechanic
@mechanics_bp.route('/<int:mechanic_id>', methods=['DELETE'])
@limiter.limit('5 per minute; 50 per day')
@token_required
def delete_mechanic(current_user_id, mechanic_id):
    mechanic = db.session.get(Mechanic, mechanic_id)
    if not mechanic:
        return jsonify({'error': 'Mechanic not found'}), 404

    db.session.delete(mechanic)
    db.session.commit()
    return jsonify({'message': 'Mechanic deleted successfully'}), 200


# GET mechanics by amount of service tickets
@mechanics_bp.route('/popular', methods=['GET'])
@limiter.limit('10 per minute; 200 per day')
@cache.cached(timeout=60)
def get_popular_mechanics():
    query = select(Mechanic)
    mechanics = db.session.execute(query).scalars().all()

    mechanics.sort(key=lambda m: len(m.service_tickets), reverse=True)

    return mechanics_schema.jsonify(mechanics), 200

# Get mechanics by name or email
@mechanics_bp.route('/search', methods=['GET'])
@limiter.limit('10 per minute; 200 per day')
def serch_mechanic():
    name = request.args.get('name')
    email = request.args.get('email')
    query = select(Mechanic)
    
    if not name and not email:
        return jsonify({'error': 'At least one search parameter is required'}), 400

    if name:
        query = query.where(Mechanic.name.ilike(f'%{name}%'))
    if email:
        query = query.where(Mechanic.email.ilike(f'%{email}%'))

    mechanics = db.session.execute(query).scalars().all()

    return mechanics_schema.jsonify(mechanics), 200
