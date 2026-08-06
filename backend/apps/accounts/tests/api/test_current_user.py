from django.apps import apps as django_apps
from rest_framework import status
from rest_framework.test import APITestCase


class CurrentUserApiTests(APITestCase):
    url = "/api/v1/users/me/"
    login_url = "/api/v1/auth/token/"
    email = "person@example.com"
    password = "safe-unrelated-passphrase-482!"

    @classmethod
    def setUpTestData(cls):
        user_model = django_apps.get_model("accounts", "User")
        cls.user = user_model.objects.create_user(
            email=cls.email,
            password=cls.password,
            first_name="Alex",
            last_name="Silva",
        )

    def authenticate(self):
        response = self.client.post(
            self.login_url,
            {"email": self.email, "password": self.password},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {response.data['access']}"
        )

    def test_get_returns_authenticated_users_public_data(self):
        self.authenticate()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data,
            {
                "id": str(self.user.id),
                "email": self.email,
                "first_name": "Alex",
                "last_name": "Silva",
            },
        )

    def test_get_requires_authentication(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_patch_partially_updates_authenticated_user(self):
        self.authenticate()

        response = self.client.patch(
            self.url,
            {"first_name": "Alexandre"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data,
            {
                "id": str(self.user.id),
                "email": self.email,
                "first_name": "Alexandre",
                "last_name": "Silva",
            },
        )
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Alexandre")
        self.assertEqual(self.user.last_name, "Silva")
        self.assertEqual(self.user.email, self.email)

    def test_patch_rejects_forbidden_field_without_partial_update(self):
        self.authenticate()

        response = self.client.patch(
            self.url,
            {"first_name": "Changed", "email": "new@example.com"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            str(response.data["detail"]),
            "Campos não permitidos: email.",
        )
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Alex")
        self.assertEqual(self.user.email, self.email)
