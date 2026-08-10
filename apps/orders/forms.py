from django import forms
from apps.orders.services.cities import fetch_pakistan_cities


class CheckoutForm(forms.Form):
    PAYMENT_CHOICES = [
        ('cod', 'Cash on Delivery'),
        ('stripe', 'Debit / Credit Card'),
    ]

    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'your@email.com'
        })
    )
    first_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'First Name'
        })
    )
    last_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Last Name'
        })
    )
    phone = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': '+92 300 0000000'
        })
    )
    address = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Street Address, Apartment, Suite'
        })
    )
    city = forms.ChoiceField(
        choices=[],
        widget=forms.Select(attrs={'class': 'form-input'})
    )
    postal_code = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Postal Code (Optional)'
        })
    )
    payment_method = forms.ChoiceField(
        choices=PAYMENT_CHOICES,
        initial='cod',
        widget=forms.RadioSelect(attrs={'class': 'payment-radio'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        cities = fetch_pakistan_cities()
        self.fields['city'].choices = [('', 'Select City')] + [(c, c) for c in cities]