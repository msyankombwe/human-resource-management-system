# HRMS Demonstration Guide

## Project overview

PeopleSpace HRMS is a Django application for demonstrating day-to-day human resource workflows in a Zambia-based organization. Its responsive interface uses a teal and turquoise theme, an authenticated left sidebar and navigation links that reflect the signed-in user's role.

Implemented modules include employee and department management, attendance, leave, payroll, performance reviews, recruitment, training and employee self-service. The dashboard provides role-scoped operational counts and upcoming training. Reports and system settings are not separate implemented modules.

## Start the application

From `C:\Users\morga\Documents\hrms`:

```powershell
python manage.py migrate
python manage.py seed_demo
python manage.py runserver 127.0.0.1:8001
```

Open [http://127.0.0.1:8001/](http://127.0.0.1:8001/) and choose **Sign in**. If using the provided Windows launcher, run `run_hrms.bat`; it activates `..\hrms-venv` and requires port 8001 to be free.

The `seed_demo` command is safe to rerun: it updates the five named demo accounts and sample HR data rather than creating duplicate demo employees. It resets the shared demonstration password on each run. Do not use these accounts or credentials in a production deployment.

## Demonstration accounts

All contacts and addresses below are fictional. Email addresses use the reserved `.test` domain and phone numbers are sample values.

| Name | Username | Role | Demonstration location |
|---|---|---|---|
| Comfort Kakumbi Limata | `comfort.kakumbi` | System Administrator | Lusaka |
| Victor Lungu | `victor.lungu` | Employee | Kabwe |
| Morgan Syankombwe | `morgan.syankombwe` | Employee | Livingstone |
| Augustine Nsofwa | `augustine.nsofwa` | Manager | Kitwe |
| Mwamba Z Mwila | `mwamba.mwila` | HR Officer | Ndola |

**Shared demo password:** `HRMS-Demo-2026!`

The administrator has Django staff and superuser privileges. The HR Officer can manage authorized HR functions but is not a Django superuser. The manager's direct report in the seeded data is Victor; Morgan reports to the HR Officer. Employees see their own sensitive records.

## Login and role walkthroughs

1. Navigate to the application URL and sign in with a username and the shared demo password.
2. The dashboard opens after successful authentication. Use the sidebar to move between implemented modules; the current section is highlighted.
3. Use the user section at the bottom of the sidebar to confirm the role or log out.

### System Administrator — `comfort.kakumbi`

- Open the dashboard and review the organization-wide employee, vacancy, leave and applicant counts.
- Open **Employees** and **Departments** to view and manage HR records.
- Explore attendance, leave, payroll, performance, recruitment and learning workflows.
- Use Django admin at `/admin/` for the framework's administrative interface.

Expected result: the administrator can access system administration and all implemented HR operations. Seeded salary and payroll amounts are shown in Zambian kwacha (ZMW).

### HR Officer — `mwamba.mwila`

- Review organization-wide employee and applicant counts.
- Add a department from **Departments** or create/update an employee record from **Employees**.
- Review leave requests and manage leave types.
- Create job postings, manage applicants/interviews, create payroll periods and enroll staff in training.

Expected result: HR operations are available, but Django admin's superuser-only controls remain unavailable to the HR account.

### Manager — `augustine.nsofwa`

- Open **Employees** to view the manager's own record and direct reports, including Victor.
- Review and decide a direct report's leave request; the seeded pending request is Victor's.
- Review team attendance and performance information and create a review for a direct report.
- Open the manager's own payslip, job postings and training enrollments.

Expected result: employee, attendance, leave, performance and training lists are restricted to the manager and direct reports. A manager cannot decide leave for a person outside their team or view another employee's payroll.

### Employee — `victor.lungu` or `morgan.syankombwe`

- Open **My workspace** to review personal leave, attendance, payslips, reviews and training.
- Use **Leave management** to submit a leave request.
- Use the employee self-service attendance actions to clock in and out.
- Browse job postings and training courses; enroll in an available course.

Expected result: employees can use authorized self-service and see their own sensitive data, but cannot open HR administration pages or see another employee's records.

## Key module outputs

- **Employees / Departments:** filtered employee directory, employee profile, validation feedback and saved HR records.
- **Attendance:** daily attendance records and clock-in/clock-out times.
- **Leave management:** pending, approved or rejected requests; managers can decide requests from their direct reports.
- **Payroll:** payroll periods and payslips with ZMW values; non-HR users can see only their own payslips.
- **Performance:** appraisal cycles and employee reviews, scoped to the user's own record or team.
- **Recruitment:** job postings for authenticated users; applicant and interview records for HR and administrators.
- **Learning:** training courses and role-scoped enrollments.
- **Dashboard:** counts scoped to the viewer's role, plus upcoming training.

## Resetting demo data

Run:

```powershell
python manage.py seed_demo
```

This refreshes demo account names, roles, passwords and employee details, and creates the seeded sample workflows. Run it only against a local/demo database: it deliberately resets the five known demonstration users.
