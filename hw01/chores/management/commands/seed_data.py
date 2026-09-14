from datetime import timedelta
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from chores.models import Chore, ChoreLog, ChoreTemplate, UserProfile


class Command(BaseCommand):
    help = "Seed the database with sample roommates, admin user, chore templates, chores, and logs."

    def add_arguments(self, parser):
        parser.add_argument(
            "--clean",
            action="store_true",
            help="Purge existing chore data and non-superuser accounts before seeding.",
        )

    def handle(self, *args, **options):
        clean = options.get("clean", False)
        with transaction.atomic():
            if clean:
                self.stdout.write("Cleaning existing data...")
                ChoreLog.objects.all().delete()
                Chore.objects.all().delete()
                ChoreTemplate.objects.all().delete()
                UserProfile.objects.filter(user__is_superuser=False).delete()
                User.objects.filter(is_superuser=False).delete()

            # Superuser
            admin_user, _ = User.objects.get_or_create(
                username="admin",
                defaults={
                    "email": "admin@example.com",
                    "is_staff": True,
                    "is_superuser": True,
                },
            )
            admin_user.email = "admin@example.com"
            admin_user.is_staff = True
            admin_user.is_superuser = True
            admin_user.set_password("adminpassword")
            admin_user.save()

            admin_profile, _ = UserProfile.objects.get_or_create(
                user=admin_user,
                defaults={"total_points": 0, "is_active_roommate": True},
            )
            admin_profile.is_active_roommate = True
            admin_profile.save()

            # Roommates
            roommates_data = [
                {"username": "alice", "email": "alice@example.com", "points": 25},
                {"username": "bob", "email": "bob@example.com", "points": 15},
                {"username": "charlie", "email": "charlie@example.com", "points": 10},
                {"username": "dana", "email": "dana@example.com", "points": 0},
            ]

            profiles = {}
            for data in roommates_data:
                user, _ = User.objects.get_or_create(
                    username=data["username"],
                    defaults={
                        "email": data["email"],
                        "is_staff": False,
                        "is_superuser": False,
                    },
                )
                user.email = data["email"]
                user.is_staff = False
                user.is_superuser = False
                user.set_password("password123")
                user.save()

                profile, _ = UserProfile.objects.get_or_create(
                    user=user,
                    defaults={
                        "total_points": data["points"],
                        "is_active_roommate": True,
                    },
                )
                profile.total_points = data["points"]
                profile.is_active_roommate = True
                profile.save()
                profiles[data["username"]] = profile

            # Chore Templates
            templates_data = [
                {
                    "title": "Take Out Trash",
                    "description": "Empty kitchen trash and recycling bins into outside containers.",
                    "points": 2,
                    "frequency": ChoreTemplate.Frequency.DAILY,
                    "assignment_strategy": ChoreTemplate.AssignmentStrategy.ROUND_ROBIN,
                    "rotation_order": [
                        profiles["alice"].id,
                        profiles["bob"].id,
                        profiles["charlie"].id,
                        profiles["dana"].id,
                    ],
                    "default_assignee": None,
                    "last_assigned_user": profiles["alice"],
                    "is_active": True,
                },
                {
                    "title": "Clean Kitchen & Counters",
                    "description": "Wipe down kitchen countertops, stove, and wash remaining dishes.",
                    "points": 5,
                    "frequency": ChoreTemplate.Frequency.WEEKLY,
                    "assignment_strategy": ChoreTemplate.AssignmentStrategy.ROUND_ROBIN,
                    "rotation_order": [
                        profiles["bob"].id,
                        profiles["charlie"].id,
                        profiles["dana"].id,
                        profiles["alice"].id,
                    ],
                    "default_assignee": None,
                    "last_assigned_user": None,
                    "is_active": True,
                },
                {
                    "title": "Mop Common Areas & Vacuum",
                    "description": "Vacuum living room rugs and mop common area floors.",
                    "points": 8,
                    "frequency": ChoreTemplate.Frequency.BIWEEKLY,
                    "assignment_strategy": ChoreTemplate.AssignmentStrategy.CLAIM_POOL,
                    "rotation_order": [],
                    "default_assignee": None,
                    "last_assigned_user": None,
                    "is_active": True,
                },
                {
                    "title": "Deep Clean Bathroom",
                    "description": "Scrub shower tiles, clean toilet, sink, and restock supplies.",
                    "points": 15,
                    "frequency": ChoreTemplate.Frequency.MONTHLY,
                    "assignment_strategy": ChoreTemplate.AssignmentStrategy.FIXED,
                    "rotation_order": [],
                    "default_assignee": profiles["charlie"],
                    "last_assigned_user": None,
                    "is_active": True,
                },
            ]

            seeded_templates = {}
            for t_data in templates_data:
                template, _ = ChoreTemplate.objects.update_or_create(
                    title=t_data["title"],
                    defaults=t_data,
                )
                seeded_templates[t_data["title"]] = template

            # Active Chores across all lifecycle states
            now = timezone.now()

            chores_data = [
                {
                    "title": "Take Out Trash - Daily Morning",
                    "template": seeded_templates["Take Out Trash"],
                    "description": "Empty trash before 10am",
                    "points": 2,
                    "status": Chore.Status.PENDING,
                    "assignee": profiles["alice"],
                    "due_date": now + timedelta(days=2),
                    "completed_at": None,
                    "completed_by": None,
                    "logs": [
                        {
                            "action": ChoreLog.Action.CREATED,
                            "user": profiles["alice"],
                            "note": "Scheduled daily trash chore assigned to Alice.",
                        }
                    ],
                },
                {
                    "title": "Mop Common Areas - Weekend Pool",
                    "template": seeded_templates["Mop Common Areas & Vacuum"],
                    "description": "Mop the common living area and vacuum rugs",
                    "points": 8,
                    "status": Chore.Status.CLAIMABLE,
                    "assignee": None,
                    "due_date": now + timedelta(days=3),
                    "completed_at": None,
                    "completed_by": None,
                    "logs": [
                        {
                            "action": ChoreLog.Action.CREATED,
                            "user": None,
                            "note": "Open chore added to claim pool.",
                        }
                    ],
                },
                {
                    "title": "Clean Kitchen & Counters - Evening Shift",
                    "template": seeded_templates["Clean Kitchen & Counters"],
                    "description": "Wipe down stove and counters before bedtime",
                    "points": 5,
                    "status": Chore.Status.PENDING,
                    "assignee": profiles["bob"],
                    "due_date": now + timedelta(hours=12),
                    "completed_at": None,
                    "completed_by": None,
                    "logs": [
                        {
                            "action": ChoreLog.Action.CREATED,
                            "user": profiles["bob"],
                            "note": "Kitchen chore generated.",
                        },
                        {
                            "action": ChoreLog.Action.CLAIMED,
                            "user": profiles["bob"],
                            "note": "Bob claimed this chore from the pool.",
                        },
                    ],
                },
                {
                    "title": "Take Out Trash - Past Due",
                    "template": seeded_templates["Take Out Trash"],
                    "description": "Overdue trash chore",
                    "points": 2,
                    "status": Chore.Status.OVERDUE,
                    "assignee": profiles["dana"],
                    "due_date": now - timedelta(days=1),
                    "completed_at": None,
                    "completed_by": None,
                    "logs": [
                        {
                            "action": ChoreLog.Action.CREATED,
                            "user": profiles["dana"],
                            "note": "Assigned to Dana.",
                        }
                    ],
                },
                {
                    "title": "Deep Clean Bathroom - Monthly Complete",
                    "template": seeded_templates["Deep Clean Bathroom"],
                    "description": "Deep clean bathroom completed",
                    "points": 15,
                    "status": Chore.Status.COMPLETED,
                    "assignee": profiles["charlie"],
                    "due_date": now - timedelta(days=2),
                    "completed_at": now - timedelta(days=1),
                    "completed_by": profiles["charlie"],
                    "logs": [
                        {
                            "action": ChoreLog.Action.CREATED,
                            "user": profiles["charlie"],
                            "note": "Created monthly bathroom chore.",
                        },
                        {
                            "action": ChoreLog.Action.COMPLETED,
                            "user": profiles["charlie"],
                            "note": "Charlie finished deep cleaning the bathroom.",
                        },
                    ],
                },
            ]

            total_chores_count = 0
            total_logs_count = 0

            for c_data in chores_data:
                logs = c_data.pop("logs")
                chore, _ = Chore.objects.update_or_create(
                    title=c_data["title"],
                    defaults=c_data,
                )
                total_chores_count += 1
                for log_data in logs:
                    ChoreLog.objects.update_or_create(
                        chore=chore,
                        action=log_data["action"],
                        defaults={
                            "user": log_data["user"],
                            "note": log_data["note"],
                        },
                    )
                    total_logs_count += 1

            self.stdout.write(self.style.SUCCESS("=== Database Seeding Complete ==="))
            self.stdout.write("Admin Superuser:")
            self.stdout.write("  - Username: admin")
            self.stdout.write("  - Email: admin@example.com")
            self.stdout.write("  - Password: adminpassword")
            self.stdout.write("\nRoommates (Password: password123):")
            for name, prof in profiles.items():
                self.stdout.write(f"  - {name} ({prof.total_points} pts)")
            self.stdout.write(f"\nSummary:")
            self.stdout.write(f"  - Chore Templates: {len(seeded_templates)}")
            self.stdout.write(f"  - Chores: {total_chores_count}")
            self.stdout.write(f"  - Chore Logs: {total_logs_count}")
