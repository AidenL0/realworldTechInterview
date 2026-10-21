import pytest


@pytest.mark.django_db
def test_supplier_detail_counts_only_open_orders(api_client, make_supplier, make_order):
    supplier = make_supplier()
    make_order(supplier=supplier, status="draft")
    make_order(supplier=supplier, status="submitted")
    make_order(supplier=supplier, status="approved")
    make_order(supplier=supplier, status="approved")
    make_order(status="draft")

    response = api_client.get(f"/api/suppliers/{supplier.id}/")

    assert response.status_code == 200
    assert response.json()["open_orders"] == 2
