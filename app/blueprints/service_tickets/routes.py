from app.utils.decorators import token_required
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
@limiter.limit('10 per minute; 200 per day')
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
        return jsonify({'message': 'No service tickets found for the given page and limit'}), 404
    
    return jsonify({
        'service_tickets': service_tickets_schema.dump(paginated_tickets),
        'total': total,
        'page': page,
        'pages': (total + limit - 1) // limit  # total pages
    }), 200

# Get service_ticket by id
@service_tickets_bp.route('/<int:ticket_id>', methods=['GET'])
@limiter.limit('10 per minute; 200 per day')
@cache.cached(timeout=30)
@token_required
def get_service_ticket(current_user_id, ticket_id):
    service_ticket = db.session.get(Service_Ticket, ticket_id)
    if not service_ticket:
        return jsonify({'error': 'Service ticket not found'}), 404
    return jsonify(service_ticket_schema.dump(service_ticket)), 200

# Get all service tickets for a customer
@service_tickets_bp.route('/my-tickets', methods=['GET'])
@token_required
@limiter.limit('10 per minute; 200 per day')
def get_customer_service_tickets(customer_id):
    query = select(Service_Ticket).where(Service_Ticket.customer_id == customer_id)
    service_ticket = db.session.execute(query).scalars().all()

    if not service_ticket:
        return jsonify({'message': 'No service tickets found for this customer'}), 404
    
    return  jsonify(service_tickets_schema.dump(service_ticket)), 200

# Edit service_ticket
@service_tickets_bp.route('/edit/<int:ticket_id>', methods=['PUT'])
@token_required
@limiter.limit('5 per minute; 50 per day')
def edit_service_ticket(current_user_id, ticket_id):
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
@limiter.limit('10 per minute; 200 per day')
def search_service_tickets():
    vin = request.args.get('vin')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    service_date = request.args.get('service_date')
    query = select(Service_Ticket)
    
    if vin:
        query = query.where(Service_Ticket.VIN.ilike(f'%{vin}%'))
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
        return jsonify({'message': 'No service tickets found'}), 404
    return jsonify(service_tickets_schema.dump(service_tickets)), 200