from importlib import import_module

from django.test import SimpleTestCase
from django.urls import Resolver404, get_resolver, resolve

from apps.accounts.views import UserRegistrationView
from health.views import HealthCheckView


class ApiRoutingTests(SimpleTestCase):
    def test_healthcheck_remains_unversioned(self):
        match = resolve("/api/health/")

        self.assertIs(match.func.view_class, HealthCheckView)

    def test_admin_remains_configured(self):
        match = resolve("/admin/")

        self.assertEqual(match.namespace, "admin")

    def test_versioned_api_prefix_is_included(self):
        root_patterns = get_resolver().url_patterns

        self.assertTrue(
            any(str(pattern.pattern) == "api/v1/" for pattern in root_patterns)
        )

    def test_application_url_modules_are_importable(self):
        for module_name in (
            "config.api_urls",
            "apps.accounts.urls",
            "apps.tasks.urls",
        ):
            with self.subTest(module_name=module_name):
                module = import_module(module_name)

                self.assertTrue(hasattr(module, "urlpatterns"))

    def test_versioned_healthcheck_does_not_exist(self):
        with self.assertRaises(Resolver404):
            resolve("/api/v1/health/")

    def test_user_registration_route_is_available(self):
        match = resolve("/api/v1/users/")

        self.assertIs(match.func.view_class, UserRegistrationView)
        self.assertEqual(match.url_name, "user-registration")

    def test_other_domain_endpoints_are_not_created_prematurely(self):
        paths = (
            "/api/v1/auth/",
            "/api/v1/categories/",
            "/api/v1/tasks/",
        )

        for path in paths:
            with self.subTest(path=path), self.assertRaises(Resolver404):
                resolve(path)
