from collections.abc import Mapping
import re

from django.db import IntegrityError, transaction
from rest_framework import serializers

from apps.tasks.models import Category, Task


DUPLICATE_CATEGORY_NAME_MESSAGE = "Já existe uma categoria com este nome."
COLOR_PATTERN = re.compile(r"^#[0-9A-Fa-f]{6}$")


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = (
            "id",
            "name",
            "description",
            "color",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")

    def run_validation(self, data=serializers.empty):
        if isinstance(data, Mapping):
            allowed_fields = {"name", "description", "color"}
            unexpected_fields = sorted(set(data) - allowed_fields)
            if unexpected_fields:
                names = ", ".join(unexpected_fields)
                raise serializers.ValidationError(
                    {"detail": f"Campos não permitidos: {names}."}
                )
            if self.partial and not data:
                raise serializers.ValidationError(
                    {"detail": "Informe ao menos um campo para atualização."}
                )

        return super().run_validation(data)

    def validate_color(self, value):
        if value and not COLOR_PATTERN.fullmatch(value):
            raise serializers.ValidationError(
                "Use uma cor no formato #RRGGBB."
            )
        return value

    def validate_name(self, value):
        request = self.context.get("request")
        owner = request.user if request is not None else None
        categories = Category.objects.filter(owner=owner, name=value)
        if self.instance is not None:
            categories = categories.exclude(id=self.instance.id)
        if categories.exists():
            raise serializers.ValidationError(DUPLICATE_CATEGORY_NAME_MESSAGE)
        return value

    def create(self, validated_data):
        try:
            with transaction.atomic():
                return super().create(validated_data)
        except IntegrityError as exc:
            raise serializers.ValidationError(
                {"name": [DUPLICATE_CATEGORY_NAME_MESSAGE]}
            ) from exc

    def update(self, instance, validated_data):
        try:
            with transaction.atomic():
                return super().update(instance, validated_data)
        except IntegrityError as exc:
            raise serializers.ValidationError(
                {"name": [DUPLICATE_CATEGORY_NAME_MESSAGE]}
            ) from exc


class TaskSerializer(serializers.ModelSerializer):
    owner_id = serializers.UUIDField(read_only=True)
    access = serializers.SerializerMethodField()
    category_id = serializers.PrimaryKeyRelatedField(
        source="category",
        queryset=Category.objects.none(),
        allow_null=True,
        required=False,
    )

    class Meta:
        model = Task
        fields = (
            "id",
            "owner_id",
            "category_id",
            "title",
            "description",
            "status",
            "priority",
            "due_date",
            "created_at",
            "updated_at",
            "access",
        )
        read_only_fields = ("id", "owner_id", "created_at", "updated_at")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        if request is not None and request.user.is_authenticated:
            self.fields["category_id"].queryset = Category.objects.filter(
                owner=request.user
            )

    def get_access(self, task):
        request = self.context["request"]
        if task.owner_id == request.user.id:
            return {"type": "owned", "permission": "owner"}

        share = task.current_user_shares[0]
        return {"type": "shared", "permission": share.permission}

    def run_validation(self, data=serializers.empty):
        if isinstance(data, Mapping):
            allowed_fields = {
                "category_id",
                "title",
                "description",
                "status",
                "priority",
                "due_date",
            }
            unexpected_fields = sorted(set(data) - allowed_fields)
            if unexpected_fields:
                names = ", ".join(unexpected_fields)
                raise serializers.ValidationError(
                    {"detail": f"Campos não permitidos: {names}."}
                )
            if self.partial and not data:
                raise serializers.ValidationError(
                    {"detail": "Informe ao menos um campo para atualização."}
                )

        return super().run_validation(data)
