from django.db import models

from employees.models import Employee


class TrainingCourse(models.Model):
    class Status(models.TextChoices):
        UPCOMING = 'UPCOMING', 'Upcoming'
        ONGOING = 'ONGOING', 'Ongoing'
        COMPLETED = 'COMPLETED', 'Completed'
        CANCELLED = 'CANCELLED', 'Cancelled'

    title = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    trainer = models.CharField(max_length=120, blank=True)
    start_date = models.DateField()
    end_date = models.DateField()
    capacity = models.PositiveIntegerField(default=20)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.UPCOMING)

    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return self.title

    @property
    def seats_taken(self):
        return self.enrollments.exclude(status='WITHDRAWN').count()


class TrainingEnrollment(models.Model):
    class Status(models.TextChoices):
        ENROLLED = 'ENROLLED', 'Enrolled'
        COMPLETED = 'COMPLETED', 'Completed'
        WITHDRAWN = 'WITHDRAWN', 'Withdrawn'

    course = models.ForeignKey(
        TrainingCourse,
        on_delete=models.CASCADE,
        related_name='enrollments',
    )
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='trainings',
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ENROLLED)
    completion_date = models.DateField(null=True, blank=True)
    score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-enrolled_at']
        unique_together = [('course', 'employee')]

    def __str__(self):
        return f'{self.employee} → {self.course}'
