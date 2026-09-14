from django import forms
from django.utils import timezone
from chores.models import Chore, ChoreTemplate, UserProfile

class ChoreCreateForm(forms.Form):
    CHORE_TYPE_CHOICES = (
        ("one_off", "One-off Chore"),
        ("template", "Recurring Template"),
    )

    chore_type = forms.ChoiceField(
        choices=CHORE_TYPE_CHOICES,
        widget=forms.RadioSelect(attrs={"class": "form-radio"}),
        initial="one_off",
    )
    title = forms.CharField(
        max_length=200,
        required=True,
        widget=forms.TextInput(attrs={"class": "form-input", "placeholder": "e.g., Clean stove"}),
    )
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"class": "form-textarea", "rows": 3, "placeholder": "Optional details..."}),
    )
    points = forms.IntegerField(
        min_value=1,
        initial=1,
        widget=forms.NumberInput(attrs={"class": "form-input"}),
    )

    # One-off specific fields
    due_date = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(attrs={"class": "form-input", "type": "datetime-local"}),
    )
    assignee = forms.ModelChoiceField(
        queryset=UserProfile.objects.filter(is_active_roommate=True),
        required=False,
        empty_label="Unassigned (Available in Pool)",
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    # Recurring specific fields
    frequency = forms.ChoiceField(
        choices=ChoreTemplate.Frequency.choices,
        required=False,
        initial=ChoreTemplate.Frequency.WEEKLY,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    assignment_strategy = forms.ChoiceField(
        choices=ChoreTemplate.AssignmentStrategy.choices,
        required=False,
        initial=ChoreTemplate.AssignmentStrategy.ROUND_ROBIN,
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    def clean_title(self):
        title = self.cleaned_data.get("title", "").strip()
        if not title:
            raise forms.ValidationError("Title cannot be empty.")
        return title

    def clean_points(self):
        points = self.cleaned_data.get("points")
        if points is None or points <= 0:
            raise forms.ValidationError("Points must be greater than 0.")
        return points

    def clean(self):
        cleaned_data = super().clean()
        chore_type = cleaned_data.get("chore_type")
        due_date = cleaned_data.get("due_date")

        if chore_type == "one_off":
            if not due_date:
                self.add_error("due_date", "Due date is required for one-off chores.")
            elif due_date <= timezone.now():
                self.add_error("due_date", "Due date must be in the future.")

        return cleaned_data
