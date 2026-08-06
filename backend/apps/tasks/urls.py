from django.urls import path

from apps.tasks.views import CategoryDetailView, CategoryListCreateView


urlpatterns = [
    path("categories/", CategoryListCreateView.as_view(), name="category-list"),
    path(
        "categories/<uuid:category_id>/",
        CategoryDetailView.as_view(),
        name="category-detail",
    ),
]
