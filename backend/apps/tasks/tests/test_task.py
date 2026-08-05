from datetime import timedelta
from uuid import UUID

from django.apps import apps as django_apps
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from apps.tasks.models import Category


class TaskModelTests(TestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_user(
            email="owner@example.com",
            password="strong-password-123",
        )
        self.category = Category.objects.create(owner=self.owner, name="Work")

    @staticmethod
    def get_task_model():
        return django_apps.get_model("tasks", "Task")

    def test_creates_task_with_minimum_fields(self):
        task_model = self.get_task_model()

        task = task_model.objects.create(owner=self.owner, title="Write report")

        self.assertIsInstance(task.id, UUID)
        self.assertEqual(task.owner, self.owner)
        self.assertEqual(task.title, "Write report")
        self.assertEqual(task.description, "")
        self.assertIsNotNone(task.created_at)
        self.assertIsNotNone(task.updated_at)
        self.assertIn(task, self.owner.tasks.all())

    def test_default_status_is_pending(self):
        task_model = self.get_task_model()

        task = task_model.objects.create(owner=self.owner, title="Write report")

        self.assertEqual(task.status, "pending")

    def test_default_priority_is_medium(self):
        task_model = self.get_task_model()

        task = task_model.objects.create(owner=self.owner, title="Write report")

        self.assertEqual(task.priority, "medium")

    def test_category_is_optional(self):
        task_model = self.get_task_model()

        task = task_model.objects.create(owner=self.owner, title="Write report")

        self.assertIsNone(task.category)

    def test_due_date_is_optional(self):
        task_model = self.get_task_model()

        task = task_model.objects.create(owner=self.owner, title="Write report")

        self.assertIsNone(task.due_date)

    def test_deleting_category_keeps_task_without_category(self):
        task_model = self.get_task_model()
        task = task_model.objects.create(
            owner=self.owner,
            category=self.category,
            title="Write report",
        )

        self.category.delete()
        task.refresh_from_db()

        self.assertIsNone(task.category)

    def test_deleting_owner_deletes_tasks(self):
        task_model = self.get_task_model()
        task = task_model.objects.create(owner=self.owner, title="Write report")

        self.owner.delete()

        self.assertFalse(task_model.objects.filter(id=task.id).exists())

    def test_full_clean_rejects_invalid_status(self):
        task_model = self.get_task_model()
        task = task_model(owner=self.owner, title="Write report", status="invalid")

        with self.assertRaises(ValidationError):
            task.full_clean()

    def test_full_clean_rejects_invalid_priority(self):
        task_model = self.get_task_model()
        task = task_model(owner=self.owner, title="Write report", priority="invalid")

        with self.assertRaises(ValidationError):
            task.full_clean()

    def test_string_representation_is_title(self):
        task_model = self.get_task_model()
        task = task_model.objects.create(owner=self.owner, title="Write report")

        self.assertEqual(str(task), "Write report")

    def test_default_ordering_is_newest_then_highest_id(self):
        task_model = self.get_task_model()
        first = task_model.objects.create(owner=self.owner, title="First")
        second = task_model.objects.create(owner=self.owner, title="Second")
        newer_created_at = timezone.now()
        task_model.objects.filter(id=first.id).update(
            created_at=newer_created_at - timedelta(seconds=1)
        )
        task_model.objects.filter(id=second.id).update(created_at=newer_created_at)

        ordered = list(task_model.objects.values_list("id", flat=True))
        self.assertEqual(ordered, [second.id, first.id])

        task_model.objects.filter(id__in=(first.id, second.id)).update(
            created_at=newer_created_at
        )
        ordered = list(task_model.objects.values_list("id", flat=True))

        self.assertEqual(ordered, sorted((first.id, second.id), reverse=True))

    def test_is_registered_in_admin(self):
        task_model = self.get_task_model()

        self.assertIn(task_model, admin.site._registry)
