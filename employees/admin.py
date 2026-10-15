from django.contrib import admin

from .models import Department, Employee


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    search_fields = ('name',)


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('employee_id', 'user', 'department', 'job_title', 'status', 'hire_date')
    list_filter = ('status', 'department')
    search_fields = ('employee_id', 'user__username', 'user__first_name', 'user__last_name')
