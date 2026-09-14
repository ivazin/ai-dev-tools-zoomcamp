import io
from datetime import timedelta
import pytest
from django.contrib.auth.models import User
from django.core.management import call_command
from django.utils import timezone

from chores.models import Chore, ChoreLog, ChoreTemplate, UserProfile


@pytest.mark.django_db
def test_seed_data_populates_all_models():
    out = io.StringIO()
    call_command("seed_data", stdout=out)

    # 1. Superuser verification
    admin_user = User.objects.get(username="admin")
    assert admin_user.email == "admin@example.com"
    assert admin_user.is_staff is True
    assert admin_user.is_superuser is True
    assert admin_user.check_password("adminpassword")
    assert hasattr(admin_user, "profile")
    assert admin_user.profile.is_active_roommate is True

    # 2. Roommates verification
    expected_roommates = {
        "alice": 25,
        "bob": 15,
        "charlie": 10,
        "dana": 0,
    }
    for username, points in expected_roommates.items():
        user = User.objects.get(username=username)
        assert user.email == f"{username}@example.com"
        assert user.is_staff is False
        assert user.is_superuser is False
        assert user.check_password("password123")
        assert user.profile.total_points == points
        assert user.profile.is_active_roommate is True

    # 3. Chore templates verification (Frequencies & Strategies)
    templates = ChoreTemplate.objects.all()
    assert templates.count() >= 4

    frequencies = set(templates.values_list("frequency", flat=True))
    assert {
        ChoreTemplate.Frequency.DAILY,
        ChoreTemplate.Frequency.WEEKLY,
        ChoreTemplate.Frequency.BIWEEKLY,
        ChoreTemplate.Frequency.MONTHLY,
    }.issubset(frequencies)

    strategies = set(templates.values_list("assignment_strategy", flat=True))
    assert {
        ChoreTemplate.AssignmentStrategy.ROUND_ROBIN,
        ChoreTemplate.AssignmentStrategy.CLAIM_POOL,
        ChoreTemplate.AssignmentStrategy.FIXED,
    }.issubset(strategies)

    round_robin_tmpl = ChoreTemplate.objects.filter(
        assignment_strategy=ChoreTemplate.AssignmentStrategy.ROUND_ROBIN
    ).first()
    assert len(round_robin_tmpl.rotation_order) > 0

    fixed_tmpl = ChoreTemplate.objects.filter(
        assignment_strategy=ChoreTemplate.AssignmentStrategy.FIXED
    ).first()
    assert fixed_tmpl.default_assignee is not None

    # 4. Chores verification across all lifecycle states
    now = timezone.now()

    # Assigned Pending
    pending_chore = Chore.objects.filter(status=Chore.Status.PENDING, assignee__isnull=False).first()
    assert pending_chore is not None

    # Claimable Pool
    claimable_chore = Chore.objects.filter(status=Chore.Status.CLAIMABLE).first()
    assert claimable_chore is not None
    assert claimable_chore.assignee is None

    # Due soon (< 24h from now)
    due_soon_chore = Chore.objects.filter(
        due_date__gt=now,
        due_date__lte=now + timedelta(hours=24),
    ).first()
    assert due_soon_chore is not None

    # Overdue (past due_date)
    overdue_chore = Chore.objects.filter(
        status=Chore.Status.OVERDUE,
        due_date__lt=now,
    ).first()
    assert overdue_chore is not None

    # Completed chore
    completed_chore = Chore.objects.filter(status=Chore.Status.COMPLETED).first()
    assert completed_chore is not None
    assert completed_chore.completed_at is not None
    assert completed_chore.completed_by is not None
    assert completed_chore.due_date < now

    # 5. ChoreLogs verification
    logs = ChoreLog.objects.all()
    assert logs.count() >= 3

    log_actions = set(logs.values_list("action", flat=True))
    assert {
        ChoreLog.Action.CREATED,
        ChoreLog.Action.CLAIMED,
        ChoreLog.Action.COMPLETED,
    }.issubset(log_actions)

    for log in logs:
        assert log.chore is not None
        assert log.timestamp is not None
        assert len(log.note) > 0


@pytest.mark.django_db
def test_seed_data_is_idempotent_when_run_consecutively():
    # First run
    call_command("seed_data")
    initial_user_count = User.objects.count()
    initial_profile_count = UserProfile.objects.count()
    initial_template_count = ChoreTemplate.objects.count()
    initial_chore_count = Chore.objects.count()
    initial_log_count = ChoreLog.objects.count()

    # Second run without --clean
    call_command("seed_data")

    assert User.objects.count() == initial_user_count
    assert UserProfile.objects.count() == initial_profile_count
    assert ChoreTemplate.objects.count() == initial_template_count
    assert Chore.objects.count() == initial_chore_count
    assert ChoreLog.objects.count() == initial_log_count


@pytest.mark.django_db
def test_seed_data_clean_flag_flushes_existing_non_superuser_data():
    # Initial seeding
    call_command("seed_data")

    # Add custom non-seeded entities
    extra_user = User.objects.create_user(username="temp_roommate", password="password123")
    extra_profile = UserProfile.objects.create(user=extra_user, total_points=50)
    extra_template = ChoreTemplate.objects.create(title="Extra Custom Chore")
    extra_chore = Chore.objects.create(
        title="Custom Extra Instance",
        due_date=timezone.now(),
        assignee=extra_profile,
    )
    extra_log = ChoreLog.objects.create(
        chore=extra_chore,
        user=extra_profile,
        action=ChoreLog.Action.CREATED,
        note="Custom temp log",
    )

    # Re-seed with --clean
    call_command("seed_data", clean=True)

    # Verify custom non-superuser data was purged
    assert not User.objects.filter(username="temp_roommate").exists()
    assert not UserProfile.objects.filter(user__username="temp_roommate").exists()
    assert not ChoreTemplate.objects.filter(title="Extra Custom Chore").exists()
    assert not Chore.objects.filter(title="Custom Extra Instance").exists()
    assert not ChoreLog.objects.filter(note="Custom temp log").exists()

    # Verify standard seeded entities are present
    assert User.objects.filter(username="admin", is_superuser=True).exists()
    assert User.objects.filter(username="alice").exists()
    assert ChoreTemplate.objects.count() == 4
    assert Chore.objects.count() == 5


@pytest.mark.django_db
def test_seed_data_superuser_privileges_and_credentials():
    call_command("seed_data")

    admin = User.objects.get(username="admin")
    assert admin.is_staff is True
    assert admin.is_superuser is True
    assert admin.email == "admin@example.com"
    assert admin.check_password("adminpassword")
    assert hasattr(admin, "profile")


@pytest.mark.django_db
def test_seed_data_stdout_summary_output():
    out = io.StringIO()
    call_command("seed_data", stdout=out)
    output = out.getvalue()

    assert "Database Seeding Complete" in output
    assert "admin" in output
    assert "adminpassword" in output
    assert "password123" in output
    assert "alice" in output
    assert "bob" in output
    assert "charlie" in output
    assert "dana" in output
    assert "Chore Templates:" in output
    assert "Chores:" in output
    assert "Chore Logs:" in output
