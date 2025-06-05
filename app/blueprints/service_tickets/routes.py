from app.utils.decorators import mechanic_required, token_required
from .schemas import service_ticket_schema, service_tickets_schema, edit_service_ticket_schema, return_service_ticket_schema
from flask import request, jsonify
from marshmallow import ValidationError
from sqlalchemy import select
from app.models import Service_Ticket, db
from . import service_tickets_bp
from app.models import Customer
from app.models import Mechanic
from app.extensions import limiter, cache
from datetime import datetime
from app.models import db, Service_Ticket, Inventory, ServiceTicketInventory
from flask import request, jsonify



#Create service_ticket
@service_tickets_bp.route('/', methods=['POST'])
@limiter.limit("5 per minute; 50 per day")
@token_required
def create_service_ticket(customer_id):
    try:
        ticket_data = request.json
        ticket_data['customer_id'] = customer_id
        service_ticket = service_ticket_schema.load(ticket_data)
    except ValidationError as e:
        return jsonify(e.messages), 400

    if not customer_id or not db.session.get(Customer, customer_id):
        return jsonify({'error': 'Missing or invalid customer ID'}), 400

    query = select(Service_Ticket).where(Service_Ticket.VIN == service_ticket.VIN)
    existing_service_ticket = db.session.execute(query).scalars().all()
    if existing_service_ticket:
        return jsonify({'error': 'Service ticket already exists'}), 400


    db.session.add(service_ticket)
    db.session.commit()
    return jsonify(service_ticket_schema.dump(service_ticket)), 201

#Get all service_tickets
@service_tickets_bp.route('/', methods=['GET'])
@cache.cached(timeout=30)
def get_service_tickets():
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
    except ValueError:
        return jsonify({'error': 'Page and limit must be integers'}), 400
    if page < 1 or limit < 1:
        return jsonify({'error': 'Page and limit must be positive integers'}), 400
    
    query = select(Service_Ticket)
    service_tickets = db.session.execute(query).scalars().all()

    total = len(service_tickets)
    if total == 0:
        return jsonify({'message': 'No service tickets found'}), 404
    
    # Pagination logic
    start = (page - 1) * limit
    end = start + limit
    paginated_tickets = service_tickets[start:end]
    if not paginated_tickets:
        return jsonify({'message': 'No service tickets found for the given page and limit.'}), 404

    return jsonify({
        'service_tickets': service_tickets_schema.dump(paginated_tickets),
        'total': total,
        'page': page,
        'pages': (total + limit - 1) // limit  # total pages
    }), 200

# Get service_ticket by id
@service_tickets_bp.route('/<int:ticket_id>', methods=['GET'])
@cache.cached(timeout=30)
@token_required
def get_service_ticket(current_user_id, ticket_id):
    service_ticket = db.session.get(Service_Ticket, ticket_id)
    if not service_ticket:
        return jsonify({'error': 'Service ticket not found.'}), 404
    return jsonify(service_ticket_schema.dump(service_ticket)), 200

# Get all service tickets for a customer
@service_tickets_bp.route('/my-tickets', methods=['GET'])
@token_required
def get_customer_service_tickets(current_user_id):
    query = select(Service_Ticket).where(Service_Ticket.customer_id == current_user_id)
    service_ticket = db.session.execute(query).scalars().all()

    if not service_ticket:
        return jsonify({'message': 'No service tickets found for this customer'}), 404
    
    return  jsonify(service_tickets_schema.dump(service_ticket)), 200

# Edit service_ticket
@service_tickets_bp.route('/edit/<int:ticket_id>', methods=['PUT'])
@mechanic_required
@limiter.limit('5 per minute; 50 per day')
def edit_service_ticket(current_user_id, current_user_role, ticket_id):
    try:
        ticket_edit = edit_service_ticket_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400

    query = select(Service_Ticket).where(Service_Ticket.id == ticket_id)
    ticket = db.session.execute(query).scalars().first()

    if not ticket:
        return jsonify({'error': 'Service ticket not found'}), 404

    # Add mechanics
    for mechanic_id in ticket_edit.get('add_mechanic_ids', []):
        query = select(Mechanic).where(Mechanic.id == mechanic_id)
        mechanic = db.session.execute(query).scalars().first()

        if not mechanic:
            return jsonify({'error': f'Mechanic with id {mechanic_id} not found'}), 404
        
        if mechanic not in ticket.mechanics:
            ticket.mechanics.append(mechanic)
        else:
            return jsonify({'message': f'Mechanic with id {mechanic_id} already assigned'}), 400

    # Remove mechanics
    for mechanic_id in ticket_edit.get('remove_mechanic_ids', []):
        query = select(Mechanic).where(Mechanic.id == mechanic_id)
        mechanic = db.session.execute(query).scalars().first()

        if not mechanic:
            return jsonify({'error': f'Mechanic with id {mechanic_id} not found'}), 404
        
        if mechanic in ticket.mechanics:
            ticket.mechanics.remove(mechanic)
        else:
            return jsonify({'message': f'Mechanic with id {mechanic_id} not assigned to this ticket'}), 400

    db.session.commit()
    return return_service_ticket_schema.jsonify(ticket), 200

