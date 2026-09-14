import pytest
from django.test import Client
from django.urls import reverse

def test_design_system_preview_renders():
    client = Client()
    response = client.get(reverse("design_system_preview"))
    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert "styles.css" in content
    assert "htmx.org" in content
    assert 'hx-headers=\'{"X-CSRFToken":' in content
    assert "Design System Test Suite" in content
    assert "badge-warning" in content
    assert "btn-primary" in content
