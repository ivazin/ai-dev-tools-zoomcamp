from django.contrib import admin
from chores.models import Chore, ChoreLog, ChoreTemplate, UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "total_points", "is_active_roommate")
    list_filter = ("is_active_roommate",)
    search_fields = (
        "user__username",
        "user__first_name",
        "user__last_name",
        "user__email",
    )


@admin.register(ChoreTemplate)
class ChoreTemplateAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "frequency",
        "assignment_strategy",
        "points",
        "is_active",
        "last_assigned_user",
    )
    list_filter = ("frequency", "assignment_strategy", "is_active")
    search_fields = ("title", "description")


class ChoreLogInline(admin.TabularInline):
    model = ChoreLog
    fields = ("action", "user", "timestamp", "note")
    readonly_fields = ("timestamp",)
    extra = 0


@admin.register(Chore)
class ChoreAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "status",
        "points",
        "assignee",
        "due_date",
        "completed_at",
        "completed_by",
    )
    list_filter = ("status", "due_date")
    search_fields = ("title", "assignee__user__username")
    readonly_fields = ("created_at",)
    inlines = [ChoreLogInline]


@admin.register(ChoreLog)
class ChoreLogAdmin(admin.ModelAdmin):
    list_display = ("chore", "action", "user", "timestamp")
    list_filter = ("action", "timestamp")
    search_fields = ("chore__title", "user__user__username", "note")
    readonly_fields = ("timestamp",)

