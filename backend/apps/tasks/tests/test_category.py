from uuid import UUID

from django.apps import apps as django_apps
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase


class CategoryModelTests(TestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_user(
            email="owner@example.com",
            password="strong-password-123",
        )

    @staticmethod
    def get_category_model():
        return django_apps.get_model("tasks", "Category")

    def test_creates_category_for_owner(self):
        category_model = self.get_category_model()

        category = category_model.objects.create(
            owner=self.owner,
            name="Work",
            description="Professional tasks",
            color="#336699",
        )

        self.assertIsInstance(category.id, UUID)
        self.assertEqual(category.owner, self.owner)
        self.assertEqual(category.name, "Work")
        self.assertEqual(category.description, "Professional tasks")
        self.assertEqual(category.color, "#336699")
        self.assertIsNotNone(category.created_at)
        self.assertIsNotNone(category.updated_at)
        self.assertIn(category, self.owner.categories.all())

    def test_allows_same_name_for_different_owners(self):
        category_model = self.get_category_model()
        another_owner = get_user_model().objects.create_user(
            email="another@example.com",
            password="strong-password-123",
        )

        first = category_model.objects.create(owner=self.owner, name="Work")
        second = category_model.objects.create(owner=another_owner, name="Work")

        self.assertNotEqual(first.id, second.id)

    def test_rejects_same_name_for_same_owner(self):
        category_model = self.get_category_model()
        category_model.objects.create(owner=self.owner, name="Work")

        with self.assertRaises(IntegrityError), transaction.atomic():
            category_model.objects.create(owner=self.owner, name="Work")

    def test_deleting_owner_deletes_categories(self):
        category_model = self.get_category_model()
        category = category_model.objects.create(owner=self.owner, name="Work")

        self.owner.delete()

        self.assertFalse(category_model.objects.filter(id=category.id).exists())

    def test_optional_text_fields_default_to_empty_strings(self):
        category_model = self.get_category_model()

        category = category_model.objects.create(owner=self.owner, name="Work")

        self.assertEqual(category.description, "")
        self.assertEqual(category.color, "")

    def test_string_representation_is_name(self):
        category_model = self.get_category_model()
        category = category_model.objects.create(owner=self.owner, name="Work")

        self.assertEqual(str(category), "Work")

    def test_default_ordering_is_by_name(self):
        category_model = self.get_category_model()
        category_model.objects.create(owner=self.owner, name="Personal")
        category_model.objects.create(owner=self.owner, name="Errands")

        names = list(category_model.objects.values_list("name", flat=True))

        self.assertEqual(names, ["Errands", "Personal"])

    def test_is_registered_in_admin(self):
        category_model = self.get_category_model()

        self.assertIn(category_model, admin.site._registry)
