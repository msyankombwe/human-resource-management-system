from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from accounts.decorators import hr_required

from .forms import ApplicantForm, InterviewForm, JobPostingForm
from .models import Applicant, Interview, JobPosting


@login_required
def job_list(request):
    jobs = JobPosting.objects.select_related('department')
    return render(request, 'recruitment/job_list.html', {'jobs': jobs})


@hr_required
def job_create(request):
    form = JobPostingForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        job = form.save(commit=False)
        job.created_by = request.user
        job.save()
        messages.success(request, 'Job posting created.')
        return redirect('recruitment:jobs')
    return render(request, 'recruitment/form.html', {'form': form, 'title': 'New Job Posting'})


@hr_required
def job_edit(request, pk):
    job = get_object_or_404(JobPosting, pk=pk)
    form = JobPostingForm(request.POST or None, instance=job)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Job posting updated.')
        return redirect('recruitment:jobs')
    return render(request, 'recruitment/form.html', {'form': form, 'title': 'Edit Job Posting'})


@login_required
def applicant_list(request):
    applicants = Applicant.objects.select_related('job')
    return render(request, 'recruitment/applicant_list.html', {'applicants': applicants})


@hr_required
def applicant_create(request):
    form = ApplicantForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Applicant recorded.')
        return redirect('recruitment:applicants')
    return render(request, 'recruitment/form.html', {'form': form, 'title': 'Add Applicant'})


@hr_required
def applicant_edit(request, pk):
    applicant = get_object_or_404(Applicant, pk=pk)
    form = ApplicantForm(request.POST or None, instance=applicant)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Applicant updated.')
        return redirect('recruitment:applicants')
    return render(request, 'recruitment/form.html', {'form': form, 'title': 'Edit Applicant'})


@login_required
def interview_list(request):
    interviews = Interview.objects.select_related('applicant', 'interviewer')
    return render(request, 'recruitment/interview_list.html', {'interviews': interviews})


@hr_required
def interview_create(request):
    form = InterviewForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Interview scheduled.')
        return redirect('recruitment:interviews')
    return render(request, 'recruitment/form.html', {'form': form, 'title': 'Schedule Interview'})
