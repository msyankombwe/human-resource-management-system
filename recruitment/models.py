from django.conf import settings
from django.db import models

from employees.models import Department, Employee


class JobPosting(models.Model):
    class Status(models.TextChoices):
        OPEN = 'OPEN', 'Open'
        CLOSED = 'CLOSED', 'Closed'
        DRAFT = 'DRAFT', 'Draft'

    title = models.CharField(max_length=150)
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='job_postings',
    )
    description = models.TextField()
    requirements = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    posted_date = models.DateField(auto_now_add=True)
    closing_date = models.DateField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ['-posted_date']

    def __str__(self):
        return self.title


class Applicant(models.Model):
    class Status(models.TextChoices):
        APPLIED = 'APPLIED', 'Applied'
        SCREENING = 'SCREENING', 'Screening'
        INTERVIEW = 'INTERVIEW', 'Interview'
        OFFERED = 'OFFERED', 'Offered'
        HIRED = 'HIRED', 'Hired'
        REJECTED = 'REJECTED', 'Rejected'

    job = models.ForeignKey(JobPosting, on_delete=models.CASCADE, related_name='applicants')
    full_name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=30, blank=True)
    resume_summary = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.APPLIED)
    applied_date = models.DateField(auto_now_add=True)

    class Meta:
        ordering = ['-applied_date']

    def __str__(self):
        return f'{self.full_name} → {self.job.title}'


class Interview(models.Model):
    class Result(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        PASS = 'PASS', 'Pass'
        FAIL = 'FAIL', 'Fail'

    applicant = models.ForeignKey(Applicant, on_delete=models.CASCADE, related_name='interviews')
    scheduled_at = models.DateTimeField()
    interviewer = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='interviews_conducted',
    )
    location = models.CharField(max_length=150, blank=True)
    notes = models.TextField(blank=True)
    result = models.CharField(max_length=20, choices=Result.choices, default=Result.PENDING)

    class Meta:
        ordering = ['scheduled_at']

    def __str__(self):
        return f'Interview: {self.applicant.full_name}'
