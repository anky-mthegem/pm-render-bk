from datetime import timedelta, date
from collections import deque, defaultdict
from typing import Set, Dict, List, Optional
from django.utils import timezone


def add_working_days(start_date: date, days: int, exclude_weekends: bool = False) -> date:
    """Add duration in days, optionally skipping Saturdays (5) and Sundays (6)."""
    if not exclude_weekends or days <= 1:
        return start_date + timedelta(days=max(0, days - 1))
    
    current = start_date
    added = 1
    while added < days:
        current += timedelta(days=1)
        if current.weekday() < 5:  # Monday to Friday
            added += 1
    return current


def check_dependency_cycle(from_task_id: int, to_task_id: int) -> bool:
    """
    Check if creating a dependency from `from_task_id` -> `to_task_id` would introduce a cycle.
    A cycle will be created if there is already a directed path from `to_task_id` to `from_task_id`.
    """
    if from_task_id == to_task_id:
        return True

    from projects.models import TaskDependency

    queue = deque([to_task_id])
    visited: Set[int] = set()

    while queue:
        curr_task_id = queue.popleft()
        if curr_task_id == from_task_id:
            return True

        if curr_task_id in visited:
            continue
        visited.add(curr_task_id)

        successor_ids = TaskDependency.objects.filter(
            from_task_id=curr_task_id
        ).values_list('to_task_id', flat=True)

        for succ_id in successor_ids:
            if succ_id not in visited:
                queue.append(succ_id)

    return False


def cascade_reschedule(task, visited: Optional[Set[int]] = None) -> List[int]:
    """
    Recursively cascades date changes to all downstream dependent tasks.
    Returns the list of modified task IDs.
    """
    if visited is None:
        visited = set()

    if task.id in visited:
        return []
    visited.add(task.id)

    modified_task_ids = []
    from projects.models import Task, TaskDependency, DependencyType

    if task.parent_task:
        task.parent_task.recalculate_from_subtasks()

    dependencies = TaskDependency.objects.filter(from_task=task).select_related('to_task')
    exclude_weekends = getattr(task.project, 'exclude_weekends', False)

    for dep in dependencies:
        to_task = dep.to_task
        changed = False
        duration = to_task.duration_days or 1

        if dep.dependency_type == DependencyType.FINISH_TO_START:
            expected_start = task.end_date + timedelta(days=1 + dep.lag_days)
            if exclude_weekends and expected_start.weekday() >= 5:
                # Move to next Monday
                expected_start += timedelta(days=(7 - expected_start.weekday()))
            if to_task.start_date < expected_start:
                to_task.start_date = expected_start
                to_task.end_date = add_working_days(expected_start, duration, exclude_weekends)
                changed = True

        elif dep.dependency_type == DependencyType.START_TO_START:
            expected_start = task.start_date + timedelta(days=dep.lag_days)
            if to_task.start_date < expected_start:
                to_task.start_date = expected_start
                to_task.end_date = add_working_days(expected_start, duration, exclude_weekends)
                changed = True

        elif dep.dependency_type == DependencyType.FINISH_TO_FINISH:
            expected_end = task.end_date + timedelta(days=dep.lag_days)
            if to_task.end_date < expected_end:
                to_task.end_date = expected_end
                to_task.start_date = expected_end - timedelta(days=duration - 1)
                changed = True

        elif dep.dependency_type == DependencyType.START_TO_FINISH:
            expected_end = task.start_date + timedelta(days=dep.lag_days)
            if to_task.end_date < expected_end:
                to_task.end_date = expected_end
                to_task.start_date = expected_end - timedelta(days=duration - 1)
                changed = True

        if changed:
            to_task.save()
            modified_task_ids.append(to_task.id)
            downstream_modified = cascade_reschedule(to_task, visited)
            modified_task_ids.extend(downstream_modified)

    return modified_task_ids


