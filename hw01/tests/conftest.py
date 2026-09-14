import pytest
from django.contrib.auth.models import User
from chores.models import UserProfile, ChoreTemplate


@pytest.fixture
def create_profile():
    def _create_profile(username, is_active_roommate=True):
        user = User.objects.create_user(username=username, password="password123")
        profile = UserProfile.objects.create(user=user, is_active_roommate=is_active_roommate)
        return profile

    return _create_profile
