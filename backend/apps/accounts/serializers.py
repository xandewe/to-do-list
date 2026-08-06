from collections.abc import Mapping

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from rest_framework import serializers

from apps.accounts.models import User


DUPLICATE_EMAIL_MESSAGE = "Já existe uma conta com este e-mail."


class StrictStringFieldMixin:
    def to_internal_value(self, data):
        if not isinstance(data, str):
            raise serializers.ValidationError(
                self.error_messages["invalid"],
                code="invalid",
            )
        return super().to_internal_value(data)


class StrictCharField(StrictStringFieldMixin, serializers.CharField):
    pass


class StrictEmailField(StrictStringFieldMixin, serializers.EmailField):
    pass


class CurrentUserSerializer(serializers.ModelSerializer):
    first_name = StrictCharField(
        required=False,
        allow_blank=True,
        allow_null=False,
        max_length=150,
    )
    last_name = StrictCharField(
        required=False,
        allow_blank=True,
        allow_null=False,
        max_length=150,
    )

    class Meta:
        model = User
        fields = ("id", "email", "first_name", "last_name")
        read_only_fields = ("id", "email")

    def run_validation(self, data=serializers.empty):
        if isinstance(data, Mapping):
            allowed_fields = {"first_name", "last_name"}
            unexpected_fields = sorted(set(data) - allowed_fields)
            if unexpected_fields:
                names = ", ".join(unexpected_fields)
                raise serializers.ValidationError(
                    {"detail": f"Campos não permitidos: {names}."}
                )
            if not data:
                raise serializers.ValidationError(
                    {"detail": "Informe ao menos um campo para atualização."}
                )

        return super().run_validation(data)


class UserRegistrationSerializer(serializers.ModelSerializer):
    email = StrictEmailField(max_length=254, allow_null=False)
    password = StrictCharField(
        write_only=True,
        allow_blank=False,
        allow_null=False,
        trim_whitespace=False,
    )
    first_name = StrictCharField(
        required=False,
        allow_blank=True,
        allow_null=False,
        max_length=150,
    )
    last_name = StrictCharField(
        required=False,
        allow_blank=True,
        allow_null=False,
        max_length=150,
    )

    class Meta:
        model = User
        fields = ("id", "email", "password", "first_name", "last_name")
        read_only_fields = ("id",)

    def run_validation(self, data=serializers.empty):
        if isinstance(data, Mapping):
            allowed_fields = {"email", "password", "first_name", "last_name"}
            unexpected_fields = sorted(set(data) - allowed_fields)
            if unexpected_fields:
                names = ", ".join(unexpected_fields)
                raise serializers.ValidationError(
                    {"detail": f"Campos não permitidos: {names}."}
                )

        return super().run_validation(data)

    def validate_email(self, value):
        normalized_email = User.objects.normalize_email(value)
        if User.objects.filter(email=normalized_email).exists():
            raise serializers.ValidationError(DUPLICATE_EMAIL_MESSAGE)
        return normalized_email

    def validate(self, attrs):
        candidate = User(
            email=attrs.get("email", ""),
            first_name=attrs.get("first_name", ""),
            last_name=attrs.get("last_name", ""),
        )
        try:
            validate_password(attrs["password"], candidate)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(
                {"password": list(exc.messages)}
            ) from exc

        return attrs

    def create(self, validated_data):
        try:
            with transaction.atomic():
                return User.objects.create_user(**validated_data)
        except IntegrityError as exc:
            raise serializers.ValidationError(
                {"email": [DUPLICATE_EMAIL_MESSAGE]}
            ) from exc
