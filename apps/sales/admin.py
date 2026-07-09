from django.contrib import admin
from .models import Customer, SalesOrder, SalesOrderLine, Shipment, ShipmentLine

admin.site.register([Customer, SalesOrder, SalesOrderLine, Shipment, ShipmentLine])
