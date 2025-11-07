from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('dashboard.urls')),
    path('auth/', include(('core.urls', 'core'), namespace='core')),
    path("tasks/", include("tasks.urls")),
    path("announcements/", include("comms.urls")),
    path("bookings/", include("booking.urls")),
    path("feedbacks/", include("feedbacks.urls")),
    path("departments/", include("departments.urls")),
]
