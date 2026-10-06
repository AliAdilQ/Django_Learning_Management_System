from django.contrib import admin

from .models import Assignment, Submission


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "due_date", "maximum_marks")
    list_filter = ("course", "due_date")
    search_fields = ("title", "description")
    readonly_fields = ("created_at",)
    date_hierarchy = "due_date"


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ("student", "assignment", "submitted_at", "marks", "status")
    list_filter = ("assignment__course", "graded_at")
    search_fields = ("student__username", "assignment__title", "text")
    readonly_fields = ("submitted_at",)
    date_hierarchy = "submitted_at"
