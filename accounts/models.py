from django.conf import settings
from django.db import models


class UserProfile(models.Model):
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'Administrator'
        HR = 'HR', 'HR Officer'
        MANAGER = 'MANAGER', 'Manager'
        EMPLOYEE = 'EMPLOYEE', 'Employee'

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile',
    )
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.EMPLOYEE)
    phone = models.CharField(max_length=30, blank=True)

    def __str__(self):
        return f'{self.user.username} ({self.get_role_display()})'

    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN

    @property
    def is_hr(self):
        return self.role in {self.Role.ADMIN, self.Role.HR}

    @property
    def is_manager(self):
        return self.role in {self.Role.ADMIN, self.Role.HR, self.Role.MANAGER}
