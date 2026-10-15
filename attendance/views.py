from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.decorators import manager_required

from .forms import AttendanceForm
from .models import AttendanceRecord


@login_required
def attendance_list(request):
    records = AttendanceRecord.objects.select_related('employee', 'employee__user')
    date_filter = request.GET.get('date')
    if date_filter:
        records = records.filter(date=date_filter)
    else:
        records = records.order_by('-date')[:50]
    return render(
        request,
        'attendance/list.html',
        {'records': records, 'date_filter': date_filter or ''},
    )


@manager_required
def attendance_create(request):
    form = AttendanceForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Attendance recorded.')
        return redirect('attendance:list')
    return render(request, 'attendance/form.html', {'form': form, 'title': 'Record Attendance'})


@manager_required
def attendance_edit(request, pk):
    record = get_object_or_404(AttendanceRecord, pk=pk)
    form = AttendanceForm(request.POST or None, instance=record)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Attendance updated.')
        return redirect('attendance:list')
    return render(request, 'attendance/form.html', {'form': form, 'title': 'Edit Attendance'})


@login_required
def clock_in(request):
    employee = getattr(request.user, 'employee', None)
    if not employee:
        messages.error(request, 'No employee profile linked to your account.')
        return redirect('accounts:dashboard')
    today = timezone.localdate()
    record, created = AttendanceRecord.objects.get_or_create(
        employee=employee,
        date=today,
        defaults={
            'check_in': timezone.localtime().time(),
            'status': AttendanceRecord.Status.PRESENT,
        },
    )
    if not created and not record.check_in:
        record.check_in = timezone.localtime().time()
        record.save()
        messages.success(request, 'Clock-in recorded.')
    elif created:
        messages.success(request, 'Clock-in recorded.')
    else:
        messages.info(request, 'You already clocked in today.')
    return redirect('self_service:home')


@login_required
def clock_out(request):
    employee = getattr(request.user, 'employee', None)
    if not employee:
        messages.error(request, 'No employee profile linked to your account.')
        return redirect('accounts:dashboard')
    today = timezone.localdate()
    try:
        record = AttendanceRecord.objects.get(employee=employee, date=today)
    except AttendanceRecord.DoesNotExist:
        messages.error(request, 'Clock in first before clocking out.')
        return redirect('self_service:home')
    record.check_out = timezone.localtime().time()
    record.save()
    messages.success(request, 'Clock-out recorded.')
    return redirect('self_service:home')
