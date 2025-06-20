"""Marshmallow schemas for inventory item serialization and validation."""
from app.models import Inventory
from app.extensions import ma


class InventorySchema(ma.SQLAlchemyAutoSchema):
    """Schema for serializing and validating inventory items."""

    class Meta:
        model = Inventory


inventory_schema = InventorySchema()
inventories_schema = InventorySchema(many=True)
