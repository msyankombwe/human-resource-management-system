from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import UserProfile
from employees.models import Department, Employee
from leave.models import LeaveRequest, LeaveType


class LocalNavigationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(
            username='hrms-test-user',
            password='test-password',
        )

    def test_root_redirects_to_dashboard(self):
        response = self.client.get('/')

        self.assertRedirects(
            response,
            reverse('accounts:dashboard'),
            fetch_redirect_response=False,
        )

    def test_login_and_dashboard_render(self):
        response = self.client.get(reverse('accounts:login'))
        self.assertContains(response, 'Sign in to your HRMS account')

        response = self.client.post(
            reverse('accounts:login'),
            {'username': 'hrms-test-user', 'password': 'test-password'},
        )
        self.assertRedirects(
            response,
            reverse('accounts:dashboard'),
            fetch_redirect_response=False,
        )
        self.assertEqual(self.client.get(reverse('accounts:dashboard')).status_code, 200)


class DemoRoleIntegrationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('seed_demo', verbosity=0)

    def demo_user(self, username):
        return get_user_model().objects.get(username=username)

    def test_seed_creates_five_fictional_zambian_accounts_idempotently(self):
        User = get_user_model()
        expected = {
            'comfort.kakumbi': (UserProfile.Role.ADMIN, 'Comfort Kakumbi Limata'),
            'victor.lungu': (UserProfile.Role.EMPLOYEE, 'Victor Lungu'),
            'morgan.syankombwe': (UserProfile.Role.EMPLOYEE, 'Morgan Syankombwe'),
            'augustine.nsofwa': (UserProfile.Role.MANAGER, 'Augustine Nsofwa'),
            'mwamba.mwila': (UserProfile.Role.HR, 'Mwamba Z Mwila'),
        }
        self.assertEqual(User.objects.count(), len(expected))
        for username, (role, full_name) in expected.items():
            user = self.demo_user(username)
            self.assertEqual(user.get_full_name(), full_name)
            self.assertEqual(user.profile.role, role)
            self.assertTrue(user.check_password('HRMS-Demo-2026!'))
            self.assertTrue(user.email.endswith('@hrms.example.test'))
            self.assertTrue(user.is_active)

        admin = self.demo_user('comfort.kakumbi')
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)
        self.assertFalse(self.demo_user('mwamba.mwila').is_staff)
        self.assertTrue(
            all('Zambia' in user.employee.address for user in User.objects.all())
        )
        self.assertEqual(
            set(Employee.objects.values_list('address', flat=True)),
            {
                'Kabulonga, Lusaka, Zambia',
                'Central Kabwe, Kabwe, Zambia',
                'Livingstone, Zambia',
                'Riverside, Kitwe, Zambia',
                'Town Centre, Ndola, Zambia',
            },
        )

        call_command('seed_demo', verbosity=0)
        self.assertEqual(User.objects.count(), len(expected))
        self.assertEqual(
            LeaveRequest.objects.filter(
                employee=self.demo_user('victor.lungu').employee,
                reason='Family holiday',
            ).count(),
            1,
        )

    def test_each_demo_role_can_sign_in_and_open_dashboard(self):
        for username in (
            'comfort.kakumbi',
            'victor.lungu',
            'morgan.syankombwe',
            'augustine.nsofwa',
            'mwamba.mwila',
        ):
            with self.subTest(username=username):
                response = self.client.post(
                    reverse('accounts:login'),
                    {'username': username, 'password': 'HRMS-Demo-2026!'},
                )
                self.assertRedirects(
                    response,
                    reverse('accounts:dashboard'),
                    fetch_redirect_response=False,
                )
                self.assertEqual(
                    self.client.get(reverse('accounts:dashboard')).status_code,
                    200,
                )
                self.client.get(reverse('accounts:logout'))
        self.client.force_login(self.demo_user('comfort.kakumbi'))
        self.assertEqual(self.client.get(reverse('admin:index')).status_code, 200)

    def test_navigation_only_shows_role_appropriate_links(self):
        cases = (
            ('comfort.kakumbi', True, True, True),
            ('mwamba.mwila', True, True, True),
            ('augustine.nsofwa', True, False, False),
            ('victor.lungu', False, False, False),
        )
        for username, can_manage_people, can_recruit, can_run_payroll in cases:
            with self.subTest(username=username):
                self.client.force_login(self.demo_user(username))
                response = self.client.get(reverse('accounts:dashboard'))
                html = response.content.decode()
                self.assertEqual(
                    reverse('employees:list') in html,
                    can_manage_people,
                )
                self.assertEqual(
                    reverse('employees:departments') in html,
                    username in {'comfort.kakumbi', 'mwamba.mwila'},
                )
                self.assertEqual(
                    reverse('recruitment:applicants') in html,
                    can_recruit,
                )
                self.assertEqual(
                    reverse('payroll:periods') in html,
                    can_run_payroll,
                )
                self.assertIn(reverse('leave:list'), html)
                self.assertIn(reverse('self_service:home'), html)
                self.client.get(reverse('accounts:logout'))

    def test_dashboard_metrics_are_role_scoped_without_duplicate_cards(self):
        self.client.force_login(self.demo_user('comfort.kakumbi'))
        response = self.client.get(reverse('accounts:dashboard'))
        self.assertEqual(response.content.decode().count('Pending Leave'), 1)
        self.assertContains(response, 'Applicants')

        self.client.force_login(self.demo_user('augustine.nsofwa'))
        response = self.client.get(reverse('accounts:dashboard'))
        self.assertContains(response, 'Direct reports')
        self.assertNotContains(response, 'Applicants')
        self.assertEqual(response.context['direct_report_count'], 1)
        self.assertEqual(response.context['employee_count'], 1)

        self.client.force_login(self.demo_user('victor.lungu'))
        response = self.client.get(reverse('accounts:dashboard'))
        self.assertContains(response, 'My courses')
        self.assertNotContains(response, 'Applicants')
        self.assertNotContains(response, 'Morgan Syankombwe')

    def test_employee_manager_and_hr_employee_records_are_scoped(self):
        victor = self.demo_user('victor.lungu')
        augustine = self.demo_user('augustine.nsofwa')
        morgan = self.demo_user('morgan.syankombwe')

        self.client.force_login(victor)
        response = self.client.get(reverse('employees:list'))
        self.assertEqual(
            set(response.context['employees'].values_list('user__username', flat=True)),
            {'victor.lungu'},
        )
        self.assertEqual(
            self.client.get(
                reverse('employees:detail', args=[morgan.employee.pk])
            ).status_code,
            404,
        )

        self.client.force_login(augustine)
        response = self.client.get(reverse('employees:list'))
        self.assertEqual(
            set(response.context['employees'].values_list('user__username', flat=True)),
            {'victor.lungu', 'augustine.nsofwa'},
        )
        self.assertEqual(
            self.client.get(
                reverse('employees:detail', args=[victor.employee.pk])
            ).status_code,
            200,
        )
        self.assertEqual(
            self.client.get(
                reverse('employees:detail', args=[morgan.employee.pk])
            ).status_code,
            404,
        )

        self.client.force_login(self.demo_user('mwamba.mwila'))
        response = self.client.get(reverse('employees:list'))
        self.assertEqual(response.context['employees'].count(), 5)

    def test_private_hr_pages_reject_employees_and_managers(self):
        for username in ('victor.lungu', 'augustine.nsofwa'):
            with self.subTest(username=username):
                self.client.force_login(self.demo_user(username))
                response = self.client.get(reverse('recruitment:applicants'))
                self.assertRedirects(
                    response,
                    reverse('accounts:dashboard'),
                    fetch_redirect_response=False,
                )
                response = self.client.get(reverse('employees:departments'))
                self.assertRedirects(
                    response,
                    reverse('accounts:dashboard'),
                    fetch_redirect_response=False,
                )

    def test_payroll_and_attendance_views_only_show_authorised_records(self):
        self.client.force_login(self.demo_user('victor.lungu'))
        response = self.client.get(reverse('payroll:payslips'))
        self.assertEqual(
            set(response.context['payslips'].values_list('employee__user__username', flat=True)),
            {'victor.lungu'},
        )
        response = self.client.get(reverse('attendance:list'))
        self.assertEqual(
            set(response.context['records'].values_list('employee__user__username', flat=True)),
            {'victor.lungu'},
        )

        self.client.force_login(self.demo_user('augustine.nsofwa'))
        response = self.client.get(reverse('payroll:payslips'))
        self.assertEqual(
            set(response.context['payslips'].values_list('employee__user__username', flat=True)),
            {'augustine.nsofwa'},
        )
        response = self.client.get(reverse('attendance:list'))
        self.assertEqual(
            set(response.context['records'].values_list('employee__user__username', flat=True)),
            {'augustine.nsofwa', 'victor.lungu'},
        )

    def test_manager_performance_and_training_data_is_team_scoped(self):
        manager = self.demo_user('augustine.nsofwa')
        self.client.force_login(manager)
        response = self.client.get(reverse('performance:reviews'))
        self.assertEqual(
            set(response.context['reviews'].values_list('employee__user__username', flat=True)),
            {'victor.lungu'},
        )
        response = self.client.get(reverse('performance:review_create'))
        self.assertEqual(
            set(
                response.context['form'].fields['employee'].queryset.values_list(
                    'user__username', flat=True,
                )
            ),
            {'victor.lungu'},
        )
        response = self.client.get(reverse('training:enrollments'))
        self.assertEqual(
            set(
                response.context['enrollments'].values_list(
                    'employee__user__username', flat=True,
                )
            ),
            {'victor.lungu'},
        )

        self.client.force_login(self.demo_user('mwamba.mwila'))
        response = self.client.get(reverse('performance:reviews'))
        self.assertEqual(response.context['reviews'].count(), 1)
        response = self.client.get(reverse('training:enrollments'))
        self.assertEqual(response.context['enrollments'].count(), 2)

    def test_employee_registration_and_department_management(self):
        hr = self.demo_user('mwamba.mwila')
        new_user = get_user_model().objects.create_user(
            username='new-employee', password='Valid-Demo-Password-1',
        )
        department = Department.objects.get(name='Operations')
        self.client.force_login(hr)
        response = self.client.post(
            reverse('employees:create'),
            {
                'user': new_user.pk,
                'employee_id': 'EMP005',
                'department': department.pk,
                'job_title': 'Project Assistant',
                'hire_date': timezone.localdate().isoformat(),
                'date_of_birth': '',
                'phone': '+260 97 000 0020',
                'address': 'Ndola, Zambia',
                'emergency_contact': '',
                'base_salary': '12500.00',
                'status': Employee.Status.ACTIVE,
                'manager': '',
                'notes': '',
            },
        )
        self.assertRedirects(
            response,
            reverse('employees:list'),
            fetch_redirect_response=False,
        )
        self.assertTrue(Employee.objects.filter(employee_id='EMP005').exists())
        employee = Employee.objects.get(employee_id='EMP005')
        self.assertEqual(employee.user.profile.role, UserProfile.Role.EMPLOYEE)

        response = self.client.post(
            reverse('employees:departments'),
            {'name': 'Student Services', 'description': 'Campus people support.'},
        )
        self.assertRedirects(
            response,
            reverse('employees:departments'),
            fetch_redirect_response=False,
        )
        self.assertTrue(Department.objects.filter(name='Student Services').exists())
        self.assertTrue(
            self.client.login(username='new-employee', password='Valid-Demo-Password-1')
        )
        self.assertEqual(self.client.get(reverse('self_service:home')).status_code, 200)

    def test_employee_form_validation_prevents_incomplete_registration(self):
        self.client.force_login(self.demo_user('mwamba.mwila'))
        response = self.client.post(
            reverse('employees:create'),
            {'employee_id': '', 'job_title': '', 'hire_date': ''},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].errors)
        self.assertFalse(Employee.objects.filter(employee_id='').exists())

    def test_manager_can_decide_direct_report_leave_only(self):
        manager = self.demo_user('augustine.nsofwa')
        victor = self.demo_user('victor.lungu').employee
        annual = LeaveType.objects.get(name='Annual Leave')
        leave = LeaveRequest.objects.create(
            employee=victor,
            leave_type=annual,
            start_date=timezone.localdate() + timedelta(days=30),
            end_date=timezone.localdate() + timedelta(days=32),
            reason='Demonstration leave request',
        )
        self.client.force_login(manager)
        response = self.client.post(
            reverse('leave:decide', args=[leave.pk]),
            {'status': LeaveRequest.Status.APPROVED, 'decision_notes': 'Approved.'},
        )
        self.assertRedirects(
            response,
            reverse('leave:list'),
            fetch_redirect_response=False,
        )
        leave.refresh_from_db()
        self.assertEqual(leave.status, LeaveRequest.Status.APPROVED)
        self.assertEqual(leave.approved_by, manager)

        unrelated_leave = LeaveRequest.objects.get(
            employee=self.demo_user('morgan.syankombwe').employee,
        )
        response = self.client.post(
            reverse('leave:decide', args=[unrelated_leave.pk]),
            {'status': LeaveRequest.Status.REJECTED, 'decision_notes': 'Not in my team.'},
        )
        self.assertRedirects(
            response,
            reverse('leave:list'),
            fetch_redirect_response=False,
        )
        unrelated_leave.refresh_from_db()
        self.assertNotEqual(unrelated_leave.status, LeaveRequest.Status.REJECTED)

    def test_module_urls_render_for_the_administrator_and_zambian_timezone_is_set(self):
        self.client.force_login(self.demo_user('comfort.kakumbi'))
        for route_name in (
            'employees:list',
            'employees:departments',
            'attendance:list',
            'leave:list',
            'payroll:payslips',
            'payroll:periods',
            'performance:cycles',
            'performance:reviews',
            'performance:review_create',
            'recruitment:jobs',
            'recruitment:applicants',
            'recruitment:interviews',
            'training:courses',
            'training:enrollments',
            'self_service:home',
            'leave:types',
            'attendance:create',
        ):
            with self.subTest(route=route_name):
                self.assertEqual(self.client.get(reverse(route_name)).status_code, 200)
        self.assertEqual(settings.TIME_ZONE, 'Africa/Lusaka')
