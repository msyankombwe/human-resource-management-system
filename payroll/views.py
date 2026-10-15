from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.decorators import hr_required
from employees.models import Employee

from .forms import PayrollPeriodForm, PayslipForm
from .models import PayrollPeriod, Payslip


@hr_required
def period_list(request):
    periods = PayrollPeriod.objects.all()
    form = PayrollPeriodForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Payroll period created.')
        return redirect('payroll:periods')
    return render(request, 'payroll/periods.html', {'periods': periods, 'form': form})


@hr_required
def generate_payslips(request, pk):
    period = get_object_or_404(PayrollPeriod, pk=pk)
    created = 0
    for emp in Employee.objects.filter(status='ACTIVE'):
        _, was_created = Payslip.objects.get_or_create(
            employee=emp,
            period=period,
            defaults={
                'basic_salary': emp.base_salary,
                'allowances': emp.base_salary * 0,
                'deductions': emp.base_salary * 0,
                'net_pay': emp.base_salary,
            },
        )
        if was_created:
            created += 1
    period.status = PayrollPeriod.Status.PROCESSED
    period.processed_at = timezone.now()
    period.save()
    messages.success(request, f'Generated {created} new payslip(s) for {period}.')
    return redirect('payroll:payslips')


@login_required
def payslip_list(request):
    profile = getattr(request.user, 'profile', None)
    slips = Payslip.objects.select_related('employee', 'period', 'employee__user')
    if profile and profile.role == 'EMPLOYEE':
        employee = getattr(request.user, 'employee', None)
        slips = slips.filter(employee=employee) if employee else slips.none()
    return render(request, 'payroll/payslips.html', {'payslips': slips})


@hr_required
def payslip_create(request):
    form = PayslipForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Payslip created.')
        return redirect('payroll:payslips')
    return render(request, 'payroll/form.html', {'form': form, 'title': 'Create Payslip'})


@login_required
def payslip_detail(request, pk):
    slip = get_object_or_404(
        Payslip.objects.select_related('employee', 'period', 'employee__user'),
        pk=pk,
    )
    profile = getattr(request.user, 'profile', None)
    if profile and profile.role == 'EMPLOYEE':
        employee = getattr(request.user, 'employee', None)
        if not employee or slip.employee_id != employee.id:
            messages.error(request, 'You can only view your own payslips.')
            return redirect('payroll:payslips')
    return render(request, 'payroll/detail.html', {'payslip': slip})
