from app.models import Mechanic
from app.extensions import ma

class MechanicSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Mechanic
        exclude = ('service_tickets',)
        
mechanic_schema = MechanicSchema()
mechanics_schema = MechanicSchema(many=True)