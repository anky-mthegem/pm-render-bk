from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_protect
from collections import defaultdict
import json

from teams.models import Department, Team, TeamMembership


def get_user_avatar_initials(user):
    if user.first_name and user.last_name:
        return (user.first_name[0] + user.last_name[0]).upper()
    elif user.first_name:
        return user.first_name[:2].upper()
    return user.username[:2].upper()


@login_required
@require_GET
def team_hierarchy_api(request):
    """
    Returns full nested Department & Team hierarchy with lead, member rosters, and project counts.
    Explicitly excludes master administrative user 'aman'.
    """
    departments = Department.objects.select_related('parent', 'head').prefetch_related('teams__lead', 'teams__memberships__user').all()
    standalone_teams = Team.objects.filter(department__isnull=True).select_related('lead', 'parent_team').prefetch_related('memberships__user')

    dept_tree = []
    dept_map = {}

    for d in departments:
        head_data = None
        if d.head and d.head.username != 'aman':
            head_data = {
                'id': d.head.id,
                'username': d.head.username,
                'name': d.head.get_full_name() or d.head.username,
                'initials': get_user_avatar_initials(d.head),
                'email': d.head.email
            }
        
        dept_data = {
            'id': d.id,
            'name': d.name,
            'code': d.code,
            'description': d.description,
            'head': head_data,
            'teams': [],
            'sub_departments': []
        }
        dept_map[d.id] = dept_data

    # Populate teams inside departments
    for d in departments:
        for t in d.teams.all():
            lead_data = None
            if t.lead and t.lead.username != 'aman':
                lead_data = {
                    'id': t.lead.id,
                    'username': t.lead.username,
                    'name': t.lead.get_full_name() or t.lead.username,
                    'initials': get_user_avatar_initials(t.lead),
                    'email': t.lead.email
                }
            members_list = [
                {
                    'id': m.user.id,
                    'membership_id': m.id,
                    'username': m.user.username,
                    'name': m.user.get_full_name() or m.user.username,
                    'role': m.role,
                    'initials': get_user_avatar_initials(m.user),
                    'email': m.user.email,
                    'reporting_to': m.reporting_to.get_full_name() if (m.reporting_to and m.reporting_to.username != 'aman') else None,
                    'reporting_to_id': m.reporting_to_id if (m.reporting_to and m.reporting_to.username != 'aman') else None
                }
                for m in t.memberships.select_related('user', 'reporting_to').all()
                if m.user.username != 'aman'
            ]
            
            dept_map[d.id]['teams'].append({
                'id': t.id,
                'name': t.name,
                'code': t.code,
                'description': t.description,
                'color': t.color,
                'parent_team_id': t.parent_team_id,
                'lead': lead_data,
                'members_count': len(members_list),
                'members': members_list,
                'projects_count': t.assigned_projects.count() if hasattr(t, 'assigned_projects') else 0
            })

    # Assemble nested departments
    for d in departments:
        if d.parent_id and d.parent_id in dept_map:
            dept_map[d.parent_id]['sub_departments'].append(dept_map[d.id])
        else:
            dept_tree.append(dept_map[d.id])

    # Standalone teams (no department)
    standalone_data = []
    for t in standalone_teams:
        lead_data = None
        if t.lead and t.lead.username != 'aman':
            lead_data = {
                'id': t.lead.id,
                'username': t.lead.username,
                'name': t.lead.get_full_name() or t.lead.username,
                'initials': get_user_avatar_initials(t.lead),
                'email': t.lead.email
            }
        members_list = [
            {
                'id': m.user.id,
                'membership_id': m.id,
                'username': m.user.username,
                'name': m.user.get_full_name() or m.user.username,
                'role': m.role,
                'initials': get_user_avatar_initials(m.user),
                'email': m.user.email,
                'reporting_to': m.reporting_to.get_full_name() if (m.reporting_to and m.reporting_to.username != 'aman') else None,
                'reporting_to_id': m.reporting_to_id if (m.reporting_to and m.reporting_to.username != 'aman') else None
            }
            for m in t.memberships.select_related('user', 'reporting_to').all()
            if m.user.username != 'aman'
        ]
        standalone_data.append({
            'id': t.id,
            'name': t.name,
            'code': t.code,
            'description': t.description,
            'color': t.color,
            'parent_team_id': t.parent_team_id,
            'lead': lead_data,
            'members_count': len(members_list),
            'members': members_list,
            'projects_count': t.assigned_projects.count() if hasattr(t, 'assigned_projects') else 0
        })

    return JsonResponse({
        'departments': dept_tree,
        'standalone_teams': standalone_data
    })


@login_required
@require_GET
def org_chart_api(request):
    """
    Returns personnel reporting hierarchy formatted for MS Teams / Workday Org Chart cards.
    Master user 'aman' is strictly excluded from organization teams.
    """
    users = list(User.objects.filter(is_active=True).exclude(username='aman').select_related())
    memberships = list(TeamMembership.objects.filter(user__is_active=True).exclude(user__username='aman').select_related('team', 'team__department', 'user', 'reporting_to').all())
    
    # Map user to their primary team membership
    user_team_map = {}
    for m in memberships:
        if m.user_id not in user_team_map or m.role in ('Lead', 'Tech Lead', 'Manager'):
            user_team_map[m.user_id] = m

    # Count direct reports for each user
    direct_reports_count_map = defaultdict(int)
    for m in memberships:
        if m.reporting_to_id and m.reporting_to.username != 'aman':
            direct_reports_count_map[m.reporting_to_id] += 1

    # Build node list
    nodes = []
    for u in users:
        m = user_team_map.get(u.id)
        team_name = m.team.name if m else 'General Team'
        dept_name = m.team.department.name if m and m.team.department else 'Operations'
        role = m.role if m else 'Team Member'
        color = m.team.color if m else '#6366f1'
        manager_id = m.reporting_to_id if m and m.reporting_to_id and m.reporting_to.username != 'aman' else None

        nodes.append({
            'id': u.id,
            'username': u.username,
            'name': u.get_full_name() or u.username,
            'email': u.email or f"{u.username}@company.local",
            'role': role,
            'team_name': team_name,
            'team_id': m.team_id if m else None,
            'department_name': dept_name,
            'color': color,
            'initials': get_user_avatar_initials(u),
            'parent_id': manager_id,
            'direct_reports_count': direct_reports_count_map[u.id],
            'is_master': False
        })

    return JsonResponse({
        'nodes': nodes,
        'total_count': len(nodes)
    })


@login_required
@require_POST
@csrf_protect
def update_reporting_api(request):
    """
    AJAX endpoint to update direct reporting line for a team member.
    """
    try:
        data = json.loads(request.body)
        user_id = data.get('user_id')
        reporting_to_id = data.get('reporting_to_id')

        if not user_id:
            return JsonResponse({'status': 'error', 'message': 'user_id is required'}, status=400)

        user = User.objects.filter(id=user_id).first()
        if not user or user.username == 'aman':
            return JsonResponse({'status': 'error', 'message': 'Invalid user or administrative user cannot be assigned.'}, status=400)

        if user_id == reporting_to_id:
            return JsonResponse({'status': 'error', 'message': 'A member cannot report to themselves.'}, status=400)

        manager = User.objects.filter(id=reporting_to_id).exclude(username='aman').first() if reporting_to_id else None
        updated_count = TeamMembership.objects.filter(user_id=user_id).update(reporting_to=manager)

        return JsonResponse({
            'status': 'success',
            'message': f'Reporting line updated successfully for {updated_count} membership(s).'
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
