from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from accounts.decorators import hr_required

from .forms import DepartmentForm, EmployeeForm
from .models import Department, Employee


@login_required
def employee_list(request):
    employees = Employee.objects.select_related('user', 'department', 'manager')
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
    employee = get_object_or_404(
        Employee.objects.select_related('user', 'department', 'manager'),
        pk=pk,
    )
    return render(request, 'employees/detail.html', {'employee': employee})


@hr_required
def employee_create(request):
    form = EmployeeForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Employee record created.')
        return redirect('employees:list')
    return render(request, 'employees/form.html', {'form': form, 'title': 'Add Employee'})


@hr_required
def employee_edit(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    form = EmployeeForm(request.POST or None, instance=employee)
    if request.method == 'POST' and form.is_valid():
        form.save()
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
