from django.conf import settings
from django.db import models

from employees.models import Employee


class LeaveType(models.Model):
    name = models.CharField(max_length=80, unique=True)
    days_allowed = models.PositiveIntegerField(default=0)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class LeaveRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'
        CANCELLED = 'CANCELLED', 'Cancelled'

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='leave_requests',
    )
    leave_type = models.ForeignKey(
        LeaveType,
        on_delete=models.PROTECT,
        related_name='requests',
    )
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='leave_approvals',
    )
    decision_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.employee} — {self.leave_type} ({self.status})'

    @property
    def duration_days(self):
        return (self.end_date - self.start_date).days + 1
