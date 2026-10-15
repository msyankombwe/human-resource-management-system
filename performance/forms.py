from django import forms

from .models import AppraisalCycle, PerformanceReview


class AppraisalCycleForm(forms.ModelForm):
    class Meta:
        model = AppraisalCycle
        fields = ['name', 'start_date', 'end_date', 'status']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }


class PerformanceReviewForm(forms.ModelForm):
    class Meta:
        model = PerformanceReview
        fields = [
            'employee',
            'cycle',
            'reviewer',
            'goals',
            'achievements',
            'rating',
            'comments',
            'status',
        ]
        widgets = {
            'employee': forms.Select(attrs={'class': 'form-select'}),
            'cycle': forms.Select(attrs={'class': 'form-select'}),
            'reviewer': forms.Select(attrs={'class': 'form-select'}),
            'goals': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'achievements': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'rating': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 5}),
            'comments': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }
