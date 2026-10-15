from datetime import date, datetime, time, timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import UserProfile
from attendance.models import AttendanceRecord
from employees.models import Department, Employee
from leave.models import LeaveRequest, LeaveType
from payroll.models import PayrollPeriod, Payslip
from performance.models import AppraisalCycle, PerformanceReview
from recruitment.models import Applicant, Interview, JobPosting
from training.models import TrainingCourse, TrainingEnrollment


class Command(BaseCommand):
    help = 'Load academic demo users and sample HRMS data'

    def handle(self, *args, **options):
        self.stdout.write('Seeding HRMS demo data...')

        departments = {}
        for name, desc in [
            ('Human Resources', 'People operations and talent'),
            ('Information Technology', 'Systems and infrastructure'),
            ('Finance', 'Accounting and payroll support'),
            ('Operations', 'Day-to-day business operations'),
        ]:
            departments[name], _ = Department.objects.get_or_create(
                name=name, defaults={'description': desc}
            )

        def make_user(username, first, last, email, role, password='demo1234'):
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'first_name': first,
                    'last_name': last,
                    'email': email,
                    'is_staff': role == 'ADMIN',
                    'is_superuser': role == 'ADMIN',
                },
            )
            if created:
                user.set_password(password)
                user.save()
            else:
                user.first_name = first
                user.last_name = last
                user.email = email
                user.set_password(password)
                user.is_staff = role == 'ADMIN'
                user.is_superuser = role == 'ADMIN'
                user.save()
            UserProfile.objects.update_or_create(
                user=user,
                defaults={'role': role, 'phone': '+27 11 000 0000'},
            )
            return user

        admin = make_user('admin', 'System', 'Admin', 'admin@hrms.demo', 'ADMIN')
        hr = make_user('hr.officer', 'Helen', 'Roberts', 'hr@hrms.demo', 'HR')
        manager = make_user('manager1', 'Mark', 'Ndlovu', 'manager@hrms.demo', 'MANAGER')
        emp1 = make_user('employee1', 'Emma', 'Dlamini', 'emma@hrms.demo', 'EMPLOYEE')
        emp2 = make_user('employee2', 'Thabo', 'Molefe', 'thabo@hrms.demo', 'EMPLOYEE')

        def make_employee(user, eid, dept, title, salary, manager_emp=None, hire=None):
            emp, _ = Employee.objects.update_or_create(
                user=user,
                defaults={
                    'employee_id': eid,
                    'department': dept,
                    'job_title': title,
                    'hire_date': hire or date(2022, 3, 1),
                    'date_of_birth': date(1992, 6, 15),
                    'phone': '+27 82 555 0100',
                    'address': 'Johannesburg, South Africa',
                    'emergency_contact': 'Next of kin — 082 000 1111',
                    'base_salary': Decimal(salary),
                    'status': Employee.Status.ACTIVE,
                    'manager': manager_emp,
                },
            )
            return emp

        hr_emp = make_employee(hr, 'EMP001', departments['Human Resources'], 'HR Officer', '28000')
        mgr_emp = make_employee(
            manager, 'EMP002', departments['Information Technology'], 'IT Manager', '45000'
        )
        e1 = make_employee(
            emp1,
            'EMP003',
            departments['Information Technology'],
            'Software Developer',
            '32000',
            manager_emp=mgr_emp,
            hire=date(2023, 1, 10),
        )
        e2 = make_employee(
            emp2,
            'EMP004',
            departments['Finance'],
            'Payroll Clerk',
            '24000',
            manager_emp=hr_emp,
            hire=date(2023, 8, 1),
        )
        make_employee(
            admin, 'EMP000', departments['Human Resources'], 'System Administrator', '50000'
        )

        annual, _ = LeaveType.objects.get_or_create(
            name='Annual Leave', defaults={'days_allowed': 21, 'description': 'Paid annual leave'}
        )
        sick, _ = LeaveType.objects.get_or_create(
            name='Sick Leave', defaults={'days_allowed': 30, 'description': 'Medical leave'}
        )
        LeaveType.objects.get_or_create(
            name='Family Responsibility',
            defaults={'days_allowed': 5, 'description': 'Family responsibility leave'},
        )

        LeaveRequest.objects.get_or_create(
            employee=e1,
            leave_type=annual,
            start_date=date.today() + timedelta(days=14),
            end_date=date.today() + timedelta(days=18),
            defaults={
                'reason': 'Family holiday',
                'status': LeaveRequest.Status.PENDING,
            },
        )
        LeaveRequest.objects.get_or_create(
            employee=e2,
            leave_type=sick,
            start_date=date.today() - timedelta(days=5),
            end_date=date.today() - timedelta(days=4),
            defaults={
                'reason': 'Flu recovery',
                'status': LeaveRequest.Status.APPROVED,
                'approved_by': manager,
            },
        )

        today = date.today()
        for emp, cin, cout, status in [
            (e1, time(8, 0), time(16, 30), AttendanceRecord.Status.PRESENT),
            (e2, time(8, 45), time(16, 30), AttendanceRecord.Status.LATE),
            (mgr_emp, time(7, 50), time(17, 0), AttendanceRecord.Status.PRESENT),
        ]:
            AttendanceRecord.objects.update_or_create(
                employee=emp,
                date=today,
                defaults={'check_in': cin, 'check_out': cout, 'status': status},
            )

        job, _ = JobPosting.objects.get_or_create(
            title='Junior Developer',
            defaults={
                'department': departments['Information Technology'],
                'description': 'Support web application development for internal systems.',
                'requirements': 'Python/Django basics, teamwork, willingness to learn.',
                'status': JobPosting.Status.OPEN,
                'closing_date': today + timedelta(days=30),
                'created_by': hr,
            },
        )
        applicant, _ = Applicant.objects.get_or_create(
            job=job,
            email='candidate@example.com',
            defaults={
                'full_name': 'Sipho Khumalo',
                'phone': '+27 83 111 2222',
                'resume_summary': 'Recent IT graduate with internship experience.',
                'status': Applicant.Status.INTERVIEW,
            },
        )
        Interview.objects.get_or_create(
            applicant=applicant,
            scheduled_at=timezone.make_aware(datetime.combine(today + timedelta(days=3), time(10, 0))),
            defaults={
                'interviewer': mgr_emp,
                'location': 'Meeting Room B',
                'result': Interview.Result.PENDING,
            },
        )

        period, _ = PayrollPeriod.objects.get_or_create(
            month=today.month,
            year=today.year,
            defaults={'status': PayrollPeriod.Status.PROCESSED, 'processed_at': timezone.now()},
        )
        for emp in [hr_emp, mgr_emp, e1, e2]:
            Payslip.objects.update_or_create(
                employee=emp,
                period=period,
                defaults={
                    'basic_salary': emp.base_salary,
                    'allowances': Decimal('1500.00'),
                    'deductions': Decimal('2200.00'),
                    'net_pay': emp.base_salary + Decimal('1500.00') - Decimal('2200.00'),
                },
            )

        cycle, _ = AppraisalCycle.objects.get_or_create(
            name=f'{today.year} Mid-Year Review',
            defaults={
                'start_date': date(today.year, 6, 1),
                'end_date': date(today.year, 7, 31),
                'status': AppraisalCycle.Status.ACTIVE,
            },
        )
        PerformanceReview.objects.update_or_create(
            employee=e1,
            cycle=cycle,
            defaults={
                'reviewer': mgr_emp,
                'goals': 'Deliver HRMS module features on schedule.',
                'achievements': 'Completed leave and attendance modules.',
                'rating': 4,
                'comments': 'Strong contributor with good collaboration.',
                'status': PerformanceReview.Status.SUBMITTED,
            },
        )

        course, _ = TrainingCourse.objects.get_or_create(
            title='Workplace Health & Safety',
            defaults={
                'description': 'Mandatory safety awareness for all staff.',
                'trainer': 'External Facilitator',
                'start_date': today + timedelta(days=7),
                'end_date': today + timedelta(days=8),
                'capacity': 25,
                'status': TrainingCourse.Status.UPCOMING,
            },
        )
        TrainingCourse.objects.get_or_create(
            title='Django for HR Systems',
            defaults={
                'description': 'Internal technical upskilling.',
                'trainer': 'Mark Ndlovu',
                'start_date': today + timedelta(days=21),
                'end_date': today + timedelta(days=23),
                'capacity': 12,
                'status': TrainingCourse.Status.UPCOMING,
            },
        )
        TrainingEnrollment.objects.get_or_create(
            course=course,
            employee=e1,
            defaults={'status': TrainingEnrollment.Status.ENROLLED},
        )
        TrainingEnrollment.objects.get_or_create(
            course=course,
            employee=e2,
            defaults={'status': TrainingEnrollment.Status.ENROLLED},
        )

        self.stdout.write(self.style.SUCCESS('Demo data loaded.'))
        self.stdout.write('Login accounts (password: demo1234):')
        self.stdout.write('  admin / hr.officer / manager1 / employee1 / employee2')
