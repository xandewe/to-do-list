import os
from datetime import timedelta

from django.conf import settings
from django.test import SimpleTestCase
from rest_framework.permissions import IsAuthenticated
from rest_framework.settings import api_settings
from rest_framework_simplejwt.authentication import JWTAuthentication

from config.pagination import DefaultPageNumberPagination


class EnvironmentConfigurationTests(SimpleTestCase):
    def test_secret_key_is_read_from_environment(self):
        self.assertEqual(settings.SECRET_KEY, os.environ["DJANGO_SECRET_KEY"])

    def test_allowed_hosts_defaults_to_localhost(self):
        # O runner de testes anexa "testserver"; validamos os hosts locais.
        self.assertIn("localhost", settings.ALLOWED_HOSTS)
        self.assertIn("127.0.0.1", settings.ALLOWED_HOSTS)


class RestFrameworkConfigurationTests(SimpleTestCase):
    def test_rest_framework_is_installed(self):
        self.assertIn("rest_framework", settings.INSTALLED_APPS)

    def test_default_permission_requires_authentication(self):
        self.assertEqual(
            api_settings.DEFAULT_PERMISSION_CLASSES,
            [IsAuthenticated],
        )

    def test_default_pagination_uses_project_class(self):
        self.assertIs(
            api_settings.DEFAULT_PAGINATION_CLASS,
            DefaultPageNumberPagination,
        )

    def test_jwt_authentication_is_the_only_default(self):
        self.assertEqual(
            api_settings.DEFAULT_AUTHENTICATION_CLASSES,
            [JWTAuthentication],
        )

    def test_simple_jwt_blacklist_is_installed(self):
        self.assertIn(
            "rest_framework_simplejwt.token_blacklist",
            settings.INSTALLED_APPS,
        )

    def test_simple_jwt_has_explicit_security_settings(self):
        self.assertEqual(
            settings.SIMPLE_JWT,
            {
                "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
                "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
                "ROTATE_REFRESH_TOKENS": True,
                "BLACKLIST_AFTER_ROTATION": True,
                "UPDATE_LAST_LOGIN": False,
                "ALGORITHM": "HS256",
                "SIGNING_KEY": os.getenv("JWT_SIGNING_KEY", settings.SECRET_KEY),
                "AUTH_HEADER_TYPES": ("Bearer",),
                "USER_ID_FIELD": "id",
                "USER_ID_CLAIM": "user_id",
            },
        )
