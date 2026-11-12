from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


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
