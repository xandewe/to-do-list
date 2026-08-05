from django.conf import settings
from django.test import SimpleTestCase
from rest_framework.permissions import IsAuthenticated
from rest_framework.settings import api_settings

from config.pagination import DefaultPageNumberPagination


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

    def test_simple_jwt_is_not_configured_yet(self):
        self.assertNotIn("simplejwt", repr(settings.REST_FRAMEWORK).lower())
