"""Smoke tests to verify Django project configuration and test harness."""

from io import StringIO
import pytest
from django.conf import settings
from django.core.management import call_command


def test_django_settings_load_cleanly():
    """Assert Django settings load properly and core configuration is intact."""
    assert settings.SECRET_KEY is not None
    assert len(settings.SECRET_KEY) > 0
    assert isinstance(settings.DEBUG, bool)
    assert isinstance(settings.ALLOWED_HOSTS, list)
    assert 'chore_manager' in settings.ROOT_URLCONF


@pytest.mark.django_db
def test_manage_check_reports_zero_errors():
    """Assert manage.py check reports no system errors or configuration issues."""
    out = StringIO()
    call_command("check", stdout=out)
    output = out.getvalue()
    assert "System check identified no issues" in output

