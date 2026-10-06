from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import redirect, render

from accounts.models import User
from assignments.models import Assignment, Submission
from courses.models import (
    Announcement,
    Category,
    Course,
    Enrollment,
    Lesson,
    LessonProgress,
    Review,
)
from courses.permissions import role_required
from quizzes.models import QuizAttempt

from .forms import ContactForm


def home(request):
    courses = Course.objects.published().with_stats()
    return render(
        request,
        "core/home.html",
        {
            "featured": courses.filter(is_featured=True)[:3],
            "popular": courses.order_by("-student_count", "pk")[:3],
            "categories": Category.objects.annotate(
                course_count=Count("courses", filter=Q(courses__is_published=True))
            ),
            "stats": {
                "courses": courses.count(),
                "students": User.objects.filter(role="student").count(),
                "instructors": User.objects.filter(role="instructor").count(),
                "lessons": Lesson.objects.filter(
                    is_published=True, module__course__is_published=True
                ).count(),
            },
            "testimonials": Review.objects.filter(
                rating__gte=4, course__is_published=True
            ).select_related("student", "course")[:3],
        },
    )


def about(request):
    return render(request, "core/about.html")


def contact(request):
    form = ContactForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Your message was saved for the project administrator.")
        return redirect("core:contact")
    return render(
        request,
        "core/form.html",
        {
            "form": form,
            "title": "Let's talk learning.",
            "eyebrow": "GET IN TOUCH",
            "description": "Messages are saved locally for the administrator. This portfolio demo does not send email.",
            "button": "Send message",
        },
    )


@login_required
def dashboard(request):
    if request.user.is_staff or request.user.is_superuser:
        return redirect("admin:index")
    if request.user.is_instructor:
        return redirect("core:instructor_dashboard")
    return redirect("core:student_dashboard")


@role_required("student")
def student_dashboard(request):
    enrollments = Enrollment.objects.filter(
        student=request.user, course__is_published=True
    ).select_related("course__instructor", "course__category")
    pending = (
        Assignment.objects.filter(
            course__enrollments__student=request.user, course__is_published=True
        )
        .exclude(submissions__student=request.user)
        .select_related("course")
    )
    attempts = QuizAttempt.objects.filter(
        student=request.user, submitted_at__isnull=False, quiz__course__is_published=True
    ).select_related("quiz__course")
    completed = LessonProgress.objects.filter(
        student=request.user, lesson__is_published=True, lesson__module__course__is_published=True
    ).count()
    return render(
        request,
        "core/student_dashboard.html",
        {
            "enrollments": enrollments,
            "recent_enrollments": enrollments[:2],
            "pending": pending[:4],
            "attempts": attempts[:4],
            "announcements": Announcement.objects.filter(
                course__enrollments__student=request.user, course__is_published=True
            ).select_related("course")[:3],
            "stats": {
                "enrolled": enrollments.count(),
                "completed": completed,
                "pending": pending.count(),
                "attempts": attempts.count(),
            },
        },
    )


@role_required("instructor")
def instructor_dashboard(request):
    courses = Course.objects.filter(instructor=request.user).with_stats()
    enrollments = Enrollment.objects.filter(course__instructor=request.user).select_related(
        "student", "course"
    )
    submissions = Submission.objects.filter(
        assignment__course__instructor=request.user, marks__isnull=True
    ).select_related("student", "assignment")[:5]
    return render(
        request,
        "core/instructor_dashboard.html",
        {
            "courses": courses,
            "enrollments": enrollments.order_by("-enrolled_at")[:5],
            "submissions": submissions,
            "stats": {
                "courses": courses.count(),
                "students": enrollments.values("student").distinct().count(),
                "lessons": Lesson.objects.filter(module__course__instructor=request.user).count(),
                "assignments": Assignment.objects.filter(course__instructor=request.user).count(),
            },
        },
    )


def error_403(request, exception=None):
    return render(request, "403.html", status=403)


def error_404(request, exception=None):
    return render(request, "404.html", status=404)


def error_500(request):
    return render(request, "500.html", status=500)
