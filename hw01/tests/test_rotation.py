import pytest
from chores.models import ChoreTemplate, UserProfile
from chores.services.rotation_service import get_next_assignee, advance_rotation


@pytest.mark.django_db
def test_get_next_assignee_first_in_order_when_last_assigned_none(create_profile):
    p1 = create_profile("alice")
    p2 = create_profile("bob")
    p3 = create_profile("charlie")

    template = ChoreTemplate.objects.create(
        title="Dishes",
        rotation_order=[p1.id, p2.id, p3.id],
        last_assigned_user=None,
    )

    assignee = get_next_assignee(template)
    assert assignee == p1


@pytest.mark.django_db
def test_get_next_assignee_first_in_order_when_last_assigned_not_in_rotation_order(create_profile):
    p1 = create_profile("alice")
    p2 = create_profile("bob")
    p_other = create_profile("dave")

    template = ChoreTemplate.objects.create(
        title="Dishes",
        rotation_order=[p1.id, p2.id],
        last_assigned_user=p_other,
    )

    assignee = get_next_assignee(template)
    assert assignee == p1


@pytest.mark.django_db
def test_get_next_assignee_advances_sequentially(create_profile):
    p1 = create_profile("alice")
    p2 = create_profile("bob")
    p3 = create_profile("charlie")

    template = ChoreTemplate.objects.create(
        title="Dishes",
        rotation_order=[p1.id, p2.id, p3.id],
        last_assigned_user=p1,
    )

    assignee = get_next_assignee(template)
    assert assignee == p2


@pytest.mark.django_db
def test_get_next_assignee_wraps_around_to_beginning(create_profile):
    p1 = create_profile("alice")
    p2 = create_profile("bob")
    p3 = create_profile("charlie")

    template = ChoreTemplate.objects.create(
        title="Dishes",
        rotation_order=[p1.id, p2.id, p3.id],
        last_assigned_user=p3,
    )

    assignee = get_next_assignee(template)
    assert assignee == p1


@pytest.mark.django_db
def test_get_next_assignee_skips_inactive_roommates(create_profile):
    p1 = create_profile("alice", is_active_roommate=True)
    p2 = create_profile("bob", is_active_roommate=False)
    p3 = create_profile("charlie", is_active_roommate=True)

    template = ChoreTemplate.objects.create(
        title="Trash",
        rotation_order=[p1.id, p2.id, p3.id],
        last_assigned_user=p1,
    )

    assignee = get_next_assignee(template)
    assert assignee == p3


@pytest.mark.django_db
def test_get_next_assignee_skips_nonexistent_ids(create_profile):
    p1 = create_profile("alice")
    p2 = create_profile("bob")
    non_existent_id = 99999

    template = ChoreTemplate.objects.create(
        title="Trash",
        rotation_order=[p1.id, non_existent_id, p2.id],
        last_assigned_user=p1,
    )

    assignee = get_next_assignee(template)
    assert assignee == p2


@pytest.mark.django_db
def test_get_next_assignee_returns_none_when_empty_rotation_order():
    template = ChoreTemplate.objects.create(
        title="Trash",
        rotation_order=[],
    )

    assignee = get_next_assignee(template)
    assert assignee is None


@pytest.mark.django_db
def test_get_next_assignee_returns_none_when_all_nonexistent_ids():
    template = ChoreTemplate.objects.create(
        title="Trash",
        rotation_order=[8888, 9999],
    )

    assignee = get_next_assignee(template)
    assert assignee is None


@pytest.mark.django_db
def test_get_next_assignee_returns_none_when_no_active_roommates(create_profile):
    p1 = create_profile("alice", is_active_roommate=False)
    p2 = create_profile("bob", is_active_roommate=False)

    template = ChoreTemplate.objects.create(
        title="Trash",
        rotation_order=[p1.id, p2.id],
    )

    assignee = get_next_assignee(template)
    assert assignee is None


@pytest.mark.django_db
def test_get_next_assignee_single_active_roommate(create_profile):
    p1 = create_profile("alice", is_active_roommate=True)

    template = ChoreTemplate.objects.create(
        title="Trash",
        rotation_order=[p1.id],
        last_assigned_user=p1,
    )

    assignee = get_next_assignee(template)
    assert assignee == p1


@pytest.mark.django_db
def test_advance_rotation_updates_last_assigned_user_and_persists(create_profile):
    p1 = create_profile("alice")
    p2 = create_profile("bob")

    template = ChoreTemplate.objects.create(
        title="Kitchen Cleaning",
        rotation_order=[p1.id, p2.id],
        last_assigned_user=p1,
    )

    assigned = advance_rotation(template)
    assert assigned == p2
    assert template.last_assigned_user == p2

    template.refresh_from_db()
    assert template.last_assigned_user == p2


@pytest.mark.django_db
def test_advance_rotation_full_cycle(create_profile):
    p1 = create_profile("alice")
    p2 = create_profile("bob")
    p3 = create_profile("charlie")

    template = ChoreTemplate.objects.create(
        title="Bathroom Cleaning",
        rotation_order=[p1.id, p2.id, p3.id],
        last_assigned_user=None,
    )

    # First advance -> p1
    res1 = advance_rotation(template)
    assert res1 == p1
    template.refresh_from_db()
    assert template.last_assigned_user == p1

    # Second advance -> p2
    res2 = advance_rotation(template)
    assert res2 == p2
    template.refresh_from_db()
    assert template.last_assigned_user == p2

    # Third advance -> p3
    res3 = advance_rotation(template)
    assert res3 == p3
    template.refresh_from_db()
    assert template.last_assigned_user == p3

    # Fourth advance -> wrap around to p1
    res4 = advance_rotation(template)
    assert res4 == p1
    template.refresh_from_db()
    assert template.last_assigned_user == p1


@pytest.mark.django_db
def test_advance_rotation_returns_none_and_leaves_unchanged_when_no_assignee(create_profile):
    p1 = create_profile("alice", is_active_roommate=False)

    template = ChoreTemplate.objects.create(
        title="Yard Work",
        rotation_order=[p1.id],
        last_assigned_user=None,
    )

    result = advance_rotation(template)
    assert result is None
    template.refresh_from_db()
    assert template.last_assigned_user is None


@pytest.mark.django_db
def test_advance_rotation_preserves_previous_last_assigned_when_no_active_assignee(create_profile):
    p1 = create_profile("alice", is_active_roommate=False)
    p_prev = create_profile("bob", is_active_roommate=False)

    template = ChoreTemplate.objects.create(
        title="Yard Work",
        rotation_order=[p1.id],
        last_assigned_user=p_prev,
    )

    result = advance_rotation(template)
    assert result is None
    template.refresh_from_db()
    assert template.last_assigned_user == p_prev
