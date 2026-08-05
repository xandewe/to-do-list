import uuid

from django.conf import settings
from django.db import models

from apps.tasks.models.task import Task


class TaskShare(models.Model):
    class Permission(models.TextChoices):
        VIEW = "view", "View"
        EDIT = "edit", "Edit"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name="shares",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="shared_tasks",
    )
    permission = models.CharField(
        max_length=4,
        choices=Permission.choices,
        default=Permission.VIEW,
    )
    shared_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_task_shares",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = (
            models.UniqueConstraint(
                fields=("task", "user"),
                name="unique_task_share_task_user",
            ),
        )

    def __str__(self):
        return f"{self.task} shared with {self.user}"
