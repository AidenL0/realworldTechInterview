import pytest


def approve_url(order):
    return f"/api/purchase-orders/{order.id}/approve/"


@pytest.mark.django_db
def test_approve_submitted_order(api_client, make_order, make_line):
    order = make_order(status="submitted", requested_by="Jordan Blake")
    make_line(order)

    response = api_client.post(approve_url(order), {"approver": "Morgan Diaz"}, format="json")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "approved"
    assert body["approved_by"] == "Morgan Diaz"
    assert body["approved_at"] is not None


@pytest.mark.django_db
def test_approve_draft_order_returns_409(api_client, make_order, make_line):
    order = make_order(status="draft")
    make_line(order)

    response = api_client.post(approve_url(order), {"approver": "Morgan Diaz"}, format="json")

    assert response.status_code == 409
    order.refresh_from_db()
    assert order.status == "draft"
