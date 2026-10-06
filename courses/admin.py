from django.contrib import admin

from .models import (
    Announcement,
    Category,
    Course,
    Enrollment,
    Lesson,
    LessonProgress,
    Module,
    Review,
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "icon")
    search_fields = ("name", "description")
    prepopulated_fields = {"slug": ("name",)}


class ModuleInline(admin.TabularInline):
    model = Module
    extra = 0
    show_change_link = True


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "instructor",
        "category",
        "difficulty",
        "is_published",
        "is_featured",
        "updated_at",
    )
    list_filter = ("is_published", "is_featured", "difficulty", "category")
    search_fields = ("title", "instructor__username")
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("created_at", "updated_at")
    date_hierarchy = "created_at"
    inlines = [ModuleInline]
    list_select_related = ("instructor", "category")


class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 0
    show_change_link = True


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "order")
    search_fields = ("title", "course__title")
    list_filter = ("course",)
    inlines = [LessonInline]


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ("title", "module", "duration", "order", "is_published")
    search_fields = ("title", "content")
    list_filter = ("is_published", "module__course")


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ("student", "course", "enrolled_at", "last_accessed")
    search_fields = ("student__username", "course__title")
    list_filter = ("course",)
    date_hierarchy = "enrolled_at"
    readonly_fields = ("enrolled_at", "last_accessed")


@admin.register(LessonProgress)
class ProgressAdmin(admin.ModelAdmin):
    list_display = ("student", "lesson", "completed_at")
    search_fields = ("student__username", "lesson__title")
    list_filter = ("lesson__module__course",)
    readonly_fields = ("completed_at",)
    date_hierarchy = "completed_at"


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "created_at")
    search_fields = ("title", "content")
    list_filter = ("course",)
    readonly_fields = ("created_at",)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("course", "student", "rating", "created_at")
    search_fields = ("text", "student__username", "course__title")
    list_filter = ("rating", "course")
    readonly_fields = ("created_at", "updated_at")
