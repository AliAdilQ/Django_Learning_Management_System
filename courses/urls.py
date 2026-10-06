from django.urls import path

from . import views

app_name = "courses"
urlpatterns = [
    path("", views.course_list, name="list"),
    path("categories/", views.categories, name="categories"),
    path("<slug:slug>/", views.detail, name="detail"),
    path("<slug:slug>/enroll/", views.enroll, name="enroll"),
    path("<slug:slug>/review/", views.review, name="review"),
    path("<slug:slug>/lessons/<int:pk>/", views.lesson, name="lesson"),
    path("<slug:slug>/lessons/<int:pk>/complete/", views.complete_lesson, name="complete_lesson"),
]
