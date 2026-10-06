from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        STUDENT = "student", "Student"
        INSTRUCTOR = "instructor", "Instructor"
        ADMIN = "admin", "Administrator"

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.STUDENT)

    @property
    def display_name(self):
        return self.get_full_name() or self.username

    @property
    def initials(self):
        parts = self.display_name.split()
        return "".join(part[0] for part in parts[:2]).upper()

    @property
    def is_instructor(self):
        return self.role == self.Role.INSTRUCTOR


class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile"
    )
    bio = models.TextField(blank=True, max_length=1200)
    headline = models.CharField(max_length=120, blank=True)
    avatar = models.ImageField(upload_to="avatars/%Y/%m/", blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.display_name
