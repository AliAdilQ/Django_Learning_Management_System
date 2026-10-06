from django import forms
from django.core.exceptions import ValidationError

from .models import ContactMessage


class StyledFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                css = "form-check-input"
            elif isinstance(field.widget, forms.Select):
                css = "form-select"
            else:
                css = "form-control"
            field.widget.attrs["class"] = css
            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs.setdefault("rows", 4)


def validate_image(upload):
    if not upload:
        return
    if upload.size > 5 * 1024 * 1024:
        raise ValidationError("Images must be 5 MB or smaller.")
    from PIL import Image

    try:
        image = Image.open(upload)
        if image.format not in {"JPEG", "PNG", "WEBP"}:
            raise ValidationError("Choose a JPEG, PNG, or WebP image.")
        if image.width * image.height > 20_000_000:
            raise ValidationError("Choose an image smaller than 20 megapixels.")
        image.verify()
    except (OSError, ValueError, Image.DecompressionBombError) as exc:
        raise ValidationError("This image could not be read.") from exc
    finally:
        upload.seek(0)


class ContactForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ("name", "email", "message")
