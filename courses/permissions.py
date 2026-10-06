from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

from .models import Course, Enrollment


def role_required(role):
    def decorator(view):
        @login_required
        @wraps(view)
        def wrapped(request, *args, **kwargs):
            if request.user.role != role:
                raise PermissionDenied
            return view(request, *args, **kwargs)

        return wrapped

    return decorator


def owned_course(user, pk):
    # Ownership is enforced even for staff users using instructor routes.
    return get_object_or_404(Course, pk=pk, instructor=user)


def can_study(user, course):
    if not user.is_authenticated:
        return False
    if user.is_superuser or (user.is_instructor and course.instructor_id == user.pk):
        return True
    return (
        user.role == "student"
        and course.is_published
        and Enrollment.objects.filter(student=user, course=course).exists()
    )
