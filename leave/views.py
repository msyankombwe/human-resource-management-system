from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from accounts.decorators import hr_required, manager_required

from .forms import LeaveDecisionForm, LeaveRequestForm, LeaveTypeForm
from .models import LeaveRequest, LeaveType


@login_required
def leave_list(request):
    profile = getattr(request.user, 'profile', None)
    qs = LeaveRequest.objects.select_related('employee', 'leave_type', 'employee__user')
    if profile and profile.role == 'EMPLOYEE':
        employee = getattr(request.user, 'employee', None)
        qs = qs.filter(employee=employee) if employee else qs.none()
    elif profile and profile.role == 'MANAGER':
        employee = getattr(request.user, 'employee', None)
        if employee:
            qs = qs.filter(Q(employee__manager=employee) | Q(employee=employee)).distinct()
    return render(request, 'leave/list.html', {'requests': qs})


@login_required
def leave_create(request):
    employee = getattr(request.user, 'employee', None)
    if not employee:
        messages.error(request, 'No employee profile linked to your account.')
        return redirect('leave:list')
    form = LeaveRequestForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        leave = form.save(commit=False)
        leave.employee = employee
        leave.save()
        messages.success(request, 'Leave request submitted.')
        return redirect('leave:list')
    return render(request, 'leave/form.html', {'form': form, 'title': 'Request Leave'})


@manager_required
def leave_decide(request, pk):
    leave = get_object_or_404(LeaveRequest, pk=pk)
    form = LeaveDecisionForm(request.POST or None, instance=leave)
    if request.method == 'POST' and form.is_valid():
        decision = form.save(commit=False)
        decision.approved_by = request.user
        decision.save()
        messages.success(request, 'Leave decision saved.')
        return redirect('leave:list')
    return render(
        request,
        'leave/decide.html',
        {'form': form, 'leave': leave, 'title': 'Approve / Reject Leave'},
    )


@hr_required
def leave_types(request):
    types = LeaveType.objects.all()
    form = LeaveTypeForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Leave type added.')
        return redirect('leave:types')
    return render(request, 'leave/types.html', {'types': types, 'form': form})
