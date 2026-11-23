from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory
from django.utils import timezone

from boats.admin import BoatAdmin, MooringCheckOverdueFilter, ServiceOrderAdmin
from boats.models import (
    MAX_PHOTO_SIZE_BYTES,
    Boat,
    BoatPhoto,
    Customer,
    Employee,
    OrderDetail,
    Product,
    ServiceOrder,
    ServiceProofPhoto,
    service_proof_upload_path,
    validate_photo_size,
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


@pytest.mark.django_db
def test_service_order_admin_csv_export() -> None:
    customer = Customer.objects.create(
        contact_first_name="Sofia",
        contact_last_name="Vega",
        phone_number="3310005555",
        email="sofia@example.com",
    )
    employee = Employee.objects.create(
        first_name="Luis",
        last_name="Gomez",
        work_phone="3310006666",
    )
    boat = Boat.objects.create(
        name="Coral Queen",
        mooring_no="M-07",
        mooring_location="Marina Vallarta",
        customer=customer,
    )
    order = ServiceOrder.objects.create(
        customer=customer,
        employee=employee,
        boat=boat,
        order_date=date(2026, 11, 19),
        service_date=date(2026, 11, 21),
        status=ServiceOrder.Status.COMPLETED,
    )
    service = Product.objects.create(name="Propeller Inspection", unit_price=Decimal("85.00"))
    OrderDetail.objects.create(
        order=order,
        product=service,
        quantity=Decimal("1.00"),
        unit_price=service.unit_price,
    )

    model_admin = ServiceOrderAdmin(ServiceOrder, admin.site)
    request = RequestFactory().get("/admin/boats/serviceorder/")
    response = model_admin.export_as_csv(request, ServiceOrder.objects.filter(pk=order.pk))

    assert response.status_code == 200
    assert response["Content-Type"] == "text/csv"
    assert 'filename="service_orders.csv"' in response["Content-Disposition"]

    csv_text = response.content.decode("utf-8")
    expected_header = (
        "Order ID,Boat,Mooring No,Customer,Employee,Service Date,Status,Proof Count,Total"
    )
    assert expected_header in csv_text
    assert "Coral Queen,M-07,Sofia Vega,Luis Gomez,2026-11-21,Completed,0,85.00" in csv_text


def test_photo_validation_rejects_oversized_and_bad_extensions() -> None:
    small_file = SimpleUploadedFile("hull.jpg", b"abc", content_type="image/jpeg")
    validate_photo_size(small_file)

    class OversizedStub:
        size = MAX_PHOTO_SIZE_BYTES + 1

    with pytest.raises(ValidationError, match="5 MB"):
        validate_photo_size(OversizedStub())

    bad_ext = SimpleUploadedFile("script.svg", b"<svg/>", content_type="image/svg+xml")
    photo = BoatPhoto(image=bad_ext)
    with pytest.raises(ValidationError):
        photo.image.field.run_validators(photo.image)


@pytest.mark.django_db
def test_service_order_admin_bulk_status_actions() -> None:
    customer = Customer.objects.create(
        contact_first_name="Mateo",
        contact_last_name="Cruz",
        phone_number="3310007777",
        email="mateo@example.com",
    )
    employee = Employee.objects.create(
        first_name="Lucia",
        last_name="Perez",
        work_phone="3310008888",
    )
    boat = Boat.objects.create(
        name="Wave Runner",
        mooring_no="M-88",
        mooring_location="Marina Vallarta",
        customer=customer,
    )
    order = ServiceOrder.objects.create(
        customer=customer,
        employee=employee,
        boat=boat,
        order_date=date(2026, 11, 20),
        service_date=date(2026, 11, 21),
    )
    assert order.status == ServiceOrder.Status.SCHEDULED

    model_admin = ServiceOrderAdmin(ServiceOrder, admin.site)
    model_admin.message_user = lambda *args, **kwargs: None  # type: ignore[method-assign]
    request = RequestFactory().post("/admin/boats/serviceorder/")

    qs = ServiceOrder.objects.filter(pk=order.pk)
    model_admin.mark_in_progress(request, qs)
    order.refresh_from_db()
    assert order.status == ServiceOrder.Status.IN_PROGRESS

    model_admin.mark_completed(request, qs)
    order.refresh_from_db()
    assert order.status == ServiceOrder.Status.COMPLETED


@pytest.mark.django_db
def test_service_order_rejects_service_date_before_order_date() -> None:
    customer = Customer.objects.create(
        contact_first_name="Diego",
        contact_last_name="Silva",
        phone_number="3310009999",
        email="diego@example.com",
    )
    employee = Employee.objects.create(
        first_name="Carla",
        last_name="Ruiz",
        work_phone="3310000001",
    )
    boat = Boat.objects.create(
        name="Blue Marlin",
        mooring_no="M-03",
        mooring_location="Marina Vallarta",
        customer=customer,
    )
    invalid_order = ServiceOrder(
        customer=customer,
        employee=employee,
        boat=boat,
        order_date=date(2026, 11, 20),
        service_date=date(2026, 11, 19),
    )
    with pytest.raises(ValidationError, match="Service date cannot be earlier"):
        invalid_order.full_clean()

    valid_order = ServiceOrder(
        customer=customer,
        employee=employee,
        boat=boat,
        order_date=date(2026, 11, 20),
        service_date=date(2026, 11, 20),
    )
    valid_order.full_clean()


def test_boat_days_since_last_check() -> None:
    boat_admin = BoatAdmin(Boat, admin.site)

    unchecked = Boat(name="Drifter", mooring_no="M-10", mooring_location="Bay")
    assert unchecked.days_since_last_check is None
    assert boat_admin.last_check_status(unchecked) == "Never checked"

    today = timezone.localdate()
    checked_today = Boat(
        name="Horizon", mooring_no="M-11", mooring_location="Bay", last_check=today
    )
    assert checked_today.days_since_last_check == 0
    assert boat_admin.last_check_status(checked_today) == "Today"

    checked_ago = Boat(
        name="Nautilus",
        mooring_no="M-12",
        mooring_location="Bay",
        last_check=today - timedelta(days=12),
    )
    assert checked_ago.days_since_last_check == 12
    assert boat_admin.last_check_status(checked_ago) == "12d ago"


@pytest.mark.django_db
def test_boat_admin_overdue_filter() -> None:
    today = timezone.localdate()
    overdue = Boat.objects.create(
        name="Old Salt",
        mooring_no="M-21",
        mooring_location="Bay",
        last_check=today - timedelta(days=45),
    )
    current = Boat.objects.create(
        name="Fresh Wind",
        mooring_no="M-22",
        mooring_location="Bay",
        last_check=today - timedelta(days=5),
    )
    never = Boat.objects.create(
        name="Uninspected",
        mooring_no="M-23",
        mooring_location="Bay",
    )

    boat_admin = BoatAdmin(Boat, admin.site)
    qs = Boat.objects.all()

    f_overdue = MooringCheckOverdueFilter(
        RequestFactory().get("/admin/boats/boat/"),
        {"inspection_status": ["overdue"]},
        Boat,
        boat_admin,
    )
    assert list(f_overdue.queryset(RequestFactory().get("/"), qs)) == [overdue]

    f_current = MooringCheckOverdueFilter(
        RequestFactory().get("/admin/boats/boat/"),
        {"inspection_status": ["current"]},
        Boat,
        boat_admin,
    )
    assert list(f_current.queryset(RequestFactory().get("/"), qs)) == [current]

    f_never = MooringCheckOverdueFilter(
        RequestFactory().get("/admin/boats/boat/"),
        {"inspection_status": ["never"]},
        Boat,
        boat_admin,
    )
    assert list(f_never.queryset(RequestFactory().get("/"), qs)) == [never]
