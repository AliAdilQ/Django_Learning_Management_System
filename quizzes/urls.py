from django.urls import path

from . import views

app_name = "quizzes"
urlpatterns = [
    path("", views.quiz_list, name="list"),
    path("<int:pk>/", views.take, name="take"),
    path("results/<int:pk>/", views.result, name="result"),
]
