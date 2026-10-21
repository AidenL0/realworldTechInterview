from django.utils import timezone
from rest_framework import serializers

from . import services
from .models import OrderLine, PurchaseOrder, Supplier


class SupplierSerializer(serializers.ModelSerializer):
    open_orders = serializers.SerializerMethodField()

    class Meta:
        model = Supplier
        fields = [
            "id",
            "name",
            "contact_email",
            "payment_terms_days",
            "is_active",
            "open_orders",
            "created_at",
        ]
        read_only_fields = ["created_at"]

    def get_open_orders(self, supplier):
        return services.open_order_count(supplier)


class OrderLineSerializer(serializers.ModelSerializer):
    line_total = serializers.SerializerMethodField()

    class Meta:
        model = OrderLine
        fields = [
            "id",
            "sku",
            "description",
            "quantity",
            "unit_price",
            "discount_percent",
            "line_total",
        ]

    def get_line_total(self, line):
        return str(services.line_total(line))

    def validate_sku(self, value):
        sku = value.strip().upper()
        if not sku:
            raise serializers.ValidationError("This field may not be blank.")
        return sku


class PurchaseOrderListSerializer(serializers.ModelSerializer):
    """Short representation used by the list endpoint."""

    number = serializers.CharField(read_only=True)
    supplier_name = serializers.CharField(source="supplier.name", read_only=True)
    line_count = serializers.SerializerMethodField()
    total = serializers.SerializerMethodField()

    class Meta:
        model = PurchaseOrder
        fields = [
            "id",
            "number",
            "supplier",
            "supplier_name",
            "requested_by",
            "needed_by",
            "status",
            "line_count",
            "total",
            "created_at",
        ]

    def get_line_count(self, order):
        return services.line_count(order)

    def get_total(self, order):
        return str(services.order_total(order))


class PurchaseOrderSerializer(serializers.ModelSerializer):
    """Full representation used by create, detail, update and the status actions."""

    number = serializers.CharField(read_only=True)
    supplier_name = serializers.CharField(source="supplier.name", read_only=True)
    lines = OrderLineSerializer(many=True, read_only=True)
    line_count = serializers.SerializerMethodField()
    total = serializers.SerializerMethodField()
    payment_due_date = serializers.SerializerMethodField()

    class Meta:
        model = PurchaseOrder
        fields = [
            "id",
            "number",
            "supplier",
            "supplier_name",
            "requested_by",
            "needed_by",
            "notes",
            "status",
            "lines",
            "line_count",
            "total",
            "submitted_at",
            "approved_by",
            "approved_at",
            "payment_due_date",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "submitted_at",
            "approved_by",
            "approved_at",
            "created_at",
            "updated_at",
        ]

    def get_line_count(self, order):
        return services.line_count(order)

    def get_total(self, order):
        return str(services.order_total(order))

    def get_payment_due_date(self, order):
        due = services.payment_due_date(order)
        return due.isoformat() if due else None

    def validate_supplier(self, supplier):
        if not supplier.is_active:
            raise serializers.ValidationError("Purchase orders can't be raised for an inactive supplier.")
        return supplier

    def validate_needed_by(self, value):
        if value < timezone.localdate():
            raise serializers.ValidationError("The date can't be in the past.")
        return value
