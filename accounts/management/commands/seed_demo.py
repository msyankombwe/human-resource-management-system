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
    help = 'Load fictional Zambia-based HRMS demonstration users and sample data'

    def handle(self, *args, **options):
        self.stdout.write('Seeding HRMS demo data...')
        demo_password = 'HRMS-Demo-2026!'
        today = timezone.localdate()

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

        def make_user(username, first, last, email, role, phone, legacy_username=None):
            user = User.objects.filter(username=username).first()
            if user is None and legacy_username:
                user = User.objects.filter(username=legacy_username).first()
                if user:
                    user.username = username
            if user is None:
                user = User(username=username)
            user.first_name = first
            user.last_name = last
            user.email = email
            user.is_staff = role == UserProfile.Role.ADMIN
            user.is_superuser = role == UserProfile.Role.ADMIN
            user.is_active = True
            user.set_password(demo_password)
            user.save()
            UserProfile.objects.update_or_create(
                user=user,
                defaults={'role': role, 'phone': phone},
            )
            return user

        admin = make_user(
            'comfort.kakumbi', 'Comfort Kakumbi', 'Limata',
            'comfort.kakumbi@hrms.example.test', UserProfile.Role.ADMIN,
            '+260 97 000 0001', legacy_username='admin',
        )
        employee1 = make_user(
            'victor.lungu', 'Victor', 'Lungu', 'victor.lungu@hrms.example.test',
            UserProfile.Role.EMPLOYEE, '+260 97 000 0002', legacy_username='employee1',
        )
        employee2 = make_user(
            'morgan.syankombwe', 'Morgan', 'Syankombwe',
            'morgan.syankombwe@hrms.example.test', UserProfile.Role.EMPLOYEE,
            '+260 97 000 0003', legacy_username='employee2',
        )
        manager = make_user(
            'augustine.nsofwa', 'Augustine', 'Nsofwa',
            'augustine.nsofwa@hrms.example.test', UserProfile.Role.MANAGER,
            '+260 97 000 0004', legacy_username='manager1',
        )
        hr = make_user(
            'mwamba.mwila', 'Mwamba Z', 'Mwila', 'mwamba.mwila@hrms.example.test',
            UserProfile.Role.HR, '+260 97 000 0005', legacy_username='hr.officer',
        )

        def make_employee(
            user, eid, dept, title, salary, address, manager_emp=None, hire=None,
        ):
            emp, _ = Employee.objects.update_or_create(
                user=user,
                defaults={
                    'employee_id': eid,
                    'department': dept,
                    'job_title': title,
                    'hire_date': hire or date(2022, 3, 1),
                    'date_of_birth': date(1992, 6, 15),
                    'phone': user.profile.phone,
                    'address': address,
                    'emergency_contact': 'Demo contact: +260 97 000 0099',
                    'base_salary': Decimal(salary),
                    'status': Employee.Status.ACTIVE,
                    'manager': manager_emp,
                },
            )
            return emp

        hr_emp = make_employee(
            hr, 'EMP001', departments['Human Resources'], 'HR Officer', '28000',
            'Town Centre, Ndola, Zambia',
        )
        mgr_emp = make_employee(
            manager, 'EMP002', departments['Information Technology'], 'Manager', '45000',
            'Riverside, Kitwe, Zambia',
        )
        e1 = make_employee(
            employee1,
            'EMP003',
            departments['Information Technology'],
            'Software Developer',
            '32000',
            'Central Kabwe, Kabwe, Zambia',
            manager_emp=mgr_emp,
            hire=date(2023, 1, 10),
        )
        e2 = make_employee(
            employee2,
            'EMP004',
            departments['Finance'],
            'Payroll Clerk',
            '24000',
            'Livingstone, Zambia',
            manager_emp=hr_emp,
            hire=date(2023, 8, 1),
        )
        make_employee(
            admin, 'EMP000', departments['Human Resources'], 'System Administrator', '50000',
            'Kabulonga, Lusaka, Zambia',
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

        LeaveRequest.objects.update_or_create(
            employee=e1,
            leave_type=annual,
            reason='Family holiday',
            defaults={
                'start_date': today + timedelta(days=14),
                'end_date': today + timedelta(days=18),
                'status': LeaveRequest.Status.PENDING,
            },
        )
        LeaveRequest.objects.update_or_create(
            employee=e2,
            leave_type=sick,
            reason='Flu recovery',
            defaults={
                'start_date': today - timedelta(days=5),
                'end_date': today - timedelta(days=4),
                'status': LeaveRequest.Status.APPROVED,
                'approved_by': hr,
            },
        )

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
        Applicant.objects.filter(
            job=job,
            email='candidate@example.com',
        ).update(
            email='candidate@hrms.example.test',
            full_name='Demo Candidate',
            phone='+260 97 000 0010',
        )
        applicant, _ = Applicant.objects.get_or_create(
            job=job,
            email='candidate@hrms.example.test',
            defaults={
                'full_name': 'Demo Candidate',
                'phone': '+260 97 000 0010',
                'resume_summary': 'Recent IT graduate with internship experience.',
                'status': Applicant.Status.INTERVIEW,
            },
        )
        Interview.objects.update_or_create(
            applicant=applicant,
            defaults={
                'scheduled_at': timezone.make_aware(
                    datetime.combine(today + timedelta(days=3), time(10, 0))
                ),
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
        for emp in [admin.employee, hr_emp, mgr_emp, e1, e2]:
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

        course, _ = TrainingCourse.objects.update_or_create(
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
        TrainingCourse.objects.update_or_create(
            title='Django for HR Systems',
            defaults={
                'description': 'Internal technical upskilling.',
                'trainer': 'Demo Trainer',
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
        self.stdout.write(f'Demo password for all accounts: {demo_password}')
        self.stdout.write('  comfort.kakumbi (Administrator)')
        self.stdout.write('  victor.lungu, morgan.syankombwe (Employees)')
        self.stdout.write('  augustine.nsofwa (Manager)')
        self.stdout.write('  mwamba.mwila (HR Officer)')
