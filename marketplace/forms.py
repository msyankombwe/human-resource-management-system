from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

from .models import BuyerOffer, Listing, MarketplaceProfile

User = get_user_model()


class MarketplaceLoginForm(forms.Form):
    username = forms.CharField(
        label='Email address',
        widget=forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'username'}),
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'current-password'}),
    )


class MarketplaceSignupForm(UserCreationForm):
    first_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    role = forms.ChoiceField(
        choices=MarketplaceProfile.Role.choices,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    phone = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    organization = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    location = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ('username', 'password1', 'password2'):
            self.fields[name].widget.attrs['class'] = 'form-control'

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            MarketplaceProfile.objects.create(
                user=user,
                role=self.cleaned_data['role'],
                phone=self.cleaned_data['phone'],
                organization=self.cleaned_data['organization'],
                location=self.cleaned_data['location'],
            )
        return user


class ListingForm(forms.ModelForm):
    class Meta:
        model = Listing
        fields = [
            'crop', 'description', 'quantity_tonnes', 'price_per_tonne',
            'location', 'quality',
        ]
        widgets = {
            'crop': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Maize'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'quantity_tonnes': forms.NumberInput(attrs={'class': 'form-control', 'min': '0.01', 'step': '0.01'}),
            'price_per_tonne': forms.NumberInput(attrs={'class': 'form-control', 'min': '0.01', 'step': '0.01'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Mkushi'}),
            'quality': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Grade, moisture, packaging'}),
        }


class BuyerOfferForm(forms.ModelForm):
    class Meta:
        model = BuyerOffer
        fields = ['quantity_tonnes', 'price_per_tonne', 'message']
        widgets = {
            'quantity_tonnes': forms.NumberInput(attrs={'class': 'form-control', 'min': '0.01', 'step': '0.01'}),
            'price_per_tonne': forms.NumberInput(attrs={'class': 'form-control', 'min': '0.01', 'step': '0.01'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, listing, buyer, **kwargs):
        self.listing = listing
        self.buyer = buyer
        super().__init__(*args, **kwargs)

    def clean_quantity_tonnes(self):
        quantity = self.cleaned_data['quantity_tonnes']
        if quantity > self.listing.quantity_tonnes:
            raise forms.ValidationError('Offer quantity cannot exceed the available quantity.')
        return quantity

    def clean(self):
        cleaned_data = super().clean()
        if self.listing.seller_id == self.buyer.pk:
            raise forms.ValidationError('You cannot make an offer on your own listing.')
        if not self.listing.is_available:
            raise forms.ValidationError('This listing is no longer available.')
        return cleaned_data
