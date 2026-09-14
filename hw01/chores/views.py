from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from chores.models import Chore

@login_required
def dashboard_view(request):
    tab = request.GET.get("tab", "my")
    user_profile = getattr(request.user, "profile", None)

    # Base querysets
    my_chores_qs = Chore.objects.filter(
        assignee=user_profile
    ).exclude(status=Chore.Status.COMPLETED).order_by("due_date")

    all_chores_qs = Chore.objects.exclude(
        status=Chore.Status.COMPLETED
    ).order_by("due_date")

    completed_chores_qs = Chore.objects.filter(
        status=Chore.Status.COMPLETED
    ).order_by("-completed_at")

    if tab == "all":
        chores = all_chores_qs
    elif tab == "completed":
        chores = completed_chores_qs
    else:
        tab = "my"
        chores = my_chores_qs

    context = {
        "active_tab": tab,
        "chores": chores,
        "my_chores_count": my_chores_qs.count(),
        "all_chores_count": all_chores_qs.count(),
        "completed_chores_count": completed_chores_qs.count(),
    }
    return render(request, "chores/dashboard.html", context)


@login_required
def claim_pool_view(request):
    chores = Chore.objects.filter(
        status=Chore.Status.CLAIMABLE,
        assignee__isnull=True,
    ).order_by("due_date")

    return render(request, "chores/claim_pool.html", {"chores": chores})


@login_required
def claim_chore_view(request, chore_id):
    from django.shortcuts import get_object_or_404, redirect
    from django.http import HttpResponse
    from chores.services.chore_service import claim_chore

    if request.method != "POST":
        return HttpResponse("Method not allowed", status=405)

    chore = get_object_or_404(Chore, id=chore_id)
    user_profile = getattr(request.user, "profile", None)

    if not user_profile:
        return HttpResponse('<div class="alert alert-danger">User profile not found.</div>', status=400)

    try:
        updated_chore = claim_chore(chore, user_profile)
    except ValueError as e:
        return HttpResponse(
            f'<div class="alert alert-danger" id="chore-{chore.id}">{str(e)}</div>',
            status=409,
        )

    if request.headers.get("HX-Request") == "true":
        return render(
            request,
            "chores/partials/chore_card.html",
            {"chore": updated_chore, "user": request.user},
        )

    return redirect("claim_pool")


@login_required
def complete_chore_view(request, chore_id):
    from django.shortcuts import get_object_or_404, redirect
    from django.http import HttpResponse
    from chores.services.chore_service import complete_chore

    if request.method != "POST":
        return HttpResponse("Method not allowed", status=405)

    chore = get_object_or_404(Chore, id=chore_id)
    user_profile = getattr(request.user, "profile", None)

    if not user_profile:
        return HttpResponse('<div class="alert alert-danger">User profile not found.</div>', status=400)

    # Permission check: assignee or staff
    if chore.assignee != user_profile and not request.user.is_staff:
        return HttpResponse(
            '<div class="alert alert-danger">Unauthorized: you can only complete chores assigned to you.</div>',
            status=403,
        )

    try:
        updated_chore = complete_chore(chore, user_profile)
    except ValueError as e:
        return HttpResponse(
            f'<div class="alert alert-danger" id="chore-{chore.id}">{str(e)}</div>',
            status=409,
        )

    if request.headers.get("HX-Request") == "true":
        card_html = render(
            request,
            "chores/partials/chore_card.html",
            {"chore": updated_chore, "user": request.user},
        ).content.decode("utf-8")

        # Include OOB swap for user points in navbar
        user_profile.refresh_from_db()
        oob_badge = f'<span class="badge badge-points" id="user-points-badge" hx-swap-oob="true">⭐ {user_profile.total_points} pts</span>'
        return HttpResponse(card_html + "\n" + oob_badge)

    return redirect("dashboard")


@login_required
def chore_create_view(request):
    from django.contrib import messages
    from django.shortcuts import redirect
    from chores.forms import ChoreCreateForm
    from chores.models import Chore, ChoreTemplate, ChoreLog, UserProfile

    if request.method == "POST":
        form = ChoreCreateForm(request.POST)
        if form.is_valid():
            chore_type = form.cleaned_data["chore_type"]
            title = form.cleaned_data["title"]
            description = form.cleaned_data["description"]
            points = form.cleaned_data["points"]
            user_profile = getattr(request.user, "profile", None)

            if chore_type == "one_off":
                due_date = form.cleaned_data["due_date"]
                assignee = form.cleaned_data["assignee"]
                status = Chore.Status.PENDING if assignee else Chore.Status.CLAIMABLE

                chore = Chore.objects.create(
                    title=title,
                    description=description,
                    points=points,
                    due_date=due_date,
                    assignee=assignee,
                    status=status,
                )
                ChoreLog.objects.create(
                    chore=chore,
                    user=user_profile,
                    action=ChoreLog.Action.CREATED,
                    note=f"Created one-off chore by {request.user.username}",
                )
                messages.success(request, f"Chore '{title}' created successfully!")
            else:
                frequency = form.cleaned_data["frequency"]
                assignment_strategy = form.cleaned_data["assignment_strategy"]

                active_roommates = list(
                    UserProfile.objects.filter(is_active_roommate=True).values_list("id", flat=True)
                )
                template = ChoreTemplate.objects.create(
                    title=title,
                    description=description,
                    points=points,
                    frequency=frequency,
                    assignment_strategy=assignment_strategy,
                    is_active=True,
                    rotation_order=active_roommates if assignment_strategy == ChoreTemplate.AssignmentStrategy.ROUND_ROBIN else [],
                )
                messages.success(request, f"Recurring template '{title}' created successfully!")

            return redirect("dashboard")
    else:
        form = ChoreCreateForm()

    return render(request, "chores/chore_form.html", {"form": form})


@login_required
def leaderboard_view(request):
    from django.db.models import Count, Q
    from chores.models import UserProfile, Chore

    # Active roommates ordered by total_points descending, then completed count
    active_profiles = (
        UserProfile.objects.filter(is_active_roommate=True)
        .annotate(
            completed_count=Count(
                "completed_chores",
                filter=Q(completed_chores__status=Chore.Status.COMPLETED),
            )
        )
        .order_by("-total_points", "-completed_count", "user__username")
    )

    top_points = active_profiles.first().total_points if active_profiles.exists() else 0
    total_household_points = sum(p.total_points for p in active_profiles)

    leaderboard_data = []
    has_any_points = any(p.total_points > 0 for p in active_profiles)

    if has_any_points:
        for index, profile in enumerate(active_profiles, start=1):
            percentage = round((profile.total_points / top_points * 100)) if top_points > 0 else 0
            is_champion = (index == 1 and profile.total_points > 0)
            leaderboard_data.append({
                "rank": index,
                "profile": profile,
                "completed_count": profile.completed_count,
                "percentage": percentage,
                "is_champion": is_champion,
            })

    context = {
        "leaderboard_data": leaderboard_data,
        "total_household_points": total_household_points,
    }
    return render(request, "chores/leaderboard.html", context)




