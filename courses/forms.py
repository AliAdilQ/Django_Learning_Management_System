from django import forms
from django.core.exceptions import ValidationError

from core.forms import StyledFormMixin, validate_image

from .models import Announcement, Course, Lesson, Module, Review


class CourseForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Course
        fields = (
            "title",
            "slug",
            "category",
            "short_description",
            "description",
            "thumbnail",
            "difficulty",
            "duration",
            "is_published",
            "is_featured",
        )

    def clean_thumbnail(self):
        image = self.cleaned_data.get("thumbnail")
        if image and hasattr(image, "content_type"):
            validate_image(image)
        return image


class ModuleForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Module
        fields = ("title", "description", "order")


class LessonForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ("module", "title", "content", "order", "video_url", "duration", "is_published")

    def __init__(self, *args, course, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["module"].queryset = course.modules.all()

    def clean_video_url(self):
        url = self.cleaned_data["video_url"]
        if url and not url.startswith("https://"):
            raise ValidationError("Use an HTTPS video link.")
        return url


class AnnouncementForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ("title", "content")


class ReviewForm(StyledFormMixin, forms.ModelForm):
    rating = forms.TypedChoiceField(
        choices=[(i, f"{i} stars") for i in range(5, 0, -1)], coerce=int
    )

    class Meta:
        model = Review
        fields = ("rating", "text")
