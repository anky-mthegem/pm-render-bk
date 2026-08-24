# 📊 Gantt Excel PRO — Enterprise Project Management System

[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.14-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.1%2B-092E20.svg)](https://www.djangoproject.com/)
[![Django REST Framework](https://img.shields.io/badge/DRF-3.15%2B-red.svg)](https://www.django-rest-framework.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)](https://github.com/anky-mthegem/project_management_GB)
[![License](https://img.shields.io/badge/License-Proprietary%20%2F%20Internal-orange.svg)](#)

**Gantt Excel PRO** is a web-based, enterprise-grade project management application that combines the familiarity and speed of **Microsoft Excel** with the power of modern **Gantt Charts**, **Critical Path Method (CPM) automated scheduling**, and **Work Breakdown Structure (WBS)**.

---

## ✨ Key Features

- **⚡ Dual-Pane Gantt & Spreadsheet Interface**: Real-time side-by-side view with interactive spreadsheet grid on the left and dynamic SVG timeline/Gantt chart on the right.
- **🔄 Critical Path Method (CPM) Engine**: Automated forward/backward pass algorithm identifying the critical path, total float, and slack days with instant visual red-highlighting.
- **🗂️ Multi-Level Work Breakdown Structure (WBS)**: Infinite parent/subtask nesting with automated rollup calculations for progress (%), duration, estimated cost, and actual cost.
- **₹ Indian Standard Currency (INR) & Cost Tracking**: Native Lakhs/Crores budget tracking with real-time variance calculations.
- **📥 Native Excel (.xlsx) Import & Export**: One-click export to formatted Excel spreadsheets with styling, and bulk import to create tasks instantly.
- **👑 Master Admin Safeguards**: Built-in permanent master user protection guaranteeing database security and immutable superuser authority.
- **🚀 Zero-Install Portable Execution**: Single-click launcher (`run_app.bat`) that works on any Windows PC even if Python is **not** installed!

---

## 🚀 Quick Start (Single-Click)

### 💻 Windows (No Python installation required!)
1. Clone or download this repository:
   ```bash
   git clone https://github.com/anky-mthegem/project_management_GB.git
   ```
2. Open the folder and double-click **`run_app.bat`** (or **`start.bat`**).
3. The launcher will automatically configure the environment, setup the database, and launch your browser at:
   👉 **`http://127.0.0.1:8000/login/`**

---

## 🛠️ Manual Installation (Cross-Platform)

If you prefer using your own Python virtual environment on **macOS, Linux, or Windows**:

```bash
# 1. Clone repository
git clone https://github.com/anky-mthegem/project_management_GB.git
cd project_management_GB

# 2. Create and activate a virtual environment
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Apply database migrations
python manage.py migrate

# 5. Populate initial master user and sample data
python manage.py seed_data

# 6. Start the server
python manage.py runserver 127.0.0.1:8000
```
Open **`http://127.0.0.1:8000/login/`** in your browser.

---

## 📂 Project Architecture

```
project_management_GB/
├── gantt_app/                  # Django project root settings & URL router
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── projects/                   # Core application module
│   ├── api/                    # Django REST Framework viewsets & serializers
│   ├── services/
│   │   ├── scheduler.py        # CPM Engine, cascade reschedule & cyclic check
│   │   └── excel_service.py    # OpenPyXL import/export handler
│   ├── management/commands/    # Data seeding scripts (seed_data.py)
│   ├── models.py               # Project, Task, Dependency, ActivityLog models
│   ├── signals.py              # Master User protection & automated enrollment
│   ├── tests.py                # Automated test suite
│   └── views.py                # Web views and dashboard controller
├── static/                     # CSS stylesheets and JavaScript client
├── templates/                  # Django HTML templates (Gantt UI, Team, Auth)
├── db.sqlite3                  # Pre-configured SQLite database
├── requirements.txt            # Python dependencies
├── run_app.bat                 # Windows Smart Zero-Install Launcher
└── start.bat                   # Quick launcher shortcut
```

---

## 🧪 Running Automated Tests

Run the full automated test suite (including model validation, scheduling engine, and master security tests):

```bash
python manage.py test
```
*Expected result: `Ran 16 tests in 6.8s — OK`*

---

## 📋 System Requirements

- **OS**: Windows 10/11, macOS 10.15+, or Linux (Ubuntu 20.04+)
- **Python**: Python 3.10+ *(or run using the bundled `run_app.bat` without manual install)*
- **RAM**: Minimum 512 MB (1 GB recommended)
- **Disk Space**: ~50 MB
- **Browser**: Chrome, Edge, Safari, Firefox, or Brave

---

## 📄 License
This repository is maintained for internal project management and enterprise workflow automation.
