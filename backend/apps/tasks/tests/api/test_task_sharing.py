from django.apps import apps as django_apps
from rest_framework import status
from rest_framework.test import APITestCase

from apps.tasks.models import Task, TaskShare


class TaskSharingApiTests(APITestCase):
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
        cls.stranger = user_model.objects.create_user(
            email="stranger@example.com",
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

    def shares_url(self, task_id):
        return f"{self.list_url}{task_id}/shares/"

    def share_detail_url(self, task_id, share_id):
        return f"{self.list_url}{task_id}/shares/{share_id}/"

    # --- Listagem ---------------------------------------------------------

    def test_owner_lists_task_shares(self):
        task = Task.objects.create(owner=self.owner, title="Tarefa")
        share = TaskShare.objects.create(
            task=task,
            user=self.editor,
            shared_by=self.owner,
            permission=TaskShare.Permission.EDIT,
        )
        self.authenticate(self.owner)

        response = self.client.get(self.shares_url(task.id))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        result = response.data["results"][0]
        self.assertEqual(result["id"], str(share.id))
        self.assertEqual(result["user_email"], self.editor.email)
        self.assertEqual(result["permission"], TaskShare.Permission.EDIT)
        self.assertIn("created_at", result)

    def test_shared_user_cannot_list_shares(self):
        task = Task.objects.create(owner=self.owner, title="Tarefa")
        TaskShare.objects.create(
            task=task,
            user=self.editor,
            shared_by=self.owner,
            permission=TaskShare.Permission.EDIT,
        )
        self.authenticate(self.editor)

        response = self.client.get(self.shares_url(task.id))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_stranger_listing_shares_gets_not_found(self):
        task = Task.objects.create(owner=self.owner, title="Tarefa")
        self.authenticate(self.stranger)

        response = self.client.get(self.shares_url(task.id))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        body = response.content.decode()
        self.assertNotIn(self.owner.email, body)

    # --- Criação ----------------------------------------------------------

    def test_owner_shares_task_with_default_view_permission(self):
        task = Task.objects.create(owner=self.owner, title="Tarefa")
        self.authenticate(self.owner)

        response = self.client.post(
            self.shares_url(task.id),
            {"email": self.viewer.email},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["user_email"], self.viewer.email)
        self.assertEqual(
            response.data["permission"], TaskShare.Permission.VIEW
        )
        share = TaskShare.objects.get(id=response.data["id"])
        self.assertEqual(share.task, task)
        self.assertEqual(share.user, self.viewer)
        self.assertEqual(share.shared_by, self.owner)
        self.assertEqual(share.permission, TaskShare.Permission.VIEW)

    def test_owner_shares_task_with_edit_permission(self):
        task = Task.objects.create(owner=self.owner, title="Tarefa")
        self.authenticate(self.owner)

        response = self.client.post(
            self.shares_url(task.id),
            {"email": self.editor.email, "permission": "edit"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            response.data["permission"], TaskShare.Permission.EDIT
        )

    def test_sharing_with_unknown_email_returns_not_found(self):
        task = Task.objects.create(owner=self.owner, title="Tarefa")
        self.authenticate(self.owner)

        response = self.client.post(
            self.shares_url(task.id),
            {"email": "ghost@example.com"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(TaskShare.objects.filter(task=task).exists())

    def test_owner_cannot_share_task_with_self(self):
        task = Task.objects.create(owner=self.owner, title="Tarefa")
        self.authenticate(self.owner)

        response = self.client.post(
            self.shares_url(task.id),
            {"email": self.owner.email},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(TaskShare.objects.filter(task=task).exists())

    def test_cannot_share_duplicate_with_same_user(self):
        task = Task.objects.create(owner=self.owner, title="Tarefa")
        TaskShare.objects.create(
            task=task,
            user=self.editor,
            shared_by=self.owner,
            permission=TaskShare.Permission.VIEW,
        )
        self.authenticate(self.owner)

        response = self.client.post(
            self.shares_url(task.id),
            {"email": self.editor.email, "permission": "edit"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(TaskShare.objects.filter(task=task).count(), 1)

    def test_sharing_with_invalid_permission_is_rejected(self):
        task = Task.objects.create(owner=self.owner, title="Tarefa")
        self.authenticate(self.owner)

        response = self.client.post(
            self.shares_url(task.id),
            {"email": self.viewer.email, "permission": "admin"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(TaskShare.objects.filter(task=task).exists())

    def test_shared_editor_cannot_redistribute_task(self):
        task = Task.objects.create(owner=self.owner, title="Tarefa")
        TaskShare.objects.create(
            task=task,
            user=self.editor,
            shared_by=self.owner,
            permission=TaskShare.Permission.EDIT,
        )
        self.authenticate(self.editor)

        response = self.client.post(
            self.shares_url(task.id),
            {"email": self.stranger.email},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(
            TaskShare.objects.filter(task=task, user=self.stranger).exists()
        )

    def test_stranger_cannot_share_others_task(self):
        task = Task.objects.create(owner=self.owner, title="Tarefa")
        self.authenticate(self.stranger)

        response = self.client.post(
            self.shares_url(task.id),
            {"email": self.viewer.email},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(TaskShare.objects.filter(task=task).exists())

    # --- Alteração de permissão ------------------------------------------

    def test_owner_changes_share_permission(self):
        task = Task.objects.create(owner=self.owner, title="Tarefa")
        share = TaskShare.objects.create(
            task=task,
            user=self.viewer,
            shared_by=self.owner,
            permission=TaskShare.Permission.VIEW,
        )
        self.authenticate(self.owner)

        response = self.client.patch(
            self.share_detail_url(task.id, share.id),
            {"permission": "edit"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        share.refresh_from_db()
        self.assertEqual(share.permission, TaskShare.Permission.EDIT)

    def test_empty_permission_update_is_rejected(self):
        task = Task.objects.create(owner=self.owner, title="Tarefa")
        share = TaskShare.objects.create(
            task=task,
            user=self.viewer,
            shared_by=self.owner,
            permission=TaskShare.Permission.VIEW,
        )
        self.authenticate(self.owner)

        response = self.client.patch(
            self.share_detail_url(task.id, share.id),
            {},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        share.refresh_from_db()
        self.assertEqual(share.permission, TaskShare.Permission.VIEW)

    def test_shared_editor_cannot_change_permission(self):
        task = Task.objects.create(owner=self.owner, title="Tarefa")
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
        self.authenticate(self.editor)

        response = self.client.patch(
            self.share_detail_url(task.id, viewer_share.id),
            {"permission": "edit"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        viewer_share.refresh_from_db()
        self.assertEqual(
            viewer_share.permission, TaskShare.Permission.VIEW
        )
        self.assertTrue(
            TaskShare.objects.filter(id=editor_share.id).exists()
        )

    # --- Remoção / revogação ---------------------------------------------

    def test_owner_removes_share_and_revokes_access_immediately(self):
        task = Task.objects.create(owner=self.owner, title="Tarefa")
        share = TaskShare.objects.create(
            task=task,
            user=self.viewer,
            shared_by=self.owner,
            permission=TaskShare.Permission.VIEW,
        )

        self.authenticate(self.viewer)
        before = self.client.get(f"{self.list_url}{task.id}/")
        self.assertEqual(before.status_code, status.HTTP_200_OK)

        self.authenticate(self.owner)
        response = self.client.delete(
            self.share_detail_url(task.id, share.id)
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.content, b"")
        self.assertFalse(TaskShare.objects.filter(id=share.id).exists())

        self.authenticate(self.viewer)
        after = self.client.get(f"{self.list_url}{task.id}/")
        self.assertEqual(after.status_code, status.HTTP_404_NOT_FOUND)

    def test_shared_editor_cannot_remove_share(self):
        task = Task.objects.create(owner=self.owner, title="Tarefa")
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
        self.authenticate(self.editor)

        response = self.client.delete(
            self.share_detail_url(task.id, viewer_share.id)
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(
            TaskShare.objects.filter(id=viewer_share.id).exists()
        )
        self.assertTrue(
            TaskShare.objects.filter(id=editor_share.id).exists()
        )
