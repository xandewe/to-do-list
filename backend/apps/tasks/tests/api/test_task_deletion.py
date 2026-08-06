from django.apps import apps as django_apps
from rest_framework import status
from rest_framework.test import APITestCase

from apps.tasks.models import Category, Task, TaskShare


class TaskDeletionApiTests(APITestCase):
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

    def test_owner_deletes_task_and_cascades_shares(self):
        category = Category.objects.create(owner=self.owner, name="Trabalho")
        task = Task.objects.create(
            owner=self.owner,
            category=category,
            title="Remover esta tarefa",
        )
        other_task = Task.objects.create(
            owner=self.owner,
            category=category,
            title="Preservar esta tarefa",
        )
        editor_share = TaskShare.objects.create(
            task=task,
            user=self.editor,
            shared_by=self.owner,
            permission=TaskShare.Permission.EDIT,
        )
        viewer_share = TaskShare.objects.create(
            task=task,
            user=self.viewer,
            shared_by=self.owner,
            permission=TaskShare.Permission.VIEW,
        )
        self.authenticate(self.owner)

        response = self.client.delete(f"{self.list_url}{task.id}/")

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.content, b"")
        self.assertFalse(Task.objects.filter(id=task.id).exists())
        self.assertFalse(TaskShare.objects.filter(id=editor_share.id).exists())
        self.assertFalse(TaskShare.objects.filter(id=viewer_share.id).exists())
        self.assertTrue(Category.objects.filter(id=category.id).exists())
        self.assertTrue(Task.objects.filter(id=other_task.id).exists())

    def test_shared_editor_cannot_delete_task(self):
        task = Task.objects.create(
            owner=self.owner,
            title="Tarefa compartilhada protegida",
        )
        share = TaskShare.objects.create(
            task=task,
            user=self.editor,
            shared_by=self.owner,
            permission=TaskShare.Permission.EDIT,
        )
        self.authenticate(self.editor)

        response = self.client.delete(f"{self.list_url}{task.id}/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Task.objects.filter(id=task.id).exists())
        self.assertTrue(TaskShare.objects.filter(id=share.id).exists())
        response_body = response.content.decode()
        self.assertNotIn(str(self.owner.id), response_body)
        self.assertNotIn(self.owner.email, response_body)
        self.assertNotIn("owner", response.data)
