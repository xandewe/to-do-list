from uuid import UUID

from django.apps import apps as django_apps
from rest_framework import status
from rest_framework.test import APITestCase


class UserRegistrationApiTests(APITestCase):
    url = "/api/v1/users/"
    password = "safe-unrelated-passphrase-482!"

    @staticmethod
    def get_user_model():
        return django_apps.get_model("accounts", "User")

    def valid_payload(self, **overrides):
        payload = {
            "email": "person@example.com",
            "password": self.password,
        }
        payload.update(overrides)
        return payload

    def test_registers_minimum_payload_anonymously(self):
        response = self.client.post(self.url, self.valid_payload(), format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            set(response.data),
            {"id", "email", "first_name", "last_name"},
        )
        UUID(response.data["id"])
        self.assertEqual(response.data["email"], "person@example.com")
        self.assertEqual(response.data["first_name"], "")
        self.assertEqual(response.data["last_name"], "")
        self.assertEqual(self.get_user_model().objects.count(), 1)

    def test_registers_complete_payload_and_hashes_password(self):
        response = self.client.post(
            self.url,
            self.valid_payload(
                email="Person@EXAMPLE.COM",
                first_name="Álex",
                last_name="Silva 日本",
            ),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            response.data,
            {
                "id": response.data["id"],
                "email": "Person@example.com",
                "first_name": "Álex",
                "last_name": "Silva 日本",
            },
        )
        user = self.get_user_model().objects.get()
        self.assertNotEqual(user.password, self.password)
        self.assertTrue(user.check_password(self.password))
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertTrue(user.is_active)

    def test_ignores_invalid_authorization_header(self):
        response = self.client.post(
            self.url,
            self.valid_payload(),
            format="json",
            HTTP_AUTHORIZATION="Bearer invalid-token",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_ignores_query_parameters(self):
        response = self.client.post(
            f"{self.url}?is_staff=true&page=2",
            self.valid_payload(),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = self.get_user_model().objects.get()
        self.assertFalse(user.is_staff)

    def test_duplicate_email_returns_bad_request_without_second_user(self):
        first_response = self.client.post(
            self.url,
            self.valid_payload(email="Person@EXAMPLE.COM"),
            format="json",
        )
        second_response = self.client.post(
            self.url,
            self.valid_payload(email="Person@example.com"),
            format="json",
        )

        self.assertEqual(first_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(second_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            [str(error) for error in second_response.data["email"]],
            ["Já existe uma conta com este e-mail."],
        )
        self.assertEqual(self.get_user_model().objects.count(), 1)

    def test_rejects_each_forbidden_field_without_applying_it(self):
        forbidden_fields = (
            "id",
            "username",
            "is_staff",
            "is_superuser",
            "is_active",
            "groups",
            "user_permissions",
            "date_joined",
            "last_login",
        )

        for field in forbidden_fields:
            with self.subTest(field=field):
                response = self.client.post(
                    self.url,
                    self.valid_payload(**{field: True}),
                    format="json",
                )
                self.assertEqual(
                    response.status_code,
                    status.HTTP_400_BAD_REQUEST,
                )
                self.assertEqual(
                    str(response.data["detail"]),
                    f"Campos não permitidos: {field}.",
                )

        self.assertEqual(self.get_user_model().objects.count(), 0)

    def test_rejects_unknown_fields_in_deterministic_order(self):
        response = self.client.post(
            self.url,
            self.valid_payload(z_field=True, a_field=True),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            str(response.data["detail"]),
            "Campos não permitidos: a_field, z_field.",
        )

    def test_empty_payload_reports_required_fields(self):
        response = self.client.post(self.url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)
        self.assertIn("password", response.data)

    def test_invalid_password_error_is_associated_with_password(self):
        response = self.client.post(
            self.url,
            self.valid_payload(password="short"),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)
        self.assertNotIn("email", response.data)

    def test_rejects_non_object_json_payloads(self):
        for payload in ([], "text", 123, None):
            with self.subTest(payload=payload):
                response = self.client.post(self.url, payload, format="json")
                self.assertEqual(
                    response.status_code,
                    status.HTTP_400_BAD_REQUEST,
                )

    def test_rejects_malformed_json(self):
        response = self.client.generic(
            "POST",
            self.url,
            data='{"email":',
            content_type="application/json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_rejects_unsupported_content_type(self):
        response = self.client.post(
            self.url,
            data="email=person@example.com",
            content_type="text/plain",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        )

    def test_non_post_methods_are_not_allowed(self):
        for method in ("get", "put", "patch", "delete"):
            with self.subTest(method=method):
                response = getattr(self.client, method)(
                    self.url,
                    self.valid_payload(),
                    format="json",
                )
                self.assertEqual(
                    response.status_code,
                    status.HTTP_405_METHOD_NOT_ALLOWED,
                )
