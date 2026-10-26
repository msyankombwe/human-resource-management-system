from datetime import date
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import BuyerOffer, Listing, MarketPrice, MarketplaceProfile, Order

User = get_user_model()


class MarketplaceWorkflowTests(TestCase):
    def setUp(self):
        self.farmer = User.objects.create_user(
            username='farmer',
            password='FarmDemo123!',
            first_name='Farmer',
            last_name='Demo',
        )
        self.farmer_profile = MarketplaceProfile.objects.create(
            user=self.farmer,
            role=MarketplaceProfile.Role.FARMER,
            location='Mkushi',
        )
        self.buyer = User.objects.create_user(
            username='buyer',
            password='BuyerDemo123!',
            first_name='Buyer',
            last_name='Demo',
        )
        self.buyer_profile = MarketplaceProfile.objects.create(
            user=self.buyer,
            role=MarketplaceProfile.Role.BUYER,
        )

    def test_homepage_shows_marketplace_and_indicative_prices(self):
        MarketPrice.objects.create(
            crop='Maize',
            market='Lusaka',
            price_per_tonne=Decimal('5200'),
            observed_on=date(2026, 10, 25),
            source='Demo market update',
        )
        response = self.client.get(reverse('marketplace:home'))
        self.assertContains(response, 'Zambia grows it.')
        self.assertContains(response, 'Indicative market prices')
        self.assertContains(response, 'Lusaka')
        self.assertContains(response, '5200.00')

    def test_farmer_lists_and_buyer_searches_produce(self):
        self.client.force_login(self.farmer)
        response = self.client.post(
            reverse('marketplace:listing_create'),
            {
                'crop': 'Maize',
                'description': 'Dry white maize',
                'quantity_tonnes': '100',
                'price_per_tonne': '',
                'location': 'Mkushi',
                'quality': 'Grade A',
            },
        )
        self.assertEqual(response.status_code, 302)
        listing = Listing.objects.get(crop='Maize', location='Mkushi')
        self.client.logout()
        response = self.client.get(reverse('marketplace:listing_list'), {'q': 'maize', 'location': 'mkushi'})
        self.assertContains(response, '100.00 tonnes')
        self.assertContains(response, f'href="{reverse("marketplace:listing_detail", args=[listing.pk])}"')
        self.client.force_login(self.buyer)
        self.client.post(
            reverse('marketplace:offer_create', args=[listing.pk]),
            {'quantity_tonnes': '100', 'price_per_tonne': '5000', 'message': 'Ready for collection.'},
        )
        offer = BuyerOffer.objects.get(listing=listing, buyer=self.buyer_profile)
        self.client.force_login(self.farmer)
        self.client.post(reverse('marketplace:offer_decide', args=[offer.pk, 'accept']))
        self.assertTrue(Order.objects.filter(offer=offer, status=Order.Status.CONFIRMED).exists())
        listing.refresh_from_db()
        self.assertEqual(listing.status, Listing.Status.SOLD)
        self.client.force_login(self.buyer)
        self.assertContains(self.client.get(reverse('marketplace:dashboard')), 'Confirmed')

    def test_accepting_offer_creates_order_and_reserves_listing_quantity(self):
        listing = Listing.objects.create(
            seller=self.farmer_profile,
            crop='Maize',
            quantity_tonnes=Decimal('100'),
            location='Mkushi',
        )
        offer = BuyerOffer.objects.create(
            listing=listing,
            buyer=self.buyer_profile,
            quantity_tonnes=Decimal('40'),
            price_per_tonne=Decimal('5200'),
        )

        self.client.force_login(self.farmer)
        response = self.client.post(
            reverse('marketplace:offer_decide', args=[offer.pk, 'accept'])
        )

        self.assertRedirects(response, reverse('marketplace:dashboard'))
        offer.refresh_from_db()
        listing.refresh_from_db()
        self.assertEqual(offer.status, BuyerOffer.Status.ACCEPTED)
        self.assertEqual(listing.quantity_tonnes, Decimal('60'))
        self.assertEqual(Order.objects.get(offer=offer).status, Order.Status.CONFIRMED)

        self.client.force_login(self.buyer)
        buyer_dashboard = self.client.get(reverse('marketplace:dashboard'))
        self.assertContains(buyer_dashboard, 'Confirmed')
        self.assertContains(buyer_dashboard, 'Mkushi')

    def test_offer_larger_than_available_is_not_created(self):
        listing = Listing.objects.create(
            seller=self.farmer_profile,
            crop='Maize',
            quantity_tonnes=Decimal('10'),
            location='Mkushi',
        )
        self.client.force_login(self.buyer)
        response = self.client.post(
            reverse('marketplace:offer_create', args=[listing.pk]),
            {'quantity_tonnes': '11', 'price_per_tonne': '5000', 'message': ''},
        )
        self.assertRedirects(response, reverse('marketplace:listing_detail', args=[listing.pk]))
        self.assertEqual(BuyerOffer.objects.count(), 0)

    def test_acceptance_cannot_overcommit_remaining_listing(self):
        listing = Listing.objects.create(
            seller=self.farmer_profile,
            crop='Maize',
            quantity_tonnes=Decimal('25'),
            location='Mkushi',
        )
        offer = BuyerOffer.objects.create(
            listing=listing,
            buyer=self.buyer_profile,
            quantity_tonnes=Decimal('30'),
            price_per_tonne=Decimal('5000'),
        )
        self.client.force_login(self.farmer)
        self.client.post(reverse('marketplace:offer_decide', args=[offer.pk, 'accept']))
        listing.refresh_from_db()
        offer.refresh_from_db()
        self.assertEqual(listing.quantity_tonnes, Decimal('25'))
        self.assertEqual(offer.status, BuyerOffer.Status.PENDING)
        self.assertFalse(Order.objects.filter(offer=offer).exists())

    def test_seller_can_advance_order_status(self):
        listing = Listing.objects.create(
            seller=self.farmer_profile,
            crop='Maize',
            quantity_tonnes=Decimal('10'),
            location='Mkushi',
        )
        offer = BuyerOffer.objects.create(
            listing=listing,
            buyer=self.buyer_profile,
            quantity_tonnes=Decimal('5'),
            price_per_tonne=Decimal('5000'),
            status=BuyerOffer.Status.ACCEPTED,
        )
        order = Order.objects.create(offer=offer)
        self.client.force_login(self.farmer)
        response = self.client.post(
            reverse('marketplace:order_update', args=[order.pk]),
            {'status': Order.Status.PREPARING},
        )
        self.assertRedirects(response, reverse('marketplace:dashboard'))
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.PREPARING)

    def test_local_registration_creates_profile_and_signs_in(self):
        response = self.client.post(
            reverse('marketplace:register'),
            {
                'username': 'newfarmer',
                'first_name': 'New',
                'last_name': 'Farmer',
                'email': 'newfarmer@example.com',
                'password1': 'SecureDemoPass123!',
                'password2': 'SecureDemoPass123!',
                'role': MarketplaceProfile.Role.FARMER,
                'phone': '',
                'organization': '',
                'location': 'Mkushi',
            },
        )
        self.assertRedirects(response, reverse('marketplace:dashboard'))
        profile = MarketplaceProfile.objects.get(user__username='newfarmer')
        self.assertEqual(profile.location, 'Mkushi')
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    @override_settings(SUPABASE_URL='https://example.supabase.co', SUPABASE_ANON_KEY='test-anon-key')
    @patch('marketplace.views.supabase_auth_request')
    def test_supabase_registration_does_not_store_password_in_django(self, auth_request):
        auth_request.return_value = {
            'user': {'id': 'supabase-farmer-id'},
            'access_token': 'test-access-token',
        }
        response = self.client.post(
            reverse('marketplace:register'),
            {
                'username': 'remote-farmer',
                'first_name': 'Remote',
                'last_name': 'Farmer',
                'email': 'remote@example.com',
                'password1': 'SecureRemotePass123!',
                'password2': 'SecureRemotePass123!',
                'role': MarketplaceProfile.Role.FARMER,
                'phone': '',
                'organization': '',
                'location': 'Mkushi',
            },
        )
        self.assertRedirects(response, reverse('marketplace:dashboard'))
        user = User.objects.get(username='remote-farmer')
        self.assertFalse(user.has_usable_password())
        self.assertEqual(user.marketplace_profile.supabase_uid, 'supabase-farmer-id')
        auth_request.assert_called_once()

    @override_settings(SUPABASE_URL='https://example.supabase.co', SUPABASE_ANON_KEY='test-anon-key')
    @patch('marketplace.views.supabase_auth_request')
    def test_supabase_sign_in_creates_local_session_mirror(self, auth_request):
        auth_request.return_value = {
            'user': {
                'id': 'supabase-buyer-id',
                'email': 'remote-buyer@example.com',
                'user_metadata': {
                    'username': 'remote-buyer',
                    'role': MarketplaceProfile.Role.BUYER,
                    'location': 'Lusaka',
                },
            },
            'access_token': 'test-access-token',
        }
        response = self.client.post(
            reverse('marketplace:login'),
            {'username': 'remote-buyer@example.com', 'password': 'RemotePass123!'},
        )
        self.assertRedirects(response, reverse('marketplace:dashboard'))
        user = User.objects.get(username='remote-buyer')
        self.assertFalse(user.has_usable_password())
        self.assertEqual(user.marketplace_profile.supabase_uid, 'supabase-buyer-id')
        self.assertEqual(user.marketplace_profile.role, MarketplaceProfile.Role.BUYER)
        self.assertTrue(response.wsgi_request.user.is_authenticated)
        auth_request.assert_called_once()
