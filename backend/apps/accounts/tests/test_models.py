from uuid import UUID

from django.apps import apps as django_apps
from django.conf import settings
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.db import IntegrityError, transaction
from django.test import TestCase


class UserModelTests(TestCase):
    @staticmethod
    def get_user_model():
        return django_apps.get_model("accounts", "User")

    def test_creates_user_with_email_and_hashed_password(self):
        user_model = self.get_user_model()

        user = user_model.objects.create_user(
            email="person@example.com",
            password="strong-password-123",
        )

        self.assertIsInstance(user.id, UUID)
        self.assertEqual(user.email, "person@example.com")
        self.assertIsNone(user.username)
        self.assertNotEqual(user.password, "strong-password-123")
        self.assertTrue(user.check_password("strong-password-123"))

    def test_normalizes_email_domain(self):
        user_model = self.get_user_model()

        user = user_model.objects.create_user(
            email="Person@EXAMPLE.COM",
            password="strong-password-123",
        )

        self.assertEqual(user.email, "Person@example.com")

    def test_creates_superuser_with_required_flags(self):
        user_model = self.get_user_model()

        user = user_model.objects.create_superuser(
            email="admin@example.com",
            password="strong-password-123",
        )

        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.check_password("strong-password-123"))

    def test_requires_email(self):
        user_model = self.get_user_model()

        with self.assertRaises(ValueError):
            user_model.objects.create_user(
                email="",
                password="strong-password-123",
            )

    def test_requires_unique_email(self):
        user_model = self.get_user_model()
        user_model.objects.create_user(
            email="person@example.com",
            password="strong-password-123",
        )

        with self.assertRaises(IntegrityError), transaction.atomic():
            user_model.objects.create_user(
                email="person@example.com",
                password="another-password-123",
            )

    def test_rejects_superuser_without_staff_flag(self):
        user_model = self.get_user_model()

        with self.assertRaises(ValueError):
            user_model.objects.create_superuser(
                email="admin@example.com",
                password="strong-password-123",
                is_staff=False,
            )

    def test_rejects_superuser_without_superuser_flag(self):
        user_model = self.get_user_model()

        with self.assertRaises(ValueError):
            user_model.objects.create_superuser(
                email="admin@example.com",
                password="strong-password-123",
                is_superuser=False,
            )

    def test_uses_email_as_authentication_identifier(self):
        user_model = self.get_user_model()

        self.assertEqual(settings.AUTH_USER_MODEL, "accounts.User")
        self.assertEqual(user_model.USERNAME_FIELD, "email")
        self.assertEqual(user_model.REQUIRED_FIELDS, [])

    def test_is_registered_with_compatible_user_admin(self):
        user_model = self.get_user_model()

        self.assertIsInstance(admin.site._registry[user_model], UserAdmin)
