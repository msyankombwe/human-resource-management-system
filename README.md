# PeopleSpace HRMS

PeopleSpace is a Django-based Human Resource Management System demonstration for a Zambian organization. It includes a responsive, role-aware workspace for employee records, departments, leave, attendance, payroll, performance, recruitment, training and employee self-service.

## Run locally

From `C:\Users\morga\Documents\hrms`, activate the project's Python environment and run:

```powershell
python manage.py migrate
python manage.py seed_demo
python manage.py runserver 127.0.0.1:8001
```

Open [http://127.0.0.1:8001/](http://127.0.0.1:8001/). The optional `run_hrms.bat` launcher uses the sibling `..\hrms-venv` environment and checks that port 8001 is available. If dependencies are not installed, install those in `requirements.txt` first.

The local default database is SQLite (`db.sqlite3`); setting `DATABASE_URL` configures another Django-supported database. The application uses the `Africa/Lusaka` time zone. Use `python manage.py seed_demo` to create or refresh the fictional demonstration records and accounts. All five demo accounts use `HRMS-Demo-2026!`; these shared demo credentials are for local demonstration only.

## Project modules

| Django app | Main capabilities |
|---|---|
| `accounts` | Login, role profiles, dashboard and demonstration data |
| `employees` | Employee records and departments |
| `attendance` | Daily records and employee clock in/out |
| `leave` | Leave requests, decisions and leave types |
| `payroll` | Payroll periods and payslips (ZMW) |
| `performance` | Appraisal cycles and performance reviews |
| `recruitment` | Job postings, applicants and interviews |
| `training` | Courses and employee enrollments |
| `self_service` | Employee profile, attendance, leave, payslip and learning views |

The `admin` URL is available to the system administrator. The application does not currently have separate reporting or system-settings modules; the dashboard is the implemented overview.

## Documentation and tests

- [HRMS_DEMONSTRATION_GUIDE.md](./HRMS_DEMONSTRATION_GUIDE.md) — startup, demo identities and walkthroughs by role.
- [HRMS_SYSTEM_DOCUMENTATION.md](./HRMS_SYSTEM_DOCUMENTATION.md) — architecture, permissions, workflows, setup and verification.

Run the checks and test suite with:

```powershell
python manage.py check
python manage.py test
```
