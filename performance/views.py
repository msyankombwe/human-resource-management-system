from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from accounts.access import visible_employees
from accounts.decorators import hr_required, manager_required

from .forms import AppraisalCycleForm, PerformanceReviewForm
from .models import AppraisalCycle, PerformanceReview


@login_required
def cycle_list(request):
    cycles = AppraisalCycle.objects.all()
    return render(request, 'performance/cycles.html', {'cycles': cycles})


@hr_required
def cycle_create(request):
    form = AppraisalCycleForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Appraisal cycle created.')
        return redirect('performance:cycles')
    return render(request, 'performance/form.html', {'form': form, 'title': 'New Appraisal Cycle'})


@login_required
def review_list(request):
    profile = getattr(request.user, 'profile', None)
    reviews = PerformanceReview.objects.select_related(
        'employee', 'cycle', 'reviewer', 'employee__user'
    )
    if not profile or profile.role not in {'ADMIN', 'HR'}:
        reviews = reviews.filter(employee__in=visible_employees(request.user))
    return render(request, 'performance/reviews.html', {'reviews': reviews})


@manager_required
def review_create(request):
    form = PerformanceReviewForm(request.POST or None)
    _limit_review_form(request, form)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Performance review saved.')
        return redirect('performance:reviews')
    return render(request, 'performance/form.html', {'form': form, 'title': 'New Performance Review'})


@manager_required
def review_edit(request, pk):
    review = get_object_or_404(
        PerformanceReview.objects.filter(employee__in=visible_employees(request.user)),
        pk=pk,
    )
    form = PerformanceReviewForm(request.POST or None, instance=review)
    _limit_review_form(request, form)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Performance review updated.')
        return redirect('performance:reviews')
    return render(request, 'performance/form.html', {'form': form, 'title': 'Edit Performance Review'})


def _limit_review_form(request, form):
    profile = getattr(request.user, 'profile', None)
    if profile and profile.role == 'MANAGER':
        employee = getattr(request.user, 'employee', None)
        if employee:
            form.fields['employee'].queryset = visible_employees(request.user).exclude(
                pk=employee.pk,
            )
            form.fields['reviewer'].queryset = visible_employees(request.user).filter(
                pk=employee.pk,
            )
        else:
            form.fields['employee'].queryset = form.fields['employee'].queryset.none()
            form.fields['reviewer'].queryset = form.fields['reviewer'].queryset.none()
