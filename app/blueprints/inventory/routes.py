"""Inventory blueprint routes for part management (CRUD)."""

from .schemas import inventory_schema, inventories_schema
from flask import request, jsonify
from marshmallow import ValidationError
from sqlalchemy import select
from app.models import Inventory, db
from . import inventory_bp
from app.extensions import limiter, cache
from app.utils.decorators import mechanic_required, token_required, customer_required


# Create a new inventory item (RBAC: Mechanic only)
@inventory_bp.route('/', methods=['POST'])
@mechanic_required
def create_inventory_item(current_user_id, current_user_role):
    """Create a new inventory item."""
    try:
        inventory_data = inventory_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
    # Negative value check
    if inventory_data.get('quantity', 0) < 0 or inventory_data.get('price', 0) < 0:
        return jsonify({'error': 'Quantity and price must be non-negative'}), 400

    query = select(Inventory).where(
        Inventory.part_number == inventory_data['part_number'])
    existing_inventory_item = db.session.execute(query).scalars().all()
    if existing_inventory_item:
        return jsonify({'error': "Part number already exists"}), 400

    new_inventory_item = Inventory(
        part_name=inventory_data['part_name'],
        part_number=inventory_data['part_number'],
        quantity=inventory_data['quantity'],
        price=inventory_data['price']
    )
    db.session.add(new_inventory_item)
    db.session.commit()
    return inventory_schema.jsonify(new_inventory_item), 201

# Get all inventory items (Open to all)


@inventory_bp.route('/', methods=['GET'])
@cache.cached(timeout=30)
def get_inventory_items():
    """Retrieve all inventory items with pagination."""
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 20))
    query = select(Inventory)

    pagination = db.paginate(query, page=page, per_page=limit)
    inventory_items = pagination.items

    return jsonify({
        "inventory_items": inventories_schema.dump(inventory_items),
        "page": page,
        "per_page": limit,
        "total": pagination.total,
        "pages": pagination.pages
    }), 200

# Get an inventory item by ID (Open to all)


@inventory_bp.route('/<int:inventory_item_id>', methods=['GET'])
@cache.cached(timeout=60)
def get_inventory_item(inventory_item_id):
    """Retrieve a specific inventory item by its ID."""
    inventory_item = db.session.get(Inventory, inventory_item_id)
    if not inventory_item:
        return jsonify({'error': 'Inventory item not found'}), 404
    return inventory_schema.jsonify(inventory_item), 200

# Update an inventory item (RBAC: Mechanic only)


@inventory_bp.route('/<int:inventory_item_id>', methods=['PUT'])
@mechanic_required
@limiter.limit('5 per minute; 50 per day')
def update_inventory_item(current_user_id, current_user_role, inventory_item_id):
    """Update an existing inventory item."""
    inventory_item = db.session.get(Inventory, inventory_item_id)
    if not inventory_item:
        return jsonify({'error': 'Inventory item not found'}), 404
    try:
        inventory_data = inventory_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
    # Negative value check
    if inventory_data.get('quantity', 0) < 0 or inventory_data.get('price', 0) < 0:
        return jsonify({'error': 'Quantity and price must be non-negative'}), 400

    for key, value in inventory_data.items():
        setattr(inventory_item, key, value)

    db.session.commit()
    return inventory_schema.jsonify(inventory_item), 200

# Partial update an inventory item (RBAC: Mechanic only)


@inventory_bp.route('/<int:inventory_item_id>', methods=['PATCH'])
@mechanic_required
@limiter.limit('5 per minute; 50 per day')
def partial_update_inventory_item(current_user_id, current_user_role, inventory_item_id):
    """Partially update an existing inventory item."""
    inventory_item = db.session.get(Inventory, inventory_item_id)
    if not inventory_item:
        return jsonify({'error': 'Inventory item not found'}), 404
    # Empty payload check
    if not request.json or not bool(request.json):
        return jsonify({'error': 'No data provided for update'}), 400
    try:
        inventory_data = inventory_schema.load(request.json, partial=True)
    except ValidationError as e:
        return jsonify(e.messages), 400
    # Negative value check (if present)
    if 'quantity' in inventory_data and inventory_data['quantity'] < 0:
        return jsonify({'error': 'Quantity and price must be non-negative'}), 400
    if 'price' in inventory_data and inventory_data['price'] < 0:
        return jsonify({'error': 'Quantity and price must be non-negative'}), 400

    for key, value in inventory_data.items():
        setattr(inventory_item, key, value)

    db.session.commit()
    return jsonify(inventory_schema.dump(inventory_item)), 200

# Delete an inventory item (RBAC: Mechanic can delete inventory items)


@inventory_bp.route('/<int:inventory_item_id>', methods=['DELETE'])
@mechanic_required
@limiter.limit('5 per minute; 50 per day')
def delete_inventory_item(current_user_id, current_user_role, inventory_item_id):
    """Delete an inventory item."""
    inventory_item = db.session.get(Inventory, inventory_item_id)
    if not inventory_item:
        return jsonify({'error': 'Inventory item not found'}), 404

    db.session.delete(inventory_item)
    db.session.commit()
    return jsonify({'message': f'Inventory item: {inventory_item.id}, successfully deleted!'}), 200
