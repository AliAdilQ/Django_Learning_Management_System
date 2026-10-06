from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from courses.permissions import can_study, role_required

from .forms import TakeQuizForm
from .models import Quiz, QuizAnswer, QuizAttempt


@login_required
def quiz_list(request):
    if request.user.role == "student":
        items = Quiz.objects.filter(
            course__enrollments__student=request.user, course__is_published=True
        )
    elif request.user.is_instructor:
        items = Quiz.objects.filter(course__instructor=request.user)
    elif request.user.is_superuser:
        items = Quiz.objects.all()
    else:
        raise PermissionDenied
    return render(
        request,
        "quizzes/list.html",
        {
            "quizzes": items.select_related("course"),
            "attempts": request.user.quiz_attempts.filter(
                submitted_at__isnull=False
            ).select_related("quiz")[:10],
        },
    )


@role_required("student")
def take(request, pk):
    quiz = get_object_or_404(Quiz.objects.select_related("course"), pk=pk)
    if not can_study(request.user, quiz.course):
        raise PermissionDenied
    questions = list(quiz.questions.prefetch_related("choices"))
    ready = bool(questions) and all(
        question.choices.count() >= 2 and sum(c.is_correct for c in question.choices.all()) == 1
        for question in questions
    )
    attempt = QuizAttempt.objects.filter(
        student=request.user, quiz=quiz, submitted_at__isnull=True
    ).first()
    if request.method == "POST" and request.POST.get("action") == "start":
        if not ready:
            messages.error(request, "Your instructor is still preparing this quiz.")
        else:
            QuizAttempt.objects.get_or_create(
                student=request.user,
                quiz=quiz,
                submitted_at__isnull=True,
                defaults={
                    "passing_percentage": quiz.passing_percentage,
                    "time_limit": quiz.time_limit,
                },
            )
        return redirect("quizzes:take", pk=pk)
    form = TakeQuizForm(request.POST if request.method == "POST" else None, questions=questions)
    deadline = (
        attempt.started_at + timedelta(minutes=attempt.time_limit)
        if attempt and attempt.time_limit
        else None
    )
    if request.method == "POST":
        if not attempt:
            raise PermissionDenied
        expired = deadline and timezone.now() > deadline
        if form.is_valid() or expired:
            with transaction.atomic():
                # The conditional update claims the attempt once, including concurrent submits.
                claimed = QuizAttempt.objects.filter(
                    pk=attempt.pk, submitted_at__isnull=True
                ).update(submitted_at=timezone.now())
                if claimed:
                    score = 0
                    for question in questions:
                        choice = next(
                            (
                                c
                                for c in question.choices.all()
                                if str(c.pk) == form.cleaned_data.get(f"question_{question.pk}")
                            ),
                            None,
                        )
                        correct = bool(choice and choice.is_correct and not expired)
                        marks = question.marks if correct else 0
                        score += marks
                        QuizAnswer.objects.create(
                            attempt=attempt,
                            question=question,
                            choice=choice,
                            question_text=question.text,
                            choice_text=choice.text if choice else "No answer",
                            is_correct=correct,
                            awarded_marks=marks,
                        )
                    QuizAttempt.objects.filter(pk=attempt.pk).update(
                        score=score,
                        maximum_score=sum(q.marks for q in questions),
                        timed_out=bool(expired),
                    )
            messages.success(request, "Quiz submitted. Your results are ready.")
            return redirect("quizzes:result", pk=attempt.pk)
    return render(
        request,
        "quizzes/take.html",
        {
            "quiz": quiz,
            "attempt": attempt,
            "form": form,
            "ready": ready,
            "question_count": len(questions),
            "deadline": deadline,
        },
    )


@login_required
def result(request, pk):
    attempt = get_object_or_404(
        QuizAttempt.objects.select_related("quiz__course", "student"),
        pk=pk,
        submitted_at__isnull=False,
    )
    if (
        request.user.pk != attempt.student_id
        and request.user.pk != attempt.quiz.course.instructor_id
        and not request.user.is_superuser
    ):
        raise PermissionDenied
    return render(request, "quizzes/result.html", {"attempt": attempt})
