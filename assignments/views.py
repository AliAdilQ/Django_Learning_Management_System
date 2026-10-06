from pathlib import Path

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from courses.permissions import can_study, role_required

from .forms import GradeForm, SubmissionForm
from .models import Assignment, Submission


@login_required
def assignment_list(request):
    if request.user.role == "student":
        items = Assignment.objects.filter(
            course__enrollments__student=request.user, course__is_published=True
        )
    elif request.user.is_instructor:
        items = Assignment.objects.filter(course__instructor=request.user)
    elif request.user.is_superuser:
        items = Assignment.objects.all()
    else:
        raise PermissionDenied
    items = items.select_related("course")
    own = {item.assignment_id: item for item in Submission.objects.filter(student=request.user)}
    rows = [(item, own.get(item.pk)) for item in items]
    return render(request, "assignments/list.html", {"rows": rows})


@login_required
def detail(request, pk):
    assignment = get_object_or_404(Assignment.objects.select_related("course"), pk=pk)
    if not can_study(request.user, assignment.course):
        raise PermissionDenied
    submission = Submission.objects.filter(assignment=assignment, student=request.user).first()
    form = SubmissionForm(request.POST or None, request.FILES or None, instance=submission)
    if request.method == "POST":
        if request.user.role != "student" or (submission and submission.marks is not None):
            raise PermissionDenied
        if form.is_valid():
            item = form.save(commit=False)
            item.student, item.assignment = request.user, assignment
            item.submitted_at = timezone.now()
            item.save()
            messages.success(
                request, "Assignment submitted. Your instructor can now review your work."
            )
            return redirect("assignments:detail", pk=pk)
    submissions = (
        assignment.submissions.select_related("student")
        if request.user.pk == assignment.course.instructor_id or request.user.is_superuser
        else []
    )
    return render(
        request,
        "assignments/detail.html",
        {
            "assignment": assignment,
            "submission": submission,
            "form": form,
            "submissions": submissions,
        },
    )


@role_required("instructor")
def grade(request, pk):
    submission = get_object_or_404(
        Submission.objects.select_related("assignment__course", "student"),
        pk=pk,
        assignment__course__instructor=request.user,
    )
    form = GradeForm(request.POST or None, instance=submission)
    if request.method == "POST" and form.is_valid():
        item = form.save(commit=False)
        item.graded_at = timezone.now()
        item.save()
        messages.success(request, "Grade and feedback saved.")
        return redirect("assignments:detail", pk=submission.assignment_id)
    return render(request, "assignments/grade.html", {"form": form, "submission": submission})


@login_required
def download(request, pk):
    submission = get_object_or_404(Submission.objects.select_related("assignment__course"), pk=pk)
    if (
        request.user.pk != submission.student_id
        and request.user.pk != submission.assignment.course.instructor_id
        and not request.user.is_superuser
    ):
        raise PermissionDenied
    if not submission.file:
        raise Http404
    try:
        response = FileResponse(
            submission.file.open("rb"),
            as_attachment=True,
            filename=f"submission-{pk}{Path(submission.file.name).suffix}",
        )
    except FileNotFoundError as exc:
        raise Http404 from exc
    response["X-Content-Type-Options"] = "nosniff"
    return response
