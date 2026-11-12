from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from attendance.models import AttendanceRecord
from leave.models import LeaveRequest
from recruitment.models import Applicant, JobPosting
from training.models import TrainingCourse, TrainingEnrollment

from .access import visible_employees
from .forms import LoginForm
from .models import UserProfile


def login_view(request):
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')
    form = LoginForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        login(request, form.get_user())
        messages.success(request, f'Welcome back, {request.user.get_full_name() or request.user.username}!')
        return redirect('accounts:dashboard')
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('accounts:login')


@login_required
def dashboard(request):
    profile = getattr(request.user, 'profile', None)
    role = profile.role if profile else UserProfile.Role.EMPLOYEE
    employees = visible_employees(request.user)
    leaves = LeaveRequest.objects.filter(status='PENDING')
    if role not in {UserProfile.Role.ADMIN, UserProfile.Role.HR}:
        leaves = leaves.filter(employee__in=employees)
    context = {
        'role': role,
        'employee_count': employees.exclude(status='SEPARATED').count(),
        'open_jobs': JobPosting.objects.filter(status='OPEN').count(),
        'pending_leaves': leaves.count(),
        'applicants': Applicant.objects.count()
        if role in {UserProfile.Role.ADMIN, UserProfile.Role.HR} else None,
        'show_applicant_count': role in {UserProfile.Role.ADMIN, UserProfile.Role.HR},
        'today_attendance': AttendanceRecord.objects.filter(
            employee__in=employees,
        ).order_by('-date')[:5],
        'upcoming_trainings': TrainingCourse.objects.filter(status='UPCOMING')[:5],
    }

    employee = getattr(request.user, 'employee', None)
    if employee:
        if role == UserProfile.Role.MANAGER:
            context['employee_count'] = employees.exclude(pk=employee.pk).exclude(
                status='SEPARATED',
            ).count()
            context['direct_report_count'] = employee.direct_reports.count()
        elif role == UserProfile.Role.EMPLOYEE:
            context['my_training_count'] = TrainingEnrollment.objects.filter(
                employee=employee,
            ).count()
        context['my_pending_leaves'] = LeaveRequest.objects.filter(
            employee=employee, status='PENDING'
        ).count()
        context['my_attendance'] = AttendanceRecord.objects.filter(employee=employee)[:5]
        context['employee'] = employee

    return render(request, 'accounts/dashboard.html', context)
