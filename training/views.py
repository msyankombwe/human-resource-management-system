from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from accounts.decorators import hr_required

from .forms import TrainingCourseForm, TrainingEnrollmentForm
from .models import TrainingCourse, TrainingEnrollment


@login_required
def course_list(request):
    courses = TrainingCourse.objects.all()
    return render(request, 'training/courses.html', {'courses': courses})


@hr_required
def course_create(request):
    form = TrainingCourseForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Training course created.')
        return redirect('training:courses')
    return render(request, 'training/form.html', {'form': form, 'title': 'New Training Course'})


@hr_required
def course_edit(request, pk):
    course = get_object_or_404(TrainingCourse, pk=pk)
    form = TrainingCourseForm(request.POST or None, instance=course)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Training course updated.')
        return redirect('training:courses')
    return render(request, 'training/form.html', {'form': form, 'title': 'Edit Training Course'})


@login_required
def enrollment_list(request):
    profile = getattr(request.user, 'profile', None)
    enrollments = TrainingEnrollment.objects.select_related(
        'course', 'employee', 'employee__user'
    )
    if profile and profile.role == 'EMPLOYEE':
        employee = getattr(request.user, 'employee', None)
        enrollments = enrollments.filter(employee=employee) if employee else enrollments.none()
    return render(request, 'training/enrollments.html', {'enrollments': enrollments})


@hr_required
def enrollment_create(request):
    form = TrainingEnrollmentForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Employee enrolled in training.')
        return redirect('training:enrollments')
    return render(request, 'training/form.html', {'form': form, 'title': 'Enroll Employee'})


@login_required
def self_enroll(request, pk):
    course = get_object_or_404(TrainingCourse, pk=pk)
    employee = getattr(request.user, 'employee', None)
    if not employee:
        messages.error(request, 'No employee profile linked to your account.')
        return redirect('training:courses')
    if course.seats_taken >= course.capacity:
        messages.error(request, 'This course is full.')
        return redirect('training:courses')
    _, created = TrainingEnrollment.objects.get_or_create(
        course=course,
        employee=employee,
        defaults={'status': TrainingEnrollment.Status.ENROLLED},
    )
    if created:
        messages.success(request, f'Enrolled in {course.title}.')
    else:
        messages.info(request, 'You are already enrolled in this course.')
    return redirect('training:enrollments')
