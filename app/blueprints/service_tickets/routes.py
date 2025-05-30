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
@token_required
@limiter.limit('10 per minute; 200 per day')
@cache.cached(timeout=30)
def get_service_tickets(customer_id):
    query = select(Service_Ticket).where(Service_Ticket.customer_id == customer_id)
    service_tickets = db.session.execute(query).scalars().all()
    return jsonify(service_tickets_schema.dump(service_tickets)), 200

# Get service_ticket by id
@service_tickets_bp.route('/<int:ticket_id>', methods=['GET'])
@token_required
@limiter.limit('10 per minute; 200 per day')
@cache.cached(timeout=30)
def get_service_ticket(customer_id,ticket_id):
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
@service_tickets_bp.route('/<int:ticket_id>', methods=['PUT'])
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

