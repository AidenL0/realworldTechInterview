import pytest

from purchasing.models import PurchaseOrder

ORDERS_URL = "/api/purchase-orders/"


@pytest.mark.django_db
def test_create_order_ignores_status_in_body(api_client, make_supplier, in_two_weeks):
    supplier = make_supplier()

    response = api_client.post(
        ORDERS_URL,
        {
            "supplier": supplier.id,
            "requested_by": "Jordan Blake",
            "needed_by": in_two_weeks.isoformat(),
            "status": "approved",
        },
        format="json",
    )

    assert response.status_code == 201
    assert response.json()["status"] == "draft"
    assert PurchaseOrder.objects.get().status == "draft"


@pytest.mark.django_db
def test_update_draft_order_ignores_status_in_body(api_client, make_order):
    order = make_order(status="draft", notes="")

    response = api_client.patch(
        f"{ORDERS_URL}{order.id}/",
        {"status": "submitted", "notes": "Deliver to loading dock B"},
        format="json",
    )

    assert response.status_code == 200
    order.refresh_from_db()
    assert order.status == "draft"
    assert order.notes == "Deliver to loading dock B"


@pytest.mark.django_db
def test_rejected_update_leaves_submitted_order_unchanged(api_client, make_order):
    order = make_order(status="submitted", notes="Original notes", requested_by="Jordan Blake")

    response = api_client.patch(
        f"{ORDERS_URL}{order.id}/",
        {"notes": "Changed after submitting", "requested_by": "Someone Else"},
        format="json",
    )

    assert response.status_code == 409
    order.refresh_from_db()
    assert order.notes == "Original notes"
    assert order.requested_by == "Jordan Blake"


@pytest.mark.django_db
def test_list_total_rounds_discounted_lines_half_up(api_client, make_order, make_line):
    order = make_order()
    make_line(order, quantity=1, unit_price="10.25", discount_percent=10)
    make_line(order, quantity=3, unit_price="19.99", discount_percent=15)

    response = api_client.get(ORDERS_URL)

    assert response.status_code == 200
    [listed] = response.json()
    assert listed["line_count"] == 2
    assert listed["total"] == "60.20"


@pytest.mark.django_db
def test_submit_without_lines_keeps_order_in_draft(api_client, make_order):
    order = make_order()

    response = api_client.post(f"{ORDERS_URL}{order.id}/submit/")

    assert response.status_code == 400
    order.refresh_from_db()
    assert order.status == "draft"
    assert order.submitted_at is None


@pytest.mark.django_db
def test_submit_already_submitted_order_returns_409(api_client, make_order, make_line):
    order = make_order(status="submitted")
    make_line(order)

    response = api_client.post(f"{ORDERS_URL}{order.id}/submit/")

    assert response.status_code == 409
