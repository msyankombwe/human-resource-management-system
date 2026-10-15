from django.urls import path

from . import views

app_name = 'payroll'

urlpatterns = [
    path('periods/', views.period_list, name='periods'),
    path('periods/<int:pk>/generate/', views.generate_payslips, name='generate'),
    path('payslips/', views.payslip_list, name='payslips'),
    path('payslips/add/', views.payslip_create, name='payslip_create'),
    path('payslips/<int:pk>/', views.payslip_detail, name='payslip_detail'),
]
