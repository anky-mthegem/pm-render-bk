from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta, date
from decimal import Decimal

from projects.models import (
    Project, ProjectMember, Task, TaskDependency,
    ProjectStatus, TaskStatus, TaskPriority, DependencyType, ProjectRole
)
from projects.services.scheduler import cascade_reschedule, calculate_critical_path, save_project_baseline


class Command(BaseCommand):
    help = 'Populates the database with sample projects, Indian Standard (INR ₹) budgets, WBS tasks, and dependencies.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Seeding Milestone Management data as per Indian Standard..."))

        # 1. Create Superuser and Authorized Users
        aman_user, _ = User.objects.get_or_create(
            username='aman',
            defaults={
                'email': 'aman@milestonemanagement.local',
                'first_name': 'Aman',
                'last_name': 'Admin',
                'is_staff': True,
                'is_superuser': True,
                'is_active': True,
            }
        )
        aman_user.first_name = 'Aman'
        aman_user.last_name = 'Admin'
        aman_user.set_password('123456')
        aman_user.is_staff = True
        aman_user.is_superuser = True
        aman_user.is_active = True
        aman_user.save()

        amandeep_user, _ = User.objects.get_or_create(
            username='amanr',
            defaults={
                'email': 'amanr@godrej.com',
                'first_name': 'Amandeep',
                'last_name': 'Singh',
                'is_staff': True,
                'is_active': True,
            }
        )
        amandeep_user.first_name = 'Amandeep'
        amandeep_user.last_name = 'Singh'
        amandeep_user.email = 'amanr@godrej.com'
        amandeep_user.set_password('123456')
        amandeep_user.save()

        swapnil_user, _ = User.objects.get_or_create(
            username='smali',
            defaults={
                'email': 'smali@godrej.com',
                'first_name': 'Swapnil',
                'last_name': 'Mali',
                'is_staff': True,
                'is_active': True,
            }
        )
        swapnil_user.first_name = 'Swapnil'
        swapnil_user.last_name = 'Mali'
        swapnil_user.email = 'smali@godrej.com'
        swapnil_user.set_password('123456')
        swapnil_user.save()

        self.stdout.write(self.style.SUCCESS("Users created (aman / amanr / smali)."))

        # Base reference date
        today = timezone.now().date() if isinstance(timezone.now(), timezone.datetime) else date.today()

        # 2. Create Primary Sample Project: ERP Cloud Modernization (Budget ₹25,00,000 INR)
        project, _ = Project.objects.update_or_create(
            code='erp-cloud-auto',
            defaults={
                'name': 'Enterprise Cloud Migration & ERP Automation',
                'description': 'End-to-end cloud modernization, microservice architecture refactoring, and real-time Gantt automation.',
                'status': ProjectStatus.ACTIVE,
                'owner': aman_user,
                'budget': Decimal('2500000.00'),  # ₹25 Lakhs
                'start_date': today - timedelta(days=14),
                'end_date': today + timedelta(days=45),
            }
        )

        # Clear existing tasks and deps for clean idempotency
        project.tasks.all().delete()

        # Assign memberships
        ProjectMember.objects.get_or_create(project=project, user=aman_user, defaults={'role': ProjectRole.ADMIN})
        ProjectMember.objects.get_or_create(project=project, user=amandeep_user, defaults={'role': ProjectRole.MANAGER})
        ProjectMember.objects.get_or_create(project=project, user=swapnil_user, defaults={'role': ProjectRole.MANAGER})

        # --- PHASE 1: Architecture & Planning ---
        p1 = Task.objects.create(
            project=project,
            name='1.0 Architecture & Strategy',
            description='Discovery, cloud migration blueprint, and security compliance signoff.',
            start_date=today - timedelta(days=14),
            end_date=today - timedelta(days=5),
            status=TaskStatus.COMPLETE,
            priority=TaskPriority.HIGH,
            assignee=amandeep_user,
            sort_order=10
        )

        t1_1 = Task.objects.create(
            project=project,
            parent_task=p1,
            name='1.1 Stakeholder Discovery & Requirement Scoping',
            description='Interview department heads and document legacy system dependencies.',
            start_date=today - timedelta(days=14),
            end_date=today - timedelta(days=10),
            progress=100,
            status=TaskStatus.COMPLETE,
            priority=TaskPriority.MEDIUM,
            estimated_cost=Decimal('150000.00'),  # ₹1.5 Lakhs
            actual_cost=Decimal('145000.00'),
            estimated_hours=40,
            actual_hours=38,
            assignee=amandeep_user,
            sort_order=11
        )

        t1_2 = Task.objects.create(
            project=project,
            parent_task=p1,
            name='1.2 Cloud Infrastructure Blueprint & Security Framework',
            description='Draft Terraform architecture diagrams and VPC networking topologies.',
            start_date=today - timedelta(days=9),
            end_date=today - timedelta(days=5),
            progress=100,
            status=TaskStatus.COMPLETE,
            priority=TaskPriority.CRITICAL,
            estimated_cost=Decimal('220000.00'),  # ₹2.2 Lakhs
            actual_cost=Decimal('210000.00'),
            estimated_hours=50,
            actual_hours=48,
            assignee=swapnil_user,
            sort_order=12
        )

        t1_3 = Task.objects.create(
            project=project,
            parent_task=p1,
            name='1.3 Milestone: Architecture Board Approval',
            description='Executive leadership and security board formal sign-off.',
            start_date=today - timedelta(days=5),
            end_date=today - timedelta(days=5),
            is_milestone=True,
            progress=100,
            status=TaskStatus.COMPLETE,
            priority=TaskPriority.CRITICAL,
            estimated_cost=Decimal('50000.00'),
            actual_cost=Decimal('50000.00'),
            estimated_hours=10,
            actual_hours=10,
            assignee=amandeep_user,
            sort_order=13
        )

        # Dependencies for Phase 1
        TaskDependency.objects.create(from_task=t1_1, to_task=t1_2, dependency_type=DependencyType.FINISH_TO_START)
        TaskDependency.objects.create(from_task=t1_2, to_task=t1_3, dependency_type=DependencyType.FINISH_TO_START)

        # --- PHASE 2: Core Engineering ---
        p2 = Task.objects.create(
            project=project,
            name='2.0 Core Implementation',
            description='Backend microservices, database migration, and frontend UI.',
            start_date=today - timedelta(days=4),
            end_date=today + timedelta(days=18),
            status=TaskStatus.IN_PROGRESS,
            priority=TaskPriority.CRITICAL,
            assignee=amandeep_user,
            sort_order=20
        )

        t2_1 = Task.objects.create(
            project=project,
            parent_task=p2,
            name='2.1 Backend Microservices & REST API',
            description='Build Django REST Framework endpoints, scheduler services, and cascade algorithms.',
            start_date=today - timedelta(days=4),
            end_date=today + timedelta(days=8),
            progress=75,
            status=TaskStatus.IN_PROGRESS,
            priority=TaskPriority.HIGH,
            estimated_cost=Decimal('350000.00'),  # ₹3.5 Lakhs
            actual_cost=Decimal('280000.00'),
            estimated_hours=80,
            actual_hours=60,
            assignee=amandeep_user,
            sort_order=21
        )

        t2_2 = Task.objects.create(
            project=project,
            parent_task=p2,
            name='2.2 Database Schema & Data Migration Pipeline',
            description='Migrate PostgreSQL models, indexes, and write zero-downtime ETL scripts.',
            start_date=today + timedelta(days=2),
            end_date=today + timedelta(days=12),
            progress=40,
            status=TaskStatus.IN_PROGRESS,
            priority=TaskPriority.MEDIUM,
            estimated_cost=Decimal('200000.00'),  # ₹2 Lakhs
            actual_cost=Decimal('85000.00'),
            estimated_hours=45,
            actual_hours=20,
            assignee=swapnil_user,
            sort_order=22
        )

        t2_3 = Task.objects.create(
            project=project,
            parent_task=p2,
            name='2.3 Interactive Milestone Gantt UI & Real-Time Sync',
            description='Dual-pane split view, SVG arrows, drag-to-resize timeline, and Alpine.js reactivity.',
            start_date=today - timedelta(days=2),
            end_date=today + timedelta(days=14),
            progress=65,
            status=TaskStatus.IN_PROGRESS,
            priority=TaskPriority.CRITICAL,
            estimated_cost=Decimal('280000.00'),  # ₹2.8 Lakhs
            actual_cost=Decimal('190000.00'),
            estimated_hours=65,
            actual_hours=45,
            assignee=amandeep_user,
            sort_order=23
        )

        t2_4 = Task.objects.create(
            project=project,
            parent_task=p2,
            name='2.4 Role-Based Access Control & Session Auth',
            description='Admin, Manager, and Member permission layers with audit logs.',
            start_date=today + timedelta(days=5),
            end_date=today + timedelta(days=16),
            progress=20,
            status=TaskStatus.IN_PROGRESS,
            priority=TaskPriority.MEDIUM,
            estimated_cost=Decimal('120000.00'),  # ₹1.2 Lakhs
            actual_cost=Decimal('30000.00'),
            estimated_hours=30,
            actual_hours=8,
            assignee=swapnil_user,
            sort_order=24
        )

        # Dependencies for Phase 2
        TaskDependency.objects.create(from_task=t1_3, to_task=t2_1, dependency_type=DependencyType.FINISH_TO_START)
        TaskDependency.objects.create(from_task=t2_1, to_task=t2_2, dependency_type=DependencyType.START_TO_START, lag_days=3)
        TaskDependency.objects.create(from_task=t2_1, to_task=t2_3, dependency_type=DependencyType.START_TO_START, lag_days=2)
        TaskDependency.objects.create(from_task=t2_1, to_task=t2_4, dependency_type=DependencyType.FINISH_TO_START)

        # --- PHASE 3: Testing & Security ---
        p3 = Task.objects.create(
            project=project,
            name='3.0 Quality Assurance & Security Audits',
            description='Automated regression suite, load testing, and penetration testing.',
            start_date=today + timedelta(days=17),
            end_date=today + timedelta(days=32),
            status=TaskStatus.NOT_STARTED,
            priority=TaskPriority.HIGH,
            assignee=swapnil_user,
            sort_order=30
        )

        t3_1 = Task.objects.create(
            project=project,
            parent_task=p3,
            name='3.1 End-to-End Scheduling Engine & Cascade Tests',
            description='Unit and integration tests for cyclic graph detection and duration recalculations.',
            start_date=today + timedelta(days=17),
            end_date=today + timedelta(days=24),
            progress=0,
            status=TaskStatus.NOT_STARTED,
            priority=TaskPriority.HIGH,
            estimated_cost=Decimal('160000.00'),
            actual_cost=Decimal('0.00'),
            estimated_hours=35,
            actual_hours=0,
            assignee=swapnil_user,
            sort_order=31
        )

        t3_2 = Task.objects.create(
            project=project,
            parent_task=p3,
            name='3.2 Performance Profiling & Stress Testing (1,000+ Tasks)',
            description='Verify sub-100ms render speeds under large enterprise project graphs.',
            start_date=today + timedelta(days=25),
            end_date=today + timedelta(days=30),
            progress=0,
            status=TaskStatus.NOT_STARTED,
            priority=TaskPriority.MEDIUM,
            estimated_cost=Decimal('110000.00'),
            actual_cost=Decimal('0.00'),
            estimated_hours=25,
            actual_hours=0,
            assignee=amandeep_user,
            sort_order=32
        )

        t3_3 = Task.objects.create(
            project=project,
            parent_task=p3,
            name='3.3 Milestone: Security Certification & QA Signoff',
            description='Compliance audit completion with OWASP Top 10 certification.',
            start_date=today + timedelta(days=31),
            end_date=today + timedelta(days=31),
            is_milestone=True,
            progress=0,
            status=TaskStatus.NOT_STARTED,
            priority=TaskPriority.CRITICAL,
            estimated_cost=Decimal('75000.00'),
            actual_cost=Decimal('0.00'),
            estimated_hours=15,
            actual_hours=0,
            assignee=swapnil_user,
            sort_order=33
        )

        # Dependencies for Phase 3
        TaskDependency.objects.create(from_task=t2_3, to_task=t3_1, dependency_type=DependencyType.FINISH_TO_START)
        TaskDependency.objects.create(from_task=t3_1, to_task=t3_2, dependency_type=DependencyType.FINISH_TO_START)
        TaskDependency.objects.create(from_task=t3_2, to_task=t3_3, dependency_type=DependencyType.FINISH_TO_START)

        # --- PHASE 4: Deployment & Go-Live ---
        p4 = Task.objects.create(
            project=project,
            name='4.0 Production Rollout & Enterprise Go-Live',
            description='Kubernetes cluster provisioning, canary rollout, and user training.',
            start_date=today + timedelta(days=32),
            end_date=today + timedelta(days=45),
            status=TaskStatus.NOT_STARTED,
            priority=TaskPriority.CRITICAL,
            assignee=amandeep_user,
            sort_order=40
        )

        t4_1 = Task.objects.create(
            project=project,
            parent_task=p4,
            name='4.1 Production Kubernetes Cluster & Ingress Setup',
            description='Deploy production cluster with autoscaling and multi-zone failover.',
            start_date=today + timedelta(days=32),
            end_date=today + timedelta(days=38),
            progress=0,
            status=TaskStatus.NOT_STARTED,
            priority=TaskPriority.HIGH,
            estimated_cost=Decimal('180000.00'),
            actual_cost=Decimal('0.00'),
            estimated_hours=40,
            actual_hours=0,
            assignee=amandeep_user,
            sort_order=41
        )

        t4_2 = Task.objects.create(
            project=project,
            parent_task=p4,
            name='4.2 Canary Deployment & 100% Traffic Migration',
            description='Gradual traffic migration: 10% -> 50% -> 100% with telemetry verification.',
            start_date=today + timedelta(days=39),
            end_date=today + timedelta(days=44),
            progress=0,
            status=TaskStatus.NOT_STARTED,
            priority=TaskPriority.CRITICAL,
            estimated_cost=Decimal('200000.00'),
            actual_cost=Decimal('0.00'),
            estimated_hours=40,
            actual_hours=0,
            assignee=swapnil_user,
            sort_order=42
        )

        t4_3 = Task.objects.create(
            project=project,
            parent_task=p4,
            name='4.3 Milestone: Enterprise Go-Live & Handover',
            description='Live operations active with 24/7 hypercare support.',
            start_date=today + timedelta(days=45),
            end_date=today + timedelta(days=45),
            is_milestone=True,
            progress=0,
            status=TaskStatus.NOT_STARTED,
            priority=TaskPriority.CRITICAL,
            estimated_cost=Decimal('50000.00'),
            actual_cost=Decimal('0.00'),
            estimated_hours=10,
            actual_hours=0,
            assignee=amandeep_user,
            sort_order=43
        )

        # Dependencies for Phase 4
        TaskDependency.objects.create(from_task=t3_3, to_task=t4_1, dependency_type=DependencyType.FINISH_TO_START)
        TaskDependency.objects.create(from_task=t4_1, to_task=t4_2, dependency_type=DependencyType.FINISH_TO_START)
        TaskDependency.objects.create(from_task=t4_2, to_task=t4_3, dependency_type=DependencyType.FINISH_TO_START)

        # Recalculate parent rollups and CPM
        p1.recalculate_from_subtasks()
        p2.recalculate_from_subtasks()
        p3.recalculate_from_subtasks()
        p4.recalculate_from_subtasks()
        calculate_critical_path(project)
        save_project_baseline(project)
        project.save()

        # 3. Create Second Sample Project: AI Data Platform (Budget ₹15,00,000 INR)
        p_ai, _ = Project.objects.update_or_create(
            code='ai-analytics-platform',
            defaults={
                'name': 'AI Analytics Engine & Data Lakehouse',
                'description': 'Real-time Apache Iceberg lakehouse and generative AI predictive modeling pipeline.',
                'status': ProjectStatus.PLANNING,
                'owner': aman_user,
                'budget': Decimal('1500000.00'),
                'start_date': today,
                'end_date': today + timedelta(days=60),
            }
        )
        p_ai.tasks.all().delete()
        ProjectMember.objects.get_or_create(project=p_ai, user=aman_user, defaults={'role': ProjectRole.ADMIN})
        ProjectMember.objects.get_or_create(project=p_ai, user=amandeep_user, defaults={'role': ProjectRole.MANAGER})
        ProjectMember.objects.get_or_create(project=p_ai, user=swapnil_user, defaults={'role': ProjectRole.MANAGER})

        ai_t1 = Task.objects.create(
            project=p_ai,
            name='1.0 Lakehouse Ingestion Pipeline Setup',
            description='Configure Kafka connectors and Iceberg storage tier.',
            start_date=today,
            end_date=today + timedelta(days=14),
            progress=25,
            status=TaskStatus.IN_PROGRESS,
            priority=TaskPriority.HIGH,
            estimated_cost=Decimal('400000.00'),
            actual_cost=Decimal('100000.00'),
            estimated_hours=60,
            actual_hours=20,
            assignee=amandeep_user,
            sort_order=1
        )
        ai_t2 = Task.objects.create(
            project=p_ai,
            name='2.0 Feature Store & ML Model Training',
            description='Build embeddings pipeline and fine-tune forecasting models.',
            start_date=today + timedelta(days=15),
            end_date=today + timedelta(days=35),
            progress=0,
            status=TaskStatus.NOT_STARTED,
            priority=TaskPriority.CRITICAL,
            estimated_cost=Decimal('600000.00'),
            actual_cost=Decimal('0.00'),
            estimated_hours=90,
            actual_hours=0,
            assignee=swapnil_user,
            sort_order=2
        )
        TaskDependency.objects.create(from_task=ai_t1, to_task=ai_t2, dependency_type=DependencyType.FINISH_TO_START)
        calculate_critical_path(p_ai)
        save_project_baseline(p_ai)
        p_ai.save()

        self.stdout.write(self.style.SUCCESS(f"Successfully seeded {Project.objects.count()} projects with Indian Standard INR (Rs) budgets and tasks!"))
