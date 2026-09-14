from typing import Optional
from chores.models import ChoreTemplate, UserProfile


def get_next_assignee(template: ChoreTemplate) -> Optional[UserProfile]:
    """Deterministically selects the next assignee for a chore template using round-robin rotation.

    - Returns the UserProfile whose ID immediately follows template.last_assigned_user_id in template.rotation_order
      when that user is active (is_active_roommate=True).
    - Loops back to the beginning of template.rotation_order when template.last_assigned_user is the last user
      or when reaching the end of the order.
    - Returns the first active UserProfile in template.rotation_order if template.last_assigned_user is None
      or its ID is not present in rotation_order.
    - Inactive roommates (is_active_roommate=False) are skipped, advancing in circular sequence until an active
      roommate is found.
    - Skips IDs in rotation_order that do not correspond to existing UserProfile records.
    - Returns None if template.rotation_order is empty, contains only nonexistent IDs, or if no roommates in
      rotation_order are active.
    """
    rotation_order = template.rotation_order
    if not rotation_order or not isinstance(rotation_order, list):
        return None

    # Fetch active user profiles corresponding to IDs in rotation_order
    active_profiles = {
        profile.id: profile
        for profile in UserProfile.objects.filter(id__in=rotation_order, is_active_roommate=True)
    }

    n = len(rotation_order)
    start_index = 0

    last_assigned_user_id = template.last_assigned_user_id
    if last_assigned_user_id is not None and last_assigned_user_id in rotation_order:
        start_index = (rotation_order.index(last_assigned_user_id) + 1) % n

    for i in range(n):
        user_id = rotation_order[(start_index + i) % n]
        if user_id in active_profiles:
            return active_profiles[user_id]

    return None


def advance_rotation(template: ChoreTemplate) -> Optional[UserProfile]:
    """Advances the chore template rotation to the next active assignee.

    - Sets template.last_assigned_user to the result of get_next_assignee(template).
    - Persists the update via template.save(update_fields=["last_assigned_user"]).
    - Returns the assigned UserProfile.
    - Leaves template.last_assigned_user unchanged and returns None when get_next_assignee(template) returns None.
    """
    next_assignee = get_next_assignee(template)
    if next_assignee is None:
        return None

    template.last_assigned_user = next_assignee
    template.save(update_fields=["last_assigned_user"])
    return next_assignee
