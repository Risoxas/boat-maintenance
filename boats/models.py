from decimal import Decimal

from django.core.validators import MinValueValidator, RegexValidator
from django.db import models

postal_validator = RegexValidator(
    regex=r"^\d{4,5}$",
    message="Postal code must be 4 or 5 digits.",
    code="invalid_postal_code",
)


def boat_photo_upload_path(instance: "BoatPhoto", filename: str) -> str:
    return f"boats/{instance.boat_id or 'unassigned'}/{filename}"


def service_proof_upload_path(instance: "ServiceProofPhoto", filename: str) -> str:
    return f"orders/{instance.order_id or 'unassigned'}/{instance.stage}/{filename}"


class Customer(models.Model):
    company_name = models.CharField(max_length=200, blank=True)
    contact_first_name = models.CharField(max_length=50)
    contact_last_name = models.CharField(max_length=50)
    billing_address = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state_province = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=5, validators=[postal_validator], blank=True)
    country = models.CharField(max_length=50, blank=True)
    phone_number = models.CharField(max_length=20)
    mobile_phone_number = models.CharField(max_length=20, blank=True)
    email = models.EmailField(unique=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["contact_last_name", "contact_first_name"]

    def __str__(self) -> str:
        full_name = f"{self.contact_first_name} {self.contact_last_name}".strip()
        return f"{full_name} ({self.company_name})" if self.company_name else full_name


class Boat(models.Model):
    name = models.CharField(max_length=100)
    boat_type = models.CharField(max_length=150, blank=True)
    mooring_no = models.CharField(max_length=100, db_index=True)
    mooring_location = models.CharField(max_length=200)
    depth = models.PositiveIntegerField(blank=True, null=True, help_text="Mooring depth in feet")
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name="boats",
        blank=True,
        null=True,
    )
    last_check = models.DateField(blank=True, null=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["name", "mooring_no"]

    def __str__(self) -> str:
        return f"{self.name} (Mooring {self.mooring_no})"


class BoatPhoto(models.Model):
    boat = models.ForeignKey(Boat, on_delete=models.CASCADE, related_name="photos")
    image = models.ImageField(upload_to=boat_photo_upload_path)
    caption = models.CharField(max_length=200, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"Photo for {self.boat.name}"


class Employee(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    work_phone = models.CharField(max_length=20)

    class Meta:
        ordering = ["last_name", "first_name"]

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()


class ServiceOrder(models.Model):
    class Status(models.TextChoices):
        SCHEDULED = "scheduled", "Scheduled"
        IN_PROGRESS = "in_progress", "In Progress"
        COMPLETED = "completed", "Completed"

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="service_orders")
    employee = models.ForeignKey(Employee, on_delete=models.PROTECT, related_name="service_orders")
    boat = models.ForeignKey(Boat, on_delete=models.CASCADE, related_name="service_orders")
    order_date = models.DateField()
    service_date = models.DateField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SCHEDULED)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-service_date", "-id"]

    def __str__(self) -> str:
        return f"Order #{self.pk} · {self.boat.name} ({self.service_date})"

    @property
    def total_amount(self) -> Decimal:
        return sum((item.line_total for item in self.items.all()), Decimal("0.00"))


class ServiceProofPhoto(models.Model):
    class Stage(models.TextChoices):
        BEFORE = "before", "Before Service"
        AFTER = "after", "After Service"

    order = models.ForeignKey(ServiceOrder, on_delete=models.CASCADE, related_name="proof_photos")
    stage = models.CharField(max_length=10, choices=Stage.choices, default=Stage.BEFORE)
    image = models.ImageField(upload_to=service_proof_upload_path)
    caption = models.CharField(max_length=200, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["stage", "uploaded_at"]

    def __str__(self) -> str:
        return f"{self.get_stage_display()} proof for Order #{self.order_id}"


class Product(models.Model):
    name = models.CharField(max_length=100, unique=True)
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return f"{self.name} (${self.unit_price})"


class OrderDetail(models.Model):
    order = models.ForeignKey(ServiceOrder, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="order_items")
    quantity = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )

    def __str__(self) -> str:
        return f"{self.product.name} x {self.quantity} (Order #{self.order_id})"

    @property
    def line_total(self) -> Decimal:
        return (self.quantity * self.unit_price).quantize(Decimal("0.01"))
