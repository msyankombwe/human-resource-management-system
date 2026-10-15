from django.urls import path

from . import views

app_name = 'attendance'

urlpatterns = [
    path('', views.attendance_list, name='list'),
    path('add/', views.attendance_create, name='create'),
    path('<int:pk>/edit/', views.attendance_edit, name='edit'),
    path('clock-in/', views.clock_in, name='clock_in'),
    path('clock-out/', views.clock_out, name='clock_out'),
]
