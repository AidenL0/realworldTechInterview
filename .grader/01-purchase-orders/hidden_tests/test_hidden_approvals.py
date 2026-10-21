from datetime import timedelta

import pytest
from django.utils import timezone


def approve_url(order):
    return f"/api/purchase-orders/{order.id}/approve/"


@pytest.mark.django_db
def test_requester_cannot_approve_own_order(api_client, make_order, make_line):
    order = make_order(status="submitted", requested_by="Priya Raman")
    make_line(order)

    response = api_client.post(approve_url(order), {"approver": "priya raman"}, format="json")

    assert response.status_code == 400
    assert "approver" in response.json()
    order.refresh_from_db()
    assert order.status == "submitted"


@pytest.mark.django_db
def test_approve_sets_payment_due_date_from_supplier_terms(api_client, make_supplier, make_order, make_line):
    supplier = make_supplier(payment_terms_days=45)
    order = make_order(supplier=supplier, status="submitted")
    make_line(order)

    response = api_client.post(approve_url(order), {"approver": "Dana Whitfield"}, format="json")

    assert response.status_code == 200
    order.refresh_from_db()
    assert order.status == "approved"
    assert order.approved_by == "Dana Whitfield"
    expected_due = timezone.localdate(order.approved_at) + timedelta(days=45)
    assert response.json()["payment_due_date"] == expected_due.isoformat()


@pytest.mark.django_db
def test_approve_without_approver_returns_400(api_client, make_order, make_line):
    order = make_order(status="submitted")
    make_line(order)

    response = api_client.post(approve_url(order), {}, format="json")

    assert response.status_code == 400
    assert "approver" in response.json()
    order.refresh_from_db()
    assert order.status == "submitted"
