"""Integration coverage for permissions, real workflows, and reproducible setup."""

import io
import tempfile
from datetime import timedelta
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.storage import FileSystemStorage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from assignments.models import Assignment, Submission
from courses.models import (
    Announcement,
    Category,
    Course,
    Enrollment,
    Lesson,
    LessonProgress,
    Module,
    Review,
)
from quizzes.models import Choice, Question, Quiz, QuizAnswer, QuizAttempt

User = get_user_model()


class LMSIntegrationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        with override_settings(DEBUG=True):
            call_command("seed_data", stdout=io.StringIO())
        cls.student = User.objects.get(username="student1")
        cls.instructor = User.objects.get(username="instructor1")
        cls.other_instructor = User.objects.get(username="instructor2")
        cls.course = Course.objects.get(slug="python-programming-fundamentals")
        cls.other_course = Course.objects.get(slug="django-web-development")

    def login_student(self):
        self.client.force_login(self.student)

    def test_home_and_public_pages(self):
        for name in (
            "core:home",
            "core:about",
            "core:contact",
            "courses:list",
            "courses:categories",
            "accounts:login",
            "accounts:register",
        ):
            with self.subTest(name=name):
                self.assertEqual(self.client.get(reverse(name)).status_code, 200)
        self.assertContains(self.client.get(reverse("core:home")), "Learn without")

    def test_listing_search_filters_sort_and_empty_state(self):
        response = self.client.get(
            reverse("courses:list"),
            {
                "q": "Django",
                "difficulty": "intermediate",
                "category": "web-development",
                "sort": "popular",
            },
        )
        self.assertContains(response, "Django Web Development")
        self.assertEqual(response.context["page_obj"].paginator.count, 1)
        self.assertContains(
            self.client.get(reverse("courses:list"), {"q": "nonexistent-topic"}), "No courses found"
        )

    def test_course_detail_and_draft_visibility(self):
        self.assertContains(self.client.get(self.course.get_absolute_url()), "Course curriculum")
        self.course.is_published = False
        self.course.save()
        self.assertEqual(self.client.get(self.course.get_absolute_url()).status_code, 404)
        self.client.force_login(self.instructor)
        self.assertEqual(self.client.get(self.course.get_absolute_url()).status_code, 200)

    def test_registration_never_elevates_role(self):
        response = self.client.post(
            reverse("accounts:register"),
            {
                "username": "newlearner",
                "first_name": "New",
                "last_name": "Learner",
                "email": "new@example.com",
                "password1": "Strong-Learning-Password-42!",
                "password2": "Strong-Learning-Password-42!",
                "role": "admin",
                "is_staff": "on",
            },
        )
        self.assertRedirects(response, reverse("core:dashboard"), fetch_redirect_response=False)
        user = User.objects.get(username="newlearner")
        self.assertEqual(user.role, "student")
        self.assertFalse(user.is_staff)
        self.assertTrue(hasattr(user, "profile"))

    def test_registration_rejects_duplicate_email(self):
        response = self.client.post(
            reverse("accounts:register"),
            {
                "username": "newlearner",
                "email": "STUDENT1@example.com",
                "password1": "Strong-Learning-Password-42!",
                "password2": "Strong-Learning-Password-42!",
            },
        )
        self.assertContains(response, "already uses this email")
        self.assertFalse(User.objects.filter(username="newlearner").exists())

    def test_login_logout_and_safe_next(self):
        response = self.client.post(
            reverse("accounts:login"),
            {
                "username": "student1",
                "password": "Student123!",
                "next": "https://malicious.example/",
            },
        )
        self.assertRedirects(response, reverse("core:dashboard"), fetch_redirect_response=False)
        self.assertEqual(self.client.get(reverse("accounts:logout")).status_code, 405)
        self.assertRedirects(self.client.post(reverse("accounts:logout")), reverse("core:home"))
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_csrf_enforced_on_state_changes(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.student)
        self.assertEqual(
            client.post(reverse("courses:enroll", args=[self.course.slug])).status_code, 403
        )

    def test_student_dashboard_permissions(self):
        self.assertEqual(self.client.get(reverse("core:student_dashboard")).status_code, 302)
        self.login_student()
        self.assertContains(
            self.client.get(reverse("core:student_dashboard")), "Continue your journey"
        )
        self.assertEqual(self.client.get(reverse("core:instructor_dashboard")).status_code, 403)
        self.client.force_login(self.instructor)
        self.assertEqual(self.client.get(reverse("core:student_dashboard")).status_code, 403)
        self.assertEqual(self.client.get(reverse("core:instructor_dashboard")).status_code, 200)

    def test_admin_dashboard_and_model_registration(self):
        self.client.force_login(User.objects.get(username="admin"))
        self.assertRedirects(self.client.get(reverse("core:dashboard")), reverse("admin:index"))
        for app, model in [
            ("accounts", "user"),
            ("accounts", "profile"),
            ("courses", "category"),
            ("courses", "course"),
            ("courses", "module"),
            ("courses", "lesson"),
            ("courses", "enrollment"),
            ("courses", "lessonprogress"),
            ("courses", "announcement"),
            ("courses", "review"),
            ("assignments", "assignment"),
            ("assignments", "submission"),
            ("quizzes", "quiz"),
            ("quizzes", "question"),
            ("quizzes", "choice"),
            ("quizzes", "quizattempt"),
            ("quizzes", "quizanswer"),
            ("core", "contactmessage"),
        ]:
            with self.subTest(model=model):
                self.assertEqual(
                    self.client.get(reverse(f"admin:{app}_{model}_changelist")).status_code, 200
                )

    def test_enrollment_idempotent_and_database_unique(self):
        self.login_student()
        new_course = Course.objects.get(slug="flask-web-development")
        url = reverse("courses:enroll", args=[new_course.slug])
        self.assertEqual(self.client.get(url).status_code, 405)
        for _ in range(2):
            self.assertEqual(self.client.post(url).status_code, 302)
        self.assertEqual(
            Enrollment.objects.filter(student=self.student, course=new_course).count(), 1
        )
        with self.assertRaises(IntegrityError), transaction.atomic():
            Enrollment.objects.create(student=self.student, course=new_course)

    def test_only_students_enroll(self):
        self.client.force_login(self.instructor)
        self.assertEqual(
            self.client.post(reverse("courses:enroll", args=[self.course.slug])).status_code, 403
        )

    def test_lesson_access_and_completion_progress(self):
        self.login_student()
        lesson = Lesson.objects.filter(module__course=self.course).last()
        enrollment = Enrollment.objects.get(student=self.student, course=self.course)
        before = enrollment.progress
        self.assertEqual(self.client.get(lesson.get_absolute_url()).status_code, 200)
        url = reverse("courses:complete_lesson", args=[self.course.slug, lesson.pk])
        self.client.post(url)
        self.client.post(url)
        self.assertGreater(enrollment.progress, before)
        self.assertEqual(
            LessonProgress.objects.filter(student=self.student, lesson=lesson).count(), 1
        )
        inaccessible = Lesson.objects.filter(module__course__slug="flask-web-development").first()
        self.assertEqual(self.client.get(inaccessible.get_absolute_url()).status_code, 403)

    def test_unpublished_content_denies_student(self):
        self.login_student()
        lesson = self.course.modules.first().lessons.first()
        lesson.is_published = False
        lesson.save()
        self.assertEqual(self.client.get(lesson.get_absolute_url()).status_code, 403)
        self.course.is_published = False
        self.course.save()
        self.assertEqual(
            self.client.get(
                reverse("assignments:detail", args=[self.course.assignments.first().pk])
            ).status_code,
            403,
        )

    def test_instructor_ownership_all_content_types(self):
        self.client.force_login(self.other_instructor)
        self.assertEqual(
            self.client.get(reverse("core:course_edit", args=[self.course.pk])).status_code, 404
        )
        self.assertEqual(
            self.client.get(reverse("core:course_manage", args=[self.course.pk])).status_code, 404
        )
        for resource in ("module", "lesson", "assignment", "quiz", "announcement"):
            self.assertEqual(
                self.client.get(
                    reverse("core:resource_create", args=[self.course.pk, resource])
                ).status_code,
                404,
            )
        self.assertEqual(
            self.client.get(
                reverse("core:question_create", args=[self.course.quizzes.first().pk])
            ).status_code,
            404,
        )

    def test_lesson_form_blocks_foreign_module(self):
        self.client.force_login(self.instructor)
        response = self.client.post(
            reverse("core:resource_create", args=[self.course.pk, "lesson"]),
            {
                "module": self.other_course.modules.first().pk,
                "title": "Injected lesson",
                "content": "Hidden",
                "order": 1,
                "duration": 10,
                "is_published": "on",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Lesson.objects.filter(title="Injected lesson").exists())
        self.assertIn("module", response.context["form"].errors)

    def test_instructor_create_edit_delete_course(self):
        self.client.force_login(self.instructor)
        data = {
            "title": "New practical course",
            "slug": "new-practical-course",
            "category": self.course.category_id,
            "short_description": "Learn by doing.",
            "description": "A new curriculum.",
            "difficulty": "beginner",
            "duration": 4,
            "instructor": self.other_instructor.pk,
        }
        response = self.client.post(reverse("core:course_create"), data)
        course = Course.objects.get(slug="new-practical-course")
        self.assertEqual(course.instructor, self.instructor)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            self.client.get(reverse("core:course_manage", args=[course.pk])).status_code, 200
        )
        data["title"] = "Updated practical course"
        self.client.post(reverse("core:course_edit", args=[course.pk]), data)
        course.refresh_from_db()
        self.assertEqual(course.title, "Updated practical course")
        self.client.post(reverse("core:resource_delete", args=[course.pk, "course", course.pk]))
        self.assertFalse(Course.objects.filter(pk=course.pk).exists())

    def test_instructor_resource_crud(self):
        self.client.force_login(self.instructor)
        resources = {
            "module": {"title": "Practice module", "description": "Practice", "order": 3},
            "lesson": {
                "module": self.course.modules.first().pk,
                "title": "Practice lesson",
                "content": "Practice content",
                "order": 8,
                "duration": 10,
                "is_published": "on",
            },
            "assignment": {
                "title": "Practice assignment",
                "description": "Build a project",
                "due_date": "2030-01-01T12:00",
                "maximum_marks": 20,
            },
            "quiz": {
                "title": "Practice quiz",
                "description": "A check-in",
                "passing_percentage": 60,
                "time_limit": 0,
            },
            "announcement": {"title": "Practice announcement", "content": "A new update"},
        }
        models = {
            "module": Module,
            "lesson": Lesson,
            "assignment": Assignment,
            "quiz": Quiz,
            "announcement": Announcement,
        }
        for resource, data in resources.items():
            with self.subTest(resource=resource):
                self.assertEqual(
                    self.client.post(
                        reverse("core:resource_create", args=[self.course.pk, resource]), data
                    ).status_code,
                    302,
                )
                item = models[resource].objects.get(title=data["title"])
                self.assertEqual(
                    self.client.get(
                        reverse("core:resource_edit", args=[self.course.pk, resource, item.pk])
                    ).status_code,
                    200,
                )
                data["title"] += " updated"
                self.assertEqual(
                    self.client.post(
                        reverse("core:resource_edit", args=[self.course.pk, resource, item.pk]),
                        data,
                    ).status_code,
                    302,
                )
                self.assertEqual(
                    self.client.post(
                        reverse("core:resource_delete", args=[self.course.pk, resource, item.pk])
                    ).status_code,
                    302,
                )
                self.assertFalse(models[resource].objects.filter(pk=item.pk).exists())

    def test_question_choices_validate_exactly_one_correct(self):
        self.client.force_login(self.instructor)
        quiz = self.course.quizzes.first()
        data = {
            "text": "A new question?",
            "marks": 2,
            "order": 4,
            "choices-TOTAL_FORMS": 2,
            "choices-INITIAL_FORMS": 0,
            "choices-MIN_NUM_FORMS": 0,
            "choices-MAX_NUM_FORMS": 6,
            "choices-0-text": "One",
            "choices-1-text": "Two",
            "choices-0-is_correct": "on",
            "choices-1-is_correct": "on",
        }
        url = reverse("core:question_create", args=[quiz.pk])
        self.assertContains(self.client.post(url, data), "exactly one correct")
        self.assertFalse(Question.objects.filter(text="A new question?").exists())
        data.pop("choices-1-is_correct")
        self.assertEqual(self.client.post(url, data).status_code, 302)
        question = Question.objects.get(text="A new question?")
        self.assertEqual(question.choices.count(), 2)

    def test_submission_grading_and_private_download(self):
        self.login_student()
        assignment = self.other_course.assignments.first()
        with (
            tempfile.TemporaryDirectory(dir=settings.BASE_DIR) as directory,
            patch.object(
                Submission._meta.get_field("file"), "storage", FileSystemStorage(location=directory)
            ),
        ):
            upload = SimpleUploadedFile(
                "work.txt", b"My private assignment", content_type="text/plain"
            )
            self.assertEqual(
                self.client.post(
                    reverse("assignments:detail", args=[assignment.pk]),
                    {"text": "My approach", "file": upload},
                ).status_code,
                302,
            )
            submission = Submission.objects.get(student=self.student, assignment=assignment)
            self.assertEqual(submission.status, "Submitted")
            download = reverse("assignments:download", args=[submission.pk])
            response = self.client.get(download)
            self.assertEqual(response.status_code, 200)
            response.close()
            self.client.force_login(User.objects.get(username="student2"))
            self.assertEqual(self.client.get(download).status_code, 403)
            self.client.force_login(self.instructor)
            self.assertEqual(self.client.get(download).status_code, 403)
            self.client.force_login(self.other_instructor)
            response = self.client.get(download)
            self.assertEqual(response.status_code, 200)
            response.close()
            grade = reverse("assignments:grade", args=[submission.pk])
            self.assertContains(
                self.client.post(grade, {"marks": 101, "feedback": "Over limit"}), "cannot exceed"
            )
            self.assertEqual(
                self.client.post(grade, {"marks": 95, "feedback": "Great application"}).status_code,
                302,
            )
            submission.refresh_from_db()
            self.assertEqual(submission.status, "Graded")
            self.assertEqual(submission.marks, 95)
            self.login_student()
            self.assertEqual(
                self.client.post(
                    reverse("assignments:detail", args=[assignment.pk]), {"text": "Changed"}
                ).status_code,
                403,
            )

    def test_assignment_upload_validation_and_late_status(self):
        self.login_student()
        assignment = self.other_course.assignments.first()
        response = self.client.post(
            reverse("assignments:detail", args=[assignment.pk]),
            {
                "text": "A project",
                "file": SimpleUploadedFile("unsafe.html", b"<script>bad</script>"),
            },
        )
        self.assertContains(response, "Choose a PDF, TXT, or Markdown")
        assignment.due_date = timezone.now() - timedelta(days=1)
        assignment.save()
        self.client.post(
            reverse("assignments:detail", args=[assignment.pk]), {"text": "A late project"}
        )
        self.assertEqual(
            Submission.objects.get(student=self.student, assignment=assignment).status, "Late"
        )

    def test_quiz_scoring_and_replay_protection(self):
        self.login_student()
        quiz = self.course.quizzes.first()
        url = reverse("quizzes:take", args=[quiz.pk])
        self.assertEqual(self.client.post(url, {"action": "start"}).status_code, 302)
        attempt = QuizAttempt.objects.get(
            student=self.student, quiz=quiz, submitted_at__isnull=True
        )
        data = {"action": "submit"}
        for question in quiz.questions.all():
            data[f"question_{question.pk}"] = str(question.choices.get(is_correct=True).pk)
        response = self.client.post(url, data)
        self.assertRedirects(response, reverse("quizzes:result", args=[attempt.pk]))
        attempt.refresh_from_db()
        self.assertEqual(attempt.score, 6)
        self.assertTrue(attempt.passed)
        self.assertEqual(attempt.answers.count(), 3)
        self.assertEqual(self.client.post(url, data).status_code, 403)

    def test_quiz_rejects_foreign_choice_and_non_enrolled_access(self):
        self.login_student()
        quiz = self.course.quizzes.first()
        url = reverse("quizzes:take", args=[quiz.pk])
        self.client.post(url, {"action": "start"})
        question = quiz.questions.first()
        foreign = Choice.objects.exclude(question__quiz=quiz).first()
        response = self.client.post(url, {f"question_{question.pk}": foreign.pk})
        self.assertEqual(response.status_code, 200)
        self.assertIn(f"question_{question.pk}", response.context["form"].errors)
        other = Quiz.objects.get(course__slug="flask-web-development")
        self.assertEqual(self.client.get(reverse("quizzes:take", args=[other.pk])).status_code, 403)

    def test_quiz_timer_is_enforced_on_server(self):
        self.login_student()
        quiz = self.course.quizzes.first()
        attempt = QuizAttempt.objects.create(
            student=self.student,
            quiz=quiz,
            started_at=timezone.now() - timedelta(minutes=3),
            time_limit=1,
        )
        data = {f"question_{q.pk}": q.choices.get(is_correct=True).pk for q in quiz.questions.all()}
        self.client.post(reverse("quizzes:take", args=[quiz.pk]), data)
        attempt.refresh_from_db()
        self.assertTrue(attempt.timed_out)
        self.assertFalse(attempt.passed)
        self.assertEqual(attempt.score, 0)

    def test_quiz_pass_threshold_uses_unrounded_score(self):
        attempt = QuizAttempt(
            score=6496, maximum_score=10000, passing_percentage=65, submitted_at=timezone.now()
        )
        self.assertEqual(attempt.percentage, 65.0)
        self.assertFalse(attempt.passed)

    def test_quiz_result_private_and_historical_answers(self):
        attempt = QuizAttempt.objects.filter(
            student=self.student, submitted_at__isnull=False
        ).first()
        self.client.force_login(User.objects.get(username="student2"))
        self.assertEqual(
            self.client.get(reverse("quizzes:result", args=[attempt.pk])).status_code, 403
        )
        saved_text = attempt.answers.first().question_text
        Question.objects.filter(pk=attempt.answers.first().question_id).update(
            text="Updated wording"
        )
        self.login_student()
        self.assertContains(
            self.client.get(reverse("quizzes:result", args=[attempt.pk])), saved_text
        )

    def test_review_upsert_and_rating_validation(self):
        self.login_student()
        url = reverse("courses:review", args=[self.course.slug])
        for text in ("Very useful practice.", "Updated after finishing."):
            self.client.post(url, {"rating": 5, "text": text})
        self.assertEqual(Review.objects.filter(student=self.student, course=self.course).count(), 1)
        self.client.post(url, {"rating": 9, "text": "Invalid"})
        self.assertEqual(Review.objects.get(student=self.student, course=self.course).rating, 5)

    def test_profile_and_password_change(self):
        self.login_student()
        response = self.client.post(
            reverse("accounts:edit_profile"),
            {
                "first_name": "Updated",
                "last_name": "Name",
                "email": "updated@example.com",
                "headline": "Learning Python",
                "bio": "A new chapter",
                "role": "admin",
            },
        )
        self.assertRedirects(response, reverse("accounts:profile"))
        self.student.refresh_from_db()
        self.assertEqual(self.student.role, "student")
        self.assertEqual(self.student.profile.headline, "Learning Python")
        response = self.client.post(
            reverse("accounts:password_change"),
            {
                "old_password": "Student123!",
                "new_password1": "Changed-Learning-Password-42!",
                "new_password2": "Changed-Learning-Password-42!",
            },
        )
        self.assertRedirects(response, reverse("accounts:profile"))
        self.student.refresh_from_db()
        self.assertTrue(self.student.check_password("Changed-Learning-Password-42!"))

    def test_seed_is_stable_and_preserves_passwords(self):
        models = [
            User,
            Category,
            Course,
            Module,
            Lesson,
            Enrollment,
            LessonProgress,
            Assignment,
            Submission,
            Quiz,
            Question,
            Choice,
            QuizAttempt,
            QuizAnswer,
            Announcement,
            Review,
        ]
        before = {model.__name__: model.objects.count() for model in models}
        self.student.set_password("Personally-Changed-Password-42!")
        self.student.save()
        with override_settings(DEBUG=True):
            for _ in range(2):
                call_command("seed_data", stdout=io.StringIO())
        after = {model.__name__: model.objects.count() for model in models}
        self.assertEqual(before, after)
        self.student.refresh_from_db()
        self.assertTrue(self.student.check_password("Personally-Changed-Password-42!"))

    def test_seed_disabled_in_production(self):
        from django.core.management.base import CommandError

        with override_settings(DEBUG=False), self.assertRaises(CommandError):
            call_command("seed_data", stdout=io.StringIO())

    @override_settings(DEBUG=False)
    def test_branded_errors(self):
        self.assertContains(self.client.get("/missing-page/"), "learning path", status_code=404)
        self.login_student()
        self.assertContains(
            self.client.get(reverse("core:instructor_dashboard")),
            "chapter isn't available",
            status_code=403,
        )
