from django.urls import path

from apps.tasks.views import (
    CategoryDetailView,
    CategoryListCreateView,
    TaskDetailView,
    TaskListCreateView,
)


urlpatterns = [
    path("categories/", CategoryListCreateView.as_view(), name="category-list"),
    path(
        "categories/<uuid:category_id>/",
        CategoryDetailView.as_view(),
        name="category-detail",
    ),
    path("tasks/", TaskListCreateView.as_view(), name="task-list"),
    path(
        "tasks/<uuid:task_id>/",
        TaskDetailView.as_view(),
        name="task-detail",
    ),
]
