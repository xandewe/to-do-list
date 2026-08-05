from django.urls import reverse
from rest_framework import status
from rest_framework.test import APISimpleTestCase


class HealthCheckTests(APISimpleTestCase):
    def test_get_returns_online_status(self):
        response = self.client.get(reverse("health-check"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {"status": "online"})

    def test_post_is_not_allowed(self):
        response = self.client.post(reverse("health-check"), {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
