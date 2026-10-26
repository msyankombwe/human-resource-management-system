from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('marketplace.urls')),
    path('', include('accounts.urls')),
    path('employees/', include('employees.urls')),
    path('recruitment/', include('recruitment.urls')),
    path('attendance/', include('attendance.urls')),
    path('leave/', include('leave.urls')),
    path('payroll/', include('payroll.urls')),
    path('performance/', include('performance.urls')),
    path('training/', include('training.urls')),
    path('self-service/', include('self_service.urls')),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

admin.site.site_header = 'HRMS Administration'
admin.site.site_title = 'HRMS Admin'
admin.site.index_title = 'Human Resource Management System'
