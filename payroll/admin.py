from django.contrib import admin

from .models import PayrollPeriod, Payslip


@admin.register(PayrollPeriod)
class PayrollPeriodAdmin(admin.ModelAdmin):
    list_display = ('year', 'month', 'status', 'processed_at')


@admin.register(Payslip)
class PayslipAdmin(admin.ModelAdmin):
    list_display = ('employee', 'period', 'basic_salary', 'net_pay', 'generated_at')
