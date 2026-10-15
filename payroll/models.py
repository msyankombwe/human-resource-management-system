from django.db import models

from employees.models import Employee


class PayrollPeriod(models.Model):
    class Status(models.TextChoices):
        OPEN = 'OPEN', 'Open'
        PROCESSED = 'PROCESSED', 'Processed'
        CLOSED = 'CLOSED', 'Closed'

    month = models.PositiveSmallIntegerField()
    year = models.PositiveSmallIntegerField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-year', '-month']
        unique_together = [('month', 'year')]

    def __str__(self):
        return f'{self.year}-{self.month:02d}'


class Payslip(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='payslips')
    period = models.ForeignKey(PayrollPeriod, on_delete=models.CASCADE, related_name='payslips')
    basic_salary = models.DecimalField(max_digits=12, decimal_places=2)
    allowances = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    deductions = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    net_pay = models.DecimalField(max_digits=12, decimal_places=2)
    notes = models.TextField(blank=True)
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-generated_at']
        unique_together = [('employee', 'period')]

    def __str__(self):
        return f'Payslip {self.employee} — {self.period}'

    def save(self, *args, **kwargs):
        self.net_pay = self.basic_salary + self.allowances - self.deductions
        super().save(*args, **kwargs)
