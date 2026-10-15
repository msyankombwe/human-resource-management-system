from django import forms

from .models import LeaveRequest, LeaveType


class LeaveTypeForm(forms.ModelForm):
    class Meta:
        model = LeaveType
        fields = ['name', 'days_allowed', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'days_allowed': forms.NumberInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class LeaveRequestForm(forms.ModelForm):
    class Meta:
        model = LeaveRequest
        fields = ['leave_type', 'start_date', 'end_date', 'reason']
        widgets = {
            'leave_type': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class LeaveDecisionForm(forms.ModelForm):
    class Meta:
        model = LeaveRequest
        fields = ['status', 'decision_notes']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'decision_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
