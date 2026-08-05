from unittest.mock import patch

from django.db import DatabaseError
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class HealthCheckTests(APITestCase):
    def test_get_returns_api_and_database_online(self):
        response = self.client.get(reverse("health-check"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json(),
            {"api": "online", "database": "online"},
        )

    @patch(
        "health.views.connection.cursor",
        side_effect=DatabaseError("database unavailable"),
    )
    def test_get_returns_service_unavailable_when_database_is_offline(
        self, mocked_cursor
    ):
        response = self.client.get(reverse("health-check"))

        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertEqual(
            response.json(),
            {"api": "online", "database": "offline"},
        )
        mocked_cursor.assert_called_once_with()

    def test_post_is_not_allowed(self):
        response = self.client.post(reverse("health-check"), {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
