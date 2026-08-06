from django.apps import apps as django_apps
from rest_framework import status
from rest_framework.test import APITestCase

from apps.tasks.models import Category, Task, TaskShare


class TaskFilteringApiTests(APITestCase):
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
        cls.work = Category.objects.create(owner=cls.user, name="Trabalho")
        cls.home = Category.objects.create(owner=cls.user, name="Casa")

        cls.pending_work = Task.objects.create(
            owner=cls.user,
            category=cls.work,
            title="Pendente trabalho",
            status=Task.Status.PENDING,
        )
        cls.completed_work = Task.objects.create(
            owner=cls.user,
            category=cls.work,
            title="Concluida trabalho",
            status=Task.Status.COMPLETED,
        )
        cls.pending_home = Task.objects.create(
            owner=cls.user,
            category=cls.home,
            title="Pendente casa",
            status=Task.Status.PENDING,
        )
        cls.uncategorized = Task.objects.create(
            owner=cls.user,
            title="Sem categoria",
            status=Task.Status.COMPLETED,
        )

    def authenticate(self, user=None):
        user = user or self.user
        response = self.client.post(
            self.login_url,
            {"email": user.email, "password": self.password},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {response.data['access']}"
        )

    def result_ids(self, response):
        return {item["id"] for item in response.data["results"]}

    def test_filter_by_status(self):
        self.authenticate()

        response = self.client.get(self.list_url, {"status": "pending"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)
        self.assertEqual(
            self.result_ids(response),
            {str(self.pending_work.id), str(self.pending_home.id)},
        )

    def test_filter_by_category(self):
        self.authenticate()

        response = self.client.get(
            self.list_url, {"category": str(self.work.id)}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)
        self.assertEqual(
            self.result_ids(response),
            {str(self.pending_work.id), str(self.completed_work.id)},
        )

    def test_filter_by_status_and_category_combined(self):
        self.authenticate()

        response = self.client.get(
            self.list_url,
            {"status": "completed", "category": str(self.work.id)},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(
            self.result_ids(response), {str(self.completed_work.id)}
        )

    def test_invalid_status_is_ignored(self):
        self.authenticate()

        response = self.client.get(self.list_url, {"status": "banana"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 4)

    def test_invalid_category_is_ignored(self):
        self.authenticate()

        response = self.client.get(self.list_url, {"category": "not-a-uuid"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 4)

    def test_filter_only_applies_to_accessible_tasks(self):
        shared_pending = Task.objects.create(
            owner=self.other_user,
            title="Compartilhada pendente",
            status=Task.Status.PENDING,
        )
        Task.objects.create(
            owner=self.other_user,
            title="Privada pendente",
            status=Task.Status.PENDING,
        )
        TaskShare.objects.create(
            task=shared_pending,
            user=self.user,
            shared_by=self.other_user,
            permission=TaskShare.Permission.VIEW,
        )
        self.authenticate()

        response = self.client.get(self.list_url, {"status": "pending"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 3)
        self.assertIn(str(shared_pending.id), self.result_ids(response))
