from django.contrib import admin
from .models import Location, Warehouse, Zone

admin.site.register([Warehouse, Zone, Location])

