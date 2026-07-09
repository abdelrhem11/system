from decimal import Decimal
from django.db import transaction
from rest_framework.exceptions import ValidationError
from .models import StockBalance, StockMovement

OUTBOUND = {StockMovement.Type.TRANSFER_OUT, StockMovement.Type.PURCHASE_RTN, StockMovement.Type.SALE, StockMovement.Type.INTERNAL_USE, StockMovement.Type.DAMAGE}


@transaction.atomic
def record_movement(*, user, validated_data):
    movement_data = validated_data.copy()
    item = validated_data["item"]
    warehouse = validated_data["warehouse"]
    location = validated_data["location"]
    amount = abs(movement_data.pop("quantity"))
    signed_quantity = -amount if validated_data["movement_type"] in OUTBOUND else amount
    balance, _ = StockBalance.all_objects.select_for_update().get_or_create(item=item, warehouse=warehouse, location=location, defaults={"quantity": 0})
    before = balance.quantity
    after = before + signed_quantity
    if after < balance.reserved_quantity or after < 0:
        raise ValidationError({"quantity": "الرصيد المتاح غير كافٍ لإتمام الحركة."})
    unit_cost = validated_data.get("unit_cost", Decimal("0"))
    movement = StockMovement.objects.create(**movement_data, quantity=signed_quantity, total_cost=amount * unit_cost, quantity_before=before, quantity_after=after, created_by=user, is_approved=True, approved_by=user)
    balance.quantity = after
    if signed_quantity > 0 and unit_cost > 0:
        old_value = before * balance.average_cost
        balance.average_cost = (old_value + amount * unit_cost) / after if after else Decimal("0")
    balance.version += 1
    balance.save(update_fields=["quantity", "average_cost", "version", "updated_at"])
    return movement
