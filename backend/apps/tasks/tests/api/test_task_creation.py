from django.apps import apps as django_apps
from django.utils.dateparse import parse_datetime
from rest_framework import status
from rest_framework.test import APITestCase

from apps.tasks.models import Category, Task


class TaskCreationApiTests(APITestCase):
    list_url = "/api/v1/tasks/"
    login_url = "/api/v1/auth/token/"
    password = "safe-unrelated-passphrase-482!"

    @classmethod
    def setUpTestData(cls):
        user_model = django_apps.get_model("accounts", "User")
        cls.user = user_model.objects.create_user(
            email="owner@example.com",
            password=cls.password,
        )
        cls.other_user = user_model.objects.create_user(
            email="other@example.com",
            password=cls.password,
        )

    def authenticate(self):
        response = self.client.post(
            self.login_url,
            {"email": self.user.email, "password": self.password},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {response.data['access']}"
        )

    def test_create_task_with_owned_category(self):
        category = Category.objects.create(owner=self.user, name="Trabalho")
        self.authenticate()
        payload = {
            "category_id": str(category.id),
            "title": "Preparar relatorio",
            "description": "Consolidar resultados do mes",
            "status": "pending",
            "priority": "high",
            "due_date": "2026-08-10T18:00:00-03:00",
        }

        response = self.client.post(self.list_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Task.objects.count(), 1)
        task = Task.objects.get()
        self.assertEqual(task.owner, self.user)
        self.assertEqual(task.category, category)
        self.assertEqual(task.title, payload["title"])
        self.assertEqual(task.description, payload["description"])
        self.assertEqual(task.status, payload["status"])
        self.assertEqual(task.priority, payload["priority"])
        self.assertEqual(task.due_date, parse_datetime(payload["due_date"]))
        self.assertEqual(
            set(response.data),
            {
                "id",
                "owner_id",
                "category_id",
                "title",
                "description",
                "status",
                "priority",
                "due_date",
                "created_at",
                "updated_at",
                "access",
            },
        )
        self.assertEqual(response.data["owner_id"], str(self.user.id))
        self.assertEqual(response.data["category_id"], category.id)
        self.assertEqual(
            parse_datetime(response.data["due_date"]),
            parse_datetime(payload["due_date"]),
        )
        self.assertIsNotNone(response.data["created_at"])
        self.assertIsNotNone(response.data["updated_at"])
        self.assertEqual(
            response.data["access"],
            {"type": "owned", "permission": "owner"},
        )
        self.assertNotIn("owner", response.data)

    def test_create_task_rejects_another_users_category(self):
        category = Category.objects.create(owner=self.other_user, name="Alheia")
        original_category = (
            category.owner_id,
            category.name,
            category.description,
            category.color,
        )
        self.authenticate()

        response = self.client.post(
            self.list_url,
            {
                "category_id": str(category.id),
                "title": "Preparar relatorio",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("category_id", response.data)
        self.assertEqual(Task.objects.count(), 0)
        category.refresh_from_db()
        self.assertEqual(
            (
                category.owner_id,
                category.name,
                category.description,
                category.color,
            ),
            original_category,
        )
        self.assertNotIn(self.other_user.email, str(response.data))
        self.assertNotIn(str(self.other_user.id), str(response.data))