def calculate_critical_path(project) -> Dict:
    """
    Computes Early Start/Finish (Forward Pass), Late Start/Finish (Backward Pass),
    and Total Float (Slack) for all tasks in the project using Critical Path Method (CPM).
    Updates tasks with `is_critical` flag.
    """
    from projects.models import Task, TaskDependency

    tasks = list(project.tasks.all())
    if not tasks:
        return {'critical_task_ids': [], 'total_project_days': 0}

    task_map = {t.id: t for t in tasks}
    predecessors_map = defaultdict(list)
    successors_map = defaultdict(list)

    for dep in TaskDependency.objects.filter(from_task__project=project):
        if dep.from_task_id in task_map and dep.to_task_id in task_map:
            successors_map[dep.from_task_id].append((dep.to_task_id, dep.lag_days))
            predecessors_map[dep.to_task_id].append((dep.from_task_id, dep.lag_days))

    # --- FORWARD PASS (Early Start & Early Finish) ---
    in_degree = {t.id: len(predecessors_map[t.id]) for t in tasks}
    queue = deque([t.id for t in tasks if in_degree[t.id] == 0])

    proj_start = min(t.start_date for t in tasks)
    es_map = {}
    ef_map = {}

    for t_id in queue:
        t = task_map[t_id]
        es_map[t_id] = t.start_date
        ef_map[t_id] = t.end_date

    topo_order = []
    while queue:
        curr_id = queue.popleft()
        topo_order.append(curr_id)
        curr_ef = ef_map[curr_id]

        for succ_id, lag in successors_map[curr_id]:
            succ_task = task_map[succ_id]
            earliest_possible = curr_ef + timedelta(days=1 + lag)
            if succ_id not in es_map or earliest_possible > es_map[succ_id]:
                es_map[succ_id] = earliest_possible
                ef_map[succ_id] = earliest_possible + timedelta(days=max(1, succ_task.duration_days) - 1)

            in_degree[succ_id] -= 1
            if in_degree[succ_id] == 0:
                queue.append(succ_id)

    # In case there are unvisited disconnected tasks
    for t in tasks:
        if t.id not in es_map:
            es_map[t.id] = t.start_date
            ef_map[t.id] = t.end_date
            topo_order.append(t.id)

    # Project max finish date
    proj_finish = max(ef_map.values(), default=proj_start)

    # --- BACKWARD PASS (Late Finish & Late Start) ---
    lf_map = {}
    ls_map = {}

    for t_id in reversed(topo_order):
        succs = successors_map[t_id]
        t = task_map[t_id]
        if not succs:
            lf_map[t_id] = proj_finish
        else:
            min_late_finish = min(
                ls_map[s_id] - timedelta(days=1 + lag)
                for s_id, lag in succs
                if s_id in ls_map
            )
            lf_map[t_id] = min_late_finish
        
        ls_map[t_id] = lf_map[t_id] - timedelta(days=max(1, t.duration_days) - 1)

    # --- TOTAL FLOAT & CRITICAL PATH ---
    critical_task_ids = []
    for t in tasks:
        es = es_map.get(t.id, t.start_date)
        ef = ef_map.get(t.id, t.end_date)
        ls = ls_map.get(t.id, t.start_date)
        lf = lf_map.get(t.id, t.end_date)

        total_float = max(0, (ls - es).days)
        is_crit = (total_float == 0)

        t.early_start = es
        t.early_finish = ef
        t.late_start = ls
        t.late_finish = lf
        t.total_float_days = total_float
        t.is_critical = is_crit

        if is_crit:
            critical_task_ids.append(t.id)

        Task.objects.filter(pk=t.pk).update(
            early_start=es,
            early_finish=ef,
            late_start=ls,
            late_finish=lf,
            total_float_days=total_float,
            is_critical=is_crit
        )

    return {
        'critical_task_ids': critical_task_ids,
        'project_start': proj_start.isoformat(),
        'project_finish': proj_finish.isoformat(),
        'total_duration_days': (proj_finish - proj_start).days + 1
    }


def save_project_baseline(project) -> int:
    """Saves current dates and durations as baseline for variance tracking."""
    from projects.models import Task
    tasks = project.tasks.all()
    count = 0
    for t in tasks:
        t.baseline_start_date = t.start_date
        t.baseline_end_date = t.end_date
        t.baseline_duration_days = t.duration_days
        t.save(update_fields=['baseline_start_date', 'baseline_end_date', 'baseline_duration_days'])
        count += 1

    project.baseline_saved_at = timezone.now()
    project.save(update_fields=['baseline_saved_at'])
    return count


def calculate_evm_metrics(project) -> Dict:
    """Calculates Earned Value Management (EVM) indicators."""
    tasks = project.tasks.filter(parent_task__isnull=True)  # Or all leaf tasks
    leaf_tasks = project.tasks.filter(subtasks__isnull=True)
    target_tasks = leaf_tasks if leaf_tasks.exists() else tasks

    pv = sum(float(t.estimated_cost) for t in target_tasks)
    ev = sum(float(t.estimated_cost) * (t.progress / 100.0) for t in target_tasks)
    ac = sum(float(t.actual_cost) for t in target_tasks)

    cv = ev - ac
    sv = ev - pv
    cpi = round(ev / ac, 2) if ac > 0 else (1.0 if ev == 0 else round(ev, 2))
    spi = round(ev / pv, 2) if pv > 0 else (1.0 if ev == 0 else round(ev, 2))

    return {
        'budget': float(project.budget) or pv,
        'planned_value': round(pv, 2),
        'earned_value': round(ev, 2),
        'actual_cost': round(ac, 2),
        'cost_variance': round(cv, 2),
        'schedule_variance': round(sv, 2),
        'cpi': cpi,
        'spi': spi,
        'cost_status': 'Under Budget' if cv >= 0 else 'Over Budget',
        'schedule_status': 'Ahead of Schedule' if sv >= 0 else 'Behind Schedule',
    }


