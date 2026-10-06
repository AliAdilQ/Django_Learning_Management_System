from django import forms
from django.forms import BaseInlineFormSet, inlineformset_factory

from core.forms import StyledFormMixin

from .models import Choice, Question, Quiz


class QuizForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Quiz
        fields = ("title", "description", "passing_percentage", "time_limit")


class QuestionForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Question
        fields = ("text", "marks", "order")


class ChoiceForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Choice
        fields = ("text", "is_correct")


class ValidChoiceFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        if any(self.errors):
            return
        choices = [
            form.cleaned_data
            for form in self.forms
            if form.cleaned_data and not form.cleaned_data.get("DELETE")
        ]
        if len(choices) < 2:
            raise forms.ValidationError("Each question needs at least two choices.")
        if sum(bool(choice.get("is_correct")) for choice in choices) != 1:
            raise forms.ValidationError("Choose exactly one correct answer.")


ChoiceFormSet = inlineformset_factory(
    Question,
    Choice,
    form=ChoiceForm,
    formset=ValidChoiceFormSet,
    extra=4,
    max_num=6,
    validate_max=True,
    can_delete=True,
)


class TakeQuizForm(forms.Form):
    def __init__(self, *args, questions, **kwargs):
        super().__init__(*args, **kwargs)
        for question in questions:
            self.fields[f"question_{question.pk}"] = forms.ChoiceField(
                label=question.text,
                choices=[(choice.pk, choice.text) for choice in question.choices.all()],
                widget=forms.RadioSelect,
                required=True,
            )
