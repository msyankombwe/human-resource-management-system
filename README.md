# Human Resource Management System (HRMS)

Academic Django web application for automating HR operations with role-based access.

## Modules

1. **Employee Information Management** — departments, employee records
2. **Recruitment Management** — job postings, applicants, interviews
3. **Attendance Management** — daily records, clock-in / clock-out
4. **Leave Management** — leave types, requests, approvals
5. **Payroll Management** — periods, payslip generation
6. **Performance Management** — appraisal cycles and reviews
7. **Training and Development** — courses and enrollments
8. **Employee Self-Service** — personal leave, attendance, payslips, training

## Roles

| Role | Username (demo) | Access highlight |
|------|-----------------|------------------|
| Administrator | `admin` | Full access + Django admin |
| HR Officer | `hr.officer` | HR operations across modules |
| Manager | `manager1` | Team leave, attendance, reviews |
| Employee | `employee1` / `employee2` | Self-service focused |

All demo passwords: `demo1234`

## Setup

```powershell
cd C:\Users\morga\Documents\hrms
..\hrms-venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

Open http://127.0.0.1:8000/ and sign in with a demo account.

Django admin: http://127.0.0.1:8000/admin/ (use `admin` / `demo1234`).

## Project layout

```
hrms/
  accounts/          # Auth, roles, dashboard, seed command
  employees/         # Employee Information Management
  recruitment/       # Recruitment Management
  attendance/        # Attendance Management
  leave/             # Leave Management
  payroll/           # Payroll Management
  performance/       # Performance Management
  training/          # Training and Development
  self_service/      # Employee Self-Service
  templates/         # Shared UI templates
  static/css/        # Styles
  hrms_project/      # Django settings & URLs
```

## Notes

- SQLite database (`db.sqlite3`) for easy academic demos
- Bootstrap 5 CDN UI
- Not production-hardened (DEBUG on, demo secret key)
