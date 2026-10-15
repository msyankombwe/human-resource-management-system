from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User

from .models import UserProfile


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}),
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}),
    )


class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    first_name = forms.CharField(required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    role = forms.ChoiceField(
        choices=UserProfile.Role.choices,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2', 'role']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ['username', 'password1', 'password2']:
            self.fields[name].widget.attrs['class'] = 'form-control'
