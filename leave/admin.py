from django.contrib import admin

from .models import LeaveRequest, LeaveType


@admin.register(LeaveType)
class LeaveTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'days_allowed')


@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ('employee', 'leave_type', 'start_date', 'end_date', 'status')
    list_filter = ('status', 'leave_type')
