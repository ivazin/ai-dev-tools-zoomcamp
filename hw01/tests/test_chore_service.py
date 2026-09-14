from datetime import timedelta
from unittest.mock import patch
import pytest
from django.db import DatabaseError
from django.utils import timezone

from chores.models import Chore, ChoreLog, ChoreTemplate, UserProfile
from chores.services.chore_service import claim_chore, complete_chore, reassign_chore


@pytest.fixture
def sample_chore(create_profile):
    def _sample_chore(
        status=Chore.Status.CLAIMABLE,
        assignee=None,
        points=5,
        template=None,
    ):
        return Chore.objects.create(
            title="Clean Kitchen",
            description="Wipe counters and mop floor",
            points=points,
            status=status,
            assignee=assignee,
            due_date=timezone.now() + timedelta(days=1),
            template=template,
        )

    return _sample_chore


# --- claim_chore tests ---


@pytest.mark.django_db
def test_claim_chore_success(create_profile, sample_chore):
    user = create_profile("alice")
    chore = sample_chore(status=Chore.Status.CLAIMABLE, assignee=None)

    updated_chore = claim_chore(chore, user)

    assert updated_chore.assignee == user
    assert updated_chore.status == Chore.Status.PENDING

    chore.refresh_from_db()
    assert chore.assignee == user
    assert chore.status == Chore.Status.PENDING

    logs = ChoreLog.objects.filter(chore=chore)
    assert logs.count() == 1
    log = logs.first()
    assert log.user == user
    assert log.action == ChoreLog.Action.CLAIMED


@pytest.mark.django_db
def test_claim_chore_fails_when_user_inactive(create_profile, sample_chore):
    user = create_profile("inactive_user", is_active_roommate=False)
    chore = sample_chore(status=Chore.Status.CLAIMABLE, assignee=None)

    with pytest.raises(ValueError, match="not an active roommate"):
        claim_chore(chore, user)

    chore.refresh_from_db()
    assert chore.assignee is None
    assert chore.status == Chore.Status.CLAIMABLE
    assert ChoreLog.objects.filter(chore=chore).count() == 0


@pytest.mark.django_db
@pytest.mark.parametrize(
    "invalid_status",
    [Chore.Status.PENDING, Chore.Status.COMPLETED, Chore.Status.OVERDUE],
)
def test_claim_chore_fails_when_status_not_claimable(create_profile, sample_chore, invalid_status):
    user = create_profile("alice")
    chore = sample_chore(status=invalid_status, assignee=None)

    with pytest.raises(ValueError, match="status must be CLAIMABLE"):
        claim_chore(chore, user)

    chore.refresh_from_db()
    assert chore.status == invalid_status
    assert ChoreLog.objects.filter(chore=chore).count() == 0


@pytest.mark.django_db
def test_claim_chore_fails_when_assignee_already_set(create_profile, sample_chore):
    alice = create_profile("alice")
    bob = create_profile("bob")
    chore = sample_chore(status=Chore.Status.CLAIMABLE, assignee=alice)

    with pytest.raises(ValueError, match="already assigned"):
        claim_chore(chore, bob)

    chore.refresh_from_db()
    assert chore.assignee == alice
    assert ChoreLog.objects.filter(chore=chore).count() == 0


@pytest.mark.django_db
def test_claim_chore_atomic_rollback_on_error(create_profile, sample_chore):
    user = create_profile("alice")
    chore = sample_chore(status=Chore.Status.CLAIMABLE, assignee=None)

    with patch("chores.services.chore_service.ChoreLog.objects.create", side_effect=DatabaseError("DB error")):
        with pytest.raises(DatabaseError):
            claim_chore(chore, user)

    chore.refresh_from_db()
    assert chore.assignee is None
    assert chore.status == Chore.Status.CLAIMABLE
    assert ChoreLog.objects.filter(chore=chore).count() == 0


# --- complete_chore tests ---


