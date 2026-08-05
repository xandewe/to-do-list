from uuid import UUID

from django.apps import apps as django_apps
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.tasks.models import Task


class TaskShareModelTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.owner = user_model.objects.create_user(
            email="owner@example.com",
            password="strong-password-123",
        )
        self.recipient = user_model.objects.create_user(
            email="recipient@example.com",
            password="strong-password-123",
        )
        self.task = Task.objects.create(owner=self.owner, title="Write report")

    @staticmethod
    def get_task_share_model():
        return django_apps.get_model("tasks", "TaskShare")

    def test_creates_task_share(self):
        task_share_model = self.get_task_share_model()

        task_share = task_share_model.objects.create(
            task=self.task,
            user=self.recipient,
            shared_by=self.owner,
        )

        self.assertIsInstance(task_share.id, UUID)
        self.assertEqual(task_share.task, self.task)
        self.assertEqual(task_share.user, self.recipient)
        self.assertEqual(task_share.shared_by, self.owner)
        self.assertIsNotNone(task_share.created_at)
        self.assertIn(task_share, self.task.shares.all())
        self.assertIn(task_share, self.recipient.shared_tasks.all())
        self.assertIn(task_share, self.owner.created_task_shares.all())

    def test_default_permission_is_view(self):
        task_share_model = self.get_task_share_model()

        task_share = task_share_model.objects.create(
            task=self.task,
            user=self.recipient,
            shared_by=self.owner,
        )

        self.assertEqual(task_share.permission, "view")

    def test_allows_edit_permission(self):
        task_share_model = self.get_task_share_model()

        task_share = task_share_model.objects.create(
            task=self.task,
            user=self.recipient,
            permission="edit",
            shared_by=self.owner,
        )

        self.assertEqual(task_share.permission, "edit")

    def test_rejects_duplicate_task_and_user(self):
        task_share_model = self.get_task_share_model()
        task_share_model.objects.create(
            task=self.task,
            user=self.recipient,
            shared_by=self.owner,
        )

        with self.assertRaises(IntegrityError), transaction.atomic():
            task_share_model.objects.create(
                task=self.task,
                user=self.recipient,
                shared_by=self.owner,
            )

    def test_allows_same_task_for_different_users(self):
        task_share_model = self.get_task_share_model()
        another_user = get_user_model().objects.create_user(
            email="another@example.com",
            password="strong-password-123",
        )

        first = task_share_model.objects.create(
            task=self.task,
            user=self.recipient,
            shared_by=self.owner,
        )
        second = task_share_model.objects.create(
            task=self.task,
            user=another_user,
            shared_by=self.owner,
        )

        self.assertNotEqual(first.id, second.id)

    def test_allows_same_user_for_different_tasks(self):
        task_share_model = self.get_task_share_model()
        another_task = Task.objects.create(owner=self.owner, title="Review report")

        first = task_share_model.objects.create(
            task=self.task,
            user=self.recipient,
            shared_by=self.owner,
        )
        second = task_share_model.objects.create(
            task=another_task,
            user=self.recipient,
            shared_by=self.owner,
        )

        self.assertNotEqual(first.id, second.id)

    def test_deleting_task_deletes_shares(self):
        task_share_model = self.get_task_share_model()
        task_share = task_share_model.objects.create(
            task=self.task,
            user=self.recipient,
            shared_by=self.owner,
        )

        self.task.delete()

        self.assertFalse(task_share_model.objects.filter(id=task_share.id).exists())

    def test_deleting_recipient_deletes_shares(self):
        task_share_model = self.get_task_share_model()
        task_share = task_share_model.objects.create(
            task=self.task,
            user=self.recipient,
            shared_by=self.owner,
        )

        self.recipient.delete()

        self.assertFalse(task_share_model.objects.filter(id=task_share.id).exists())

    def test_deleting_shared_by_deletes_shares(self):
        task_share_model = self.get_task_share_model()
        sharer = get_user_model().objects.create_user(
            email="sharer@example.com",
            password="strong-password-123",
        )
        task_share = task_share_model.objects.create(
            task=self.task,
            user=self.recipient,
            shared_by=sharer,
        )

        sharer.delete()

        self.assertTrue(Task.objects.filter(id=self.task.id).exists())
        self.assertFalse(task_share_model.objects.filter(id=task_share.id).exists())

    def test_full_clean_rejects_invalid_permission(self):
        task_share_model = self.get_task_share_model()
        task_share = task_share_model(
            task=self.task,
            user=self.recipient,
            permission="invalid",
            shared_by=self.owner,
        )

        with self.assertRaises(ValidationError):
            task_share.full_clean()

    def test_string_representation_identifies_task_and_user(self):
        task_share_model = self.get_task_share_model()
        task_share = task_share_model.objects.create(
            task=self.task,
            user=self.recipient,
            shared_by=self.owner,
        )

        self.assertEqual(
            str(task_share),
            "Write report shared with recipient@example.com",
        )

    def test_is_registered_in_admin(self):
        task_share_model = self.get_task_share_model()

        self.assertIn(task_share_model, admin.site._registry)
