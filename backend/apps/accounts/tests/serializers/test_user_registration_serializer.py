from unittest import mock

from django.apps import apps as django_apps
from django.db import IntegrityError, connection
from django.test import TestCase
from rest_framework import serializers

from apps.accounts.serializers import UserRegistrationSerializer


class UserRegistrationSerializerTests(TestCase):
    password = "safe-unrelated-passphrase-482!"

    @staticmethod
    def get_user_model():
        return django_apps.get_model("accounts", "User")

    def valid_payload(self, **overrides):
        payload = {
            "email": "person@example.com",
            "password": self.password,
        }
        payload.update(overrides)
        return payload

    def assert_field_error(self, payload, field):
        serializer = UserRegistrationSerializer(data=payload)

        self.assertFalse(serializer.is_valid())
        self.assertIn(field, serializer.errors)

    def test_minimum_payload_is_valid_and_defaults_names(self):
        serializer = UserRegistrationSerializer(data=self.valid_payload())

        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()

        self.assertEqual(user.first_name, "")
        self.assertEqual(user.last_name, "")

    def test_complete_payload_accepts_unicode_names(self):
        serializer = UserRegistrationSerializer(
            data=self.valid_payload(first_name="Álex", last_name="Silva 日本")
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()

        self.assertEqual(user.first_name, "Álex")
        self.assertEqual(user.last_name, "Silva 日本")

    def test_normalizes_only_the_email_domain(self):
        serializer = UserRegistrationSerializer(
            data=self.valid_payload(email="Person@EXAMPLE.COM")
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()

        self.assertEqual(user.email, "Person@example.com")

    def test_rejects_missing_email(self):
        payload = self.valid_payload()
        payload.pop("email")

        self.assert_field_error(payload, "email")

    def test_rejects_blank_email(self):
        self.assert_field_error(self.valid_payload(email=""), "email")

    def test_rejects_invalid_email(self):
        self.assert_field_error(self.valid_payload(email="not-an-email"), "email")

    def test_rejects_email_above_254_characters(self):
        email = f"{'a' * 243}@example.com"

        self.assertGreater(len(email), 254)
        self.assert_field_error(self.valid_payload(email=email), "email")

    def test_rejects_null_email(self):
        self.assert_field_error(self.valid_payload(email=None), "email")

    def test_rejects_missing_password(self):
        payload = self.valid_payload()
        payload.pop("password")

        self.assert_field_error(payload, "password")

    def test_rejects_blank_password(self):
        self.assert_field_error(self.valid_payload(password=""), "password")

    def test_rejects_null_password(self):
        self.assert_field_error(self.valid_payload(password=None), "password")

    def test_does_not_trim_password(self):
        password = "  safe-unrelated-passphrase-482!  "
        serializer = UserRegistrationSerializer(
            data=self.valid_payload(password=password)
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()

        self.assertTrue(user.check_password(password))
        self.assertFalse(user.check_password(password.strip()))

    def test_rejects_first_name_above_150_characters(self):
        self.assert_field_error(
            self.valid_payload(first_name="a" * 151),
            "first_name",
        )

    def test_rejects_last_name_above_150_characters(self):
        self.assert_field_error(
            self.valid_payload(last_name="a" * 151),
            "last_name",
        )

    def test_rejects_null_names(self):
        for field in ("first_name", "last_name"):
            with self.subTest(field=field):
                self.assert_field_error(self.valid_payload(**{field: None}), field)

    def test_rejects_non_string_text_fields(self):
        non_string_values = {
            "email": 123,
            "password": 123456789012.345,
            "first_name": 123,
            "last_name": 123,
        }

        for field, value in non_string_values.items():
            with self.subTest(field=field):
                self.assert_field_error(
                    self.valid_payload(**{field: value}),
                    field,
                )

    def test_rejects_unknown_fields_in_deterministic_order(self):
        serializer = UserRegistrationSerializer(
            data=self.valid_payload(z_field=True, is_staff=True)
        )

        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            str(serializer.errors["detail"]),
            "Campos não permitidos: is_staff, z_field.",
        )

    def test_rejects_each_administrative_field(self):
        forbidden_fields = (
            "id",
            "username",
            "is_staff",
            "is_superuser",
            "is_active",
            "groups",
            "user_permissions",
            "date_joined",
            "last_login",
        )

        for field in forbidden_fields:
            with self.subTest(field=field):
                serializer = UserRegistrationSerializer(
                    data=self.valid_payload(**{field: True})
                )
                self.assertFalse(serializer.is_valid())
                self.assertEqual(
                    str(serializer.errors["detail"]),
                    f"Campos não permitidos: {field}.",
                )

    def test_rejects_short_password(self):
        self.assert_field_error(self.valid_payload(password="Ab1!"), "password")

    def test_rejects_common_password(self):
        self.assert_field_error(self.valid_payload(password="password"), "password")

    def test_rejects_numeric_password(self):
        self.assert_field_error(
            self.valid_payload(password="1234567890123456"),
            "password",
        )

    def test_rejects_password_similar_to_user_data(self):
        self.assert_field_error(
            self.valid_payload(
                email="alexandre@example.com",
                password="alexandre@example.com",
                first_name="Alexandre",
            ),
            "password",
        )

    def test_rejects_duplicate_normalized_email(self):
        user_model = self.get_user_model()
        user_model.objects.create_user(
            email="Person@example.com",
            password=self.password,
        )
        serializer = UserRegistrationSerializer(
            data=self.valid_payload(email="Person@EXAMPLE.COM")
        )

        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            [str(error) for error in serializer.errors["email"]],
            ["Já existe uma conta com este e-mail."],
        )

    def test_save_hashes_password_and_uses_safe_flags(self):
        user_model = self.get_user_model()
        serializer = UserRegistrationSerializer(data=self.valid_payload())

        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()

        self.assertEqual(user_model.objects.count(), 1)
        self.assertNotEqual(user.password, self.password)
        self.assertTrue(user.check_password(self.password))
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertTrue(user.is_active)

    def test_serialized_result_contains_only_public_fields(self):
        serializer = UserRegistrationSerializer(data=self.valid_payload())
        self.assertTrue(serializer.is_valid(), serializer.errors)
        serializer.save()

        self.assertEqual(
            set(serializer.data),
            {"id", "email", "first_name", "last_name"},
        )

    def test_integrity_error_becomes_email_validation_error(self):
        user_model = self.get_user_model()
        serializer = UserRegistrationSerializer(data=self.valid_payload())
        self.assertTrue(serializer.is_valid(), serializer.errors)

        with mock.patch.object(
            user_model.objects,
            "create_user",
            side_effect=IntegrityError("duplicate"),
        ):
            with self.assertRaises(serializers.ValidationError) as raised:
                serializer.save()

        self.assertEqual(
            [str(error) for error in raised.exception.detail["email"]],
            ["Já existe uma conta com este e-mail."],
        )
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            self.assertEqual(cursor.fetchone(), (1,))
