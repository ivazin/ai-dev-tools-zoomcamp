import pytest
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from chores.models import UserProfile, ChoreTemplate, Chore, ChoreLog


@pytest.mark.django_db
def test_user_profile_creation_defaults_and_str():
    user = User.objects.create_user(username="alice", password="password123")
    profile = UserProfile.objects.create(user=user)

    assert profile.user == user
    assert profile.total_points == 0
    assert profile.is_active_roommate is True
    assert str(profile) == "alice (0 pts)"
    assert user.profile == profile


@pytest.mark.django_db
def test_chore_template_creation_defaults_and_str():
    template = ChoreTemplate.objects.create(
        title="Take out trash",
        description="Take the bins to the curb",
    )

    assert template.title == "Take out trash"
    assert template.description == "Take the bins to the curb"
    assert template.points == 1
    assert template.frequency == ChoreTemplate.Frequency.WEEKLY
    assert template.assignment_strategy == ChoreTemplate.AssignmentStrategy.ROUND_ROBIN
    assert template.default_assignee is None
    assert template.rotation_order == []
    assert template.last_assigned_user is None
    assert template.is_active is True
    assert str(template) == "Take out trash"


@pytest.mark.django_db
def test_chore_template_foreign_keys_and_choices():
    user1 = User.objects.create_user(username="bob", password="password123")
    profile1 = UserProfile.objects.create(user=user1)
    user2 = User.objects.create_user(username="charlie", password="password123")
    profile2 = UserProfile.objects.create(user=user2)

    template = ChoreTemplate.objects.create(
        title="Clean kitchen",
        points=5,
        frequency=ChoreTemplate.Frequency.DAILY,
        assignment_strategy=ChoreTemplate.AssignmentStrategy.FIXED,
        default_assignee=profile1,
        rotation_order=[user1.id, user2.id],
        last_assigned_user=profile2,
        is_active=False,
    )

    assert template.default_assignee == profile1
    assert template.last_assigned_user == profile2
    assert profile1.default_template_chores.first() == template
    assert profile2.last_assigned_template_chores.first() == template


@pytest.mark.django_db
def test_chore_creation_defaults_and_str():
    due = timezone.now() + timezone.timedelta(days=1)
    chore = Chore.objects.create(
        title="Vacuum living room",
        due_date=due,
    )

    assert chore.template is None
    assert chore.title == "Vacuum living room"
    assert chore.description == ""
    assert chore.points == 1
    assert chore.status == Chore.Status.PENDING
    assert chore.assignee is None
    assert chore.due_date == due
    assert chore.completed_at is None
    assert chore.completed_by is None
    assert chore.created_at is not None
    assert str(chore) == f"Vacuum living room ({Chore.Status.PENDING})"


@pytest.mark.django_db
def test_chore_with_template_and_assignees():
    user = User.objects.create_user(username="dave", password="password123")
    profile = UserProfile.objects.create(user=user)
    template = ChoreTemplate.objects.create(title="Dishes")
    now = timezone.now()

    chore = Chore.objects.create(
        template=template,
        title="Dishes",
        points=2,
        status=Chore.Status.COMPLETED,
        assignee=profile,
        due_date=now,
        completed_at=now,
        completed_by=profile,
    )

    assert chore.template == template
    assert chore.assignee == profile
    assert chore.completed_by == profile
    assert template.chores.first() == chore
    assert profile.assigned_chores.first() == chore
    assert profile.completed_chores.first() == chore
    assert str(chore) == f"Dishes ({Chore.Status.COMPLETED})"


@pytest.mark.django_db
def test_chore_log_creation_and_str():
    due = timezone.now()
    chore = Chore.objects.create(title="Wipe counters", due_date=due)
    user = User.objects.create_user(username="eve", password="password123")
    profile = UserProfile.objects.create(user=user)

    log = ChoreLog.objects.create(
        chore=chore,
        user=profile,
        action=ChoreLog.Action.CLAIMED,
        note="Claimed for morning routine",
    )

    assert log.chore == chore
    assert log.user == profile
    assert log.action == ChoreLog.Action.CLAIMED
    assert log.note == "Claimed for morning routine"
    assert log.timestamp is not None
    assert str(log) == f"{chore.title} - {log.action} at {log.timestamp}"
    assert chore.logs.first() == log
    assert profile.chore_logs.first() == log


@pytest.mark.django_db
def test_cascade_delete_user_deletes_user_profile():
    user = User.objects.create_user(username="frank", password="password123")
    profile = UserProfile.objects.create(user=user)
    profile_id = profile.id

    user.delete()

    assert not UserProfile.objects.filter(id=profile_id).exists()


@pytest.mark.django_db
def test_set_null_on_user_profile_deletion():
    user = User.objects.create_user(username="grace", password="password123")
    profile = UserProfile.objects.create(user=user)
    due = timezone.now()

    chore = Chore.objects.create(
        title="Mop floors",
        due_date=due,
        assignee=profile,
        completed_by=profile,
    )
    log = ChoreLog.objects.create(
        chore=chore,
        user=profile,
        action=ChoreLog.Action.CREATED,
    )
    template = ChoreTemplate.objects.create(
        title="Mop floors template",
        default_assignee=profile,
        last_assigned_user=profile,
    )

    # Deleting user cascades to profile, and profile's references in Chore, ChoreLog, ChoreTemplate should be SET_NULL
    user.delete()

    chore.refresh_from_db()
    log.refresh_from_db()
    template.refresh_from_db()

    assert chore.assignee is None
    assert chore.completed_by is None
    assert log.user is None
    assert template.default_assignee is None
    assert template.last_assigned_user is None


@pytest.mark.django_db
def test_set_null_on_chore_template_deletion():
    template = ChoreTemplate.objects.create(title="Dust shelves")
    chore = Chore.objects.create(
        template=template,
        title="Dust shelves",
        due_date=timezone.now(),
    )

    template.delete()
    chore.refresh_from_db()

    assert chore.template is None
    assert Chore.objects.filter(id=chore.id).exists()


@pytest.mark.django_db
def test_cascade_delete_chore_deletes_chore_logs():
    chore = Chore.objects.create(
        title="Clean bathroom",
        due_date=timezone.now(),
    )
    log = ChoreLog.objects.create(
        chore=chore,
        action=ChoreLog.Action.CREATED,
    )
    log_id = log.id

    chore.delete()

    assert not ChoreLog.objects.filter(id=log_id).exists()
