from django.urls import path
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import HttpResponse

def design_system_preview(request):
    return render(request, "design_system_preview.html")

@login_required
def placeholder_view(request):
    return HttpResponse("OK")

from chores.views import (
    dashboard_view,
    claim_pool_view,
    claim_chore_view,
    complete_chore_view,
    chore_create_view,
    leaderboard_view,
)

urlpatterns = [
    path("login/", auth_views.LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("design-system-preview/", design_system_preview, name="design_system_preview"),
    path("", dashboard_view, name="dashboard"),
    path("pool/", claim_pool_view, name="claim_pool"),
    path("chores/<int:chore_id>/claim/", claim_chore_view, name="claim_chore"),
    path("chores/<int:chore_id>/complete/", complete_chore_view, name="complete_chore"),
    path("create/", chore_create_view, name="chore_create"),
    path("leaderboard/", leaderboard_view, name="leaderboard"),
    path("profile/", placeholder_view, name="profile"),
]



