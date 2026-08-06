from django.apps import apps as django_apps
from django.utils.dateparse import parse_datetime
from rest_framework import status
from rest_framework.test import APITestCase

from apps.tasks.models import Category, Task, TaskShare


class TaskUpdateApiTests(APITestCase):
    list_url = "/api/v1/tasks/"
    login_url = "/api/v1/auth/token/"
    password = "safe-unrelated-passphrase-482!"

    @classmethod
    def setUpTestData(cls):
        user_model = django_apps.get_model("accounts", "User")
        cls.owner = user_model.objects.create_user(
            email="owner@example.com",
            password=cls.password,
        )
        cls.editor = user_model.objects.create_user(
            email="editor@example.com",
            password=cls.password,
        )
        cls.viewer = user_model.objects.create_user(
            email="viewer@example.com",
            password=cls.password,
        )

    def authenticate(self, user):
        response = self.client.post(
            self.login_url,
            {"email": user.email, "password": self.password},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {response.data['access']}"
        )

    def test_shared_editor_updates_task(self):
        category = Category.objects.create(owner=self.owner, name="Trabalho")
        task = Task.objects.create(
            owner=self.owner,
            category=category,
            title="Titulo original",
            description="Descricao original",
            priority=Task.Priority.LOW,
        )
        TaskShare.objects.create(
            task=task,
            user=self.editor,
            shared_by=self.owner,
            permission=TaskShare.Permission.EDIT,
        )
        original_created_at = task.created_at
        original_updated_at = task.updated_at
        payload = {
            "title": "Titulo atualizado",
            "description": "Descricao atualizada",
            "status": Task.Status.COMPLETED,
            "priority": Task.Priority.HIGH,
            "due_date": "2026-08-10T18:00:00-03:00",
        }
        self.authenticate(self.editor)

        response = self.client.patch(
            f"{self.list_url}{task.id}/",
            payload,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        task.refresh_from_db()
        self.assertEqual(task.title, payload["title"])
        self.assertEqual(task.description, payload["description"])
        self.assertEqual(task.status, payload["status"])
        self.assertEqual(task.priority, payload["priority"])
        self.assertEqual(task.due_date, parse_datetime(payload["due_date"]))
        self.assertEqual(task.owner, self.owner)
        self.assertEqual(task.category, category)
        self.assertEqual(task.created_at, original_created_at)
        self.assertGreater(task.updated_at, original_updated_at)
        self.assertEqual(response.data["owner_id"], str(self.owner.id))
        self.assertEqual(response.data["category_id"], category.id)
        self.assertEqual(
            parse_datetime(response.data["created_at"]),
            original_created_at,
        )
        self.assertEqual(parse_datetime(response.data["updated_at"]), task.updated_at)
        self.assertEqual(
            response.data["access"],
            {"type": "shared", "permission": "edit"},
        )

    def test_shared_viewer_cannot_update_task(self):
        task = Task.objects.create(
            owner=self.owner,
            title="Titulo protegido",
        )
        TaskShare.objects.create(
            task=task,
            user=self.viewer,
            shared_by=self.owner,
            permission=TaskShare.Permission.VIEW,
        )
        original_updated_at = task.updated_at
        self.authenticate(self.viewer)

        response = self.client.patch(
            f"{self.list_url}{task.id}/",
            {"title": "Tentativa de alteracao"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        task.refresh_from_db()
        self.assertEqual(task.title, "Titulo protegido")
        self.assertEqual(task.updated_at, original_updated_at)
        response_body = response.content.decode()
        self.assertNotIn("owner", response.data)
        self.assertNotIn(str(self.owner.id), response_body)
        self.assertNotIn(self.owner.email, response_body)
