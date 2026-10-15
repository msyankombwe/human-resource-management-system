from django import forms

from .models import PayrollPeriod, Payslip


class PayrollPeriodForm(forms.ModelForm):
    class Meta:
        model = PayrollPeriod
        fields = ['month', 'year', 'status']
        widgets = {
            'month': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 12}),
            'year': forms.NumberInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }


class PayslipForm(forms.ModelForm):
    class Meta:
        model = Payslip
        fields = ['employee', 'period', 'basic_salary', 'allowances', 'deductions', 'notes']
        widgets = {
            'employee': forms.Select(attrs={'class': 'form-select'}),
            'period': forms.Select(attrs={'class': 'form-select'}),
            'basic_salary': forms.NumberInput(attrs={'class': 'form-control'}),
            'allowances': forms.NumberInput(attrs={'class': 'form-control'}),
            'deductions': forms.NumberInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
