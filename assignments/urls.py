from django.urls import path

from . import views

app_name = "assignments"
urlpatterns = [
    path("", views.assignment_list, name="list"),
    path("<int:pk>/", views.detail, name="detail"),
    path("submissions/<int:pk>/grade/", views.grade, name="grade"),
    path("submissions/<int:pk>/download/", views.download, name="download"),
]
