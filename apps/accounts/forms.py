from django import forms
from django.contrib.auth.forms import AuthenticationForm

from .models import Address, CustomUser


# ─────────────────────────────────────────────────────────────
# Login Form
# ─────────────────────────────────────────────────────────────

class LoginForm(AuthenticationForm):
    """
    Extends Django's AuthenticationForm to provide field-specific validation errors:
    - Email not registered -> Error under Email field
    - Password incorrect -> Error under Password field
    """
    username = forms.EmailField(
        label='Email Address',
        widget=forms.EmailInput(attrs={
            'class'      : 'form-input',
            'placeholder': 'your@email.com',
            'autofocus'  : True,
        })
    )
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class'      : 'form-input',
            'placeholder': 'Enter your password',
        })
    )

    def clean(self):
        email = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if email:
            user_qs = CustomUser.objects.filter(email__iexact=email)
            if not user_qs.exists():
                self.add_error('username', 'This email is not registered.')
                return self.cleaned_data
            
            if password:
                user = user_qs.first()
                if not user.check_password(password):
                    self.add_error('password', 'Incorrect password.')
                    return self.cleaned_data
                if not user.is_active:
                    self.add_error('username', 'This account is disabled.')
                    return self.cleaned_data
                
                self.user_cache = user

        return self.cleaned_data


# ─────────────────────────────────────────────────────────────
# Registration Form
# ─────────────────────────────────────────────────────────────

class RegisterForm(forms.ModelForm):
    """User registration — email + name + password."""

    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class'      : 'form-input',
            'placeholder': 'Create a password',
        })
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={
            'class'      : 'form-input',
            'placeholder': 'Repeat your password',
        })
    )

    class Meta:
        model  = CustomUser
        fields = ('first_name', 'last_name', 'email', 'phone_number')
        widgets = {
            'first_name'  : forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'First name'}),
            'last_name'   : forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Last name'}),
            'email'       : forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'your@email.com'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '+92 300 0000000'}),
        }

    def clean_password2(self):
        p1 = self.cleaned_data.get('password1')
        p2 = self.cleaned_data.get('password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError('Passwords do not match.')
        return p2

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('This email is already registered.')
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user


# ─────────────────────────────────────────────────────────────
# Profile Update Form
# ─────────────────────────────────────────────────────────────

class ProfileUpdateForm(forms.ModelForm):
    """Let users update their name, phone number, and avatar."""

    class Meta:
        model  = CustomUser
        fields = ('first_name', 'last_name', 'phone_number', 'avatar')
        widgets = {
            'first_name'  : forms.TextInput(attrs={'class': 'form-input'}),
            'last_name'   : forms.TextInput(attrs={'class': 'form-input'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '+92 300 0000000'}),
            'avatar'      : forms.FileInput(attrs={'class': 'form-input-file'}),
        }


# ─────────────────────────────────────────────────────────────
# Address Form
# ─────────────────────────────────────────────────────────────

class AddressForm(forms.ModelForm):
    """Add or edit a saved address."""

    class Meta:
        model   = Address
        fields  = ('label', 'full_name', 'phone', 'street', 'city', 'province', 'postal_code', 'country', 'is_default')
        widgets = {
            'label'      : forms.Select(attrs={'class': 'form-input'}),
            'full_name'  : forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Full name'}),
            'phone'      : forms.TextInput(attrs={'class': 'form-input', 'placeholder': '+92 300 0000000'}),
            'street'     : forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Street address'}),
            'city'       : forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'City'}),
            'province'   : forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Province'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Postal code'}),
            'country'    : forms.TextInput(attrs={'class': 'form-input'}),
            'is_default' : forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }
