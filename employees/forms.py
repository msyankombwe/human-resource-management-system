from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.exceptions import ValidationError
from django.db.models import Q

from accounts.models import UserProfile
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
    field_sections = (
        ('Employee account', ('user',)),
        ('Personal and contact information', (
            'date_of_birth',
            'phone',
            'address',
            'emergency_contact',
        )),
        ('Employment information', (
            'employee_id',
            'department',
            'job_title',
            'hire_date',
            'status',
            'manager',
            'base_salary',
            'notes',
        )),
    )
    field_modes = {}

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
        labels = {'base_salary': 'Base salary (ZMW)'}
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

    @property
    def sections(self):
        return [
            {
                'title': title,
                'fields': [
                    {'field': self[name], 'mode': self.field_modes.get(name)}
                    for name in names
                    if name in self.fields
                ],
            }
            for title, names in self.field_sections
        ]


class EmployeeOnboardingForm(EmployeeForm):
    account_mode = forms.ChoiceField(
        choices=(
            ('new', 'Create a new account'),
            ('existing', 'Link an existing account'),
        ),
        initial='new',
        label='Account option',
        help_text='New accounts receive the Employee role automatically.',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    username = forms.CharField(
        max_length=150,
        required=False,
        validators=[UnicodeUsernameValidator()],
        widget=forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'username'}),
    )
    first_name = forms.CharField(
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'given-name'}),
    )
    last_name = forms.CharField(
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'family-name'}),
    )
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'autocomplete': 'email'}),
    )
    password1 = forms.CharField(
        required=False,
        label='Password',
        strip=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'new-password'}),
    )
    password2 = forms.CharField(
        required=False,
        label='Confirm password',
        strip=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'new-password'}),
    )

    field_sections = (
        ('System account', (
            'account_mode',
            'user',
            'username',
            'first_name',
            'last_name',
            'email',
            'password1',
            'password2',
        )),
        ('Employment information', (
            'employee_id',
            'department',
            'job_title',
            'hire_date',
            'status',
            'manager',
            'base_salary',
        )),
        ('Personal and contact information', (
            'date_of_birth',
            'phone',
            'address',
            'emergency_contact',
            'notes',
        )),
    )
    field_modes = {
        'user': 'existing',
        'username': 'new',
        'first_name': 'new',
        'last_name': 'new',
        'email': 'new',
        'password1': 'new',
        'password2': 'new',
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.is_bound and 'account_mode' not in self.data and self.data.get('user'):
            self.data = self.data.copy()
            self.data['account_mode'] = 'existing'

        User = get_user_model()
        self.fields['user'].required = False
        self.fields['user'].label = 'Existing account'
        self.fields['user'].help_text = (
            'Only unlinked, non-administrative accounts can be selected.'
        )
        self.fields['user'].queryset = (
            User.objects.filter(
                employee__isnull=True,
                is_staff=False,
                is_superuser=False,
            )
            .filter(
                Q(profile__isnull=True)
                | Q(profile__role=UserProfile.Role.EMPLOYEE)
            )
            .order_by('username')
        )

    def clean(self):
        cleaned_data = super().clean()
        account_mode = cleaned_data.get('account_mode')

        if account_mode == 'existing':
            if not cleaned_data.get('user'):
                self.add_error('user', 'Select an unlinked employee account.')
            return cleaned_data

        if account_mode != 'new':
            return cleaned_data

        required_fields = (
            'username',
            'first_name',
            'last_name',
            'email',
            'password1',
            'password2',
        )
        for field_name in required_fields:
            if not cleaned_data.get(field_name):
                self.add_error(field_name, 'This field is required for a new account.')

        username = cleaned_data.get('username')
        User = get_user_model()
        if username and User._default_manager.filter(username__iexact=username).exists():
            self.add_error('username', 'An account with this username already exists.')

        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            self.add_error('password2', 'The two password fields did not match.')
        elif password1 and username:
            candidate = User(
                username=username,
                first_name=cleaned_data.get('first_name', ''),
                last_name=cleaned_data.get('last_name', ''),
                email=cleaned_data.get('email', ''),
            )
            try:
                validate_password(password1, user=candidate)
            except ValidationError as error:
                self.add_error('password1', error)

        return cleaned_data
