from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from apps.common.audit import log_audit
from .models import StockCountSession
from .serializers import StockCountSessionSerializer, approve_session


class StockCountSessionViewSet(ModelViewSet):
    queryset = StockCountSession.objects.select_related("warehouse", "location", "created_by", "approved_by").prefetch_related("lines__item", "lines__location", "lines__unit")
    serializer_class = StockCountSessionSerializer
    filterset_fields = ["status", "warehouse", "location"]
    search_fields = ["number"]
    ordering_fields = ["created_at", "number"]

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        session = approve_session(session=self.get_object(), user=request.user)
        log_audit(request=request, action="APPROVE", instance=session)
        return Response(self.get_serializer(session).data)

    def perform_create(self, serializer):
        instance = serializer.save()
        log_audit(request=self.request, action="CREATE", instance=instance)

    def perform_update(self, serializer):
        instance = serializer.save()
        log_audit(request=self.request, action="UPDATE", instance=instance)
