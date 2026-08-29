from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone
from datetime import timedelta

from teams.models import Department, Team, TeamMembership
from projects.models import Project, Task


class Command(BaseCommand):
    help = 'Seeds team manager with Sundar Nadar as reporting manager and Suraj, Swapnil, Amandeep Singh as direct reports.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Resetting & Seeding Team Management structure..."))

        with transaction.atomic():
            # 1. Clean up old team memberships, teams, and departments
            TeamMembership.objects.all().delete()
            Team.objects.all().delete()
            Department.objects.all().delete()

            # 2. Ensure master admin 'aman' exists strictly as website manager (no teams, no tasks)
            aman, _ = User.objects.get_or_create(
                username='aman',
                defaults={
                    'first_name': 'Aman',
                    'last_name': 'Admin',
                    'email': 'aman@ganttexcel.local',
                    'is_staff': True,
                    'is_superuser': True,
                    'is_active': True,
                }
            )
            if not aman.has_usable_password():
                aman.set_password('123456')
                aman.save()

            # Unassign any tasks that might have been assigned to aman
            Task.objects.filter(assignee=aman).update(assignee=None)

            # Helper to create/get team user
            def get_or_create_user(username, first_name, last_name, email):
                u, created = User.objects.get_or_create(
                    username=username,
                    defaults={
                        'first_name': first_name,
                        'last_name': last_name,
                        'email': email,
                        'is_staff': False,
                        'is_active': True
                    }
                )
                if created:
                    u.set_password('123456')
                    u.save()
                else:
                    u.first_name = first_name
                    u.last_name = last_name
                    u.email = email
                    u.is_active = True
                    u.save()
                return u

            # 3. Create only the specified 4 users
            sundar = get_or_create_user('sundar', 'Sundar', 'Nadar', 'sundar@company.local')
            suraj = get_or_create_user('suraj', 'Suraj', '', 'suraj@company.local')
            swapnil = get_or_create_user('swapnil', 'Swapnil', '', 'swapnil@company.local')
            amandeep = get_or_create_user('amandeep', 'Amandeep', 'Singh', 'amandeep@company.local')

            # 4. Create Department
            dept_eng = Department.objects.create(
                name='Engineering & Delivery',
                code='eng-delivery',
                head=sundar,
                description='Core application architecture, project development, and milestone delivery.'
            )

            # 5. Create Core Team
            team_core = Team.objects.create(
                name='Core Delivery Team',
                code='core-delivery',
                department=dept_eng,
                lead=sundar,
                color='#6366f1',
                description='Primary execution team responsible for development and milestone achievement.'
            )

            # 6. Assign Memberships with direct reporting to Sundar Nadar
            # Sundar Nadar - Team Lead & Reporting Manager
            TeamMembership.objects.create(
                team=team_core,
                user=sundar,
                role='Lead',
                reporting_to=None,
                joined_at=timezone.now().date() - timedelta(days=90)
            )

            # Suraj -> Reports to Sundar Nadar
            TeamMembership.objects.create(
                team=team_core,
                user=suraj,
                role='Senior Developer',
                reporting_to=sundar,
                joined_at=timezone.now().date() - timedelta(days=60)
            )

            # Swapnil -> Reports to Sundar Nadar
            TeamMembership.objects.create(
                team=team_core,
                user=swapnil,
                role='Developer',
                reporting_to=sundar,
                joined_at=timezone.now().date() - timedelta(days=45)
            )

            # Amandeep Singh -> Reports to Sundar Nadar
            TeamMembership.objects.create(
                team=team_core,
                user=amandeep,
                role='Developer',
                reporting_to=sundar,
                joined_at=timezone.now().date() - timedelta(days=30)
            )

            # 7. Link Active Projects to the Core Delivery Team
            for p in Project.objects.all():
                p.assigned_team = team_core
                p.save()

            self.stdout.write(self.style.SUCCESS(
                f"Successfully reset and seeded Team Manager:\n"
                f"- Reporting Manager: Sundar Nadar\n"
                f"- Team Members: Suraj, Swapnil, Amandeep Singh (all reporting to Sundar Nadar)\n"
                f"- Admin 'aman' excluded from teams & tasks."
            ))
