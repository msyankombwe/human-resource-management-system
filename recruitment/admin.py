from django.contrib import admin

from .models import Applicant, Interview, JobPosting


@admin.register(JobPosting)
class JobPostingAdmin(admin.ModelAdmin):
    list_display = ('title', 'department', 'status', 'posted_date', 'closing_date')
    list_filter = ('status',)


@admin.register(Applicant)
class ApplicantAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'job', 'email', 'status', 'applied_date')
    list_filter = ('status',)


@admin.register(Interview)
class InterviewAdmin(admin.ModelAdmin):
    list_display = ('applicant', 'scheduled_at', 'interviewer', 'result')
    list_filter = ('result',)
