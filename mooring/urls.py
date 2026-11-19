from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path

admin.site.site_header = "Mooring & Boat Maintenance Admin"
admin.site.site_title = "Boat Maintenance"
admin.site.index_title = "Service Orders, Moorings & Photo Proofs"

urlpatterns = [
    path("admin/", admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
