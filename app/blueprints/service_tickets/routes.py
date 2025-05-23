from .schemas import service_ticket_schema, service_tickets_schema
from flask import request, jsonify
from marshmallow import ValidationError
from sqlalchemy import select
from app.models import Service_Ticket, db
from . import service_tickets_bp
from app.models import Customer

#Create service_ticket
@service_tickets_bp.route('/', methods=['POST'])
def create_service_ticket():
    try:
        service_ticket = service_ticket_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400

    customer_id = service_ticket.customer_id
    if not customer_id or not db.session.get(Customer, customer_id):
        return jsonify({'error': 'Customer ID is required'}), 400

    query = select(Service_Ticket).where(Service_Ticket.VIN == service_ticket.VIN)
    existing_service_ticket = db.session.execute(query).scalars().all()
    if existing_service_ticket:
        return jsonify({'error': 'Service ticket already exists'}), 400


    db.session.add(service_ticket)
    db.session.commit()
    return jsonify(service_ticket_schema.dump(service_ticket)), 201
