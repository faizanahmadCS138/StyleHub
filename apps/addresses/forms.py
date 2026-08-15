from django import forms
from .models import Address


class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ['full_name', 'phone_number', 'street_address', 'apartment', 'city', 'latitude', 'longitude']

    def clean_phone_number(self):
        phone = self.cleaned_data['phone_number'].strip()
        if len(phone) < 10:
            raise forms.ValidationError("Enter a valid phone number.")
        return phone

    def clean_full_name(self):
        name = self.cleaned_data['full_name'].strip()
        if len(name) < 3:
            raise forms.ValidationError("Full name is too short.")
        return name

    def clean_street_address(self):
        addr = self.cleaned_data['street_address'].strip()
        if len(addr) < 5:
            raise forms.ValidationError("Street address is too short.")
        return addr