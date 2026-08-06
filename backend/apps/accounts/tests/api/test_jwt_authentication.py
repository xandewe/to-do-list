from datetime import timedelta

from django.apps import apps as django_apps
from django.test import override_settings
from django.urls import include, path
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APITestCase
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken


class ProtectedEndpointView(APIView):
    def get(self, request):
        return Response({"user_id": str(request.user.id)})


urlpatterns = [
    path("api/", include("health.urls")),
    path("api/v1/", include("config.api_urls")),
    path("test/protected/", ProtectedEndpointView.as_view()),
]


class JwtLoginApiTests(APITestCase):
    url = "/api/v1/auth/token/"
    email = "person@example.com"
    password = "safe-unrelated-passphrase-482!"

    @classmethod
    def setUpTestData(cls):
        user_model = django_apps.get_model("accounts", "User")
        cls.user = user_model.objects.create_user(
            email=cls.email,
            password=cls.password,
        )

    def test_login_with_email_returns_access_and_refresh_tokens(self):
        response = self.client.post(
            self.url,
            {"email": self.email, "password": self.password},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(set(response.data), {"access", "refresh"})
        self.assertTrue(response.data["access"])
        self.assertTrue(response.data["refresh"])
        self.assertIsInstance(response.data["access"], str)
        self.assertIsInstance(response.data["refresh"], str)

    def test_login_tokens_have_standard_claims_and_expected_lifetimes(self):
        response = self.client.post(
            self.url,
            {"email": self.email, "password": self.password},
            format="json",
        )

        access = AccessToken(response.data["access"])
        refresh = RefreshToken(response.data["refresh"])

        for token, token_type, lifetime_seconds in (
            (access, "access", 15 * 60),
            (refresh, "refresh", 7 * 24 * 60 * 60),
        ):
            with self.subTest(token_type=token_type):
                self.assertEqual(token["token_type"], token_type)
                self.assertEqual(token["user_id"], str(self.user.id))
                self.assertEqual(token["exp"] - token["iat"], lifetime_seconds)
                self.assertTrue(token["jti"])
                self.assertNotIn("email", token.payload)
                self.assertNotIn("password", token.payload)
                self.assertNotIn("signing_key", token.payload)

    def test_invalid_credentials_and_inactive_user_share_error_shape(self):
        user_model = django_apps.get_model("accounts", "User")
        inactive_user = user_model.objects.create_user(
            email="inactive@example.com",
            password=self.password,
            is_active=False,
        )
        attempts = (
            {"email": "missing@example.com", "password": self.password},
            {"email": self.email, "password": "wrong-password"},
            {"email": inactive_user.email, "password": self.password},
        )

        responses = [
            self.client.post(self.url, payload, format="json")
            for payload in attempts
        ]

        for response in responses:
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
            self.assertEqual(set(response.data), {"detail"})
        self.assertEqual(
            [str(response.data["detail"]) for response in responses],
            [str(responses[0].data["detail"])] * len(responses),
        )

    def test_login_requires_email_and_password(self):
        for payload, missing_field in (
            ({"password": self.password}, "email"),
            ({"email": self.email}, "password"),
        ):
            with self.subTest(missing_field=missing_field):
                response = self.client.post(self.url, payload, format="json")
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn(missing_field, response.data)

        empty_response = self.client.post(self.url, {}, format="json")
        self.assertEqual(empty_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", empty_response.data)
        self.assertIn("password", empty_response.data)

    def test_login_rejects_malformed_json(self):
        response = self.client.generic(
            "POST",
            self.url,
            data='{"email":',
            content_type="application/json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_allows_only_post(self):
        for method in ("get", "put", "patch", "delete"):
            with self.subTest(method=method):
                response = getattr(self.client, method)(self.url, format="json")
                self.assertEqual(
                    response.status_code,
                    status.HTTP_405_METHOD_NOT_ALLOWED,
                )


@override_settings(ROOT_URLCONF=__name__)
class JwtLifecycleApiTests(APITestCase):
    login_url = "/api/v1/auth/token/"
    refresh_url = "/api/v1/auth/token/refresh/"
    blacklist_url = "/api/v1/auth/token/blacklist/"
    protected_url = "/test/protected/"
    email = "person@example.com"
    password = "safe-unrelated-passphrase-482!"

    @classmethod
    def setUpTestData(cls):
        user_model = django_apps.get_model("accounts", "User")
        cls.user = user_model.objects.create_user(
            email=cls.email,
            password=cls.password,
        )

    def login(self):
        response = self.client.post(
            self.login_url,
            {"email": self.email, "password": self.password},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return response.data

    @staticmethod
    def tamper(token):
        header, payload, signature = token.split(".")
        replacement = "a" if signature[0] != "a" else "b"
        return f"{header}.{payload}.{replacement}{signature[1:]}"

    def bearer_get(self, token, prefix="Bearer"):
        return self.client.get(
            self.protected_url,
            HTTP_AUTHORIZATION=f"{prefix} {token}",
        )

    def test_refresh_rotates_tokens_and_blacklists_previous_refresh(self):
        tokens = self.login()

        response = self.client.post(
            self.refresh_url,
            {"refresh": tokens["refresh"]},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(set(response.data), {"access", "refresh"})
        self.assertNotEqual(response.data["access"], tokens["access"])
        self.assertNotEqual(response.data["refresh"], tokens["refresh"])

        reused_response = self.client.post(
            self.refresh_url,
            {"refresh": tokens["refresh"]},
            format="json",
        )
        self.assertEqual(reused_response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_rotated_refresh_can_be_used_again(self):
        tokens = self.login()
        first_rotation = self.client.post(
            self.refresh_url,
            {"refresh": tokens["refresh"]},
            format="json",
        )

        second_rotation = self.client.post(
            self.refresh_url,
            {"refresh": first_rotation.data["refresh"]},
            format="json",
        )

        self.assertEqual(second_rotation.status_code, status.HTTP_200_OK)
        self.assertNotEqual(
            second_rotation.data["refresh"],
            first_rotation.data["refresh"],
        )

    def test_refresh_rejects_wrong_invalid_expired_and_missing_tokens(self):
        tokens = self.login()
        expired_refresh = RefreshToken.for_user(self.user)
        expired_refresh.set_exp(lifetime=timedelta(seconds=-1))
        attempts = (
            ({"refresh": tokens["access"]}, status.HTTP_401_UNAUTHORIZED),
            (
                {"refresh": self.tamper(tokens["refresh"])},
                status.HTTP_401_UNAUTHORIZED,
            ),
            ({"refresh": str(expired_refresh)}, status.HTTP_401_UNAUTHORIZED),
            ({}, status.HTTP_400_BAD_REQUEST),
        )

        for payload, expected_status in attempts:
            with self.subTest(expected_status=expected_status, payload=payload):
                response = self.client.post(
                    self.refresh_url,
                    payload,
                    format="json",
                )
                self.assertEqual(response.status_code, expected_status)

    def test_refresh_returns_an_access_token_that_authenticates(self):
        tokens = self.login()
        refresh_response = self.client.post(
            self.refresh_url,
            {"refresh": tokens["refresh"]},
            format="json",
        )

        response = self.bearer_get(refresh_response.data["access"])

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"user_id": str(self.user.id)})

    def test_refresh_allows_only_post(self):
        tokens = self.login()
        for method in ("get", "put", "patch", "delete"):
            with self.subTest(method=method):
                response = getattr(self.client, method)(
                    self.refresh_url,
                    {"refresh": tokens["refresh"]},
                    format="json",
                )
                self.assertEqual(
                    response.status_code,
                    status.HTTP_405_METHOD_NOT_ALLOWED,
                )

    def test_blacklist_revokes_refresh_but_not_existing_access(self):
        tokens = self.login()

        response = self.client.post(
            self.blacklist_url,
            {"refresh": tokens["refresh"]},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {})
        refresh_response = self.client.post(
            self.refresh_url,
            {"refresh": tokens["refresh"]},
            format="json",
        )
        self.assertEqual(
            refresh_response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )
        self.assertEqual(
            self.bearer_get(tokens["access"]).status_code,
            status.HTTP_200_OK,
        )

    def test_blacklist_rejects_tampered_and_missing_tokens(self):
        tokens = self.login()
        attempts = (
            ({"refresh": tokens["access"]}, status.HTTP_401_UNAUTHORIZED),
            (
                {"refresh": self.tamper(tokens["refresh"])},
                status.HTTP_401_UNAUTHORIZED,
            ),
            ({}, status.HTTP_400_BAD_REQUEST),
        )

        for payload, expected_status in attempts:
            with self.subTest(expected_status=expected_status):
                response = self.client.post(
                    self.blacklist_url,
                    payload,
                    format="json",
                )
                self.assertEqual(response.status_code, expected_status)

    def test_blacklist_rejects_an_already_revoked_refresh(self):
        tokens = self.login()
        payload = {"refresh": tokens["refresh"]}
        first_response = self.client.post(
            self.blacklist_url,
            payload,
            format="json",
        )

        second_response = self.client.post(
            self.blacklist_url,
            payload,
            format="json",
        )

        self.assertEqual(first_response.status_code, status.HTTP_200_OK)
        self.assertEqual(second_response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_blacklist_allows_only_post(self):
        tokens = self.login()
        for method in ("get", "put", "patch", "delete"):
            with self.subTest(method=method):
                response = getattr(self.client, method)(
                    self.blacklist_url,
                    {"refresh": tokens["refresh"]},
                    format="json",
                )
                self.assertEqual(
                    response.status_code,
                    status.HTTP_405_METHOD_NOT_ALLOWED,
                )

    def test_protected_endpoint_requires_a_valid_access_bearer(self):
        tokens = self.login()
        expired_access = AccessToken.for_user(self.user)
        expired_access.set_exp(lifetime=timedelta(seconds=-1))
        attempts = (
            ({}, status.HTTP_401_UNAUTHORIZED),
            (
                {"HTTP_AUTHORIZATION": f"Token {tokens['access']}"},
                status.HTTP_401_UNAUTHORIZED,
            ),
            (
                {"HTTP_AUTHORIZATION": f"Bearer {self.tamper(tokens['access'])}"},
                status.HTTP_401_UNAUTHORIZED,
            ),
            (
                {"HTTP_AUTHORIZATION": f"Bearer {expired_access}"},
                status.HTTP_401_UNAUTHORIZED,
            ),
            (
                {"HTTP_AUTHORIZATION": f"Bearer {tokens['refresh']}"},
                status.HTTP_401_UNAUTHORIZED,
            ),
            (
                {"HTTP_AUTHORIZATION": f"Bearer {tokens['access']}"},
                status.HTTP_200_OK,
            ),
        )

        for headers, expected_status in attempts:
            with self.subTest(expected_status=expected_status, headers=headers):
                response = self.client.get(self.protected_url, **headers)
                self.assertEqual(response.status_code, expected_status)

    def test_access_token_identifies_its_own_user(self):
        user_model = django_apps.get_model("accounts", "User")
        other_user = user_model.objects.create_user(
            email="other@example.com",
            password=self.password,
        )

        own_response = self.bearer_get(AccessToken.for_user(self.user))
        other_response = self.bearer_get(AccessToken.for_user(other_user))

        self.assertEqual(own_response.data, {"user_id": str(self.user.id)})
        self.assertEqual(other_response.data, {"user_id": str(other_user.id)})
        self.assertNotEqual(own_response.data, other_response.data)
