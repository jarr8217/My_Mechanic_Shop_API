"""Marshmallow schemas for customer serialization and validation."""
from app.models import Customer
from app.extensions import ma


class CustomerSchema(ma.SQLAlchemyAutoSchema):
    """Schema for serializing and validating customer data."""

    class Meta:
        model = Customer


customer_schema = CustomerSchema()
customers_schema = CustomerSchema(many=True)
login_schema = CustomerSchema(exclude=["name", "phone"])
