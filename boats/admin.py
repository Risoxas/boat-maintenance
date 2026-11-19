from django.contrib import admin
from django.utils.html import format_html, format_html_join

from boats.models import (
    Boat,
    BoatPhoto,
    Customer,
    Employee,
    OrderDetail,
    Product,
    ServiceOrder,
    ServiceProofPhoto,
)


class BoatPhotoInline(admin.TabularInline):
    model = BoatPhoto
    extra = 1
    readonly_fields = ("thumbnail",)

    @admin.display(description="Preview")
    def thumbnail(self, obj: BoatPhoto) -> str:
        if not obj.image:
            return "No image"
        return format_html(
            '<img src="{}" style="max-height:120px;border-radius:6px;" />',
            obj.image.url,
        )


class ServiceProofPhotoInline(admin.TabularInline):
    model = ServiceProofPhoto
    extra = 1
    readonly_fields = ("thumbnail",)

    @admin.display(description="Proof Preview")
    def thumbnail(self, obj: ServiceProofPhoto) -> str:
        if not obj.image:
            return "No image"
        return format_html(
            '<img src="{}" style="max-height:140px;border-radius:6px;" />',
            obj.image.url,
        )


class OrderDetailInline(admin.TabularInline):
    model = OrderDetail
    extra = 1


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = (
        "contact_first_name",
        "contact_last_name",
        "company_name",
        "email",
        "phone_number",
    )
    search_fields = ("contact_first_name", "contact_last_name", "company_name", "email")


@admin.register(Boat)
class BoatAdmin(admin.ModelAdmin):
    list_display = ("name", "mooring_no", "mooring_location", "customer", "last_check")
    list_filter = ("mooring_location", "last_check")
    search_fields = ("name", "mooring_no", "customer__contact_last_name")
    inlines = [BoatPhotoInline]


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ("first_name", "last_name", "work_phone")
    search_fields = ("first_name", "last_name")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "unit_price")
    search_fields = ("name",)


@admin.register(ServiceOrder)
class ServiceOrderAdmin(admin.ModelAdmin):
    list_display = ("id", "boat", "customer", "employee", "service_date", "status", "proof_count")
    list_filter = ("status", "service_date")
    search_fields = ("boat__name", "boat__mooring_no", "customer__contact_last_name")
    readonly_fields = ("proof_gallery",)
    inlines = [ServiceProofPhotoInline, OrderDetailInline]

    @admin.display(description="Proofs")
    def proof_count(self, obj: ServiceOrder) -> int:
        return obj.proof_photos.count()

    @admin.display(description="Before / After Proof Gallery")
    def proof_gallery(self, obj: ServiceOrder) -> str:
        photos = obj.proof_photos.all()
        if not photos:
            return "No proof photos uploaded yet."
        return format_html_join(
            "",
            '<div style="display:inline-block;margin:6px;text-align:center;">'
            '<div style="font-size:11px;font-weight:600;margin-bottom:4px;">{}</div>'
            '<img src="{}" style="max-height:180px;border-radius:6px;" />'
            "</div>",
            ((p.get_stage_display(), p.image.url) for p in photos if p.image),
        )
