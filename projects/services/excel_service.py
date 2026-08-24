import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from datetime import datetime, date
import io

from projects.models import Task, TaskDependency, Project


def export_project_to_excel(project: Project) -> io.BytesIO:
    """
    Generates a stylized Excel (.xlsx) file representing the full Milestone Management task sheet
    formatted as per Indian Standards (INR ₹, DD/MM/YYYY, Man-Hours).
    """
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = f"{project.code[:25]} - Schedule"

    # Define color palette
    header_fill = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    title_font = Font(name="Calibri", size=16, bold=True, color="1E293B")
    subtitle_font = Font(name="Calibri", size=10, italic=True, color="64748B")
    bold_font = Font(name="Calibri", size=10, bold=True)
    regular_font = Font(name="Calibri", size=10)

    thin_border = Border(
        left=Side(style='thin', color='CBD5E1'),
        right=Side(style='thin', color='CBD5E1'),
        top=Side(style='thin', color='CBD5E1'),
        bottom=Side(style='thin', color='CBD5E1')
    )

    # Title Block (Indian Standard IST timestamp)
    ws['A1'] = f"MILESTONE MANAGEMENT - {project.name}"
    ws['A1'].font = title_font
    ws['A2'] = f"Project Code: {project.code} | Status: {project.get_status_display()} | Generated: {datetime.now().strftime('%d/%m/%Y %H:%M')} IST | Currency: INR (₹)"
    ws['A2'].font = subtitle_font

    # Headers as per Indian Standard
    headers = [
        "WBS", "Task Name", "Level", "Assignee", "Start Date (DD/MM/YYYY)", "End Date (DD/MM/YYYY)",
        "Duration (Days)", "Progress %", "Status", "Priority", "Milestone",
        "Critical Path", "Predecessors", "Baseline Start", "Baseline End",
        "Variance (Days)", "Est. Cost (₹ INR)", "Actual Cost (₹ INR)", "Est. Effort (Man-Hours)", "Actual Effort (Man-Hours)"
    ]

    header_row = 4
    for col_num, header_title in enumerate(headers, 1):
        cell = ws.cell(row=header_row, column=col_num)
        cell.value = header_title
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = thin_border

    # Fetch tasks
    tasks = project.tasks.select_related('assignee', 'parent_task').prefetch_related('predecessors').order_by('sort_order', 'id')

    current_row = 5
    for task in tasks:
        # Predecessors string
        preds = task.predecessors.values_list('from_task__name', flat=True)
        preds_str = ", ".join(preds)

        ws.cell(row=current_row, column=1, value=task.wbs_code)
        ws.cell(row=current_row, column=2, value=task.name)
        ws.cell(row=current_row, column=3, value=task.wbs_code.count('.'))
        ws.cell(row=current_row, column=4, value=task.assignee.get_full_name() or task.assignee.username if task.assignee else "Unassigned")
        ws.cell(row=current_row, column=5, value=task.start_date.strftime('%d/%m/%Y') if task.start_date else "")
        ws.cell(row=current_row, column=6, value=task.end_date.strftime('%d/%m/%Y') if task.end_date else "")
        ws.cell(row=current_row, column=7, value=task.duration_days)
        ws.cell(row=current_row, column=8, value=f"{task.progress}%")
        ws.cell(row=current_row, column=9, value=task.get_status_display())
        ws.cell(row=current_row, column=10, value=task.get_priority_display())
        ws.cell(row=current_row, column=11, value="Yes" if task.is_milestone else "No")
        ws.cell(row=current_row, column=12, value="YES" if task.is_critical else "No")
        ws.cell(row=current_row, column=13, value=preds_str)
        ws.cell(row=current_row, column=14, value=task.baseline_start_date.strftime('%d/%m/%Y') if task.baseline_start_date else "-")
        ws.cell(row=current_row, column=15, value=task.baseline_end_date.strftime('%d/%m/%Y') if task.baseline_end_date else "-")
        ws.cell(row=current_row, column=16, value=task.schedule_variance_days)
        
        # Currency cells
        c_est = ws.cell(row=current_row, column=17, value=float(task.estimated_cost))
        c_est.number_format = '₹#,##,##0.00'
        c_act = ws.cell(row=current_row, column=18, value=float(task.actual_cost))
        c_act.number_format = '₹#,##,##0.00'
        
        ws.cell(row=current_row, column=19, value=task.estimated_hours)
        ws.cell(row=current_row, column=20, value=task.actual_hours)

        # Style row
        is_parent = task.is_parent
        for col_num in range(1, len(headers) + 1):
            c = ws.cell(row=current_row, column=col_num)
            c.border = thin_border
            c.font = bold_font if is_parent else regular_font

            if task.is_critical and col_num in [1, 2, 12]:
                c.fill = PatternFill(start_color="FFE4E6", end_color="FFE4E6", fill_type="solid")  # light rose
            elif is_parent:
                c.fill = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid")

        current_row += 1

    # Auto-adjust column widths
    for col in ws.columns:
        max_len = 0
        col_letter = get_column_letter(col[0].column)
        for cell in col:
            val_str = str(cell.value or '')
            if len(val_str) > max_len:
                max_len = len(val_str)
        ws.column_dimensions[col_letter].width = max(max_len + 3, 12)

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output


