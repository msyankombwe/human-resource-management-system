# HRMS System Documentation

## 1. System architecture

PeopleSpace HRMS is a server-rendered Django application. `hrms_project` owns project settings and URL routing; feature areas are split into Django apps. Django templates render HTML, Bootstrap provides responsive layout components, and `static/css/style.css` supplies the product theme. Authenticated pages share `templates/base.html`, which renders grouped, role-aware sidebar navigation and a page header with account and logout controls. The sidebar is persistent on desktop, collapsible, and presented as an off-canvas drawer on smaller screens. A small inline SVG symbol set supplies consistent navigation icons without a separate icon dependency.

Requests follow the Django URL → view → form/model → template flow. Authentication uses Django's session and authentication middleware. `accounts.UserProfile` stores the HRMS role alongside Django's user record. `accounts.decorators` checks roles on management endpoints, and `accounts.access.visible_employees` scopes employee-oriented querysets to HR/admin, manager/team or employee/self. The dashboard derives pending leave and same-day attendance panels from those scoped records; it does not fabricate trends or activity.

The interface uses a teal/turquoise and slate design system, system UI font fallbacks, reusable card/form/table/status styles, visible keyboard focus and a skip-to-content link. Responsive behavior is provided by Bootstrap breakpoints and the project stylesheet. There is no separate API or frontend build application. Bootstrap is loaded from its CDN. The project includes no dedicated Reports or System Settings app, so the interface does not expose nonfunctional links for those features.

## 2. Technology stack

- Python and Django (dependency range in `requirements.txt`: Django 5.x or 6.x)
- Django templates, Bootstrap 5.3.3, inline SVG navigation symbols and project CSS (`static/css/style.css`)
- SQLite by default; `DATABASE_URL` can configure PostgreSQL or another backend supported by `dj-database-url`
- WhiteNoise for static files and Gunicorn for WSGI deployment
- Time zone: `Africa/Lusaka`

## 3. Functional requirements

The implemented application supports:

1. User authentication and role-specific access.
2. Employee records, employee profiles and department management.
3. Attendance records and employee self-service clock-in/clock-out.
4. Employee leave requests, manager decisions and leave type administration.
5. Payroll periods and payslips, with amounts displayed as ZMW.
6. Appraisal cycles and performance reviews.
7. Job postings, applicants and interview scheduling.
8. Training courses, staff enrollment and employee self-enrollment.
9. A role-scoped dashboard with live employee, leave, vacancy, recruitment, same-day attendance and training information, plus permission-appropriate shortcuts.

## 4. Roles and permissions

| Capability | Administrator | HR Officer | Manager | Employee |
|---|---:|---:|---:|---:|
| Django admin / system administration | Yes | No | No | No |
| View all employee records and departments | Yes | Yes | No | No |
| View own and direct-report employee records | Yes | Yes | Yes | No |
| View own employee record | Yes | Yes | Yes | Yes |
| Create/edit employee and department records | Yes | Yes | No | No |
| View all attendance and maintain records | Yes | Yes | Team records | No |
| View own attendance / clock in and out | Yes | Yes | Yes | Yes |
| View all leave requests and manage leave types | Yes | Yes | No | No |
| View own/team leave and decide direct-report requests | Yes | Yes | Yes | No |
| View all payroll and manage periods/payslips | Yes | Yes | No | No |
| View own payslips | Yes | Yes | Yes | Yes |
| View all performance reviews and cycles | Yes | Yes | Team and own | Own |
| Create/edit performance reviews | Yes | Yes | Direct reports | No |
| Manage recruitment records | Yes | Yes | No | No |
| Browse job postings | Yes | Yes | Yes | Yes |
| View training enrollments | All | All | Team and own | Own |
| Browse courses and self-enroll | Yes | Yes | Yes | Yes |

The administrator account has `is_staff` and `is_superuser` set. HRMS role checks are application-level and are not a replacement for a separately configured enterprise identity or Django object-permission system. Unauthorized management actions are denied or redirected with a message; private employee detail lookups return not found when outside the user's scope.

## 5. System workflows

### Authentication and employee setup

Users sign in through `accounts:login`; successful authentication opens the dashboard. HR/admin can add or edit an employee record for an existing Django user. When an employee record is created or reassigned, the system creates a default Employee role profile if the selected user has none. The employee form captures department, employee identifier, job, contact, salary and manager details. Department records are maintained by HR/admin. Creating the underlying Django user account is a separate step.

