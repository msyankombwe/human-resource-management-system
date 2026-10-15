from django.db import models

from employees.models import Employee


class AttendanceRecord(models.Model):
    class Status(models.TextChoices):
        PRESENT = 'PRESENT', 'Present'
        ABSENT = 'ABSENT', 'Absent'
        LATE = 'LATE', 'Late'
        HALF_DAY = 'HALF_DAY', 'Half Day'
        REMOTE = 'REMOTE', 'Remote'

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='attendance_records',
    )
    date = models.DateField()
    check_in = models.TimeField(null=True, blank=True)
    check_out = models.TimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PRESENT)
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['-date', 'employee']
        unique_together = [('employee', 'date')]

    def __str__(self):
        return f'{self.employee} — {self.date} ({self.status})'
