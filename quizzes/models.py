from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

from courses.models import Course


class Quiz(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="quizzes")
    title = models.CharField(max_length=160)
    description = models.TextField()
    passing_percentage = models.PositiveSmallIntegerField(
        default=70, validators=[MaxValueValidator(100)]
    )
    time_limit = models.PositiveIntegerField(default=0, help_text="Minutes; 0 for an untimed quiz.")

    class Meta:
        ordering = ["pk"]
        verbose_name_plural = "quizzes"

    def __str__(self):
        return self.title


class Question(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="questions")
    text = models.TextField()
    marks = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["order", "pk"]

    def __str__(self):
        return self.text[:80]


class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="choices")
    text = models.CharField(max_length=300)
    is_correct = models.BooleanField(default=False)

    class Meta:
        ordering = ["pk"]

    def __str__(self):
        return self.text


class QuizAttempt(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="attempts")
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="quiz_attempts"
    )
    started_at = models.DateTimeField(default=timezone.now)
    submitted_at = models.DateTimeField(null=True, blank=True)
    score = models.PositiveIntegerField(default=0)
    maximum_score = models.PositiveIntegerField(default=0)
    passing_percentage = models.PositiveSmallIntegerField(default=70)
    time_limit = models.PositiveIntegerField(default=0)
    timed_out = models.BooleanField(default=False)

    class Meta:
        ordering = ["-started_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["student", "quiz"],
                condition=models.Q(submitted_at__isnull=True),
                name="one_active_quiz_attempt",
            )
        ]

    @property
    def percentage(self):
        return round(self.score / self.maximum_score * 100, 1) if self.maximum_score else 0

    @property
    def passed(self):
        return (
            bool(self.submitted_at)
            and not self.timed_out
            and self.maximum_score > 0
            and self.score * 100 >= self.maximum_score * self.passing_percentage
        )

    def __str__(self):
        return f"{self.student} · {self.quiz} · {self.percentage}%"


class QuizAnswer(models.Model):
    attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE, related_name="answers")
    question = models.ForeignKey(Question, on_delete=models.SET_NULL, null=True)
    choice = models.ForeignKey(Choice, on_delete=models.SET_NULL, null=True)
    question_text = models.TextField()
    choice_text = models.CharField(max_length=300)
    is_correct = models.BooleanField(default=False)
    awarded_marks = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["attempt", "question"], name="unique_quiz_answer")
        ]
