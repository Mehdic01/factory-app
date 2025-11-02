# Factory App (Django)

A modular internal app built with Django for managing departments, announcements, tasks, bookings, and feedbacks.

Current feature work lives on the `comms` branch: the Announcements module with role-based publishing and read receipts.

## Contents
- Quick start
- Configuration (.env)
- Features overview
- Announcements module (details)
- URLs
- Roles and permissions
- Development notes
- Testing
- Branch workflow
- Troubleshooting

## Quick start (Windows PowerShell)
Prerequisites: Python 3.11+ (tested with 3.13), PostgreSQL, Git.

```powershell
# From repo root
cd D:\factory\project

# Create and activate a virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Configure your environment (see .env section below)

# Create database schema
python manage.py makemigrations
python manage.py migrate

# Create an admin user
python manage.py createsuperuser

# Run the development server
python manage.py runserver
```

## Configuration (.env)
Create a `.env` file at the project root (`D:\factory\project\.env`) with values for your environment.

Example:
```
# Security
SECRET_KEY=change-me
DEBUG=True

# Locale
DJANGO_LANGUAGE_CODE=en-us
DJANGO_TIME_ZONE=Europe/Istanbul

# Database (PostgreSQL)
DB_NAME=factory
DB_USER=factory_user
DB_PASSWORD=your_password
DB_HOST=127.0.0.1
DB_PORT=5432
```

## Features overview
- Departments
  - Department management with managers and members
- Core
  - Custom User model with role and optional department
  - Roles: EMPLOYEE, MANAGER, GM (General Manager)
- Comms (Announcements) — new on `comms` branch
  - Announcements with title, slug, content
  - Statuses: Draft, Published, Archived
  - Scheduling: publish_at, expire_at
  - Pinning: pinned announcements float to the top
  - Targeting: global (no departments) or specific departments
  - Read receipts per user
  - Role-based publishing rules (see below)
  - Manager view: split into "My Announcements" and "General Manager's Announcements"
- Tasks, Booking, Feedbacks
  - App skeletons present (feature depth varies)

## Announcements module
Model: `comms.models.Announcement`
- Fields: `title`, `slug` (unique), `content`, `status`, `pinned`, `publish_at`, `expire_at`, `departments` (M2M), `author`, `created_at`, `updated_at`
- Query helpers: `.published()`, `.active()`, `.for_departments(dept_ids)`
- Methods: `publish()`, `archive()`, `is_live`, `mark_read(user)`, `is_read_by(user)`, `read_count()`
- Validation: `expire_at` must be after `publish_at`

Read receipts: `comms.models.AnnouncementRead`
- Unique per (announcement, user), timestamped at `read_at`

Admin: bulk actions to publish/archive; list filters, search, and slug prepopulation.

### Visibility rules
- Announcements are visible to users in targeted departments; if no departments are set, the announcement is global and visible to everyone.
- "Active" announcements are Published and within their schedule window (publish_at <= now < expire_at when set).

### Publishing rules
- Employee: cannot publish announcements.
- Manager:
  - Can create/publish announcements only for departments they manage.
  - Cannot publish global announcements.
- GM (General Manager):
  - Can publish globally or to any department.

These rules are enforced in `Announcement.publish()` and used by the admin bulk action and forms.

## URLs
- Announcements
  - `/announcements/` — list view
    - For Managers: split view showing "My Announcements" (no read button) and "General Manager's Announcements" (with "I read this").
  - `/announcements/new/` — creation form (GM/Manager only)
  - `/announcements/<slug>/` — detail view
  - `/announcements/<slug>/read/` — mark-as-read (POST, HTMX supported)

## Roles and permissions
Defined in `core.models.Role` and used throughout the app.
- EMPLOYEE: default; read-only access to announcements in their department(s) and global
- MANAGER: can manage announcements for their managed departments; sees GM announcements with read button
- GM: can publish globally or to any department

`core.User` (custom user) includes `role` and optional `department` FK. Departments also define `managers` and `members` M2M relations to users.

## Development notes
- Django settings: `config/settings.py`
- Installed apps include: `django_htmx`, `crispy_forms`, `rest_framework`, `django_filters`, `corsheaders`
- Templates directory: `project/templates` and app templates under each app (AppDirs enabled)
- Static files: `project/static`
- Authentication: custom user model `core.User` (AUTH_USER_MODEL)

## Testing
Run the test suite:
```powershell
python manage.py test
```

## Branch workflow
- Feature work for the Announcements module is done on the `comms` branch.
- Open a Pull Request to merge into your mainline branch when ready:
  https://github.com/Mehdic01/factory-app/pull/new/comms

## Troubleshooting
- "No module named 'django'": activate your virtualenv:
  ```powershell
  .\.venv\Scripts\Activate.ps1
  ```
- Database connection errors: confirm PostgreSQL is running and .env values are correct.
- Template syntax errors: avoid Python expressions inside Django templates (e.g., use explicit comparisons instead of `in` tuples inside `{% if %}` tags).
- Managers see empty department list when creating announcements: make sure the manager is assigned to at least one Department as a manager, or switch to a GM account.

---

If you need an API for announcements or more granular permissions (e.g., per-department visibility beyond membership/management), we can extend the module with DRF viewsets and policies.
