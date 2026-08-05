from django.db import connection
from django.test import TestCase


class PostgreSQLConfigurationTests(TestCase):
    def test_test_suite_uses_postgresql(self):
        self.assertEqual(connection.vendor, "postgresql")

        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()

        self.assertEqual(result, (1,))
