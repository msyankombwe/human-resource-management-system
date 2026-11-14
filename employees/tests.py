from datetime import date

from django.contrib.admin.models import ADDITION, CHANGE, LogEntry
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django.urls import reverse

from accounts.models import UserProfile

from .models import Department, Employee


class EmployeeOnboardingTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.department = Department.objects.create(name='Operations')

        cls.admin = User.objects.create_user(
            username='onboarding-admin',
            password='Admin-Test-Password-1!',
            is_staff=True,
            is_superuser=True,
        )
        UserProfile.objects.create(user=cls.admin, role=UserProfile.Role.ADMIN)

        cls.hr = User.objects.create_user(
            username='onboarding-hr',
            password='HR-Test-Password-1!',
        )
        UserProfile.objects.create(user=cls.hr, role=UserProfile.Role.HR)

        cls.manager = User.objects.create_user(
            username='onboarding-manager',
            password='Manager-Test-Password-1!',
        )
        UserProfile.objects.create(user=cls.manager, role=UserProfile.Role.MANAGER)
        cls.manager_employee = cls.create_employee(
            cls.manager,
            'EMP-MANAGER',
            cls.department,
        )

        cls.report = User.objects.create_user(
            username='onboarding-report',
            password='Report-Test-Password-1!',
        )
        UserProfile.objects.create(user=cls.report, role=UserProfile.Role.EMPLOYEE)
        cls.report_employee = cls.create_employee(
            cls.report,
            'EMP-REPORT',
            cls.department,
            manager=cls.manager_employee,
        )

        cls.employee = User.objects.create_user(
            username='onboarding-employee',
            password='Employee-Test-Password-1!',
        )
        UserProfile.objects.create(user=cls.employee, role=UserProfile.Role.EMPLOYEE)
        cls.employee_record = cls.create_employee(
            cls.employee,
            'EMP-SELF',
            cls.department,
        )

    @staticmethod
    def create_employee(user, employee_id, department, manager=None):
        return Employee.objects.create(
            user=user,
            employee_id=employee_id,
            department=department,
            job_title='Operations Officer',
            hire_date=date(2024, 1, 15),
            manager=manager,
        )

    def new_employee_data(self, username='new-onboarded-user', employee_id='EMP-NEW'):
        password = 'Cedar!Orbit-83-Quartz'
        return {
            'account_mode': 'new',
            'username': username,
            'first_name': 'Taylor',
            'last_name': 'Onboarded',
            'email': f'{username}@example.test',
            'password1': password,
            'password2': password,
            'employee_id': employee_id,
            'department': self.department.pk,
            'job_title': 'Project Coordinator',
            'hire_date': '2025-03-10',
            'date_of_birth': '',
            'phone': '+260 97 111 2233',
            'address': 'Lusaka, Zambia',
            'emergency_contact': '',
            'base_salary': '18000.00',
            'status': Employee.Status.ACTIVE,
            'manager': self.manager_employee.pk,
            'notes': '',
        }

    def employee_log(self, employee, action_flag):
        return LogEntry.objects.get(
            content_type=ContentType.objects.get_for_model(employee),
            object_id=str(employee.pk),
            action_flag=action_flag,
        )

    def assert_new_employee_audit(self, employee, actor):
        entry = self.employee_log(employee, ADDITION)
        self.assertEqual(entry.user, actor)
        self.assertEqual(entry.object_repr, str(employee))
        self.assertIsNotNone(entry.action_time)
        self.assertIn('Created through HRMS onboarding', entry.get_change_message())

    def test_onboarding_form_has_account_and_employment_sections_without_role_selector(self):
        self.client.force_login(self.admin)

        response = self.client.get(reverse('employees:create'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'System account')
        self.assertContains(response, 'Employment information')
        self.assertContains(response, 'Personal and contact information')
        self.assertContains(response, 'Create a new account')
        self.assertContains(response, 'Link an existing account')
        self.assertNotContains(response, 'name="role"')

    def test_administrator_can_register_new_employee_account(self):
        data = self.new_employee_data()
        self.client.force_login(self.admin)

        response = self.client.post(reverse('employees:create'), data)

        employee = Employee.objects.get(employee_id=data['employee_id'])
        self.assertRedirects(
            response,
            reverse('employees:list'),
            fetch_redirect_response=False,
        )
        self.assertContains(
            self.client.get(response.url),
            f'Employee {employee.employee_id} — {employee.full_name} onboarded successfully.',
        )
        user = employee.user
        self.assertEqual(user.profile.role, UserProfile.Role.EMPLOYEE)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertTrue(user.check_password(data['password1']))
        self.assertNotEqual(user.password, data['password1'])
        self.assert_new_employee_audit(employee, self.admin)

    def test_hr_officer_can_register_new_employee_account(self):
        data = self.new_employee_data('hr-onboarded-user', 'EMP-HR-NEW')
        self.client.force_login(self.hr)

        response = self.client.post(reverse('employees:create'), data)

        employee = Employee.objects.get(employee_id=data['employee_id'])
        self.assertRedirects(
            response,
            reverse('employees:list'),
            fetch_redirect_response=False,
        )
        self.assertEqual(employee.user.profile.role, UserProfile.Role.EMPLOYEE)
        self.assert_new_employee_audit(employee, self.hr)

    def test_existing_unlinked_account_is_reused_and_profile_is_assigned_employee_role(self):
        User = get_user_model()
        existing_user = User.objects.create_user(
            username='existing-unlinked-user',
            password='Existing-Test-Password-1!',
        )
        original_password = existing_user.password
        data = self.new_employee_data('unused-new-user', 'EMP-EXISTING')
        data.update(account_mode='existing', user=existing_user.pk)
        for field in ('username', 'first_name', 'last_name', 'email', 'password1', 'password2'):
            data.pop(field)
        user_count = User.objects.count()

        self.client.force_login(self.hr)
        response = self.client.post(reverse('employees:create'), data)

        employee = Employee.objects.get(employee_id='EMP-EXISTING')
        existing_user.refresh_from_db()
        self.assertRedirects(
            response,
            reverse('employees:list'),
            fetch_redirect_response=False,
        )
        self.assertEqual(employee.user_id, existing_user.pk)
        self.assertEqual(User.objects.count(), user_count)
        self.assertEqual(existing_user.password, original_password)
        self.assertEqual(existing_user.profile.role, UserProfile.Role.EMPLOYEE)
        self.assert_new_employee_audit(employee, self.hr)

    def test_existing_administrator_account_cannot_be_linked_as_an_employee(self):
        data = self.new_employee_data('unused-admin-link', 'EMP-ADMIN-LINK')
        data.update(account_mode='existing', user=self.admin.pk)
        for field in ('username', 'first_name', 'last_name', 'email', 'password1', 'password2'):
            data.pop(field)
        employee_count = Employee.objects.count()

        self.client.force_login(self.hr)
        response = self.client.post(reverse('employees:create'), data)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].has_error('user'))
        self.assertEqual(Employee.objects.count(), employee_count)
        self.assertFalse(Employee.objects.filter(employee_id='EMP-ADMIN-LINK').exists())

    def test_linking_already_associated_account_is_rejected(self):
        data = self.new_employee_data('unused-linked-user', 'EMP-DUPLICATE-LINK')
        data.update(account_mode='existing', user=self.report.pk)
        for field in ('username', 'first_name', 'last_name', 'email', 'password1', 'password2'):
            data.pop(field)
        user_count = get_user_model().objects.count()
        employee_count = Employee.objects.count()

        self.client.force_login(self.hr)
        response = self.client.post(reverse('employees:create'), data)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].errors)
        self.assertEqual(get_user_model().objects.count(), user_count)
        self.assertEqual(Employee.objects.count(), employee_count)

    def test_duplicate_username_and_employee_id_do_not_create_partial_accounts(self):
        User = get_user_model()
        user_count = User.objects.count()
        employee_count = Employee.objects.count()
        self.client.force_login(self.hr)

        duplicate_username = self.new_employee_data(
            self.report.username.upper(),
            'EMP-DUPLICATE-USERNAME',
        )
        response = self.client.post(reverse('employees:create'), duplicate_username)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].has_error('username'))

        duplicate_employee_id = self.new_employee_data(
            'unique-onboarding-username',
            self.report_employee.employee_id,
        )
        response = self.client.post(reverse('employees:create'), duplicate_employee_id)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].has_error('employee_id'))

        self.assertEqual(User.objects.count(), user_count)
        self.assertEqual(Employee.objects.count(), employee_count)
        self.assertFalse(User.objects.filter(username='unique-onboarding-username').exists())

    def test_invalid_password_or_employee_data_creates_no_partial_records(self):
        User = get_user_model()
        user_count = User.objects.count()
        employee_count = Employee.objects.count()
        self.client.force_login(self.hr)

        weak_password = self.new_employee_data('weak-password-user', 'EMP-WEAK-PASSWORD')
        weak_password.update(password1='password', password2='password')
        response = self.client.post(reverse('employees:create'), weak_password)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].has_error('password1'))

        invalid_employee = self.new_employee_data(
            'incomplete-employee-user',
            'EMP-INCOMPLETE',
        )
        invalid_employee.update(job_title='', hire_date='')
        response = self.client.post(reverse('employees:create'), invalid_employee)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].errors)
        self.assertContains(
            response,
            'Please correct the highlighted fields before saving.',
        )

        self.assertEqual(User.objects.count(), user_count)
        self.assertEqual(Employee.objects.count(), employee_count)
        self.assertFalse(User.objects.filter(username='weak-password-user').exists())
        self.assertFalse(User.objects.filter(username='incomplete-employee-user').exists())

    def test_manager_and_employee_cannot_create_by_direct_get_or_post(self):
        User = get_user_model()
        user_count = User.objects.count()
        employee_count = Employee.objects.count()

        for actor, username, employee_id in (
            (self.manager, 'manager-forbidden-user', 'EMP-MANAGER-DENIED'),
            (self.employee, 'employee-forbidden-user', 'EMP-EMPLOYEE-DENIED'),
        ):
            with self.subTest(role=actor.profile.role):
                self.client.force_login(actor)
                get_response = self.client.get(reverse('employees:create'))
                post_response = self.client.post(
                    reverse('employees:create'),
                    self.new_employee_data(username, employee_id),
                )
                self.assertRedirects(
                    get_response,
                    reverse('accounts:dashboard'),
                    fetch_redirect_response=False,
                )
                self.assertRedirects(
                    post_response,
                    reverse('accounts:dashboard'),
                    fetch_redirect_response=False,
                )

        self.assertEqual(User.objects.count(), user_count)
        self.assertEqual(Employee.objects.count(), employee_count)
        self.assertFalse(User.objects.filter(username__endswith='-forbidden-user').exists())

    def test_employee_modification_is_audited_with_actor_and_changed_fields(self):
        employee = self.report_employee
        self.client.force_login(self.hr)
        response = self.client.post(
            reverse('employees:edit', args=[employee.pk]),
            {
                'user': employee.user_id,
                'employee_id': employee.employee_id,
                'department': employee.department_id,
                'job_title': 'Senior Operations Officer',
                'hire_date': employee.hire_date.isoformat(),
                'date_of_birth': '',
                'phone': employee.phone,
                'address': employee.address,
                'emergency_contact': employee.emergency_contact,
                'base_salary': employee.base_salary,
                'status': employee.status,
                'manager': employee.manager_id,
                'notes': employee.notes,
            },
        )

        self.assertRedirects(
            response,
            reverse('employees:detail', args=[employee.pk]),
            fetch_redirect_response=False,
        )
        entry = self.employee_log(employee, CHANGE)
        self.assertEqual(entry.user, self.hr)
        self.assertIsNotNone(entry.action_time)
        self.assertIn('Job title', entry.get_change_message())

    def test_employee_visibility_remains_role_scoped(self):
        self.client.force_login(self.manager)
        manager_response = self.client.get(reverse('employees:list'))
        self.assertEqual(
            set(manager_response.context['employees'].values_list('pk', flat=True)),
            {self.manager_employee.pk, self.report_employee.pk},
        )
        self.assertEqual(
            self.client.get(
                reverse('employees:detail', args=[self.employee_record.pk]),
            ).status_code,
            404,
        )

        self.client.force_login(self.employee)
        employee_response = self.client.get(reverse('employees:list'))
        self.assertEqual(
            set(employee_response.context['employees'].values_list('pk', flat=True)),
            {self.employee_record.pk},
        )
        self.assertEqual(
            self.client.get(
                reverse('employees:detail', args=[self.report_employee.pk]),
            ).status_code,
            404,
        )
