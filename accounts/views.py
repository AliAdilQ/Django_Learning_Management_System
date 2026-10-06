from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView
from django.shortcuts import redirect, render
from django.urls import reverse_lazy

from .forms import ChangePasswordForm, LoginForm, ProfileForm, RegistrationForm, UserUpdateForm


class SignInView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True

    def form_valid(self, form):
        messages.success(self.request, "Welcome back. Your next chapter starts here.")
        return super().form_valid(form)


class SignOutView(LogoutView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        messages.success(request, "You have been signed out.")
        return response


class ChangePasswordView(PasswordChangeView):
    form_class = ChangePasswordForm
    template_name = "core/form.html"
    success_url = reverse_lazy("accounts:profile")
    extra_context = {
        "title": "Change password",
        "eyebrow": "ACCOUNT SECURITY",
        "button": "Update password",
    }

    def form_valid(self, form):
        messages.success(self.request, "Your password was updated.")
        return super().form_valid(form)


def register(request):
    if request.user.is_authenticated:
        return redirect("core:dashboard")
    form = RegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(
            request, "Your learning account is ready. Find something that inspires you."
        )
        return redirect("core:dashboard")
    return render(request, "accounts/register.html", {"form": form})


@login_required
def profile(request):
    return render(request, "accounts/profile.html")


@login_required
def edit_profile(request):
    user_form = UserUpdateForm(request.POST or None, instance=request.user)
    profile_form = ProfileForm(
        request.POST or None, request.FILES or None, instance=request.user.profile
    )
    if request.method == "POST" and user_form.is_valid() and profile_form.is_valid():
        user_form.save()
        profile_form.save()
        messages.success(request, "Your profile has been updated.")
        return redirect("accounts:profile")
    return render(
        request,
        "accounts/edit_profile.html",
        {"user_form": user_form, "profile_form": profile_form},
    )
