from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from . import filters, services
from .models import PurchaseOrder, Supplier
from .serializers import (
    OrderLineSerializer,
    PurchaseOrderListSerializer,
    PurchaseOrderSerializer,
    SupplierSerializer,
)


class SupplierViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """Suppliers the procurement team can raise purchase orders with."""

    serializer_class = SupplierSerializer

    def get_queryset(self):
        queryset = Supplier.objects.order_by("name")
        if self.action == "list":
            queryset = filters.filter_suppliers(queryset, self.request.query_params)
        return queryset


class PurchaseOrderViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """Purchase orders and their lines, from draft to approval."""

    serializer_class = PurchaseOrderSerializer
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_queryset(self):
        queryset = (
            PurchaseOrder.objects.select_related("supplier")
            .prefetch_related("lines")
            .order_by("-created_at", "-id")
        )
        if self.action == "list":
            queryset = filters.filter_purchase_orders(queryset, self.request.query_params)
        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return PurchaseOrderListSerializer
        return self.serializer_class

    def perform_update(self, serializer):
        order = serializer.save()
        services.ensure_draft(order, "Only draft orders can be edited.")

    def order_response(self, order):
        """The full, freshly loaded representation of an order."""
        order = self.get_queryset().get(pk=order.pk)
        return Response(PurchaseOrderSerializer(order).data)

    @action(detail=True, methods=["post"], serializer_class=OrderLineSerializer)
    def lines(self, request, pk=None):
        """Add a line to a draft order."""
        order = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        line = services.add_line(order, **serializer.validated_data)
        return Response(self.get_serializer(line).data)

    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        """Send a draft order for approval."""
        order = self.get_object()
        services.submit_order(order)
        return self.order_response(order)

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        """Approve a submitted order."""
        # TODO: Implement this endpoint. See "Feature to implement" in README.md.
        return Response({"detail": "Not implemented."}, status=status.HTTP_501_NOT_IMPLEMENTED)
