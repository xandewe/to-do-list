from django.conf import settings
from django.test import SimpleTestCase


class RestFrameworkConfigurationTests(SimpleTestCase):
    def test_rest_framework_is_installed(self):
        self.assertIn("rest_framework", settings.INSTALLED_APPS)
