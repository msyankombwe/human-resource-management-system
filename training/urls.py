from django.urls import path

from . import views

app_name = 'training'

urlpatterns = [
    path('courses/', views.course_list, name='courses'),
    path('courses/add/', views.course_create, name='course_create'),
    path('courses/<int:pk>/edit/', views.course_edit, name='course_edit'),
    path('courses/<int:pk>/enroll/', views.self_enroll, name='self_enroll'),
    path('enrollments/', views.enrollment_list, name='enrollments'),
    path('enrollments/add/', views.enrollment_create, name='enrollment_create'),
]