@pytest.mark.django_db
def test_complete_chore_success_with_existing_assignee(create_profile, sample_chore):
    user = create_profile("alice")
    user.total_points = 10
    user.save()

    chore = sample_chore(status=Chore.Status.PENDING, assignee=user, points=5)

    before_time = timezone.now()
    updated_chore = complete_chore(chore, user)
    after_time = timezone.now()

    assert updated_chore.status == Chore.Status.COMPLETED
    assert updated_chore.completed_by == user
    assert updated_chore.assignee == user
    assert updated_chore.completed_at is not None
    assert before_time <= updated_chore.completed_at <= after_time

    user.refresh_from_db()
    assert user.total_points == 15

    chore.refresh_from_db()
    assert chore.status == Chore.Status.COMPLETED
    assert chore.completed_by == user

    logs = ChoreLog.objects.filter(chore=chore)
    assert logs.count() == 1
    log = logs.first()
    assert log.user == user
    assert log.action == ChoreLog.Action.COMPLETED


@pytest.mark.django_db
def test_complete_chore_assigns_user_if_assignee_none(create_profile, sample_chore):
    user = create_profile("alice")
    chore = sample_chore(status=Chore.Status.CLAIMABLE, assignee=None, points=3)

    updated_chore = complete_chore(chore, user)

    assert updated_chore.assignee == user
    chore.refresh_from_db()
    assert chore.assignee == user


@pytest.mark.django_db
@pytest.mark.parametrize(
    "initial_status",
    [Chore.Status.PENDING, Chore.Status.CLAIMABLE, Chore.Status.OVERDUE],
)
def test_complete_chore_allowed_from_various_statuses(create_profile, sample_chore, initial_status):
    user = create_profile("alice")
    chore = sample_chore(status=initial_status, assignee=user, points=4)

    updated_chore = complete_chore(chore, user)

    assert updated_chore.status == Chore.Status.COMPLETED
    chore.refresh_from_db()
    assert chore.status == Chore.Status.COMPLETED


@pytest.mark.django_db
def test_complete_chore_fails_if_already_completed(create_profile, sample_chore):
    user = create_profile("alice")
    chore = sample_chore(status=Chore.Status.COMPLETED, assignee=user, points=5)

    with pytest.raises(ValueError, match="already completed"):
        complete_chore(chore, user)

    user.refresh_from_db()
    assert user.total_points == 0
    assert ChoreLog.objects.filter(chore=chore).count() == 0


@pytest.mark.django_db
def test_complete_chore_fails_when_user_inactive(create_profile, sample_chore):
    user = create_profile("inactive_user", is_active_roommate=False)
    chore = sample_chore(status=Chore.Status.PENDING, assignee=None, points=5)

    with pytest.raises(ValueError, match="not an active roommate"):
        complete_chore(chore, user)

    chore.refresh_from_db()
    assert chore.status == Chore.Status.PENDING
    user.refresh_from_db()
    assert user.total_points == 0
    assert ChoreLog.objects.filter(chore=chore).count() == 0


@pytest.mark.django_db
def test_complete_chore_triggers_round_robin_rotation(create_profile, sample_chore):
    p1 = create_profile("alice")
    p2 = create_profile("bob")
    p3 = create_profile("charlie")

    template = ChoreTemplate.objects.create(
        title="Dishes",
        assignment_strategy=ChoreTemplate.AssignmentStrategy.ROUND_ROBIN,
        rotation_order=[p1.id, p2.id, p3.id],
        last_assigned_user=p1,
    )

    chore = sample_chore(
        status=Chore.Status.PENDING,
        assignee=p1,
        points=2,
        template=template,
    )

    complete_chore(chore, p1)

    template.refresh_from_db()
    assert template.last_assigned_user == p2


@pytest.mark.django_db
@pytest.mark.parametrize(
    "strategy",
    [ChoreTemplate.AssignmentStrategy.CLAIM_POOL, ChoreTemplate.AssignmentStrategy.FIXED],
)
def test_complete_chore_does_not_trigger_rotation_for_non_round_robin(create_profile, sample_chore, strategy):
    p1 = create_profile("alice")
    p2 = create_profile("bob")

    template = ChoreTemplate.objects.create(
        title="Yard Work",
        assignment_strategy=strategy,
        rotation_order=[p1.id, p2.id],
        last_assigned_user=p1,
    )

    chore = sample_chore(
        status=Chore.Status.PENDING,
        assignee=p1,
        points=2,
        template=template,
    )

    complete_chore(chore, p1)

    template.refresh_from_db()
    assert template.last_assigned_user == p1


@pytest.mark.django_db
def test_complete_chore_without_template_does_not_fail(create_profile, sample_chore):
    user = create_profile("alice")
    chore = sample_chore(status=Chore.Status.PENDING, assignee=user, template=None)

    updated_chore = complete_chore(chore, user)
    assert updated_chore.status == Chore.Status.COMPLETED


