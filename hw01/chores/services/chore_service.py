from django.db import transaction
from django.utils import timezone

from chores.models import Chore, ChoreLog, ChoreTemplate, UserProfile
from chores.services.rotation_service import advance_rotation


def claim_chore(chore: Chore, user_profile: UserProfile) -> Chore:
    """Claims an open claimable chore for an active user profile.

    - Sets chore.assignee = user_profile
    - Sets chore.status = Chore.Status.PENDING
    - Saves chore
    - Creates ChoreLog(chore=chore, user=user_profile, action=ChoreLog.Action.CLAIMED)
    - Returns the updated chore.
    - Raises ValueError if user_profile.is_active_roommate is False.
    - Raises ValueError if chore.status != Chore.Status.CLAIMABLE.
    - Raises ValueError if chore.assignee is not None.
    """
    if not user_profile.is_active_roommate:
        raise ValueError("Cannot claim chore: user is not an active roommate.")

    if chore.status != Chore.Status.CLAIMABLE:
        raise ValueError(
            f"Cannot claim chore: status must be {Chore.Status.CLAIMABLE}, but got {chore.status}."
        )

    if chore.assignee is not None:
        raise ValueError("Cannot claim chore: chore is already assigned.")

    with transaction.atomic():
        chore.assignee = user_profile
        chore.status = Chore.Status.PENDING
        chore.save()

        ChoreLog.objects.create(
            chore=chore,
            user=user_profile,
            action=ChoreLog.Action.CLAIMED,
        )

    return chore


def complete_chore(chore: Chore, user_profile: UserProfile) -> Chore:
    """Completes a chore, awards points atomically, logs activity, and triggers rotation if needed.

    - Sets chore.status = Chore.Status.COMPLETED
    - Sets chore.completed_at = timezone.now()
    - Sets chore.completed_by = user_profile
    - Sets chore.assignee = user_profile if chore.assignee was None prior to completion
    - Increments user_profile.total_points by chore.points
    - Saves chore and user_profile
    - Creates ChoreLog(chore=chore, user=user_profile, action=ChoreLog.Action.COMPLETED)
    - Invokes advance_rotation(chore.template) if chore.template is present and
      chore.template.assignment_strategy == ChoreTemplate.AssignmentStrategy.ROUND_ROBIN
    - Returns the updated chore.
    - Raises ValueError if user_profile.is_active_roommate is False.
    - Raises ValueError if chore.status == Chore.Status.COMPLETED.
    """
    if not user_profile.is_active_roommate:
        raise ValueError("Cannot complete chore: user is not an active roommate.")

    if chore.status == Chore.Status.COMPLETED:
        raise ValueError("Cannot complete chore: chore is already completed.")

    with transaction.atomic():
        if chore.assignee is None:
            chore.assignee = user_profile

        chore.status = Chore.Status.COMPLETED
        chore.completed_at = timezone.now()
        chore.completed_by = user_profile
        chore.save()

        user_profile.total_points += chore.points
        user_profile.save()

        ChoreLog.objects.create(
            chore=chore,
            user=user_profile,
            action=ChoreLog.Action.COMPLETED,
        )

        if (
            chore.template is not None
            and chore.template.assignment_strategy == ChoreTemplate.AssignmentStrategy.ROUND_ROBIN
        ):
            advance_rotation(chore.template)

    return chore


def reassign_chore(chore: Chore, new_user_profile: UserProfile) -> Chore:
    """Reassigns a chore to a new active user profile and records an audit log.

    - Updates chore.assignee = new_user_profile
    - Updates chore.status to Chore.Status.PENDING if chore.status == Chore.Status.CLAIMABLE,
      while preserving PENDING or OVERDUE status
    - Saves chore
    - Creates ChoreLog(chore=chore, user=new_user_profile, action=ChoreLog.Action.REASSIGNED)
    - Returns the updated chore.
    - Raises ValueError if new_user_profile.is_active_roommate is False.
    - Raises ValueError if chore.status == Chore.Status.COMPLETED.
    """
    if not new_user_profile.is_active_roommate:
        raise ValueError("Cannot reassign chore: target user is not an active roommate.")

    if chore.status == Chore.Status.COMPLETED:
        raise ValueError("Cannot reassign chore: chore is already completed.")

    with transaction.atomic():
        chore.assignee = new_user_profile
        if chore.status == Chore.Status.CLAIMABLE:
            chore.status = Chore.Status.PENDING
        chore.save()

        ChoreLog.objects.create(
            chore=chore,
            user=new_user_profile,
            action=ChoreLog.Action.REASSIGNED,
        )

    return chore