# Search service tickets
@service_tickets_bp.route('/search', methods=['GET'])
@cache.cached(timeout=30)
@mechanic_required
def search_service_tickets():
    vin = request.args.get('vin')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    service_date = request.args.get('service_date')
    query = select(Service_Ticket)
    
    if vin:
        query = query.where(Service_Ticket.VIN.ilike(f'%{vin.lower()}%'))
    if service_date:
        query = query.where(Service_Ticket.service_date == service_date)
    
    # Validate and parse date inputs YYYY-MM-DD
    if start_date and end_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            query = query.where(Service_Ticket.service_date.between(start_date, end_date))
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD.'}), 400
    elif start_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            query = query.where(Service_Ticket.service_date >= start_date)
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD.'}), 400
    elif end_date:
        try:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            query = query.where(Service_Ticket.service_date <= end_date)
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD.'}), 400

    service_tickets = db.session.execute(query).scalars().all()
   
    if not service_tickets:
        return jsonify({'message': 'No service tickets found.'}), 404
    return jsonify(service_tickets_schema.dump(service_tickets)), 200

# ADD or Update inventory parts
@service_tickets_bp.route('/<int:ticket_id>/add_part/<int:inventory_id>', methods=['PUT'])
@mechanic_required
def add_update_inventory_parts(ticket_id, inventory_id):
    data = request.json
    quantity = data.get('quantity')

    if not isinstance(quantity, int) or quantity < 1:
        return jsonify({'error': 'Quantity must be a positive integer.'}), 400

    ticket = db.session.get(Service_Ticket, ticket_id)
    part = db.session.get(Inventory, inventory_id)

    if not ticket or not part:
        return jsonify({'error': 'Service ticket or inventory part not found.'}), 404
    
    # Check if association already exists
    association = db.session.query(ServiceTicketInventory).filter_by(service_ticket_id=ticket_id, inventory_id=inventory_id).first()

    if association:
        association.quantity = quantity
        msg = f'Updated quantity of part {part.part_name} in service ticket {ticket.id} to {quantity}.'
    else:
        new_association = ServiceTicketInventory(service_ticket_id=ticket_id, inventory_id=inventory_id, quantity=quantity)
        db.session.add(new_association)
        msg = f'Added part {part.part_name} to service ticket {ticket.id} with quantity {quantity}.'

    db.session.commit()
    return jsonify({'message': msg}), 200


# Remove inventory parts from service ticket
@service_tickets_bp.route('/<int:ticket_id>/remove_part/<int:inventory_id>', methods=['DELETE'])
@limiter.limit('5 per minute; 50 per day')
@mechanic_required
def remove_inventory_part(ticket_id, inventory_id):
    association = db.session.query(ServiceTicketInventory).filter_by(service_ticket_id=ticket_id, inventory_id=inventory_id).first()

    if not association:
        return jsonify({'error': f'Part ID {inventory_id} not found in service ticket ID {ticket_id}.'}), 404

    db.session.delete(association)
    db.session.commit()
    return jsonify({'message': f'Removed part {inventory_id} from service ticket {ticket_id}.'}), 200

#List all parts (with quantity) in a service ticket
@service_tickets_bp.route('<int:ticket_id>/parts', methods=['GET'])
@token_required
def get_service_ticket_parts(current_user_id, current_user_role, ticket_id):
    ticket = db.session.get(Service_Ticket, ticket_id)
    if not ticket:
        return jsonify({'error': f'Service ticket ID {ticket_id} not found.'}), 404

    # RBAC: Only mechanics and the customer whom the ticket belongs to can access parts
    if current_user_role != 'mechanic' and current_user_id != ticket.customer_id:
        return jsonify({'error': 'Unauthorized access to service ticket parts.'}), 403
    
    parts = []
    for association in ticket.part_associations:
        part = association.inventory
        parts.append({
            'id': part.id,
            'part_name': part.part_name,
            'quantity': association.quantity
        })

    return jsonify({'Service ticket ID': ticket_id, 'Parts': parts}), 200