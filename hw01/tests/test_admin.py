import pytest
from django.contrib.admin.sites import site
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone

from chores.admin import (
    ChoreAdmin,
    ChoreLogAdmin,
    ChoreLogInline,
    ChoreTemplateAdmin,
    UserProfileAdmin,
)
from chores.models import Chore, ChoreLog, ChoreTemplate, UserProfile


def test_user_profile_admin_registration_and_configuration():
    assert UserProfile in site._registry
    model_admin = site._registry[UserProfile]
    assert isinstance(model_admin, UserProfileAdmin)
    assert model_admin.list_display == ("user", "total_points", "is_active_roommate")
    assert model_admin.list_filter == ("is_active_roommate",)
    assert model_admin.search_fields == (
        "user__username",
        "user__first_name",
        "user__last_name",
        "user__email",
    )


def test_chore_template_admin_registration_and_configuration():
    assert ChoreTemplate in site._registry
    model_admin = site._registry[ChoreTemplate]
    assert isinstance(model_admin, ChoreTemplateAdmin)
    assert model_admin.list_display == (
        "title",
        "frequency",
        "assignment_strategy",
        "points",
        "is_active",
        "last_assigned_user",
    )
    assert model_admin.list_filter == ("frequency", "assignment_strategy", "is_active")
    assert model_admin.search_fields == ("title", "description")


def test_chore_admin_registration_and_configuration():
    assert Chore in site._registry
    model_admin = site._registry[Chore]
    assert isinstance(model_admin, ChoreAdmin)
    assert model_admin.list_display == (
        "title",
        "status",
        "points",
        "assignee",
        "due_date",
        "completed_at",
        "completed_by",
    )
    assert model_admin.list_filter == ("status", "due_date")
    assert model_admin.search_fields == ("title", "assignee__user__username")
    assert model_admin.readonly_fields == ("created_at",)
    assert len(model_admin.inlines) == 1
    assert model_admin.inlines[0] == ChoreLogInline


def test_chore_log_inline_configuration():
    inline = ChoreLogInline(Chore, site)
    assert inline.model == ChoreLog
    assert inline.fields == ("action", "user", "timestamp", "note")
    assert inline.readonly_fields == ("timestamp",)
    assert inline.extra == 0


def test_chore_log_admin_registration_and_configuration():
    assert ChoreLog in site._registry
    model_admin = site._registry[ChoreLog]
    assert isinstance(model_admin, ChoreLogAdmin)
    assert model_admin.list_display == ("chore", "action", "user", "timestamp")
    assert model_admin.list_filter == ("action", "timestamp")
    assert model_admin.search_fields == ("chore__title", "user__user__username", "note")
    assert model_admin.readonly_fields == ("timestamp",)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "model_name",
    ["userprofile", "choretemplate", "chore", "chorelog"],
)
def test_unauthenticated_requests_redirected_to_admin_login(client, model_name):
    changelist_url = reverse(f"admin:chores_{model_name}_changelist")
    response = client.get(changelist_url)
    assert response.status_code == 302
    assert "/admin/login/" in response.url


@pytest.mark.django_db
def test_superuser_changelist_and_changeform_urls_render_200(client, admin_user):
    client.force_login(admin_user)

    user = User.objects.create_user(username="roommate", email="roommate@example.com")
    profile = UserProfile.objects.create(user=user, total_points=10)

    template = ChoreTemplate.objects.create(
        title="Dishes",
        description="Wash dishes",
        points=2,
        default_assignee=profile,
        last_assigned_user=profile,
    )

    chore = Chore.objects.create(
        template=template,
        title="Dishes chore",
        description="Wash after dinner",
        points=2,
        assignee=profile,
        due_date=timezone.now(),
        completed_at=timezone.now(),
        completed_by=profile,
    )

    log = ChoreLog.objects.create(
        chore=chore,
        user=profile,
        action=ChoreLog.Action.COMPLETED,
        note="Done quickly",
    )

    instances = [
        ("userprofile", profile),
        ("choretemplate", template),
        ("chore", chore),
        ("chorelog", log),
    ]

    for model_name, instance in instances:
        changelist_url = reverse(f"admin:chores_{model_name}_changelist")
        cl_response = client.get(changelist_url)
        assert cl_response.status_code == 200

        changeform_url = reverse(f"admin:chores_{model_name}_change", args=[instance.pk])
        cf_response = client.get(changeform_url)
        assert cf_response.status_code == 200

    # Verify created_at appears in Chore change form
    chore_changeform_url = reverse("admin:chores_chore_change", args=[chore.pk])
    chore_response = client.get(chore_changeform_url)
    assert "Created at" in chore_response.content.decode("utf-8") or "created_at" in chore_response.content.decode("utf-8")


@pytest.mark.django_db
def test_admin_views_with_nullable_foreign_keys_as_none(client, admin_user):
    client.force_login(admin_user)

    user = User.objects.create_user(username="testuser")
    profile = UserProfile.objects.create(user=user)

    # Template with nullable FKs = None (default_assignee, last_assigned_user)
    template = ChoreTemplate.objects.create(
        title="Sweep",
        default_assignee=None,
        last_assigned_user=None,
    )

    # Chore with nullable FKs = None (template, assignee, completed_by)
    chore = Chore.objects.create(
        template=None,
        title="Sweep porch",
        due_date=timezone.now(),
        assignee=None,
        completed_by=None,
    )

    # ChoreLog with nullable FK = None (user)
    log = ChoreLog.objects.create(
        chore=chore,
        user=None,
        action=ChoreLog.Action.CREATED,
    )

    instances = [
        ("userprofile", profile),
        ("choretemplate", template),
        ("chore", chore),
        ("chorelog", log),
    ]

    for model_name, instance in instances:
        changelist_url = reverse(f"admin:chores_{model_name}_changelist")
        cl_response = client.get(changelist_url)
        assert cl_response.status_code == 200

        changeform_url = reverse(f"admin:chores_{model_name}_change", args=[instance.pk])
        cf_response = client.get(changeform_url)
        assert cf_response.status_code == 200
