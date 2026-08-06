from django.db.models import Prefetch, Q
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.tasks.models import Category, Task, TaskShare
from apps.tasks.serializers import CategorySerializer, TaskSerializer
from config.pagination import DefaultPageNumberPagination


class CategoryListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        categories = Category.objects.filter(owner=request.user)
        paginator = DefaultPageNumberPagination()
        page = paginator.paginate_queryset(categories, request, view=self)
        serializer = CategorySerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = CategorySerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(owner=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CategoryDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @staticmethod
    def get_category(request, category_id):
        return get_object_or_404(
            Category.objects.filter(owner=request.user),
            id=category_id,
        )

    def get(self, request, category_id):
        category = self.get_category(request, category_id)
        serializer = CategorySerializer(category)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, category_id):
        category = self.get_category(request, category_id)
        serializer = CategorySerializer(
            instance=category,
            data=request.data,
            partial=True,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, category_id):
        category = self.get_category(request, category_id)
        category.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TaskListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tasks = get_accessible_tasks(request.user)
        paginator = DefaultPageNumberPagination()
        page = paginator.paginate_queryset(tasks, request, view=self)
        serializer = TaskSerializer(
            page,
            many=True,
            context={"request": request},
        )
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = TaskSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(owner=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class TaskDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, task_id):
        task = get_object_or_404(
            get_accessible_tasks(request.user),
            id=task_id,
        )
        serializer = TaskSerializer(task, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, task_id):
        task = get_object_or_404(
            get_accessible_tasks(request.user),
            id=task_id,
        )
        is_owner = task.owner_id == request.user.id
        share = None if is_owner else task.current_user_shares[0]

        if not is_owner and share.permission == TaskShare.Permission.VIEW:
            raise PermissionDenied()
        if not is_owner and "category_id" in request.data:
            raise PermissionDenied()

        serializer = TaskSerializer(
            instance=task,
            data=request.data,
            partial=True,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, task_id):
        task = get_object_or_404(
            Task.objects.filter(id=task_id, owner=request.user),
            id=task_id,
        )
        task.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


def get_accessible_tasks(user):
    current_user_shares = TaskShare.objects.filter(user=user)
    return (
        Task.objects.filter(Q(owner=user) | Q(shares__user=user))
        .distinct()
        .prefetch_related(
            Prefetch(
                "shares",
                queryset=current_user_shares,
                to_attr="current_user_shares",
            )
        )
    )
