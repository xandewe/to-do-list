from datetime import timedelta

from django.apps import apps as django_apps
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.tasks.models import Task, TaskShare


class TaskReadingApiTests(APITestCase):
    list_url = "/api/v1/tasks/"
    login_url = "/api/v1/auth/token/"
    password = "safe-unrelated-passphrase-482!"

    @classmethod
    def setUpTestData(cls):
        user_model = django_apps.get_model("accounts", "User")
        cls.user = user_model.objects.create_user(
            email="reader@example.com",
            password=cls.password,
        )
        cls.other_user = user_model.objects.create_user(
            email="task-owner@example.com",
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

    def test_list_returns_owned_and_shared_tasks(self):
        owned_task = Task.objects.create(owner=self.user, title="Minha tarefa")
        shared_task = Task.objects.create(
            owner=self.other_user,
            title="Tarefa compartilhada",
        )
        private_task = Task.objects.create(
            owner=self.other_user,
            title="Tarefa privada",
        )
        TaskShare.objects.create(
            task=shared_task,
            user=self.user,
            shared_by=self.other_user,
            permission=TaskShare.Permission.VIEW,
        )
        now = timezone.now()
        Task.objects.filter(id=owned_task.id).update(created_at=now)
        Task.objects.filter(id=shared_task.id).update(
            created_at=now + timedelta(seconds=1)
        )
        self.authenticate()

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            set(response.data),
            {"count", "next", "previous", "results"},
        )
        self.assertEqual(response.data["count"], 2)
        self.assertIsNone(response.data["next"])
        self.assertIsNone(response.data["previous"])
        results = response.data["results"]
        self.assertEqual(
            [item["id"] for item in results],
            [str(shared_task.id), str(owned_task.id)],
        )
        self.assertEqual(len({item["id"] for item in results}), 2)
        self.assertNotIn(str(private_task.id), {item["id"] for item in results})
        self.assertEqual(
            results[0]["access"],
            {"type": "shared", "permission": "view"},
        )
        self.assertEqual(
            results[1]["access"],
            {"type": "owned", "permission": "owner"},
        )
        for item in results:
            self.assertNotIn("owner", item)
            self.assertNotIn("shares", item)
            self.assertNotIn("shared_by", item)
            self.assertNotIn("email", item)

    def test_list_requires_authentication(self):
        task = Task.objects.create(owner=self.user, title="Tarefa protegida")

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertNotIn(str(task.id), str(response.data))
        self.assertNotIn(task.title, str(response.data))

    def test_retrieve_returns_shared_task(self):
        task = Task.objects.create(
            owner=self.other_user,
            title="Tarefa compartilhada",
            description="Detalhes visiveis",
            priority=Task.Priority.HIGH,
        )
        TaskShare.objects.create(
            task=task,
            user=self.user,
            shared_by=self.other_user,
            permission=TaskShare.Permission.VIEW,
        )
        self.authenticate()

        response = self.client.get(f"{self.list_url}{task.id}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], str(task.id))
        self.assertEqual(response.data["owner_id"], str(self.other_user.id))
        self.assertEqual(response.data["title"], task.title)
        self.assertEqual(response.data["description"], task.description)
        self.assertEqual(response.data["priority"], Task.Priority.HIGH)
        self.assertEqual(
            response.data["access"],
            {"type": "shared", "permission": "view"},
        )
        self.assertNotIn("owner", response.data)
        self.assertNotIn("shares", response.data)
        self.assertNotIn("shared_by", response.data)
        self.assertNotIn("email", response.data)

    def test_retrieve_hides_private_task(self):
        task = Task.objects.create(
            owner=self.other_user,
            title="Segredo de outro usuario",
        )
        self.authenticate()

        response = self.client.get(f"{self.list_url}{task.id}/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response["Content-Type"], "application/json")
        response_body = response.content.decode()
        self.assertNotIn(str(task.id), response_body)
        self.assertNotIn(task.title, response_body)
        self.assertNotIn(str(self.other_user.id), response_body)
