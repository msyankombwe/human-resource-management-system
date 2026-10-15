from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

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
    if profile and profile.role == 'EMPLOYEE':
        employee = getattr(request.user, 'employee', None)
        reviews = reviews.filter(employee=employee) if employee else reviews.none()
    return render(request, 'performance/reviews.html', {'reviews': reviews})


@manager_required
def review_create(request):
    form = PerformanceReviewForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Performance review saved.')
        return redirect('performance:reviews')
    return render(request, 'performance/form.html', {'form': form, 'title': 'New Performance Review'})


@manager_required
def review_edit(request, pk):
    review = get_object_or_404(PerformanceReview, pk=pk)
    form = PerformanceReviewForm(request.POST or None, instance=review)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Performance review updated.')
        return redirect('performance:reviews')
    return render(request, 'performance/form.html', {'form': form, 'title': 'Edit Performance Review'})
