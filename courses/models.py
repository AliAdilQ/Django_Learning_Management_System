from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Avg, Count
from django.urls import reverse


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    icon = models.CharField(max_length=40, default="code-slash")

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name


class CourseQuerySet(models.QuerySet):
    def published(self):
        return self.filter(is_published=True)

    def with_stats(self):
        return self.select_related("instructor", "category").annotate(
            lesson_count=Count(
                "modules__lessons",
                filter=models.Q(modules__lessons__is_published=True),
                distinct=True,
            ),
            student_count=Count("enrollments", distinct=True),
            average_rating=Avg("reviews__rating"),
        )


class Course(models.Model):
    class Difficulty(models.TextChoices):
        BEGINNER = "beginner", "Beginner"
        INTERMEDIATE = "intermediate", "Intermediate"
        ADVANCED = "advanced", "Advanced"

    title = models.CharField(max_length=160)
    slug = models.SlugField(unique=True, max_length=180)
    instructor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="courses",
        limit_choices_to={"role": "instructor"},
    )
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="courses")
    short_description = models.CharField(max_length=240)
    description = models.TextField()
    thumbnail = models.ImageField(upload_to="courses/%Y/%m/", blank=True)
    artwork = models.CharField(max_length=40, default="python")
    difficulty = models.CharField(
        max_length=20, choices=Difficulty.choices, default=Difficulty.BEGINNER
    )
    duration = models.PositiveIntegerField(default=6, help_text="Estimated learning time in hours.")
    is_published = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = CourseQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("courses:detail", args=[self.slug])


class Module(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="modules")
    title = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["order", "pk"]

    def __str__(self):
        return self.title


class Lesson(models.Model):
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name="lessons")
    title = models.CharField(max_length=160)
    content = models.TextField(help_text="Plain text; separate paragraphs with a blank line.")
    order = models.PositiveIntegerField(default=1)
    video_url = models.URLField(
        blank=True, help_text="Optional HTTPS link to an educational video."
    )
    duration = models.PositiveIntegerField(default=15, help_text="Minutes")
    is_published = models.BooleanField(default=True)

    class Meta:
        ordering = ["module__order", "order", "pk"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("courses:lesson", args=[self.module.course.slug, self.pk])


class Enrollment(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="enrollments",
        limit_choices_to={"role": "student"},
    )
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="enrollments")
    enrolled_at = models.DateTimeField(auto_now_add=True)
    last_accessed = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["student", "course"], name="unique_enrollment")
        ]
        ordering = ["-last_accessed"]

    def __str__(self):
        return f"{self.student} · {self.course}"

    @property
    def progress(self):
        total = self.course.modules.filter(lessons__is_published=True).aggregate(
            total=Count("lessons")
        )["total"]
        done = LessonProgress.objects.filter(
            student=self.student, lesson__module__course=self.course, lesson__is_published=True
        ).count()
        return round(done / total * 100) if total else 0


class LessonProgress(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="lesson_progress"
    )
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="progress_records")
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "lesson progress"
        verbose_name_plural = "lesson progress"
        constraints = [
            models.UniqueConstraint(fields=["student", "lesson"], name="unique_lesson_progress")
        ]

    def __str__(self):
        return f"{self.student} · {self.lesson}"


class Announcement(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="announcements")
    title = models.CharField(max_length=160)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class Review(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="reviews")
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviews"
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    text = models.TextField(max_length=1500)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["student", "course"], name="unique_course_review"),
            models.CheckConstraint(
                condition=models.Q(rating__gte=1, rating__lte=5), name="review_rating_range"
            ),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.course} · {self.rating}/5"
