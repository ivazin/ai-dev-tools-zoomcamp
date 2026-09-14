import pytest
from django.utils import timezone
import datetime
from chores.forms import ChoreCreateForm
from chores.models import UserProfile, ChoreTemplate
from django.contrib.auth.models import User

@pytest.mark.django_db
def test_form_validation_one_off():
    # Empty title fails
    form = ChoreCreateForm(data={
        "chore_type": "one_off",
        "title": "   ",
        "points": 2,
        "due_date": (timezone.now() + datetime.timedelta(days=1)).strftime("%Y-%m-%d %H:%M"),
    })
    assert not form.is_valid()
    assert "title" in form.errors

    # Zero or negative points fails
    form2 = ChoreCreateForm(data={
        "chore_type": "one_off",
        "title": "Wash Car",
        "points": 0,
        "due_date": (timezone.now() + datetime.timedelta(days=1)).strftime("%Y-%m-%d %H:%M"),
    })
    assert not form2.is_valid()
    assert "points" in form2.errors

    # Past due date fails
    form3 = ChoreCreateForm(data={
        "chore_type": "one_off",
        "title": "Wash Car",
        "points": 3,
        "due_date": (timezone.now() - datetime.timedelta(days=1)).strftime("%Y-%m-%d %H:%M"),
    })
    assert not form3.is_valid()
    assert "due_date" in form3.errors

    # Valid one-off
    form_valid = ChoreCreateForm(data={
        "chore_type": "one_off",
        "title": "Wash Car",
        "points": 3,
        "due_date": (timezone.now() + datetime.timedelta(days=2)).strftime("%Y-%m-%d %H:%M"),
    })
    assert form_valid.is_valid()


@pytest.mark.django_db
def test_form_validation_template():
    form_valid = ChoreCreateForm(data={
        "chore_type": "template",
        "title": "Weekly Mop",
        "points": 4,
        "frequency": ChoreTemplate.Frequency.WEEKLY,
        "assignment_strategy": ChoreTemplate.AssignmentStrategy.ROUND_ROBIN,
    })
    assert form_valid.is_valid()
