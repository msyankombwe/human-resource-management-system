from django.db import models

from employees.models import Employee


class AppraisalCycle(models.Model):
    class Status(models.TextChoices):
        PLANNED = 'PLANNED', 'Planned'
        ACTIVE = 'ACTIVE', 'Active'
        CLOSED = 'CLOSED', 'Closed'

    name = models.CharField(max_length=120)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PLANNED)

    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return self.name


class PerformanceReview(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        SUBMITTED = 'SUBMITTED', 'Submitted'
        ACKNOWLEDGED = 'ACKNOWLEDGED', 'Acknowledged'

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='reviews',
    )
    cycle = models.ForeignKey(
        AppraisalCycle,
        on_delete=models.CASCADE,
        related_name='reviews',
    )
    reviewer = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviews_given',
    )
    goals = models.TextField(blank=True)
    achievements = models.TextField(blank=True)
    rating = models.PositiveSmallIntegerField(default=3)  # 1-5
    comments = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    reviewed_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-reviewed_at']
        unique_together = [('employee', 'cycle')]

    def __str__(self):
        return f'{self.employee} — {self.cycle} ({self.rating}/5)'
