from django.contrib import messages
from django.contrib.admin.models import ADDITION, CHANGE, LogEntry
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404, redirect, render

from accounts.access import visible_employees
from accounts.decorators import hr_required
from accounts.models import UserProfile

from .forms import DepartmentForm, EmployeeForm, EmployeeOnboardingForm
from .models import Department, Employee


def _ensure_employee_profile(employee):
    UserProfile.objects.get_or_create(
        user=employee.user,
        defaults={
            'role': UserProfile.Role.EMPLOYEE,
            'phone': employee.phone,
        },
    )


def _record_employee_action(actor, employee, action_flag, change_message):
    LogEntry.objects.log_actions(
        user_id=actor.pk,
        queryset=Employee.objects.filter(pk=employee.pk),
        action_flag=action_flag,
        change_message=change_message,
        single_object=True,
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
    form = EmployeeOnboardingForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        try:
            with transaction.atomic():
                if form.cleaned_data['account_mode'] == 'new':
                    User = get_user_model()
                    user = User._default_manager.create_user(
                        username=form.cleaned_data['username'],
                        first_name=form.cleaned_data['first_name'],
                        last_name=form.cleaned_data['last_name'],
                        email=form.cleaned_data['email'],
                        password=form.cleaned_data['password1'],
                        is_staff=False,
                        is_superuser=False,
                    )
                else:
                    user = form.cleaned_data['user']

                employee = form.save(commit=False)
                employee.user = user
                employee.save()
                form.save_m2m()
                _ensure_employee_profile(employee)

                _record_employee_action(
                    request.user,
                    employee,
                    ADDITION,
                    f"Created through HRMS onboarding; account mode: {form.cleaned_data['account_mode']}.",
                )
        except IntegrityError:
            form.add_error(
                None,
                'The account or employee ID already exists. Review the username, '
                'employee ID, and linked account.',
            )
            messages.error(request, 'Employee onboarding could not be completed.')
        else:
            messages.success(
                request,
                f'Employee {employee.employee_id} — {employee.full_name} onboarded successfully.',
            )
            return redirect('employees:list')

    if request.method == 'POST' and not form.is_valid():
        messages.error(request, 'Please correct the highlighted fields before saving.')

    return render(
        request,
        'employees/form.html',
        {'form': form, 'title': 'Add Employee', 'form_sections': form.sections},
    )


@hr_required
def employee_edit(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    form = EmployeeForm(request.POST or None, instance=employee)
    if request.method == 'POST' and form.is_valid():
        changed_fields = [
            form.fields[field_name].label or field_name
            for field_name in form.changed_data
        ]
        try:
            with transaction.atomic():
                employee = form.save()
                _ensure_employee_profile(employee)
                if changed_fields:
                    _record_employee_action(
                        request.user,
                        employee,
                        CHANGE,
                        f'Updated through HRMS; changed fields: {", ".join(changed_fields)}.',
                    )
        except IntegrityError:
            form.add_error(
                None,
                'The employee changes conflict with an existing account or employee ID.',
            )
            messages.error(request, 'Employee changes could not be saved.')
        else:
            messages.success(request, 'Employee record updated.')
            return redirect('employees:detail', pk=pk)

    return render(
        request,
        'employees/form.html',
        {
            'form': form,
            'title': 'Edit Employee',
            'form_sections': form.sections,
        },
    )


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
