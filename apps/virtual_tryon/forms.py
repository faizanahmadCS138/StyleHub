import os
from django import forms
from PIL import Image, UnidentifiedImageError

MAX_UPLOAD_SIZE = 8 * 1024 * 1024  # 8 MB
ALLOWED_CONTENT_TYPES = {'image/jpeg', 'image/jpg', 'image/png'}
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png'}


class TryOnUploadForm(forms.Form):
    """
    Validates the incoming Virtual Try-On request.
    Deliberately a plain Form, not a ModelForm — no VirtualTryOn model exists.
    """
    product_id = forms.IntegerField(min_value=1)
    user_image = forms.ImageField()

    def clean_user_image(self):
        image = self.cleaned_data['user_image']

        if image.size > MAX_UPLOAD_SIZE:
            raise forms.ValidationError("The uploaded image is too large. Max size is 8MB.")

        if image.content_type not in ALLOWED_CONTENT_TYPES:
            raise forms.ValidationError("Please upload a JPG, JPEG, or PNG image.")

        ext = os.path.splitext(image.name)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise forms.ValidationError("Please upload a JPG, JPEG, or PNG image.")

        # Confirm it's actually a valid, openable image (not a renamed file)
        try:
            image.seek(0)
            img = Image.open(image)
            img.verify()
        except (UnidentifiedImageError, OSError):
            raise forms.ValidationError("The uploaded file is not a valid image.")
        finally:
            image.seek(0)

        return image