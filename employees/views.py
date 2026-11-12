from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from accounts.access import visible_employees
from accounts.decorators import hr_required
from accounts.models import UserProfile

from .forms import DepartmentForm, EmployeeForm
from .models import Department, Employee


def _ensure_employee_profile(employee):
    UserProfile.objects.get_or_create(
        user=employee.user,
        defaults={
            'role': UserProfile.Role.EMPLOYEE,
            'phone': employee.phone,
        },
    )


@login_required
def employee_list(request):
    employees = visible_employees(request.user)
    status = request.GET.get('status')
    if status:
        employees = employees.filter(status=status)
    q = request.GET.get('q')
    if q:
        from django.db.models import Q

        employees = employees.filter(
            Q(user__first_name__icontains=q)
            | Q(user__last_name__icontains=q)
            | Q(employee_id__icontains=q)
        )
    return render(request, 'employees/list.html', {'employees': employees, 'q': q or '', 'status': status or ''})


@login_required
def employee_detail(request, pk):
    employee = get_object_or_404(visible_employees(request.user), pk=pk)
    return render(request, 'employees/detail.html', {'employee': employee})


@hr_required
def employee_create(request):
    form = EmployeeForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        employee = form.save()
        _ensure_employee_profile(employee)
        messages.success(request, 'Employee record created.')
        return redirect('employees:list')
    return render(request, 'employees/form.html', {'form': form, 'title': 'Add Employee'})


@hr_required
def employee_edit(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    form = EmployeeForm(request.POST or None, instance=employee)
    if request.method == 'POST' and form.is_valid():
        employee = form.save()
        _ensure_employee_profile(employee)
        messages.success(request, 'Employee record updated.')
        return redirect('employees:detail', pk=pk)
    return render(request, 'employees/form.html', {'form': form, 'title': 'Edit Employee'})


@hr_required
def department_list(request):
    departments = Department.objects.all()
    form = DepartmentForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Department added.')
        return redirect('employees:departments')
    return render(
        request,
        'employees/departments.html',
        {'departments': departments, 'form': form},
    )
