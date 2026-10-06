from django.urls import path

from . import instructor, views

app_name = "core"
urlpatterns = [
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),
    path("contact/", views.contact, name="contact"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("dashboard/student/", views.student_dashboard, name="student_dashboard"),
    path("dashboard/instructor/", views.instructor_dashboard, name="instructor_dashboard"),
    path("dashboard/instructor/courses/new/", instructor.course_edit, name="course_create"),
    path("dashboard/instructor/courses/<int:pk>/edit/", instructor.course_edit, name="course_edit"),
    path("dashboard/instructor/courses/<int:pk>/", instructor.course_manage, name="course_manage"),
    path(
        "dashboard/instructor/courses/<int:course_pk>/<str:resource>/new/",
        instructor.resource_edit,
        name="resource_create",
    ),
    path(
        "dashboard/instructor/courses/<int:course_pk>/<str:resource>/<int:pk>/edit/",
        instructor.resource_edit,
        name="resource_edit",
    ),
    path(
        "dashboard/instructor/courses/<int:course_pk>/<str:resource>/<int:pk>/delete/",
        instructor.delete,
        name="resource_delete",
    ),
    path(
        "dashboard/instructor/quizzes/<int:quiz_pk>/questions/new/",
        instructor.question_edit,
        name="question_create",
    ),
    path(
        "dashboard/instructor/quizzes/<int:quiz_pk>/questions/<int:pk>/edit/",
        instructor.question_edit,
        name="question_edit",
    ),
    path(
        "dashboard/instructor/quizzes/<int:quiz_pk>/questions/<int:pk>/delete/",
        instructor.question_delete,
        name="question_delete",
    ),
]
