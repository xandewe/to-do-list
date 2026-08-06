from django.apps import apps as django_apps
from rest_framework import status
from rest_framework.test import APITestCase

from apps.tasks.models import Task, TaskShare


class TaskStatusApiTests(APITestCase):
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

    def test_owner_can_complete_and_reopen_task(self):
        task = Task.objects.create(
            owner=self.owner,
            title="Finalizar relatorio",
            description="Enviar ate sexta-feira",
            priority=Task.Priority.HIGH,
            status=Task.Status.PENDING,
        )
        task_count = Task.objects.count()
        self.authenticate(self.owner)

        completed_response = self.client.patch(
            f"{self.list_url}{task.id}/",
            {"status": Task.Status.COMPLETED},
            format="json",
        )

        self.assertEqual(completed_response.status_code, status.HTTP_200_OK)
        self.assertEqual(completed_response.data["status"], Task.Status.COMPLETED)
        task.refresh_from_db()
        self.assertEqual(task.status, Task.Status.COMPLETED)

        repeated_response = self.client.patch(
            f"{self.list_url}{task.id}/",
            {"status": Task.Status.COMPLETED},
            format="json",
        )

        self.assertEqual(repeated_response.status_code, status.HTTP_200_OK)
        self.assertEqual(repeated_response.data["id"], str(task.id))
        task.refresh_from_db()
        self.assertEqual(task.status, Task.Status.COMPLETED)

        reopened_response = self.client.patch(
            f"{self.list_url}{task.id}/",
            {"status": Task.Status.PENDING},
            format="json",
        )

        self.assertEqual(reopened_response.status_code, status.HTTP_200_OK)
        self.assertEqual(reopened_response.data["status"], Task.Status.PENDING)
        task.refresh_from_db()
        self.assertEqual(task.status, Task.Status.PENDING)
        self.assertEqual(task.owner, self.owner)
        self.assertEqual(task.title, "Finalizar relatorio")
        self.assertEqual(task.description, "Enviar ate sexta-feira")
        self.assertEqual(task.priority, Task.Priority.HIGH)
        self.assertEqual(Task.objects.count(), task_count)

    def test_view_only_user_cannot_change_task_status(self):
        task = Task.objects.create(
            owner=self.owner,
            title="Tarefa protegida",
            description="Apenas leitura",
            priority=Task.Priority.LOW,
            status=Task.Status.PENDING,
        )
        TaskShare.objects.create(
            task=task,
            user=self.viewer,
            shared_by=self.owner,
            permission=TaskShare.Permission.VIEW,
        )
        self.authenticate(self.viewer)

        response = self.client.patch(
            f"{self.list_url}{task.id}/",
            {"status": Task.Status.COMPLETED},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        task.refresh_from_db()
        self.assertEqual(task.status, Task.Status.PENDING)
        self.assertEqual(task.owner, self.owner)
        self.assertEqual(task.title, "Tarefa protegida")
        self.assertEqual(task.description, "Apenas leitura")
        self.assertEqual(task.priority, Task.Priority.LOW)
        response_body = response.content.decode()
        self.assertNotIn("owner", response.data)
        self.assertNotIn(str(self.owner.id), response_body)
        self.assertNotIn(self.owner.email, response_body)
