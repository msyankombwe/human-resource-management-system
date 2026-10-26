# Digital Agricultural Marketplace and Export Linkage System (DAMELS)

Zambian agricultural marketplace prototype for connecting farmers, buyers and export markets. The existing HRMS modules remain available under the HRMS navigation.

## DAMELS marketplace

- Farmer, buyer and combined-role registration and sign-in
- Searchable agricultural listings, including produce quantity, location, quality and asking price
- Buyer offers and farmer accept/decline actions
- Order creation when a farmer accepts an offer; order status progression from confirmed through delivery
- Admin-managed indicative market prices
- Buyer and farmer dashboards

### Local setup

```powershell
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Visit http://127.0.0.1:8000/ to explore the marketplace. A local SQLite database is used when `DATABASE_URL` is not set. Create users through **Join DAMELS**; one account can be a farmer, a buyer, or both. Indicative prices can be entered from Django admin.

### Supabase database and Render deployment

The Django application can use a Supabase-hosted PostgreSQL database through its `DATABASE_URL` connection string. Set `DATABASE_URL`, `SUPABASE_URL` and `SUPABASE_ANON_KEY` as secret environment variables on Render, then deploy using the included `render.yaml` blueprint. Render applies migrations at startup and collects static files during the build. Set a strong `DJANGO_SECRET_KEY`; keep `DJANGO_DEBUG=False` in production.

With the Supabase Auth variables configured, marketplace registration and sign-in use Supabase Auth; Django stores only a local session/profile mirror (passwords are not saved in Django). Django's user and marketplace tables are persisted in Supabase PostgreSQL. Without those variables, local development falls back to Django authentication and SQLite. Configure Supabase Auth's site URL and allowed redirect URLs for the Render hostname, and enable email confirmation if desired. For deployment, configure Render and Supabase in their dashboards; credentials are intentionally not stored in this repository.

### Demonstration workflow

1. Register a farmer account and sign in.
2. Publish a maize listing for 100 tonnes in Mkushi.
3. Register/sign in as a buyer and search for maize in Mkushi.
4. Submit an offer for some or all of the available tonnage.
5. The farmer accepts the offer from their dashboard.
6. DAMELS creates a confirmed order and reduces the listing's available tonnage.
7. Both accounts can view the order; the farmer can progress its status through preparing, shipped and delivered.

Run the marketplace workflow tests with:

```powershell
python manage.py test marketplace
```

## Existing HRMS modules

Role-based employee management, recruitment, attendance, leave, payroll, performance, training and employee self-service remain available in the HRMS area. The existing demo credentials and seed command are retained below.

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

## HRMS demo setup

```powershell
cd C:\Users\morga\Documents\hrms
..\hrms-venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

Open http://127.0.0.1:8000/login/ and sign in with a demo account.

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

- SQLite database (`db.sqlite3`) for local demos; PostgreSQL can be configured with `DATABASE_URL`
- Bootstrap 5 CDN UI
- Not production-hardened (DEBUG on, demo secret key)
