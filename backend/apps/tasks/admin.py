from django.contrib import admin

from apps.tasks.models import Category, Task, TaskShare


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "created_at", "updated_at")
    search_fields = ("name", "owner__email")


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("title", "owner", "status", "priority", "due_date")
    list_filter = ("status", "priority")
    search_fields = ("title", "owner__email")


@admin.register(TaskShare)
class TaskShareAdmin(admin.ModelAdmin):
    list_display = ("task", "user", "permission", "shared_by", "created_at")
    list_filter = ("permission",)
    search_fields = ("task__title", "user__email", "shared_by__email")
