from pathlib import Path

from django import forms

from core.forms import StyledFormMixin

from .models import Assignment, Submission


class AssignmentForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Assignment
        fields = ("title", "description", "due_date", "maximum_marks")
        widgets = {
            "due_date": forms.DateTimeInput(
                attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"
            )
        }
        help_texts = {
            "due_date": "Date and time in UTC. Late submissions are accepted and flagged."
        }


class SubmissionForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Submission
        fields = ("text", "file")
        widgets = {"file": forms.FileInput()}
        help_texts = {
            "file": "Optional PDF, TXT, or Markdown file. Maximum 5 MB. Files are private."
        }

    def clean_file(self):
        upload = self.cleaned_data.get("file")
        if not upload or not hasattr(upload, "content_type"):
            return upload
        extension = Path(upload.name).suffix.lower()
        if extension not in {".pdf", ".txt", ".md"}:
            raise forms.ValidationError("Choose a PDF, TXT, or Markdown file.")
        if upload.size > 5 * 1024 * 1024:
            raise forms.ValidationError("Files must be 5 MB or smaller.")
        data = upload.read()
        upload.seek(0)
        if extension == ".pdf" and not data.startswith(b"%PDF-"):
            raise forms.ValidationError("This file is not a valid PDF.")
        if extension != ".pdf":
            try:
                data.decode("utf-8")
                if b"\x00" in data:
                    raise ValueError
            except (UnicodeDecodeError, ValueError) as exc:
                raise forms.ValidationError("Text files must contain UTF-8 text.") from exc
        return upload

    def clean(self):
        data = super().clean()
        if not data.get("text", "").strip() and not data.get("file"):
            raise forms.ValidationError("Add submission text or attach a file.")
        return data


class GradeForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Submission
        fields = ("marks", "feedback")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["marks"].required = True
        self.fields["marks"].widget.attrs["max"] = self.instance.assignment.maximum_marks
