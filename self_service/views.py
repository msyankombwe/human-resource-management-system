from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from attendance.models import AttendanceRecord
from leave.models import LeaveRequest
from payroll.models import Payslip
from performance.models import PerformanceReview
from training.models import TrainingEnrollment


@login_required
def home(request):
    employee = getattr(request.user, 'employee', None)
    if not employee:
        return render(request, 'self_service/no_profile.html')

    context = {
        'employee': employee,
        'leaves': LeaveRequest.objects.filter(employee=employee)[:5],
        'attendance': AttendanceRecord.objects.filter(employee=employee)[:7],
        'payslips': Payslip.objects.filter(employee=employee)[:5],
        'reviews': PerformanceReview.objects.filter(employee=employee)[:5],
        'trainings': TrainingEnrollment.objects.filter(employee=employee).select_related('course')[:5],
    }
    return render(request, 'self_service/home.html', context)


@login_required
def my_profile(request):
    employee = getattr(request.user, 'employee', None)
    if not employee:
        return render(request, 'self_service/no_profile.html')
    return redirect('employees:detail', pk=employee.pk)
