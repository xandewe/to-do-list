import uuid

from django.conf import settings
from django.db import models

from apps.tasks.models.category import Category


class Task(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        COMPLETED = "completed", "Completed"

    class Priority(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tasks",
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        related_name="tasks",
        null=True,
        blank=True,
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=9,
        choices=Status.choices,
        default=Status.PENDING,
    )
    priority = models.CharField(
        max_length=6,
        choices=Priority.choices,
        default=Priority.MEDIUM,
    )
    due_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at", "-id")
        indexes = (
            models.Index(
                fields=("owner", "status"),
                name="task_owner_status_idx",
            ),
            models.Index(
                fields=("owner", "category"),
                name="task_owner_category_idx",
            ),
            models.Index(
                fields=("owner", "priority"),
                name="task_owner_priority_idx",
            ),
            models.Index(
                fields=("owner", "due_date"),
                name="task_owner_due_date_idx",
            ),
            models.Index(
                fields=("owner", "created_at"),
                name="task_owner_created_at_idx",
            ),
        )

    def __str__(self):
        return self.title
