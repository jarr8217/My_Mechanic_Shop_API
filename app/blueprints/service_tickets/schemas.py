from app.models import ServiceTicket
from app import ma

class ServiceTicketSchema(ma.SQLAlchemyAutoSchema):
    class Meta: 
        model = ServiceTicket

ServiceTicketSchema = ServiceTicketSchema()
ServiceTicketsSchema = ServiceTicketSchema(many=True)  