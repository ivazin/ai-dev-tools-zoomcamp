import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from chores.models import UserProfile, Chore

@pytest.mark.django_db
def test_unauthenticated_redirect_to_login(client):
    response = client.get(reverse("dashboard"))
    assert response.status_code == 302
    assert response.url.startswith(reverse("login"))
    assert "next=" in response.url

@pytest.mark.django_db
def test_login_page_renders(client):
    response = client.get(reverse("login"))
    assert response.status_code == 200
    assert "Roommate Log In" in response.content.decode("utf-8")
    assert "id_username" in response.content.decode("utf-8")

@pytest.mark.django_db
def test_login_success(client):
    user = User.objects.create_user(username="alex", password="password123")
    UserProfile.objects.create(user=user, total_points=15)

    response = client.post(reverse("login"), {
        "username": "alex",
        "password": "password123",
    })
    assert response.status_code == 302
    assert response.url == reverse("dashboard")

    # Following redirect or checking session
    dashboard_resp = client.get(reverse("dashboard"))
    assert dashboard_resp.status_code == 200

@pytest.mark.django_db
def test_login_invalid_credentials(client):
    response = client.post(reverse("login"), {
        "username": "wronguser",
        "password": "wrongpassword",
    })
    assert response.status_code == 200
    assert "Your username and password didn&#x27;t match" in response.content.decode("utf-8") or "didn't match" in response.content.decode("utf-8")

@pytest.mark.django_db
def test_logout_flow(client):
    user = User.objects.create_user(username="sam", password="password123")
    client.login(username="sam", password="password123")

    response = client.post(reverse("logout"))
    assert response.status_code == 302
    assert response.url == reverse("login")

    # Now trying to access protected route redirects to login
    protected_resp = client.get(reverse("dashboard"))
    assert protected_resp.status_code == 302
    assert protected_resp.url.startswith(reverse("login"))

@pytest.mark.django_db
def test_navigation_bar_authenticated_user_points(client):
    user = User.objects.create_user(username="taylor", password="password123")
    UserProfile.objects.create(user=user, total_points=42)
    client.login(username="taylor", password="password123")

    response = client.get(reverse("design_system_preview"))
    content = response.content.decode("utf-8")
    assert "taylor" in content
    assert "⭐ 42 pts" in content
    assert "Log out" in content


@pytest.mark.django_db
def test_dashboard_tabs_and_filtering(client):
    from django.utils import timezone
    import datetime

    user1 = User.objects.create_user(username="user1", password="pw")
    p1 = UserProfile.objects.create(user=user1)

    user2 = User.objects.create_user(username="user2", password="pw")
    p2 = UserProfile.objects.create(user=user2)

    now = timezone.now()

    # Chore 1: assigned to user1 (due in 2 days)
    c1 = Chore.objects.create(
        title="Dishes",
        points=2,
        status=Chore.Status.PENDING,
        assignee=p1,
        due_date=now + datetime.timedelta(days=2),
    )

    # Chore 2: assigned to user2 (due in 5 hours -> due soon)
    c2 = Chore.objects.create(
        title="Vacuum Living Room",
        points=3,
        status=Chore.Status.PENDING,
        assignee=p2,
        due_date=now + datetime.timedelta(hours=5),
    )

    # Chore 3: completed
    c3 = Chore.objects.create(
        title="Take out Trash",
        points=1,
        status=Chore.Status.COMPLETED,
        assignee=p1,
        completed_by=p1,
        due_date=now - datetime.timedelta(days=1),
        completed_at=now - datetime.timedelta(hours=1),
    )

    client.login(username="user1", password="pw")

    # Tab: My Chores (default)
    res_my = client.get(reverse("dashboard"))
    assert res_my.status_code == 200
    assert "Dishes" in res_my.content.decode("utf-8")
    assert "Vacuum Living Room" not in res_my.content.decode("utf-8")
    assert "Take out Trash" not in res_my.content.decode("utf-8")

    # Tab: All Household Chores
    res_all = client.get(reverse("dashboard") + "?tab=all")
    assert res_all.status_code == 200
    assert "Dishes" in res_all.content.decode("utf-8")
    assert "Vacuum Living Room" in res_all.content.decode("utf-8")
    assert "Due Soon" in res_all.content.decode("utf-8")
    assert "Take out Trash" not in res_all.content.decode("utf-8")

    # Tab: Completed Recently
    res_completed = client.get(reverse("dashboard") + "?tab=completed")
    assert res_completed.status_code == 200
    assert "Take out Trash" in res_completed.content.decode("utf-8")
    assert "Dishes" not in res_completed.content.decode("utf-8")


