from django.conf import settings
from django.db import models


class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Employee(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Active'
        ON_LEAVE = 'ON_LEAVE', 'On Leave'
        PROBATION = 'PROBATION', 'Probation'
        SEPARATED = 'SEPARATED', 'Separated'

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='employee',
    )
    employee_id = models.CharField(max_length=20, unique=True)
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='employees',
    )
    job_title = models.CharField(max_length=120)
    hire_date = models.DateField()
    date_of_birth = models.DateField(null=True, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    address = models.TextField(blank=True)
    emergency_contact = models.CharField(max_length=120, blank=True)
    base_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    manager = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='direct_reports',
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['employee_id']

    def __str__(self):
        return f'{self.employee_id} — {self.user.get_full_name() or self.user.username}'

    @property
    def full_name(self):
        return self.user.get_full_name() or self.user.username
