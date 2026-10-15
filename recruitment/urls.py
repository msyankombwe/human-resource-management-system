from django.urls import path

from . import views

app_name = 'recruitment'

urlpatterns = [
    path('jobs/', views.job_list, name='jobs'),
    path('jobs/add/', views.job_create, name='job_create'),
    path('jobs/<int:pk>/edit/', views.job_edit, name='job_edit'),
    path('applicants/', views.applicant_list, name='applicants'),
    path('applicants/add/', views.applicant_create, name='applicant_create'),
    path('applicants/<int:pk>/edit/', views.applicant_edit, name='applicant_edit'),
    path('interviews/', views.interview_list, name='interviews'),
    path('interviews/add/', views.interview_create, name='interview_create'),
]