@pytest.mark.django_db
def test_dashboard_empty_states(client):
    user = User.objects.create_user(username="lonely", password="pw")
    UserProfile.objects.create(user=user)
    client.login(username="lonely", password="pw")

    res = client.get(reverse("dashboard") + "?tab=my")
    assert res.status_code == 200
    assert "No chores assigned to you!" in res.content.decode("utf-8")


@pytest.mark.django_db
def test_claim_pool_view_and_empty_state(client):
    from django.utils import timezone
    import datetime

    user = User.objects.create_user(username="claimer", password="pw")
    UserProfile.objects.create(user=user)
    client.login(username="claimer", password="pw")

    # Empty claim pool
    res = client.get(reverse("claim_pool"))
    assert res.status_code == 200
    assert "No chores in the claim pool right now!" in res.content.decode("utf-8")

    # Add claimable chore
    chore = Chore.objects.create(
        title="Mop Kitchen Floor",
        points=4,
        status=Chore.Status.CLAIMABLE,
        assignee=None,
        due_date=timezone.now() + datetime.timedelta(days=1),
    )

    res2 = client.get(reverse("claim_pool"))
    assert res2.status_code == 200
    assert "Mop Kitchen Floor" in res2.content.decode("utf-8")
    assert "Claim Chore" in res2.content.decode("utf-8")


@pytest.mark.django_db
def test_claim_chore_endpoint(client):
    from django.utils import timezone
    import datetime
    from chores.models import ChoreLog

    user = User.objects.create_user(username="sammy", password="pw")
    profile = UserProfile.objects.create(user=user)
    client.login(username="sammy", password="pw")

    chore = Chore.objects.create(
        title="Clean Microwave",
        points=2,
        status=Chore.Status.CLAIMABLE,
        assignee=None,
        due_date=timezone.now() + datetime.timedelta(days=1),
    )

    # Claim via HTMX
    res = client.post(
        reverse("claim_chore", kwargs={"chore_id": chore.id}),
        HTTP_HX_REQUEST="true",
    )
    assert res.status_code == 200
    assert "Clean Microwave" in res.content.decode("utf-8")
    assert "sammy" in res.content.decode("utf-8")

    # Check database
    chore.refresh_from_db()
    assert chore.assignee == profile
    assert chore.status == Chore.Status.PENDING

    # Check log
    log = ChoreLog.objects.filter(chore=chore, action=ChoreLog.Action.CLAIMED).first()
    assert log is not None
    assert log.user == profile

    # Attempting to claim again by another user fails with 409
    other_user = User.objects.create_user(username="other", password="pw")
    UserProfile.objects.create(user=other_user)
    client.login(username="other", password="pw")

    res_fail = client.post(
        reverse("claim_chore", kwargs={"chore_id": chore.id}),
        HTTP_HX_REQUEST="true",
    )
    assert res_fail.status_code == 409
    assert "Cannot claim chore" in res_fail.content.decode("utf-8")


@pytest.mark.django_db
def test_complete_chore_endpoint(client):
    from django.utils import timezone
    import datetime
    from chores.models import ChoreLog

    user = User.objects.create_user(username="finisher", password="pw")
    profile = UserProfile.objects.create(user=user, total_points=5)
    client.login(username="finisher", password="pw")

    chore = Chore.objects.create(
        title="Scrub Sink",
        points=3,
        status=Chore.Status.PENDING,
        assignee=profile,
        due_date=timezone.now() + datetime.timedelta(days=1),
    )

    # Complete via HTMX
    res = client.post(
        reverse("complete_chore", kwargs={"chore_id": chore.id}),
        HTTP_HX_REQUEST="true",
    )
    assert res.status_code == 200
    content = res.content.decode("utf-8")
    assert "Completed" in content
    # Out of band points update
    assert 'id="user-points-badge"' in content
    assert 'hx-swap-oob="true"' in content
    assert "⭐ 8 pts" in content

    # Check DB
    chore.refresh_from_db()
    profile.refresh_from_db()
    assert chore.status == Chore.Status.COMPLETED
    assert chore.completed_by == profile
    assert profile.total_points == 8

    # Check log
    log = ChoreLog.objects.filter(chore=chore, action=ChoreLog.Action.COMPLETED).first()
    assert log is not None
    assert log.user == profile

    # Attempting to complete already completed chore returns 409
    res_again = client.post(
        reverse("complete_chore", kwargs={"chore_id": chore.id}),
        HTTP_HX_REQUEST="true",
    )
    assert res_again.status_code == 409
    assert "already completed" in res_again.content.decode("utf-8")