def calculate_resource_workload(project) -> List[Dict]:
    """Calculates assigned task count, total hours, and active dates per assignable team member."""
    from django.contrib.auth.models import User
    
    # 1. Project members (excluding master admin 'aman')
    member_user_ids = set(project.memberships.exclude(user__username='aman').values_list('user_id', flat=True))
    
    # 2. Users assigned to tasks in this project
    task_user_ids = set(project.tasks.filter(assignee__isnull=False).exclude(assignee__username='aman').values_list('assignee_id', flat=True))
    
    combined_ids = member_user_ids | task_user_ids
    
    # 3. If no specific project members or task assignees yet, list all active company users so manager can see available capacity
    if not combined_ids:
        combined_ids = set(User.objects.filter(is_active=True).exclude(username='aman').values_list('id', flat=True))
        
    users = User.objects.filter(id__in=combined_ids, is_active=True).order_by('first_name', 'username')

    result = []
    for user in users:
        assigned_tasks = project.tasks.filter(assignee=user)
        total_hours = sum(t.estimated_hours for t in assigned_tasks)
        actual_hours = sum(t.actual_hours for t in assigned_tasks)
        active_tasks = assigned_tasks.filter(status__in=['IN_PROGRESS', 'NOT_STARTED', 'DELAYED'])
        completed_tasks = assigned_tasks.filter(status='COMPLETE')

        result.append({
            'user_id': user.id,
            'username': user.username,
            'name': user.get_full_name() or user.username,
            'initials': (user.first_name[:1] + user.last_name[:1]).upper() if user.first_name and user.last_name else user.username[:2].upper(),
            'total_tasks': assigned_tasks.count(),
            'active_tasks_count': active_tasks.count(),
            'completed_tasks_count': completed_tasks.count(),
            'estimated_hours': total_hours,
            'actual_hours': actual_hours,
            'is_overallocated': assigned_tasks.count() >= 5 or total_hours >= 40,
            'tasks': [
                {
                    'id': t.id,
                    'name': t.name,
                    'wbs_code': t.wbs_code,
                    'start_date': t.start_date.isoformat(),
                    'end_date': t.end_date.isoformat(),
                    'progress': t.progress,
                    'status': t.status,
                    'priority': t.priority
                }
                for t in assigned_tasks
            ]
        })
    return result


def compute_wbs_hierarchy(project) -> List[Dict]:
    """Returns an ordered list of task dictionaries with computed WBS codes and tree depths."""
    from projects.models import Task

    all_tasks = list(Task.objects.filter(project=project).select_related('assignee', 'parent_task').order_by('sort_order', 'id'))
    children_map: Dict[Optional[int], List[Task]] = defaultdict(list)
    for t in all_tasks:
        children_map[t.parent_task_id].append(t)

    result = []

    def traverse(parent_id: Optional[int], prefix: str, depth: int):
        tasks = children_map.get(parent_id, [])
        for idx, task in enumerate(tasks, 1):
            wbs = f"{prefix}{idx}" if prefix else f"{idx}"
            task_dict = {
                'id': task.id,
                'name': task.name,
                'wbs_code': wbs,
                'depth': depth,
                'has_children': bool(children_map.get(task.id)),
                'task_obj': task
            }
            result.append(task_dict)
            traverse(task.id, f"{wbs}.", depth + 1)

    traverse(None, "", 0)
    return result


def get_hierarchical_task_list(project) -> List:
    """
    Returns Task model instances in hierarchical DFS tree order with pre-attached
    _computed_wbs, _computed_depth, and _has_children.
    """
    from projects.models import Task

    all_tasks = list(
        project.tasks.select_related('assignee', 'parent_task')
        .prefetch_related('predecessors', 'successors')
        .order_by('sort_order', 'id')
    )
    children_map: Dict[Optional[int], List[Task]] = defaultdict(list)
    for t in all_tasks:
        children_map[t.parent_task_id].append(t)

    result = []

    def traverse(parent_id: Optional[int], prefix: str, depth: int):
        tasks = children_map.get(parent_id, [])
        for idx, task in enumerate(tasks, 1):
            wbs = f"{prefix}{idx}" if prefix else f"{idx}"
            task._computed_wbs = wbs
            task._computed_depth = depth
            task._has_children = bool(children_map.get(task.id))
            result.append(task)
            traverse(task.id, f"{wbs}.", depth + 1)

    traverse(None, "", 0)
    return result
