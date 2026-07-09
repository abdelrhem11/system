from django.db import models
from apps.common.models import TimeStampedModel

class Warehouse(TimeStampedModel):
    code = models.CharField(max_length=30, unique=True)
    name_ar = models.CharField(max_length=150)
    name_en = models.CharField(max_length=150, blank=True)
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} - {self.name_ar}"

class Zone(TimeStampedModel):
    warehouse = models.ForeignKey(Warehouse, related_name="zones", on_delete=models.PROTECT)
    code = models.CharField(max_length=30)
    name = models.CharField(max_length=100)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["warehouse", "code"], name="uq_zone_warehouse_code")]

    def __str__(self):
        return self.code

class Location(TimeStampedModel):
    class Type(models.TextChoices):
        AISLE = "AISLE", "ممر"
        RACK = "RACK", "رف"
        SHELF = "SHELF", "طابق"
        BIN = "BIN", "خانة"

    warehouse = models.ForeignKey(Warehouse, related_name="locations", on_delete=models.PROTECT)
    zone = models.ForeignKey(Zone, related_name="locations", on_delete=models.PROTECT)
    parent = models.ForeignKey("self", null=True, blank=True, related_name="children", on_delete=models.PROTECT)
    code = models.CharField(max_length=80, unique=True)
    name = models.CharField(max_length=100)
    location_type = models.CharField(max_length=10, choices=Type.choices)
    capacity = models.DecimalField(max_digits=14, decimal_places=3, null=True, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)

    def __str__(self):
        return self.code
