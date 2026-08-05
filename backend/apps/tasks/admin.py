from django.contrib import admin

from apps.tasks.models import Category, Task


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "created_at", "updated_at")
    search_fields = ("name", "owner__email")


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("title", "owner", "status", "priority", "due_date")
    list_filter = ("status", "priority")
    search_fields = ("title", "owner__email")
