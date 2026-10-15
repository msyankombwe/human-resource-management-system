from django import forms

from .models import TrainingCourse, TrainingEnrollment


class TrainingCourseForm(forms.ModelForm):
    class Meta:
        model = TrainingCourse
        fields = [
            'title',
            'description',
            'trainer',
            'start_date',
            'end_date',
            'capacity',
            'status',
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'trainer': forms.TextInput(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'capacity': forms.NumberInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }


class TrainingEnrollmentForm(forms.ModelForm):
    class Meta:
        model = TrainingEnrollment
        fields = ['course', 'employee', 'status', 'completion_date', 'score']
        widgets = {
            'course': forms.Select(attrs={'class': 'form-select'}),
            'employee': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'completion_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'score': forms.NumberInput(attrs={'class': 'form-control'}),
        }
