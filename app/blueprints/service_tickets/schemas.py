from marshmallow import fields
from app.models import Service_Ticket
from app.extensions import ma

class ServiceTicketSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Service_Ticket
        include_fk = True  # Include foreign keys
        load_instance = True # Load instances of the model

    mechanics = fields.Nested('MechanicSchema', many=True, dump_only=True)
service_ticket_schema = ServiceTicketSchema()
service_tickets_schema = ServiceTicketSchema(many=True)