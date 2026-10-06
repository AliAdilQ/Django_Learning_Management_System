from django.contrib import admin

from .models import Choice, Question, Quiz, QuizAnswer, QuizAttempt


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 2


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 0
    show_change_link = True


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "passing_percentage", "time_limit")
    search_fields = ("title", "course__title")
    list_filter = ("course",)
    inlines = [QuestionInline]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("text", "quiz", "marks", "order")
    search_fields = ("text", "quiz__title")
    list_filter = ("quiz",)
    inlines = [ChoiceInline]


@admin.register(Choice)
class ChoiceAdmin(admin.ModelAdmin):
    list_display = ("text", "question", "is_correct")
    search_fields = ("text", "question__text")
    list_filter = ("is_correct",)


class AnswerInline(admin.TabularInline):
    model = QuizAnswer
    extra = 0
    can_delete = False
    readonly_fields = (
        "question",
        "choice",
        "question_text",
        "choice_text",
        "is_correct",
        "awarded_marks",
    )

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(QuizAttempt)
class AttemptAdmin(admin.ModelAdmin):
    list_display = ("student", "quiz", "score", "maximum_score", "passed", "submitted_at")
    search_fields = ("student__username", "quiz__title")
    list_filter = ("quiz", "timed_out")
    readonly_fields = (
        "started_at",
        "submitted_at",
        "score",
        "maximum_score",
        "passing_percentage",
        "time_limit",
        "timed_out",
    )
    date_hierarchy = "started_at"
    inlines = [AnswerInline]


@admin.register(QuizAnswer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ("attempt", "question_text", "is_correct", "awarded_marks")
    search_fields = ("question_text", "attempt__student__username")
    list_filter = ("is_correct",)
    readonly_fields = (
        "attempt",
        "question",
        "choice",
        "question_text",
        "choice_text",
        "is_correct",
        "awarded_marks",
    )
