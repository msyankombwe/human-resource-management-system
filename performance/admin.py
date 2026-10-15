from django.contrib import admin

from .models import AppraisalCycle, PerformanceReview


@admin.register(AppraisalCycle)
class AppraisalCycleAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_date', 'end_date', 'status')


@admin.register(PerformanceReview)
class PerformanceReviewAdmin(admin.ModelAdmin):
    list_display = ('employee', 'cycle', 'reviewer', 'rating', 'status')
    list_filter = ('status', 'rating')