def import_project_from_excel(file_obj, project: Project) -> int:
    """
    Imports or updates tasks from an uploaded Excel (.xlsx) file with support for
    both DD/MM/YYYY (Indian Standard) and standard ISO date formats.
    """
    wb = openpyxl.load_workbook(file_obj, data_only=True)
    ws = wb.active

    headers = {}
    for col_idx in range(1, ws.max_column + 1):
        val = ws.cell(row=4, column=col_idx).value
        if val:
            headers[str(val).strip().lower()] = col_idx

    task_name_col = None
    for h, idx in headers.items():
        if "task name" in h or "name" in h:
            task_name_col = idx
            break

    start_col = None
    for h, idx in headers.items():
        if "start" in h and "baseline" not in h:
            start_col = idx
            break

    end_col = None
    for h, idx in headers.items():
        if "end" in h and "baseline" not in h:
            end_col = idx
            break

    progress_col = None
    for h, idx in headers.items():
        if "progress" in h:
            progress_col = idx
            break

    imported_count = 0
    today = date.today()

    for row_idx in range(5, ws.max_row + 1):
        name_val = ws.cell(row=row_idx, column=task_name_col or 2).value if task_name_col else ws.cell(row=row_idx, column=2).value
        if not name_val:
            continue

        name_str = str(name_val).strip()
        
        # Parse start date
        start_val = ws.cell(row=row_idx, column=start_col or 5).value if start_col else None
        if isinstance(start_val, (datetime, date)):
            start_d = start_val.date() if isinstance(start_val, datetime) else start_val
        elif isinstance(start_val, str):
            try:
                # Try DD/MM/YYYY (Indian Standard)
                start_d = datetime.strptime(start_val[:10], '%d/%m/%Y').date()
            except ValueError:
                try:
                    start_d = datetime.strptime(start_val[:10], '%Y-%m-%d').date()
                except ValueError:
                    start_d = today
        else:
            start_d = today

        # Parse end date
        end_val = ws.cell(row=row_idx, column=end_col or 6).value if end_col else None
        if isinstance(end_val, (datetime, date)):
            end_d = end_val.date() if isinstance(end_val, datetime) else end_val
        elif isinstance(end_val, str):
            try:
                # Try DD/MM/YYYY (Indian Standard)
                end_d = datetime.strptime(end_val[:10], '%d/%m/%Y').date()
            except ValueError:
                try:
                    end_d = datetime.strptime(end_val[:10], '%Y-%m-%d').date()
                except ValueError:
                    end_d = start_d
        else:
            end_d = start_d

        # Parse progress
        prog_val = ws.cell(row=row_idx, column=progress_col or 8).value if progress_col else 0
        try:
            prog_int = int(str(prog_val).replace('%', '').strip())
        except (ValueError, TypeError):
            prog_int = 0

        Task.objects.create(
            project=project,
            name=name_str,
            start_date=start_d,
            end_date=end_d,
            progress=max(0, min(100, prog_int)),
            sort_order=imported_count + 1
        )
        imported_count += 1

    return imported_count