### Leave

An employee submits a request from the leave form. The employee sees their own requests; a manager sees their own and direct reports' requests; HR/admin can see organization-wide requests. Managers can decide only requests belonging to their direct reports. HR/admin can manage leave types.

### Attendance

Employees clock in/out from self-service. HR/admin can view and maintain organization-wide attendance; a manager can view and maintain their own and direct reports' attendance; employees see their own records.

### Payroll

HR/admin create a period and generate payslips for active employees. HR/admin can view and manage payroll records. Other roles can view only their own payslips. Amounts are represented in Zambian kwacha (ZMW).

### Performance

HR/admin can access all review data. Employees see their own reviews. Managers see team reviews and may create or edit reviews for direct reports; manager review forms restrict employee and reviewer choices accordingly.

### Recruitment, training and self-service

Authenticated users can browse job postings. Applicant and interview records are HR/admin-only. HR/admin maintain training courses and enrollments; employees self-enroll when a course has space. The self-service workspace brings together an employee's own leave, attendance, payslips, reviews and learning.

## 6. Database overview

The schema is managed through Django migrations. The main entities are:

- **Accounts:** Django `auth.User` and `UserProfile` (one-to-one role and contact phone).
- **Employees:** `Department` and `Employee`, linked to a user, optional manager and department.
- **Attendance:** `AttendanceRecord`, unique per employee and date.
- **Leave:** `LeaveType` and `LeaveRequest`, including decision status and approver.
- **Payroll:** `PayrollPeriod` and `Payslip`, unique per employee and period.
- **Performance:** `AppraisalCycle` and `PerformanceReview`, unique per employee and cycle.
- **Recruitment:** `JobPosting`, `Applicant` and `Interview`.
- **Training:** `TrainingCourse` and `TrainingEnrollment`.

The default local database file is `db.sqlite3` (ignored by Git). No schema migration was required for this UI, role-scoping and seed-data update.

## 7. Installation and configuration

From the project directory:

```powershell
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver 127.0.0.1:8001
```

`run_hrms.bat` is an optional Windows launcher. It expects `..\hrms-venv\Scripts\activate.bat` and checks port 8001 before starting. Configure `DATABASE_URL` to use a non-SQLite database. For deployment, provide a unique `DJANGO_SECRET_KEY`, set `DJANGO_DEBUG=False`, configure allowed hosts and database secrets, and collect static files. Do not deploy the shared demo password or the development secret key as production credentials.

The demo command creates five fictional accounts using `.test` emails and sample Zambian phone numbers and locations. It resets their shared demonstration password each time it runs; see [HRMS_DEMONSTRATION_GUIDE.md](./HRMS_DEMONSTRATION_GUIDE.md) for usernames and role walkthroughs.

## 8. Testing results

The automated suite was run with:

```powershell
python manage.py check
python manage.py test
```

**Latest result:** `python manage.py check` passed with no issues; `python manage.py test --verbosity 1` passed all 15 tests. Coverage includes all five demo logins and role assignments, repeatable demo seeding, role-aware navigation and dashboard metrics, current-day attendance and pending-leave scoping, employee and department management, form validation, employee and payroll/attendance scoping, HR-only recruitment access, manager direct-report leave decisions, team-scoped performance/training views and module URL rendering. `collectstatic --noinput --dry-run` completed successfully (128 static files discovered).

There is no separate JavaScript package manifest or frontend build/test runner. Django's template rendering and system tests cover the server-rendered navigation and forms. During the initial investigation, the local stylesheet and Bootstrap returned successfully and the browser reported no console or failed-request errors. A post-redesign visual browser pass at the requested desktop, tablet and mobile widths remains outstanding.

## 9. Known limitations and future improvements

- No standalone Reports or System Settings modules are implemented.
- Employee account creation is separate from employee-record creation; the employee form requires an existing Django user.
- Role checks are enforced in views but are not a centralized Django object-permission or organizational policy framework.
- Sample demo users share a known password. The seeder is intended only for a local/demo database.
- Bootstrap is fetched from a CDN; offline use requires a locally hosted copy. Inter is not fetched separately; system UI fonts provide the professional fallback stack.
- The application is an academic demonstration and needs a production security/configuration review before deployment.
- Future improvements could include employee account provisioning, formal report exports, settings management, automated permission matrices, localization, and a self-hosted frontend asset pipeline.