@pytest.mark.django_db
def test_complete_chore_atomic_rollback_on_error(create_profile, sample_chore):
    user = create_profile("alice")
    chore = sample_chore(status=Chore.Status.PENDING, assignee=user, points=10)

    with patch("chores.services.chore_service.ChoreLog.objects.create", side_effect=DatabaseError("DB error")):
        with pytest.raises(DatabaseError):
            complete_chore(chore, user)

    chore.refresh_from_db()
    assert chore.status == Chore.Status.PENDING
    assert chore.completed_at is None
    assert chore.completed_by is None

    user.refresh_from_db()
    assert user.total_points == 0
    assert ChoreLog.objects.filter(chore=chore).count() == 0


# --- reassign_chore tests ---


@pytest.mark.django_db
def test_reassign_chore_success_from_pending(create_profile, sample_chore):
    alice = create_profile("alice")
    bob = create_profile("bob")
    chore = sample_chore(status=Chore.Status.PENDING, assignee=alice)

    updated_chore = reassign_chore(chore, bob)

    assert updated_chore.assignee == bob
    assert updated_chore.status == Chore.Status.PENDING

    chore.refresh_from_db()
    assert chore.assignee == bob
    assert chore.status == Chore.Status.PENDING

    logs = ChoreLog.objects.filter(chore=chore)
    assert logs.count() == 1
    log = logs.first()
    assert log.user == bob
    assert log.action == ChoreLog.Action.REASSIGNED


@pytest.mark.django_db
def test_reassign_chore_success_from_overdue_preserves_overdue(create_profile, sample_chore):
    alice = create_profile("alice")
    bob = create_profile("bob")
    chore = sample_chore(status=Chore.Status.OVERDUE, assignee=alice)

    updated_chore = reassign_chore(chore, bob)

    assert updated_chore.assignee == bob
    assert updated_chore.status == Chore.Status.OVERDUE

    chore.refresh_from_db()
    assert chore.status == Chore.Status.OVERDUE


@pytest.mark.django_db
def test_reassign_chore_from_claimable_transitions_to_pending(create_profile, sample_chore):
    bob = create_profile("bob")
    chore = sample_chore(status=Chore.Status.CLAIMABLE, assignee=None)

    updated_chore = reassign_chore(chore, bob)

    assert updated_chore.assignee == bob
    assert updated_chore.status == Chore.Status.PENDING

    chore.refresh_from_db()
    assert chore.assignee == bob
    assert chore.status == Chore.Status.PENDING


@pytest.mark.django_db
def test_reassign_chore_fails_if_completed(create_profile, sample_chore):
    alice = create_profile("alice")
    bob = create_profile("bob")
    chore = sample_chore(status=Chore.Status.COMPLETED, assignee=alice)

    with pytest.raises(ValueError, match="chore is already completed"):
        reassign_chore(chore, bob)

    chore.refresh_from_db()
    assert chore.assignee == alice
    assert ChoreLog.objects.filter(chore=chore).count() == 0


@pytest.mark.django_db
def test_reassign_chore_fails_if_target_user_inactive(create_profile, sample_chore):
    alice = create_profile("alice")
    inactive_user = create_profile("inactive_bob", is_active_roommate=False)
    chore = sample_chore(status=Chore.Status.PENDING, assignee=alice)

    with pytest.raises(ValueError, match="target user is not an active roommate"):
        reassign_chore(chore, inactive_user)

    chore.refresh_from_db()
    assert chore.assignee == alice
    assert ChoreLog.objects.filter(chore=chore).count() == 0


@pytest.mark.django_db
def test_reassign_chore_atomic_rollback_on_error(create_profile, sample_chore):
    alice = create_profile("alice")
    bob = create_profile("bob")
    chore = sample_chore(status=Chore.Status.CLAIMABLE, assignee=None)

    with patch("chores.services.chore_service.ChoreLog.objects.create", side_effect=DatabaseError("DB error")):
        with pytest.raises(DatabaseError):
            reassign_chore(chore, bob)

    chore.refresh_from_db()
    assert chore.assignee is None
    assert chore.status == Chore.Status.CLAIMABLE
    assert ChoreLog.objects.filter(chore=chore).count() == 0
