from django.contrib.auth.models import User
from django.db import models


class UserProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    total_points = models.IntegerField(default=0)
    is_active_roommate = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.username} ({self.total_points} pts)"


class ChoreTemplate(models.Model):
    class Frequency(models.TextChoices):
        DAILY = "DAILY", "Daily"
        WEEKLY = "WEEKLY", "Weekly"
        BIWEEKLY = "BIWEEKLY", "Biweekly"
        MONTHLY = "MONTHLY", "Monthly"

    class AssignmentStrategy(models.TextChoices):
        ROUND_ROBIN = "ROUND_ROBIN", "Round Robin"
        CLAIM_POOL = "CLAIM_POOL", "Claim Pool"
        FIXED = "FIXED", "Fixed"

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    points = models.PositiveIntegerField(default=1)
    frequency = models.CharField(
        max_length=20,
        choices=Frequency.choices,
        default=Frequency.WEEKLY,
    )
    assignment_strategy = models.CharField(
        max_length=20,
        choices=AssignmentStrategy.choices,
        default=AssignmentStrategy.ROUND_ROBIN,
    )
    default_assignee = models.ForeignKey(
        UserProfile,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="default_template_chores",
    )
    rotation_order = models.JSONField(default=list, blank=True)
    last_assigned_user = models.ForeignKey(
        UserProfile,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="last_assigned_template_chores",
    )
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title


class Chore(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        CLAIMABLE = "CLAIMABLE", "Claimable"
        COMPLETED = "COMPLETED", "Completed"
        OVERDUE = "OVERDUE", "Overdue"

    template = models.ForeignKey(
        ChoreTemplate,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="chores",
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    points = models.PositiveIntegerField(default=1)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    assignee = models.ForeignKey(
        UserProfile,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="assigned_chores",
    )
    due_date = models.DateTimeField()
    completed_at = models.DateTimeField(null=True, blank=True)
    completed_by = models.ForeignKey(
        UserProfile,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="completed_chores",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.status})"

    @property
    def urgency(self):
        """Returns urgency classification: 'overdue', 'due-soon', or 'normal'."""
        if self.status == self.Status.COMPLETED:
            return "completed"
        if self.status == self.Status.OVERDUE:
            return "overdue"
        from django.utils import timezone
        import datetime
        now = timezone.now()
        if self.due_date < now:
            return "overdue"
        if self.due_date <= now + datetime.timedelta(hours=24):
            return "due-soon"
        return "normal"



class ChoreLog(models.Model):
    class Action(models.TextChoices):
        CREATED = "CREATED", "Created"
        CLAIMED = "CLAIMED", "Claimed"
        COMPLETED = "COMPLETED", "Completed"
        REASSIGNED = "REASSIGNED", "Reassigned"
        OVERDUE_ALERT = "OVERDUE_ALERT", "Overdue Alert"

    chore = models.ForeignKey(
        Chore,
        on_delete=models.CASCADE,
        related_name="logs",
    )
    user = models.ForeignKey(
        UserProfile,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="chore_logs",
    )
    action = models.CharField(
        max_length=20,
        choices=Action.choices,
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    note = models.TextField(blank=True)

    def __str__(self):
        return f"{self.chore.title} - {self.action} at {self.timestamp}"

