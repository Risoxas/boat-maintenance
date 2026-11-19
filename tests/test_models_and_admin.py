from datetime import date
from decimal import Decimal

import pytest
from django.contrib import admin

from boats.models import (
    Boat,
    Customer,
    Employee,
    OrderDetail,
    Product,
    ServiceOrder,
    ServiceProofPhoto,
    service_proof_upload_path,
)


@pytest.mark.django_db
def test_service_order_and_proof_upload_path() -> None:
    customer = Customer.objects.create(
        contact_first_name="Carlos",
        contact_last_name="Mendez",
        phone_number="3310001111",
        email="carlos@example.com",
    )
    employee = Employee.objects.create(
        first_name="Ana",
        last_name="Lopez",
        work_phone="3310002222",
    )
    boat = Boat.objects.create(
        name="Sea Breeze",
        mooring_no="M-42",
        mooring_location="Marina Vallarta",
        customer=customer,
    )
    order = ServiceOrder.objects.create(
        customer=customer,
        employee=employee,
        boat=boat,
        order_date=date(2026, 11, 18),
        service_date=date(2026, 11, 19),
    )

    proof = ServiceProofPhoto(order=order, stage=ServiceProofPhoto.Stage.BEFORE)
    assert service_proof_upload_path(proof, "hull.jpg") == f"orders/{order.pk}/before/hull.jpg"
    assert "M-42" in str(boat)


def test_admin_models_registered() -> None:
    for model in (Customer, Boat, Employee, ServiceOrder):
        assert model in admin.site._registry


@pytest.mark.django_db
def test_service_order_total_amount() -> None:
    customer = Customer.objects.create(
        contact_first_name="Elena",
        contact_last_name="Rios",
        phone_number="3310003333",
        email="elena@example.com",
    )
    employee = Employee.objects.create(
        first_name="Marco",
        last_name="Diaz",
        work_phone="3310004444",
    )
    boat = Boat.objects.create(
        name="Pacific Star",
        mooring_no="M-19",
        mooring_location="Marina Nuevo",
        customer=customer,
    )
    order = ServiceOrder.objects.create(
        customer=customer,
        employee=employee,
        boat=boat,
        order_date=date(2026, 11, 19),
        service_date=date(2026, 11, 20),
    )
    assert order.total_amount == Decimal("0.00")

    zinc_anode = Product.objects.create(name="Zinc Anode", unit_price=Decimal("45.50"))
    hull_clean = Product.objects.create(name="Hull Cleaning", unit_price=Decimal("120.00"))

    d1 = OrderDetail.objects.create(
        order=order,
        product=zinc_anode,
        quantity=Decimal("2.00"),
        unit_price=zinc_anode.unit_price,
    )
    d2 = OrderDetail.objects.create(
        order=order,
        product=hull_clean,
        quantity=Decimal("1.00"),
        unit_price=hull_clean.unit_price,
    )

    assert d1.line_total == Decimal("91.00")
    assert d2.line_total == Decimal("120.00")
    assert order.total_amount == Decimal("211.00")
