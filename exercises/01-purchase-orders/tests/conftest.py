"""Shared fixtures. Every test builds the data it needs; nothing relies on `manage.py seed`."""
from datetime import timedelta
from decimal import Decimal
from itertools import count

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from purchasing.models import OrderLine, PurchaseOrder, Supplier


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def in_two_weeks():
    return timezone.localdate() + timedelta(days=14)


@pytest.fixture
def make_supplier(db):
    numbers = count(1)

    def factory(**fields):
        number = next(numbers)
        data = {
            "name": f"Test Supplier {number}",
            "contact_email": f"supplier{number}@example.com",
            "payment_terms_days": 30,
            "is_active": True,
        }
        data.update(fields)
        return Supplier.objects.create(**data)

    return factory


@pytest.fixture
def make_order(db, make_supplier, in_two_weeks):
    def factory(supplier=None, **fields):
        data = {
            "supplier": supplier or make_supplier(),
            "requested_by": "Alex Moreno",
            "needed_by": in_two_weeks,
            "status": PurchaseOrder.Status.DRAFT,
        }
        data.update(fields)
        if data["status"] != PurchaseOrder.Status.DRAFT:
            data.setdefault("submitted_at", timezone.now())
        return PurchaseOrder.objects.create(**data)

    return factory


@pytest.fixture
def make_line(db):
    skus = count(1)

    def factory(order, quantity=1, unit_price="10.00", discount_percent=0, **fields):
        number = next(skus)
        data = {
            "sku": f"SKU-{number:03d}",
            "description": f"Test item {number}",
        }
        data.update(fields)
        return OrderLine.objects.create(
            purchase_order=order,
            quantity=quantity,
            unit_price=Decimal(unit_price),
            discount_percent=discount_percent,
            **data,
        )

    return factory
