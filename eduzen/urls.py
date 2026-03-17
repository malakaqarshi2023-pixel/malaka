from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Admin panel
    path('admin/', admin.site.urls),

    # API v1
    path('api/v1/auth/',     include('apps.users.urls')),
    path('api/v1/courses/',  include('apps.courses.urls')),
    path('api/v1/payments/', include('apps.payments.urls')),
]

# Media fayllar (development)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
