from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm, UserCreationForm

from core.forms import StyledFormMixin, validate_image

from .models import Profile, User


class RegistrationForm(StyledFormMixin, UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("first_name", "last_name", "username", "email", "password1", "password2")

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account already uses this email address.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Role.STUDENT
        if commit:
            user.save()
        return user


class LoginForm(StyledFormMixin, AuthenticationForm):
    pass


class ChangePasswordForm(StyledFormMixin, PasswordChangeForm):
    pass


class UserUpdateForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "email")

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.exclude(pk=self.instance.pk).filter(email__iexact=email).exists():
            raise forms.ValidationError("An account already uses this email address.")
        return email


class ProfileForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Profile
        fields = ("headline", "bio", "avatar")

    def clean_avatar(self):
        avatar = self.cleaned_data.get("avatar")
        if avatar and hasattr(avatar, "content_type"):
            validate_image(avatar)
        return avatar
