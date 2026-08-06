from django.apps import apps as django_apps
from rest_framework import status
from rest_framework.test import APITestCase

from apps.tasks.models import Category, Task


class CategoryApiTests(APITestCase):
    list_url = "/api/v1/categories/"
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

    @staticmethod
    def detail_url(category):
        return f"/api/v1/categories/{category.id}/"

    def test_list_returns_paginated_ordered_categories_for_authenticated_user(self):
        Category.objects.create(owner=self.user, name="Trabalho", color="#336699")
        Category.objects.create(owner=self.user, name="Pessoal")
        Category.objects.create(owner=self.other_user, name="Alheia")
        self.authenticate()

        response = self.client.get(self.list_url, {"page_size": 1})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)
        self.assertIsNotNone(response.data["next"])
        self.assertIsNone(response.data["previous"])
        self.assertEqual([item["name"] for item in response.data["results"]], ["Pessoal"])
        self.assertNotIn("owner", response.data["results"][0])

    def test_list_requires_authentication(self):
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_assigns_authenticated_user_and_returns_public_fields(self):
        self.authenticate()

        response = self.client.post(
            self.list_url,
            {
                "name": "Trabalho",
                "description": "Atividades profissionais",
                "color": "#336699",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        category = Category.objects.get()
        self.assertEqual(category.owner, self.user)
        self.assertEqual(category.name, "Trabalho")
        self.assertEqual(category.description, "Atividades profissionais")
        self.assertEqual(category.color, "#336699")
        self.assertEqual(
            set(response.data),
            {"id", "name", "description", "color", "created_at", "updated_at"},
        )

    def test_create_rejects_duplicate_name_for_authenticated_user(self):
        Category.objects.create(owner=self.user, name="Trabalho")
        self.authenticate()

        response = self.client.post(
            self.list_url,
            {"name": "Trabalho"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            str(response.data["name"][0]),
            "Já existe uma categoria com este nome.",
        )
        self.assertEqual(Category.objects.filter(owner=self.user).count(), 1)

    def test_retrieve_returns_authenticated_users_category(self):
        category = Category.objects.create(
            owner=self.user,
            name="Trabalho",
            description="Atividades profissionais",
            color="#336699",
        )
        self.authenticate()

        response = self.client.get(self.detail_url(category))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], str(category.id))
        self.assertEqual(response.data["name"], "Trabalho")
        self.assertEqual(response.data["description"], "Atividades profissionais")
        self.assertEqual(response.data["color"], "#336699")
        self.assertNotIn("owner", response.data)

    def test_retrieve_hides_another_users_category(self):
        category = Category.objects.create(owner=self.other_user, name="Alheia")
        self.authenticate()

        response = self.client.get(self.detail_url(category))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_patch_partially_updates_authenticated_users_category(self):
        category = Category.objects.create(
            owner=self.user,
            name="Trabalho",
            description="Preservar",
            color="#336699",
        )
        self.authenticate()

        response = self.client.patch(
            self.detail_url(category),
            {"name": "Projetos", "color": "#AA5500"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        category.refresh_from_db()
        self.assertEqual(category.name, "Projetos")
        self.assertEqual(category.color, "#AA5500")
        self.assertEqual(category.description, "Preservar")

    def test_patch_rejects_invalid_color_without_changes(self):
        category = Category.objects.create(
            owner=self.user,
            name="Trabalho",
            description="Preservar",
            color="#336699",
        )
        self.authenticate()

        response = self.client.patch(
            self.detail_url(category),
            {"name": "Projetos", "color": "#FFF"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        category.refresh_from_db()
        self.assertEqual(category.name, "Trabalho")
        self.assertEqual(category.color, "#336699")

    def test_delete_removes_category_and_keeps_task_without_category(self):
        category = Category.objects.create(owner=self.user, name="Trabalho")
        task = Task.objects.create(
            owner=self.user,
            category=category,
            title="Entregar relatório",
        )
        self.authenticate()

        response = self.client.delete(self.detail_url(category))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Category.objects.filter(id=category.id).exists())
        task.refresh_from_db()
        self.assertIsNone(task.category)

    def test_delete_hides_and_preserves_another_users_category(self):
        category = Category.objects.create(owner=self.other_user, name="Alheia")
        self.authenticate()

        response = self.client.delete(self.detail_url(category))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Category.objects.filter(id=category.id).exists())
