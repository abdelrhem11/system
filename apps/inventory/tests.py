from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from apps.warehouses.models import Location, Warehouse, Zone
from .models import Category, Item, StockBalance, StockMovement, Unit
from .services import record_movement

class MovementServiceTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="tester", email="tester@example.com", password="StrongPass!123")
        self.warehouse = Warehouse.objects.create(code="WH1", name_ar="الرئيسي")
        self.zone = Zone.objects.create(warehouse=self.warehouse, code="A", name="A")
        self.location = Location.objects.create(warehouse=self.warehouse, zone=self.zone, code="WH1-A-01", name="01", location_type=Location.Type.BIN)
        self.unit = Unit.objects.create(code="EA", name_ar="حبة")
        self.category = Category.objects.create(name_ar="عام")
        self.item = Item.objects.create(code="ITM-1", name_ar="صنف", category=self.category, base_unit=self.unit)

    def test_opening_balance_creates_auditable_movement(self):
        movement = record_movement(user=self.user, validated_data={"movement_type": StockMovement.Type.OPENING, "reference_number": "OPEN-1", "reference_type": "OPENING", "item": self.item, "warehouse": self.warehouse, "location": self.location, "quantity": Decimal("10"), "unit": self.unit, "unit_cost": Decimal("5"), "notes": ""})
        balance = StockBalance.objects.get(item=self.item)
        self.assertEqual(balance.quantity, Decimal("10"))
        self.assertEqual(movement.quantity_before, Decimal("0"))
        self.assertEqual(movement.quantity_after, Decimal("10"))

