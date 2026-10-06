from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Profile, User


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    extra = 0
    readonly_fields = ("updated_at",)


@admin.register(User)
class LearningUserAdmin(UserAdmin):
    list_display = ("username", "email", "first_name", "last_name", "role", "is_staff", "is_active")
    list_filter = UserAdmin.list_filter + ("role",)
    fieldsets = UserAdmin.fieldsets + (("Learning role", {"fields": ("role",)}),)
    add_fieldsets = UserAdmin.add_fieldsets + (("Learning role", {"fields": ("role", "email")}),)
    inlines = [ProfileInline]


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "headline", "updated_at")
    search_fields = ("user__username", "user__email", "headline")
    readonly_fields = ("updated_at",)
