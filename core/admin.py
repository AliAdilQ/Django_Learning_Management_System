from django.contrib import admin

from .models import ContactMessage


@admin.register(ContactMessage)
class ContactAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "created_at", "is_read")
    list_filter = ("is_read",)
    search_fields = ("name", "email", "message")
    readonly_fields = ("created_at",)
    date_hierarchy = "created_at"
