from django.test import SimpleTestCase, override_settings
from django.urls import path
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.test import APIClient
from rest_framework.views import APIView

from config.pagination import DefaultPageNumberPagination


class PaginatedItemsView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        paginator = DefaultPageNumberPagination()
        page = paginator.paginate_queryset(list(range(125)), request, view=self)
        return paginator.get_paginated_response(page)


urlpatterns = [
    path("items/", PaginatedItemsView.as_view()),
]


@override_settings(ROOT_URLCONF=__name__)
class DefaultPageNumberPaginationTests(SimpleTestCase):
    def setUp(self):
        self.client = APIClient()

    def test_returns_twenty_results_by_default(self):
        response = self.client.get("/items/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()["results"]), 20)

    def test_accepts_requested_page_size(self):
        response = self.client.get("/items/?page_size=5")

        self.assertEqual(len(response.json()["results"]), 5)

    def test_accepts_maximum_page_size(self):
        response = self.client.get("/items/?page_size=100")

        self.assertEqual(len(response.json()["results"]), 100)

    def test_caps_page_size_at_one_hundred(self):
        response = self.client.get("/items/?page_size=101")

        self.assertEqual(len(response.json()["results"]), 100)

    def test_uses_standard_paginated_response_shape(self):
        response = self.client.get("/items/")

        self.assertEqual(
            set(response.json()),
            {"count", "next", "previous", "results"},
        )
        self.assertEqual(response.json()["count"], 125)

    def test_first_page_has_no_previous_link(self):
        response = self.client.get("/items/")

        self.assertIsNone(response.json()["previous"])
        self.assertIsNotNone(response.json()["next"])

    def test_last_page_has_no_next_link(self):
        response = self.client.get("/items/?page=7")

        self.assertIsNotNone(response.json()["previous"])
        self.assertIsNone(response.json()["next"])

    def test_nonexistent_page_returns_not_found(self):
        response = self.client.get("/items/?page=999")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_navigation_links_preserve_other_query_parameters(self):
        response = self.client.get("/items/?status=open")

        self.assertIn("status=open", response.json()["next"])

    def test_invalid_page_size_uses_default(self):
        for value in ("0", "-1", "invalid"):
            with self.subTest(value=value):
                response = self.client.get(f"/items/?page_size={value}")

                self.assertEqual(len(response.json()["results"]), 20)
