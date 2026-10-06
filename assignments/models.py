import uuid
from pathlib import Path

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from courses.models import Course


def private_storage():
    return FileSystemStorage(location=settings.PRIVATE_UPLOAD_ROOT)


def submission_path(instance, filename):
    return f"submissions/{instance.student_id}/{uuid.uuid4().hex}{Path(filename).suffix.lower()}"


class Assignment(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="assignments")
    title = models.CharField(max_length=160)
    description = models.TextField()
    due_date = models.DateTimeField()
    maximum_marks = models.PositiveIntegerField(default=100, validators=[MinValueValidator(1)])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["due_date", "pk"]

    def __str__(self):
        return self.title


class Submission(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name="submissions")
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="submissions"
    )
    text = models.TextField(blank=True)
    file = models.FileField(upload_to=submission_path, storage=private_storage, blank=True)
    submitted_at = models.DateTimeField(default=timezone.now)
    marks = models.PositiveIntegerField(null=True, blank=True)
    feedback = models.TextField(blank=True)
    graded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["student", "assignment"], name="unique_assignment_submission"
            )
        ]
        ordering = ["-submitted_at"]

    @property
    def is_late(self):
        return self.submitted_at > self.assignment.due_date

    @property
    def status(self):
        if self.marks is not None:
            return "Graded"
        return "Late" if self.is_late else "Submitted"

    def clean(self):
        from django.core.exceptions import ValidationError

        if self.marks is not None and self.marks > self.assignment.maximum_marks:
            raise ValidationError({"marks": "Marks cannot exceed the assignment maximum."})

    def __str__(self):
        return f"{self.student} · {self.assignment}"
