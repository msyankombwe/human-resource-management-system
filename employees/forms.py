from django import forms

from .models import Department, Employee


class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = [
            'user',
            'employee_id',
            'department',
            'job_title',
            'hire_date',
            'date_of_birth',
            'phone',
            'address',
            'emergency_contact',
            'base_salary',
            'status',
            'manager',
            'notes',
        ]
        widgets = {
            'user': forms.Select(attrs={'class': 'form-select'}),
            'employee_id': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'job_title': forms.TextInput(attrs={'class': 'form-control'}),
            'hire_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'emergency_contact': forms.TextInput(attrs={'class': 'form-control'}),
            'base_salary': forms.NumberInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'manager': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
