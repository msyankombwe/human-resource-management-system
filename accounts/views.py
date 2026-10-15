from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from attendance.models import AttendanceRecord
from employees.models import Employee
from leave.models import LeaveRequest
from recruitment.models import Applicant, JobPosting
from training.models import TrainingCourse

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
    context = {
        'role': role,
        'employee_count': Employee.objects.exclude(status='SEPARATED').count(),
        'open_jobs': JobPosting.objects.filter(status='OPEN').count(),
        'pending_leaves': LeaveRequest.objects.filter(status='PENDING').count(),
        'applicants': Applicant.objects.count(),
        'today_attendance': AttendanceRecord.objects.filter(
            date__isnull=False,
        ).order_by('-date')[:5],
        'upcoming_trainings': TrainingCourse.objects.filter(status='UPCOMING')[:5],
    }

    employee = getattr(request.user, 'employee', None)
    if employee:
        context['my_pending_leaves'] = LeaveRequest.objects.filter(
            employee=employee, status='PENDING'
        ).count()
        context['my_attendance'] = AttendanceRecord.objects.filter(employee=employee)[:5]
        context['employee'] = employee

    return render(request, 'accounts/dashboard.html', context)
