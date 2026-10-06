"""Small, explicitly scoped CRUD editor shared by instructor content types."""

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from assignments.forms import AssignmentForm
from assignments.models import Assignment
from courses.forms import AnnouncementForm, CourseForm, LessonForm, ModuleForm
from courses.models import Announcement, Course, Lesson, Module
from courses.permissions import owned_course, role_required
from quizzes.forms import ChoiceFormSet, QuestionForm, QuizForm
from quizzes.models import Question, Quiz

RESOURCES = {
    "module": (Module, ModuleForm, "Modules"),
    "lesson": (Lesson, LessonForm, "Lessons"),
    "assignment": (Assignment, AssignmentForm, "Assignments"),
    "quiz": (Quiz, QuizForm, "Quizzes"),
    "announcement": (Announcement, AnnouncementForm, "Announcements"),
}


def resource_info(resource, course):
    if resource not in RESOURCES:
        raise Http404
    model, form, title = RESOURCES[resource]
    items = (
        model.objects.filter(module__course=course)
        if resource == "lesson"
        else model.objects.filter(course=course)
    )
    return form, title, items


@role_required("instructor")
def course_edit(request, pk=None):
    course = owned_course(request.user, pk) if pk else None
    form = CourseForm(request.POST or None, request.FILES or None, instance=course)
    if request.method == "POST" and form.is_valid():
        item = form.save(commit=False)
        item.instructor = request.user
        item.save()
        messages.success(request, "Course saved. Add a curriculum to bring it to life.")
        return redirect("core:course_manage", pk=item.pk)
    return render(
        request,
        "core/form.html",
        {
            "form": form,
            "title": "Edit course" if course else "Create a course",
            "eyebrow": "INSTRUCTOR STUDIO",
            "button": "Save course",
            "back_url": reverse("core:instructor_dashboard"),
        },
    )


@role_required("instructor")
def course_manage(request, pk):
    course = owned_course(request.user, pk)
    sections = []
    for key in RESOURCES:
        _, title, items = resource_info(key, course)
        sections.append({"key": key, "title": title, "items": items})
    return render(request, "core/course_manage.html", {"course": course, "sections": sections})


@role_required("instructor")
def resource_edit(request, course_pk, resource, pk=None):
    course = owned_course(request.user, course_pk)
    form_class, title, items = resource_info(resource, course)
    instance = get_object_or_404(items, pk=pk) if pk else None
    kwargs = {"course": course} if resource == "lesson" else {}
    form = form_class(request.POST or None, request.FILES or None, instance=instance, **kwargs)
    if request.method == "POST" and form.is_valid():
        item = form.save(commit=False)
        if resource != "lesson":
            item.course = course
        item.save()
        messages.success(request, f"{resource.capitalize()} saved.")
        return redirect("core:course_manage", pk=course.pk)
    return render(
        request,
        "core/form.html",
        {
            "form": form,
            "title": f"{'Edit' if pk else 'Create'} {resource}",
            "eyebrow": course.title,
            "button": "Save changes",
            "back_url": reverse("core:course_manage", args=[course.pk]),
        },
    )


@role_required("instructor")
def delete(request, course_pk, resource, pk):
    course = owned_course(request.user, course_pk)
    if resource == "course":
        item = get_object_or_404(Course, pk=pk, pk__in=[course.pk])
    else:
        _, _, items = resource_info(resource, course)
        item = get_object_or_404(items, pk=pk)
    if request.method == "POST":
        item.delete()
        messages.success(request, f"{resource.capitalize()} deleted.")
        return (
            redirect("core:instructor_dashboard")
            if resource == "course"
            else redirect("core:course_manage", pk=course.pk)
        )
    return render(
        request, "core/delete.html", {"item": item, "course": course, "resource": resource}
    )


@role_required("instructor")
def question_edit(request, quiz_pk, pk=None):
    quiz = get_object_or_404(Quiz, pk=quiz_pk, course__instructor=request.user)
    # Preserve question sets for in-flight attempts.
    if quiz.attempts.filter(submitted_at__isnull=True).exists():
        messages.error(request, "Questions are locked while a student has an active attempt.")
        return redirect("core:course_manage", pk=quiz.course_id)
    question = get_object_or_404(Question, pk=pk, quiz=quiz) if pk else Question(quiz=quiz)
    form = QuestionForm(request.POST or None, instance=question)
    choices = ChoiceFormSet(request.POST or None, instance=question)
    if request.method == "POST" and form.is_valid() and choices.is_valid():
        with transaction.atomic():
            form.save()
            choices.save()
        messages.success(request, "Question and answer choices saved.")
        return redirect("core:course_manage", pk=quiz.course_id)
    return render(
        request, "quizzes/question_form.html", {"form": form, "choices": choices, "quiz": quiz}
    )


@role_required("instructor")
def question_delete(request, quiz_pk, pk):
    quiz = get_object_or_404(Quiz, pk=quiz_pk, course__instructor=request.user)
    question = get_object_or_404(Question, pk=pk, quiz=quiz)
    if quiz.attempts.filter(submitted_at__isnull=True).exists():
        raise PermissionDenied
    if request.method == "POST":
        question.delete()
        messages.success(request, "Question deleted.")
        return redirect("core:course_manage", pk=quiz.course_id)
    return render(
        request,
        "core/delete.html",
        {"item": question, "course": quiz.course, "resource": "question"},
    )
