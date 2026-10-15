from django import forms

from .models import Applicant, Interview, JobPosting


class JobPostingForm(forms.ModelForm):
    class Meta:
        model = JobPosting
        fields = [
            'title',
            'department',
            'description',
            'requirements',
            'status',
            'closing_date',
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'requirements': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'closing_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


class ApplicantForm(forms.ModelForm):
    class Meta:
        model = Applicant
        fields = ['job', 'full_name', 'email', 'phone', 'resume_summary', 'status']
        widgets = {
            'job': forms.Select(attrs={'class': 'form-select'}),
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'resume_summary': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }


class InterviewForm(forms.ModelForm):
    class Meta:
        model = Interview
        fields = ['applicant', 'scheduled_at', 'interviewer', 'location', 'notes', 'result']
        widgets = {
            'applicant': forms.Select(attrs={'class': 'form-select'}),
            'scheduled_at': forms.DateTimeInput(
                attrs={'class': 'form-control', 'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M',
            ),
            'interviewer': forms.Select(attrs={'class': 'form-select'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'result': forms.Select(attrs={'class': 'form-select'}),
        }
