from rest_framework.viewsets import ModelViewSet
from apps.common.audit import log_audit
from .models import Location, Warehouse, Zone
from .serializers import LocationSerializer, WarehouseSerializer, ZoneSerializer

class WarehouseViewSet(ModelViewSet):
    queryset = Warehouse.objects.all()
    serializer_class = WarehouseSerializer
    filterset_fields = ["is_active"]
    search_fields = ["code", "name_ar", "name_en"]
    ordering_fields = ["code", "name_ar", "created_at"]

    def perform_create(self, serializer):
        instance = serializer.save()
        log_audit(request=self.request, action="CREATE", instance=instance)

    def perform_update(self, serializer):
        instance = serializer.save()
        log_audit(request=self.request, action="UPDATE", instance=instance)

class ZoneViewSet(ModelViewSet):
    queryset = Zone.objects.select_related("warehouse")
    serializer_class = ZoneSerializer
    filterset_fields = ["warehouse"]
    search_fields = ["code", "name"]

    def perform_create(self, serializer):
        instance = serializer.save()
        log_audit(request=self.request, action="CREATE", instance=instance)

    def perform_update(self, serializer):
        instance = serializer.save()
        log_audit(request=self.request, action="UPDATE", instance=instance)

class LocationViewSet(ModelViewSet):
    queryset = Location.objects.select_related("warehouse", "zone", "parent")
    serializer_class = LocationSerializer
    filterset_fields = ["warehouse", "zone", "location_type", "is_active"]
    search_fields = ["code", "name"]

    def perform_create(self, serializer):
        instance = serializer.save()
        log_audit(request=self.request, action="CREATE", instance=instance)

    def perform_update(self, serializer):
        instance = serializer.save()
        log_audit(request=self.request, action="UPDATE", instance=instance)
