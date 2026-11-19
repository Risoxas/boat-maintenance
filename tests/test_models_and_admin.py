from datetime import date

import pytest
from django.contrib import admin

from boats.models import (
    Boat,
    Customer,
    Employee,
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
