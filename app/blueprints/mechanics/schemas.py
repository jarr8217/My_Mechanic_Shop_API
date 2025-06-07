from marshmallow import fields
from app.models import Mechanic
from app.extensions import ma

class MechanicSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Mechanic
        exclude = ('service_tickets',)
        
mechanic_schema = MechanicSchema()
mechanics_schema = MechanicSchema(many=True)

class MechanicCustomerViewSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Mechanic
        fields = ('id', 'name', 'email', 'phone')

    def get_ticket_count(self, obj):
        return len(obj.service_tickets) if obj.service_tickets else 0

mechanic_customer_view_schema = MechanicCustomerViewSchema()
mechanic_customer_view_schema_many = MechanicCustomerViewSchema(many=True)