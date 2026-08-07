from django.test import SimpleTestCase


class CorsHeadersTests(SimpleTestCase):
    tasks_url = "/api/v1/tasks/"
    allowed_origin = "http://localhost:5173"
    disallowed_origin = "http://evil.example.com"

    def preflight(self, origin):
        return self.client.options(
            self.tasks_url,
            HTTP_ORIGIN=origin,
            HTTP_ACCESS_CONTROL_REQUEST_METHOD="GET",
        )

    def test_allowed_origin_receives_cors_header(self):
        response = self.preflight(self.allowed_origin)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response["Access-Control-Allow-Origin"], self.allowed_origin
        )

    def test_disallowed_origin_is_not_reflected(self):
        response = self.preflight(self.disallowed_origin)

        self.assertNotIn("Access-Control-Allow-Origin", response)
