from app.utils.decorators import token_required
from .schemas import service_ticket_schema, service_tickets_schema
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
@limiter.limit('10 per minute; 200 per day')
@cache.cached(timeout=30)
@token_required
def get_service_tickets(customer_id):
    query = select(Service_Ticket).where(Service_Ticket.customer_id == customer_id)
    service_tickets = db.session.execute(query).scalars().all()
    return jsonify(service_tickets_schema.dump(service_tickets)), 200

#Get specific service_ticket
@service_tickets_bp.route('/<int:ticket_id>', methods=['GET'])
@limiter.limit('10 per minute; 200 per day')
@cache.cached(timeout=30)
@token_required
def get_service_ticket_by_id(customer_id, ticket_id):
    ticket = db.session.get(Service_Ticket, ticket_id)
    if not ticket:
        return jsonify({'error': 'Are you sure this ticket exists?'}), 404
    return jsonify(service_ticket_schema.dump(ticket)), 200


# Add mechanic to service_ticket
@service_tickets_bp.route('/<int:ticket_id>/add_mechanic/<int:mechanic_id>', methods=['PUT'])
@limiter.limit('5 per minute; 50 per day')
@token_required
def add_mechanic_to_ticket(ticket_id, mechanic_id):
    ticket = db.session.get(Service_Ticket, ticket_id)
    mechanic = db.session.get(Mechanic, mechanic_id)

    if not ticket:
        return jsonify({'error': 'COme on, that the wrong ticket id'}), 404
    
    if not mechanic:
        return jsonify({'error': 'Do not try to blame this guy he did not work on this vehicle'}), 404

    if mechanic in ticket.mechanics:
        return jsonify({'message': 'Mechanic already assigned to this ticket'}), 200
    
    ticket.mechanics.append(mechanic)
    db.session.commit()

    return jsonify({'message': 'If it breaks, its this guy\'s fault'}), 200

# Remove mechanic from service_ticket
@service_tickets_bp.route('/<int:ticket_id>/remove_mechanic/<int:mechanic_id>', methods=['PUT'])
@limiter.limit('5 per minute; 50 per day')
@token_required
def remove_mechanic_from_ticket(ticket_id, mechanic_id):
    ticket = db.session.get(Service_Ticket, ticket_id)
    mechanic = db.session.get(Mechanic, mechanic_id)

    if not ticket or not mechanic:
        return jsonify({'error': 'Ticket or Mechanic not found'}), 404
    
    if mechanic not in ticket.mechanics:
        return jsonify({'message': 'Mechanic not assigned to this ticket'}), 200
    
    ticket.mechanics.remove(mechanic)
    db.session.commit()

    return jsonify({'message': 'Mechanic removed from ticket'}), 200


# Get service_ticket by id
@service_tickets_bp.route('/<int:ticket_id>', methods=['GET'])
@limiter.limit('10 per minute; 200 per day')
@cache.cached(timeout=30)
@token_required
def get_service_ticket(customer_id,ticket_id):
    service_ticket = db.session.get(Service_Ticket, ticket_id)
    if not service_ticket:
        return jsonify({'error': 'Service ticket not found'}), 404
    return jsonify(service_ticket_schema.dump(service_ticket)), 200

# Get all service tickets for a customer
@service_tickets_bp.route('/my-tickets', methods=['GET'])
@limiter.limit('10 per minute; 200 per day')
@token_required
def get_customer_service_tickets(customer_id):
    query = select(Service_Ticket).where(Service_Ticket.customer_id == customer_id)
    service_ticket = db.session.execute(query).scalars().all()

    if not service_ticket:
        return jsonify({'message': 'No service tickets found for this customer'}), 404
    
    return  jsonify(service_tickets_schema.dump(service_ticket)), 200
