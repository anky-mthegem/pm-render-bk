# Milestone Management — Comprehensive User Guide & Operations Manual

Welcome to **Milestone Management**, a self-hosted full-stack Project Management and Interactive Gantt Scheduling web application. This guide provides instructions on navigating the system, managing project portfolios, constructing Work Breakdown Structures (WBS), calculating the Critical Path (CPM), tracking baselines, analyzing Earned Value (EVM), balancing team workloads, and importing/exporting formatted Excel files.

---

## 📑 Table of Contents
1. [System Overview & Architecture](#1-system-overview--architecture)
2. [Authentication & Access Control](#2-authentication--access-control)
3. [Project Portfolio Dashboard](#3-project-portfolio-dashboard)
4. [Team & User Management (Add, Edit, Delete Users)](#4-team--user-management-add-edit-delete-users)
5. [Multi-View Workspace Navigation](#5-multi-view-workspace-navigation)
6. [Dual-Pane Milestone Management Interface](#6-dual-pane-milestone-management-interface)
7. [Critical Path Method (CPM) & Float Calculation](#7-critical-path-method-cpm--float-calculation)
8. [Baseline vs. Actual Schedule Tracking](#8-baseline-vs-actual-schedule-tracking)
9. [Interactive Kanban Board](#9-interactive-kanban-board)
10. [Team Workload & Capacity Heatmap](#10-team-workload--capacity-heatmap)
11. [Financials & Earned Value Management (EVM)](#11-financials--earned-value-management-evm)
12. [Excel (.xlsx) Export & Import](#12-excel-xlsx-export--import)
13. [Task Detail Drawer, Comments & Attachments](#13-task-detail-drawer-comments--attachments)
14. [Django Admin Portal](#14-django-admin-portal)
15. [REST API Quick Reference](#15-rest-api-quick-reference)
16. [Troubleshooting & Maintenance](#16-troubleshooting--maintenance)

---

## 1. System Overview & Architecture

Milestone Management combines a structured spreadsheet grid with an interactive Gantt timeline customized for **Indian Standards**:

- **Currency & Financials**: Indian Rupee (**INR - `₹`**) with Indian Numbering System (Lakhs, Crores).
- **Date & Time Standards**: **`DD/MM/YYYY`** date format and **`Asia/Kolkata` (IST, UTC+05:30)** timezone.
- **Effort Measurement**: Standard **Man-Hours** (`hrs` / `man-hours`) and task duration in **Days**.
- **Backend**: Python 3.12+ / Django 5+ with Django REST Framework (DRF).
- **Frontend**: TailwindCSS (Modern Dark UI), Alpine.js reactivity, and custom SVG Frappe Gantt integration.
- **Scheduling Engine**: Critical Path Method (Forward/Backward Pass), Graph cycle detection (DFS), and recursive cascade rescheduling algorithm supporting **FS**, **SS**, **FF**, and **SF** dependencies.
- **Excel Interoperability**: Formatted `.xlsx` generation and ingestion via `openpyxl` with Indian currency headers (`₹ INR`) and dates (`DD/MM/YYYY`).
- **Database**: SQLite (default) / PostgreSQL production-ready.

---

## 2. Authentication & Access Control

### 2.1 User Login
Navigate to **`http://127.0.0.1:8000/login/`** and sign in with your authorized system credentials to access the project management dashboard.

---

### 2.2 Admin-Authorized User Registration
To ensure strict security and prevent unauthorized sign-ups, the **Create New Account** page (**`/register/`**) requires administrative authorization:

1. Click **Create new account** on the login screen (or visit `http://127.0.0.1:8000/register/`).
2. Fill in the **Admin Authorization Required** section with valid administrator credentials.
3. Fill in the **New Account Credentials**:
   - Desired Username
   - Password (and Password Confirmation)
4. Click **Authorize & Register Account**.
5. Once authorized, the new account is provisioned immediately.

---

## 3. Project Portfolio Dashboard

Once logged in, the **Portfolio Dashboard** (`/`) displays your active project landscape.

- **KPI Summary Cards**: Real-time totals for projects, active schedules, completed milestones, and tasks assigned to the current user.
- **Project Cards**: Shows each project's slug code, description, overall completion percentage progress bar, date range, and task counters.
- **Open Gantt Excel Button**: Click on any project card to enter the full dual-pane Gantt workspace.
- **Create Project Modal**: Enter Name, Description, Dates, and initial Status.

---

## 4. Team & User Management (Add, Edit, Delete Users)

Navigate to **`http://127.0.0.1:8000/team/`** or click **Team** in the top navigation bar.

### 4.1 Viewing Team Members & Workload Summary
The **Team Members** page displays all active users in the system along with:
- **Full Name & Avatar**: e.g., Sarah Jenkins (`SJ`).
- **User ID / Handle**: e.g., `@sarah_pm` (used across task assignments, WBS dropdowns, and Gantt popups).
- **Role**: Administrator, Project Manager, or Member.
- **Assigned Tasks**: Counter showing total assigned tasks and active in-progress tasks.
- **Workload Effort**: Total estimated hours vs. realized actual hours (`Est / Act`).

### 4.2 Adding a New Team Member
1. Click the **Add Team Member** button on the top right.
2. Fill in the form:
   - **First Name & Last Name**: (e.g. `Sarah` and `Jenkins`).
   - **User ID / Username (@handle)**: (e.g. `sarah_pm`).
   - **Email Address**: (e.g. `sarah.jenkins@ganttexcel.local`).
   - **Temporary Password**: Set an initial password for the user.
   - **Role**: Select Member, Project Manager, or Administrator.
3. Click **Create Member**. The user is immediately available for task assignment in all Gantt schedules and Workload heatmaps.

### 4.3 Editing a Team Member
1. Click the **Edit (pencil icon)** button next to any user.
2. Modify their Name, Email, Password, or Role.
3. Click **Update Member**.

### 4.4 Deleting a Team Member
1. Click the **Delete (trash icon)** button next to any user.
2. A confirmation modal will appear explaining that any tasks assigned to them will be safely preserved and marked as *Unassigned*.
3. Click **Yes, Remove User**.

---

## 5. Multi-View Workspace Navigation

In the top navigation ribbon of any project, toggle between 5 specialized workspace views:

1. 📊 **Gantt Excel**: Dual-pane grid and interactive timeline with Critical Path and Baseline toggles.
2. 📋 **Kanban Board**: Drag-and-drop workflow cards across *Not Started*, *In Progress*, *Delayed*, and *Complete*.
3. 👥 **Team Workload**: Real-time capacity heatmap, estimated vs. actual hours, and allocation alerts.
4. 📈 **Financials & EVM**: Earned value management metrics (PV, EV, AC, CV, SV, CPI, SPI).
5. 🕒 **Project Audit Stream**: Chronological audit trail of all scheduling updates, comments, and task modifications.

---

## 6. Dual-Pane Gantt Excel Interface

The Gantt Workspace (`/projects/<project-code>/`) provides:

### 5.1 Left Pane (Task Sheet)
- **WBS Codes**: Hierarchical numbering (`1.0`, `1.1`, `1.1.1`).
- **Hierarchy Tree**: Indented subtasks with container folder icons.
- **Assignee Avatar**: Displays team member badge and name.
- **Inline Status & Progress**: Direct visual progress bar and status pills.
- **Quick Action Triggers**: Add Subtask, Edit, Delete.

### 5.2 Right Pane (Interactive Timeline)
- **Drag-to-Move**: Drag any task bar horizontally to reschedule.
- **Drag-to-Resize**: Drag bar handles to expand or contract duration.
- **Dependency Arrows**: Visual SVG connectors from predecessors to successors.
- **Milestone Diamonds**: Key milestone markers rendered in glowing amber.
- **Zoom Levels**: Switch between **Day**, **Week**, **Month**, and **Year**.
- **Synchronized Scrolling**: 1:1 row height synchronization with the task sheet.

---

## 7. Critical Path Method (CPM) & Float Calculation

### 7.1 What is the Critical Path?
The Critical Path represents the sequence of dependent tasks that determines the absolute minimum duration of the project. A delay in any critical task directly delays the final project completion date.

### 7.2 Using CPM in Gantt Excel:
1. Click the **Critical Path** toggle button in the top ribbon.
2. All critical path tasks (`Total Float = 0 days`) are instantly highlighted with a **glowing red/rose aura** on the timeline and a **CPM badge** on the task sheet.
3. Hovering over any task displays its **Early Start**, **Late Start**, and **Total Float (Slack)** in days.

---

## 8. Baseline vs. Actual Schedule Tracking

### 8.1 Saving a Baseline
When your project schedule is approved, click **Snap Baseline** in the top ribbon. This records a permanent snapshot of:
- `baseline_start_date`
- `baseline_end_date`
- `baseline_duration_days`

### 8.2 Visualizing Slippage
1. Click the **Baseline** toggle button.
2. If tasks are rescheduled past their baseline target dates, the system calculates **Schedule Variance (in days)** and flags slipped tasks in amber.

---

## 9. Interactive Kanban Board

Click the **Kanban** tab in the workspace view switcher to enter the card board:
- Tasks are categorized into 4 columns: **Not Started**, **In Progress**, **Delayed / Critical**, and **Complete**.
- **Drag & Drop**: Drag any card to another column to automatically update its status and progress percentage on the server.
- Click any card to open the comprehensive Task Detail Drawer.

---

## 10. Team Workload & Capacity Heatmap

Click the **Workload** tab to monitor team allocation:
- Displays each team member's total assigned tasks, estimated hours, and realized hours.
- Automatically flags team members as **Overallocated** (e.g. 5+ concurrent tasks or 40+ hours) with alert badges.
- Lists all active tasks assigned to that team member.

---

## 11. Financials & Earned Value Management (EVM)

Click the **Financials** tab to view Earned Value KPIs:
- **Planned Value (PV)**: Authorized budget assigned to scheduled work.
- **Earned Value (EV)**: Budgeted value of work physically completed.
- **Actual Cost (AC)**: Total realized expenditures.
- **Cost Performance Index (CPI)**: `EV / AC` (CPI > 1.0 = Under Budget, CPI < 1.0 = Over Budget).
- **Schedule Performance Index (SPI)**: `EV / PV` (SPI > 1.0 = Ahead of Schedule).

---

## 12. Excel (.xlsx) Export & Import

### 12.1 Exporting to Excel
Click the **Excel** button in the top ribbon to download a stylized `.xlsx` workbook containing:
- Formatted headers with dark navy fills.
- Complete WBS tree, dates, duration, progress, status, priority, and predecessor dependencies.
- Financial cost estimates and actuals.
- Critical Path flags and baseline variance calculations.

### 12.2 Importing from Excel
1. Click **Import** in the top ribbon.
2. Select an `.xlsx` file formatted with Task Name, Start Date, End Date, and Progress columns.
3. Click **Import Tasks**. The system imports the rows, builds the WBS index, and recalculates the schedule automatically.

---

## 13. Task Detail Drawer, Comments & Attachments

Click any task to open the multi-tab drawer:
- **General Tab**: Edit title, description, parent task (WBS nesting), assignee, dates, progress, status, priority, and milestone toggle.
- **Dependencies Tab**: View predecessors and successors, check Total Float, and link new dependencies (**FS**, **SS**, **FF**, **SF**) with cycle detection.
- **Cost & Effort Tab**: Track estimated cost, actual cost, estimated hours, and actual hours.
- **Comments Tab**: Post live comments and status updates with author badges.

---

## 14. Django Admin Portal

For direct database operations and user management:
1. Open **`http://127.0.0.1:8000/admin/`**
2. Log in with your administrator credentials.
3. Manage **Projects**, **Tasks**, **Dependencies**, **Comments**, **Attachments**, and **Activity Logs**.

---

## 15. REST API Quick Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/projects/{id}/gantt-data/` | Complete project payload (tasks, CPM, EVM, workload, dependencies). |
| `POST` | `/api/projects/{id}/save-baseline/` | Snapshots current schedule as baseline. |
| `POST` | `/api/projects/{id}/calculate-critical-path/` | Calculates CPM and returns critical path task IDs. |
| `GET` | `/api/projects/{id}/export-excel/` | Downloads formatted `.xlsx` workbook. |
| `POST` | `/api/projects/{id}/import-excel/` | Ingests tasks from uploaded `.xlsx` file. |
| `GET` | `/api/projects/{id}/workload/` | Returns team capacity and assigned hours. |
| `GET` | `/api/projects/{id}/evm-stats/` | Returns Earned Value indicators (PV, EV, AC, CPI, SPI). |
| `GET` | `/api/projects/{id}/activity-logs/` | Retrieves project audit history. |
| `PATCH`| `/api/tasks/{id}/reschedule/` | Drag/drop handler (`{ start_date, end_date, progress }`) with cascades. |
| `PATCH`| `/api/tasks/{id}/update-status/` | Kanban status update handler (`{ status }`). |
| `GET`/`POST` | `/api/tasks/{id}/comments/` | List or post task comments. |

---

## 16. Troubleshooting & Maintenance

### 16.1 Starting the Development Server
- **Option A (Double-Click)**: Run **`run_app.bat`** (or **`start.bat`**).
- **Option B (Terminal)**: `python manage.py runserver 127.0.0.1:8000`.

### 16.2 Resetting Demo Data
```bash
python manage.py seed_data
```

### 16.3 Running the Automated Test Suite
```bash
python manage.py test projects
```
