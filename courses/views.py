from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import ReviewForm
from .models import Category, Course, Enrollment, Lesson, LessonProgress, Review
from .permissions import can_study, role_required


def course_list(request):
    courses = Course.objects.published().with_stats()
    query = request.GET.get("q", "").strip()
    category = request.GET.get("category", "")
    difficulty = request.GET.get("difficulty", "")
    sort = request.GET.get("sort", "newest")
    if query:
        courses = courses.filter(Q(title__icontains=query) | Q(short_description__icontains=query))
    if category:
        courses = courses.filter(category__slug=category)
    if difficulty:
        courses = courses.filter(difficulty=difficulty)
    courses = courses.order_by(
        {"popular": "-student_count", "rating": "-average_rating", "title": "title"}.get(
            sort, "-created_at"
        ),
        "pk",
    )
    params = request.GET.copy()
    params.pop("page", None)
    return render(
        request,
        "courses/list.html",
        {
            "page_obj": Paginator(courses, 9).get_page(request.GET.get("page")),
            "categories": Category.objects.all(),
            "difficulties": Course.Difficulty.choices,
            "query": query,
            "selected_category": category,
            "selected_difficulty": difficulty,
            "sort": sort,
            "querystring": params.urlencode(),
        },
    )


def categories(request):
    items = Category.objects.annotate(
        course_count=Count("courses", filter=Q(courses__is_published=True))
    )
    return render(request, "courses/categories.html", {"categories": items})


def detail(request, slug):
    course = get_object_or_404(
        Course.objects.with_stats().prefetch_related("modules__lessons"), slug=slug
    )
    if not course.is_published and not (
        request.user.is_authenticated
        and (request.user.is_superuser or request.user.pk == course.instructor_id)
    ):
        from django.http import Http404

        raise Http404
    enrollment = None
    review = None
    if request.user.is_authenticated:
        enrollment = Enrollment.objects.filter(student=request.user, course=course).first()
        review = Review.objects.filter(student=request.user, course=course).first()
    lessons = Lesson.objects.filter(module__course=course, is_published=True)
    first_lesson = lessons.first()
    if enrollment:
        first_lesson = (
            lessons.exclude(progress_records__student=request.user).first() or first_lesson
        )
    return render(
        request,
        "courses/detail.html",
        {
            "course": course,
            "enrollment": enrollment,
            "first_lesson": first_lesson,
            "review_form": ReviewForm(instance=review),
            "reviews": course.reviews.select_related("student")[:8],
            "can_study": can_study(request.user, course),
        },
    )


@require_POST
@role_required("student")
def enroll(request, slug):
    course = get_object_or_404(Course, slug=slug, is_published=True)
    _, created = Enrollment.objects.get_or_create(student=request.user, course=course)
    messages.success(
        request,
        "You're enrolled. Let's build something great."
        if created
        else "You're already enrolled in this course.",
    )
    return redirect("courses:detail", slug=slug)


@login_required
def lesson(request, slug, pk):
    current = get_object_or_404(
        Lesson.objects.select_related("module__course"), pk=pk, module__course__slug=slug
    )
    course = current.module.course
    if not can_study(request.user, course) or (
        not current.is_published
        and request.user.pk != course.instructor_id
        and not request.user.is_superuser
    ):
        raise PermissionDenied
    Enrollment.objects.filter(student=request.user, course=course).update(
        last_accessed=timezone.now()
    )
    lessons = list(
        Lesson.objects.filter(module__course=course, is_published=True).select_related("module")
    )
    ids = [item.pk for item in lessons]
    index = ids.index(current.pk) if current.pk in ids else -1
    completed = set(
        LessonProgress.objects.filter(
            student=request.user, lesson__module__course=course
        ).values_list("lesson_id", flat=True)
    )
    enrollment = Enrollment.objects.filter(student=request.user, course=course).first()
    return render(
        request,
        "courses/lesson.html",
        {
            "course": course,
            "lesson": current,
            "modules": course.modules.prefetch_related("lessons"),
            "completed": completed,
            "enrollment": enrollment,
            "previous": lessons[index - 1] if index > 0 else None,
            "next_lesson": lessons[index + 1] if 0 <= index < len(lessons) - 1 else None,
        },
    )


@require_POST
@role_required("student")
def complete_lesson(request, slug, pk):
    current = get_object_or_404(
        Lesson,
        pk=pk,
        module__course__slug=slug,
        is_published=True,
        module__course__is_published=True,
    )
    if not Enrollment.objects.filter(student=request.user, course=current.module.course).exists():
        raise PermissionDenied
    LessonProgress.objects.get_or_create(student=request.user, lesson=current)
    messages.success(request, "Lesson complete. One step closer to your goal!")
    return redirect("courses:lesson", slug=slug, pk=pk)


@require_POST
@role_required("student")
def review(request, slug):
    course = get_object_or_404(Course, slug=slug, is_published=True)
    if not Enrollment.objects.filter(student=request.user, course=course).exists():
        raise PermissionDenied
    existing = Review.objects.filter(student=request.user, course=course).first()
    form = ReviewForm(request.POST, instance=existing)
    if form.is_valid():
        item = form.save(commit=False)
        item.student, item.course = request.user, course
        item.save()
        messages.success(request, "Thanks for sharing your learning experience.")
    else:
        messages.error(
            request, "Choose a rating from 1 to 5 and a review of up to 1,500 characters."
        )
    return redirect("courses:detail", slug=slug)
