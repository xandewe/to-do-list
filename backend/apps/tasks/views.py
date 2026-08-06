from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.tasks.models import Category
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

    def post(self, request):
        serializer = TaskSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(owner=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
