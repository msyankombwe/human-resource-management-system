from django.contrib import admin

from .models import TrainingCourse, TrainingEnrollment


@admin.register(TrainingCourse)
class TrainingCourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'trainer', 'start_date', 'end_date', 'status', 'capacity')
    list_filter = ('status',)


@admin.register(TrainingEnrollment)
class TrainingEnrollmentAdmin(admin.ModelAdmin):
    list_display = ('employee', 'course', 'status', 'score', 'enrolled_at')
    list_filter = ('status',)