@pytest.mark.django_db
def test_complete_chore_unauthorized_attempt(client):
    from django.utils import timezone
    import datetime

    owner = User.objects.create_user(username="owner", password="pw")
    owner_profile = UserProfile.objects.create(user=owner)

    intruder = User.objects.create_user(username="intruder", password="pw")
    UserProfile.objects.create(user=intruder)

    chore = Chore.objects.create(
        title="Private Chore",
        points=5,
        status=Chore.Status.PENDING,
        assignee=owner_profile,
        due_date=timezone.now() + datetime.timedelta(days=1),
    )

    client.login(username="intruder", password="pw")
    res = client.post(reverse("complete_chore", kwargs={"chore_id": chore.id}))
    assert res.status_code == 403
    assert "Unauthorized" in res.content.decode("utf-8")


@pytest.mark.django_db
def test_create_one_off_chore_view(client):
    from django.utils import timezone
    import datetime
    from chores.models import ChoreLog

    user = User.objects.create_user(username="creator", password="pw")
    profile = UserProfile.objects.create(user=user)
    client.login(username="creator", password="pw")

    future_date = (timezone.now() + datetime.timedelta(days=2)).strftime("%Y-%m-%d %H:%M")
    res = client.post(reverse("chore_create"), {
        "chore_type": "one_off",
        "title": "Clean Oven",
        "description": "Scrub the racks and glass",
        "points": 5,
        "due_date": future_date,
        "assignee": profile.id,
    })
    assert res.status_code == 302
    assert res.url == reverse("dashboard")

    chore = Chore.objects.get(title="Clean Oven")
    assert chore.points == 5
    assert chore.assignee == profile
    assert chore.status == Chore.Status.PENDING

    log = ChoreLog.objects.filter(chore=chore, action=ChoreLog.Action.CREATED).first()
    assert log is not None


@pytest.mark.django_db
def test_create_recurring_template_view(client):
    from chores.models import ChoreTemplate

    user1 = User.objects.create_user(username="roomie1", password="pw")
    p1 = UserProfile.objects.create(user=user1, is_active_roommate=True)
    user2 = User.objects.create_user(username="roomie2", password="pw")
    p2 = UserProfile.objects.create(user=user2, is_active_roommate=True)

    client.login(username="roomie1", password="pw")

    res = client.post(reverse("chore_create"), {
        "chore_type": "template",
        "title": "Clean Bathroom",
        "description": "Weekly deep clean",
        "points": 4,
        "frequency": ChoreTemplate.Frequency.WEEKLY,
        "assignment_strategy": ChoreTemplate.AssignmentStrategy.ROUND_ROBIN,
    })
    assert res.status_code == 302
    assert res.url == reverse("dashboard")

    template = ChoreTemplate.objects.get(title="Clean Bathroom")
    assert template.points == 4
    assert template.is_active is True
    assert p1.id in template.rotation_order
    assert p2.id in template.rotation_order


@pytest.mark.django_db
def test_leaderboard_view_metrics_and_champion(client):
    from django.utils import timezone
    import datetime

    # Active roommates
    u1 = User.objects.create_user(username="alice", password="pw")
    p1 = UserProfile.objects.create(user=u1, total_points=20, is_active_roommate=True)

    u2 = User.objects.create_user(username="bob", password="pw")
    p2 = UserProfile.objects.create(user=u2, total_points=10, is_active_roommate=True)

    # Inactive roommate (should be excluded)
    u3 = User.objects.create_user(username="inactive_dave", password="pw")
    UserProfile.objects.create(user=u3, total_points=50, is_active_roommate=False)

    # Chore completed by alice
    Chore.objects.create(
        title="Dishes",
        points=5,
        status=Chore.Status.COMPLETED,
        assignee=p1,
        completed_by=p1,
        due_date=timezone.now(),
        completed_at=timezone.now(),
    )

    client.login(username="alice", password="pw")
    res = client.get(reverse("leaderboard"))
    assert res.status_code == 200
    content = res.content.decode("utf-8")

    assert "alice" in content
    assert "bob" in content
    assert "inactive_dave" not in content

    # Champion badge for Alice
    assert "🏆 Chore Champion" in content
    assert "⭐ 20 pts" in content
    assert "⭐ 10 pts" in content


@pytest.mark.django_db
def test_leaderboard_empty_state(client):
    u = User.objects.create_user(username="newbie", password="pw")
    UserProfile.objects.create(user=u, total_points=0, is_active_roommate=True)

    client.login(username="newbie", password="pw")
    res = client.get(reverse("leaderboard"))
    assert res.status_code == 200
    assert "No points earned yet — complete a chore to take the lead!" in res.content.decode("utf-8")





