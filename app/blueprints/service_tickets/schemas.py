from app.models import Service_Ticket
from app.extensions import ma
from marshmallow import fields


class PartOnTicketSchema(ma.Schema):
    id = fields.Int(attribute='inventory.id')
    part_name = fields.String(attribute='inventory.part_name')
    quantity = fields.Int()

class ServiceTicketSchema(ma.SQLAlchemyAutoSchema):
    mechanics = fields.Nested('MechanicSchema', many=True, dump_only=True)
    mechanic_ids = fields.List(fields.Int(), load_only=True)  # Accept list of mechanic IDs in request

    parts = fields.Method('get_parts', dump_only=True)
    class Meta:
        model = Service_Ticket
        include_fk = True
        load_instance = True
        fields = ('id', 'VIN', 'service_date', 'service_desc', 'customer_id', 'mechanics', 'mechanic_ids', 'parts')

    def get_parts(self, obj):
        return PartOnTicketSchema(many=True).dump(obj.part_associations)

service_ticket_schema = ServiceTicketSchema()
service_tickets_schema = ServiceTicketSchema(many=True)
return_service_ticket_schema = ServiceTicketSchema(exclude=['customer_id'])

class EditServiceTicketSchema(ma.Schema):
    add_mechanic_ids = fields.List(fields.Int(), required=True)
    remove_mechanic_ids = fields.List(fields.Int(), required=True)
    class Meta:
        fields = ('add_mechanic_ids', 'remove_mechanic_ids')

edit_service_ticket_schema = EditServiceTicketSchema()

