from django.apps import apps as django_apps
from rest_framework import status
from rest_framework.test import APITestCase

from apps.tasks.models import Task, TaskShare


class MvpFlowApiTests(APITestCase):
    """Fluxo ponta-a-ponta exercitando apenas os endpoints HTTP públicos."""

    tasks_url = "/api/v1/tasks/"
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

    def test_full_sharing_lifecycle(self):
        # 1. O proprietário cria uma tarefa.
        self.authenticate(self.owner)
        create = self.client.post(
            self.tasks_url,
            {"title": "Preparar relatório"},
            format="json",
        )
        self.assertEqual(create.status_code, status.HTTP_201_CREATED)
        task_id = create.data["id"]
        self.assertEqual(
            create.data["access"], {"type": "owned", "permission": "owner"}
        )

        # 2. O proprietário compartilha com permissão de edição.
        share = self.client.post(
            f"{self.tasks_url}{task_id}/shares/",
            {"email": self.editor.email, "permission": "edit"},
            format="json",
        )
        self.assertEqual(share.status_code, status.HTTP_201_CREATED)
        share_id = share.data["id"]
        self.assertEqual(share.data["user_email"], self.editor.email)

        # 3. O editor enxerga a tarefa na própria listagem como compartilhada.
        self.authenticate(self.editor)
        listing = self.client.get(self.tasks_url)
        self.assertEqual(listing.status_code, status.HTTP_200_OK)
        shared = [t for t in listing.data["results"] if t["id"] == task_id]
        self.assertEqual(len(shared), 1)
        self.assertEqual(
            shared[0]["access"], {"type": "shared", "permission": "edit"}
        )

        # 4. O editor conclui a tarefa (conteúdo/andamento permitido).
        edit = self.client.patch(
            f"{self.tasks_url}{task_id}/",
            {"status": "completed"},
            format="json",
        )
        self.assertEqual(edit.status_code, status.HTTP_200_OK)
        self.assertEqual(edit.data["status"], "completed")

        # 5. O proprietário revoga o compartilhamento.
        self.authenticate(self.owner)
        revoke = self.client.delete(
            f"{self.tasks_url}{task_id}/shares/{share_id}/"
        )
        self.assertEqual(revoke.status_code, status.HTTP_204_NO_CONTENT)

        # 6. O acesso do ex-editor é revogado imediatamente.
        self.authenticate(self.editor)
        after_read = self.client.get(f"{self.tasks_url}{task_id}/")
        self.assertEqual(after_read.status_code, status.HTTP_404_NOT_FOUND)
        after_edit = self.client.patch(
            f"{self.tasks_url}{task_id}/",
            {"status": "pending"},
            format="json",
        )
        self.assertEqual(after_edit.status_code, status.HTTP_404_NOT_FOUND)

        # A tarefa continua existindo e concluída para o proprietário.
        task = Task.objects.get(id=task_id)
        self.assertEqual(task.status, Task.Status.COMPLETED)
        self.assertFalse(TaskShare.objects.filter(id=share_id).exists())

    def test_viewer_cannot_edit_shared_task(self):
        # O proprietário cria e compartilha somente para leitura.
        self.authenticate(self.owner)
        create = self.client.post(
            self.tasks_url,
            {"title": "Somente leitura"},
            format="json",
        )
        task_id = create.data["id"]
        self.client.post(
            f"{self.tasks_url}{task_id}/shares/",
            {"email": self.viewer.email, "permission": "view"},
            format="json",
        )

        # O leitor consegue ler, mas não editar.
        self.authenticate(self.viewer)
        read = self.client.get(f"{self.tasks_url}{task_id}/")
        self.assertEqual(read.status_code, status.HTTP_200_OK)
        self.assertEqual(
            read.data["access"], {"type": "shared", "permission": "view"}
        )

        edit = self.client.patch(
            f"{self.tasks_url}{task_id}/",
            {"title": "Tentativa de alteração"},
            format="json",
        )
        self.assertEqual(edit.status_code, status.HTTP_403_FORBIDDEN)

    def test_filtering_within_shared_and_owned_tasks(self):
        # O proprietário cria duas tarefas em estados diferentes e compartilha
        # a concluída com o leitor.
        self.authenticate(self.owner)
        pending = self.client.post(
            self.tasks_url,
            {"title": "Pendente"},
            format="json",
        )
        completed = self.client.post(
            self.tasks_url,
            {"title": "Concluída", "status": "completed"},
            format="json",
        )
        completed_id = completed.data["id"]
        self.client.post(
            f"{self.tasks_url}{completed_id}/shares/",
            {"email": self.viewer.email, "permission": "view"},
            format="json",
        )

        # O leitor filtra por status e vê apenas a tarefa compartilhada.
        self.authenticate(self.viewer)
        filtered = self.client.get(self.tasks_url, {"status": "completed"})
        self.assertEqual(filtered.status_code, status.HTTP_200_OK)
        ids = {t["id"] for t in filtered.data["results"]}
        self.assertEqual(ids, {completed_id})
        self.assertNotIn(pending.data["id"], ids)
