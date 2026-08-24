from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from datetime import date
from django.db import transaction

from projects.models import (
    Project, ProjectMember, Task, TaskDependency,
    ProjectStatus, TaskStatus, TaskPriority, DependencyType, ProjectRole, ActivityLog
)


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        admin_username = request.POST.get('admin_username', '').strip()
        admin_password = request.POST.get('admin_password', '').strip()

        # Check authorization from user 'aman' with password '123456'
        auth_admin = authenticate(request, username=admin_username, password=admin_password)
        if not auth_admin or auth_admin.username != 'aman':
            messages.error(
                request,
                "Authorization Failed: Creating a new user requires valid authorization credentials from admin user 'aman' (password: 123456)."
            )
            form = UserCreationForm(request.POST)
            return render(request, 'auth/register.html', {
                'form': form,
                'admin_username': admin_username
            })

        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Welcome to Milestone Management, {user.username}! (Authorized by admin {auth_admin.username})")
            return redirect('dashboard')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field.capitalize()}: {error}")
    else:
        form = UserCreationForm()
    
    return render(request, 'auth/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.get_full_name() or user.username}!")
            next_url = request.GET.get('next', 'dashboard')
            return redirect(next_url)
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()

    return render(request, 'auth/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('login')


@login_required
def dashboard_view(request):
    projects = Project.objects.all().select_related('owner').prefetch_related('tasks').order_by('-updated_at')
    
    total_projects = projects.count()
    active_projects = projects.filter(status=ProjectStatus.ACTIVE).count()
    completed_projects = projects.filter(status=ProjectStatus.COMPLETED).count()
    
    # User's assigned tasks
    my_tasks = Task.objects.filter(
        assignee=request.user
    ).select_related('project').order_by('end_date')[:10]

    all_users = User.objects.filter(is_active=True).exclude(username='aman').order_by('username')
    
    context = {
        'projects': projects,
        'total_projects': total_projects,
        'active_projects': active_projects,
        'completed_projects': completed_projects,
        'my_tasks': my_tasks,
        'all_users': all_users,
        'project_statuses': ProjectStatus.choices,
    }
    return render(request, 'projects/dashboard.html', context)


@login_required
def project_gantt_view(request, code):
    project = get_object_or_404(Project, code=code)
    all_projects = Project.objects.all().order_by('name')
    all_users = User.objects.filter(is_active=True).exclude(username='aman').order_by('first_name', 'username')
    
    context = {
        'project': project,
        'all_projects': all_projects,
        'all_users': all_users,
        'project_statuses': ProjectStatus.choices,
        'task_statuses': TaskStatus.choices,
        'task_priorities': TaskPriority.choices,
        'dependency_types': DependencyType.choices,
    }
    return render(request, 'projects/gantt_view.html', context)


@login_required
@require_POST
def create_project_view(request):
    name = request.POST.get('name', '').strip()
    description = request.POST.get('description', '').strip()
    status = request.POST.get('status', ProjectStatus.PLANNING)
    start_date = request.POST.get('start_date') or timezone.now().date().isoformat()
    end_date = request.POST.get('end_date') or timezone.now().date().isoformat()

    if not name:
        messages.error(request, "Project name is required.")
        return redirect('dashboard')

    owner = request.user if request.user.is_authenticated else User.objects.get(username='aman')
    project = Project.objects.create(
        name=name,
        description=description,
        status=status,
        start_date=start_date,
        end_date=end_date,
        owner=owner
    )
    # Ensure creator membership (aman is already auto-added as ADMIN via Project.save / signal)
    if owner.username != 'aman':
        ProjectMember.objects.get_or_create(
            project=project,
            user=owner,
            defaults={'role': ProjectRole.ADMIN}
        )

    messages.success(request, f"Project '{project.name}' created successfully (Master: @aman)!")
    return redirect('project_gantt', code=project.code)


# =========================================================================
# TEAM & USER MANAGEMENT VIEWS (Add, Edit, Delete Users)
# =========================================================================

@login_required
def team_management_view(request):
    """Lists all team members with their task workload and assignment stats."""
    users = User.objects.all().order_by('first_name', 'username')
    
    user_list = []
    for u in users:
        tasks = Task.objects.filter(assignee=u)
        total_tasks = tasks.count()
        active_tasks = tasks.filter(status__in=['NOT_STARTED', 'IN_PROGRESS', 'DELAYED']).count()
        completed_tasks = tasks.filter(status='COMPLETE').count()
        total_hours = sum(t.estimated_hours for t in tasks)
        actual_hours = sum(t.actual_hours for t in tasks)

        # Get role in projects
        memberships = ProjectMember.objects.filter(user=u).select_related('project')
        is_aman = (u.username == 'aman')
        if is_aman:
            role_display = "Master Admin"
        elif u.is_superuser or memberships.filter(role=ProjectRole.ADMIN).exists():
            role_display = "Admin"
        elif memberships.filter(role=ProjectRole.MANAGER).exists():
            role_display = "Manager"
        else:
            role_display = "Member"

        initials = (u.first_name[:1] + u.last_name[:1]).upper() if u.first_name and u.last_name else u.username[:2].upper()

        user_list.append({
            'id': u.id,
            'user': u,
            'username': u.username,
            'full_name': u.get_full_name() or u.username,
            'first_name': u.first_name,
            'last_name': u.last_name,
            'email': u.email or 'N/A',
            'initials': initials,
            'role_display': role_display,
            'total_tasks': total_tasks,
            'active_tasks': active_tasks,
            'completed_tasks': completed_tasks,
            'estimated_hours': total_hours,
            'actual_hours': actual_hours,
            'projects_count': memberships.count(),
            'is_aman': is_aman,
            'date_joined': u.date_joined
        })

    all_projects = Project.objects.all().order_by('name')
    context = {
        'team_users': user_list,
        'total_members': len(user_list),
        'all_projects': all_projects,
        'roles': ProjectRole.choices
    }
    return render(request, 'users/team_management.html', context)


@login_required
@require_POST
def create_team_user_view(request):
    """Creates a new team member with Username (ID), Name, Email, Password, and Role."""
    username = request.POST.get('username', '').strip()
    first_name = request.POST.get('first_name', '').strip()
    last_name = request.POST.get('last_name', '').strip()
    email = request.POST.get('email', '').strip()
    password = request.POST.get('password', '').strip() or '123456'
    role = request.POST.get('role', ProjectRole.MEMBER)
    assigned_project_id = request.POST.get('project_id')

    if not username:
        messages.error(request, "User ID / Username is required.")
        return redirect('team_management')

    if User.objects.filter(username=username).exists():
        messages.error(request, f"User with username '@{username}' already exists.")
        return redirect('team_management')

    with transaction.atomic():
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        if role == ProjectRole.ADMIN:
            user.is_staff = True
            user.save()

        # Add to all active projects as member or specific project
        if assigned_project_id:
            proj = Project.objects.filter(id=assigned_project_id).first()
            if proj:
                ProjectMember.objects.create(project=proj, user=user, role=role)
        else:
            for p in Project.objects.all():
                ProjectMember.objects.get_or_create(project=p, user=user, defaults={'role': role})

    messages.success(request, f"Team member '{user.get_full_name() or user.username}' (@{user.username}) created successfully!")
    return redirect('team_management')


@login_required
@require_POST
def edit_team_user_view(request, user_id):
    """Edits an existing team member's details."""
    user = get_object_or_404(User, id=user_id)
    
    first_name = request.POST.get('first_name', '').strip()
    last_name = request.POST.get('last_name', '').strip()
    email = request.POST.get('email', '').strip()
    new_password = request.POST.get('new_password', '').strip()
    role = request.POST.get('role')

    user.first_name = first_name
    user.last_name = last_name
    user.email = email
    
    if new_password:
        user.set_password(new_password)

    if user.username == 'aman':
        # Master user protection
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        role = ProjectRole.ADMIN
    elif role == ProjectRole.ADMIN:
        user.is_staff = True

    user.save()

    # Update project role
    if role:
        ProjectMember.objects.filter(user=user).update(role=role)

    messages.success(request, f"User details for @{user.username} updated.")
    return redirect('team_management')


@login_required
@require_POST
def delete_team_user_view(request, user_id):
    """Safely deletes a team member, reassigning their tasks to Unassigned."""
    user_to_delete = get_object_or_404(User, id=user_id)

    # Protect master admin
    if user_to_delete.username == 'aman':
        messages.error(request, "Cannot delete master administrator account 'aman'.")
        return redirect('team_management')

    if user_to_delete == request.user:
        messages.error(request, "You cannot delete your own currently logged-in account.")
        return redirect('team_management')

    username = user_to_delete.username
    full_name = user_to_delete.get_full_name() or username

    with transaction.atomic():
        # Unassign tasks before deletion to preserve tasks
        Task.objects.filter(assignee=user_to_delete).update(assignee=None)
        user_to_delete.delete()

    messages.success(request, f"Team member '{full_name}' (@{username}) was successfully removed.")
    return redirect('team_management')

