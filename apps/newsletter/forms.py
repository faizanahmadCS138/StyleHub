from django import forms


class NewsletterForm(forms.Form):

    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'placeholder': 'ENTER YOUR EMAIL',
            'class': 'newsletter-input',
            'autocomplete': 'email',
        })
    )