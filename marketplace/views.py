from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .auth import SupabaseAuthError, is_supabase_auth_configured, supabase_auth_request
from accounts.forms import LoginForm

from .forms import BuyerOfferForm, ListingForm, MarketplaceLoginForm, MarketplaceSignupForm
from .models import BuyerOffer, Listing, MarketPrice, MarketplaceProfile, Order

User = get_user_model()


def home(request):
    listings = Listing.objects.filter(status=Listing.Status.ACTIVE, quantity_tonnes__gt=0)[:6]
    prices = MarketPrice.objects.all()[:4]
    return render(request, 'marketplace/home.html', {'listings': listings, 'prices': prices})


def listing_list(request):
    listings = Listing.objects.filter(status=Listing.Status.ACTIVE, quantity_tonnes__gt=0)
    query = request.GET.get('q', '').strip()
    location = request.GET.get('location', '').strip()
    if query:
        listings = listings.filter(
            Q(crop__icontains=query) | Q(description__icontains=query) | Q(quality__icontains=query)
        )
    if location:
        listings = listings.filter(location__icontains=location)
    return render(
        request,
        'marketplace/listing_list.html',
        {'listings': listings, 'query': query, 'location': location},
    )


def listing_detail(request, pk):
    listing = get_object_or_404(Listing.objects.select_related('seller__user'), pk=pk)
    form = None
    if request.user.is_authenticated and listing.is_available:
        profile = getattr(request.user, 'marketplace_profile', None)
        if profile and profile.can_buy and profile.pk != listing.seller_id:
            form = BuyerOfferForm(listing=listing, buyer=profile)
    return render(request, 'marketplace/listing_detail.html', {'listing': listing, 'offer_form': form})


def register(request):
    if request.user.is_authenticated:
        return redirect('marketplace:dashboard')
    form = MarketplaceSignupForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        if is_supabase_auth_configured():
            try:
                result = supabase_auth_request(
                    'signup',
                    {
                        'email': form.cleaned_data['email'],
                        'password': form.cleaned_data['password1'],
                        'data': {
                            'username': form.cleaned_data['username'],
                            'first_name': form.cleaned_data['first_name'],
                            'last_name': form.cleaned_data['last_name'],
                            'role': form.cleaned_data['role'],
                            'phone': form.cleaned_data['phone'],
                            'organization': form.cleaned_data['organization'],
                            'location': form.cleaned_data['location'],
                        },
                    },
                )
            except SupabaseAuthError as exc:
                form.add_error(None, str(exc))
            else:
                remote_user = result.get('user') or {}
                if not isinstance(remote_user.get('id'), str) or not remote_user['id']:
                    form.add_error(None, 'Supabase did not return a user profile. Please try again.')
                else:
                    with transaction.atomic():
                        user = form.save(commit=False)
                        user.set_unusable_password()
                        user.save()
                        MarketplaceProfile.objects.create(
                            user=user,
                            supabase_uid=remote_user['id'],
                            role=form.cleaned_data['role'],
                            phone=form.cleaned_data['phone'],
                            organization=form.cleaned_data['organization'],
                            location=form.cleaned_data['location'],
                        )
                    if result.get('access_token'):
                        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                        messages.success(request, 'Your DAMELS account is ready. Welcome!')
                        return redirect('marketplace:dashboard')
                    messages.info(
                        request,
                        'Account created. Confirm your email using the Supabase verification link, then sign in.',
                    )
                    return redirect('marketplace:login')
        else:
            user = form.save()
            login(request, user)
            messages.success(request, 'Your DAMELS account is ready. Welcome!')
            return redirect('marketplace:dashboard')
    return render(request, 'marketplace/register.html', {'form': form})


def marketplace_login(request):
    if request.user.is_authenticated:
        return redirect('marketplace:dashboard')
    if not is_supabase_auth_configured():
        form = LoginForm(request, data=request.POST or None)
        if request.method == 'POST' and form.is_valid():
            login(request, form.get_user())
            destination = request.POST.get('next') or request.GET.get('next')
            if destination and url_has_allowed_host_and_scheme(
                destination,
                allowed_hosts={request.get_host()},
                require_https=request.is_secure(),
            ):
                return redirect(destination)
            return redirect('marketplace:dashboard')
        return render(request, 'marketplace/login.html', {'form': form})
    form = MarketplaceLoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        identity = form.cleaned_data['username'].strip()
        if '@' not in identity:
            local_user = User.objects.filter(username=identity).first()
            identity = local_user.email if local_user else identity
        try:
            result = supabase_auth_request(
                'token?grant_type=password',
                {'email': identity, 'password': form.cleaned_data['password']},
            )
        except SupabaseAuthError as exc:
            form.add_error(None, str(exc))
        else:
            remote_user = result.get('user') or {}
            remote_id = remote_user.get('id')
            if not isinstance(remote_id, str) or not remote_id or not result.get('access_token'):
                form.add_error(None, 'Sign-in is incomplete. Confirm your email, then try again.')
            else:
                profile = MarketplaceProfile.objects.filter(supabase_uid=remote_id).select_related('user').first()
                if profile:
                    user = profile.user
                else:
                    metadata = remote_user.get('user_metadata') or {}
                    if not isinstance(metadata, dict):
                        metadata = {}
                    username = metadata.get('username')
                    if not isinstance(username, str) or not username.strip():
                        username = identity.split('@', 1)[0]
                    username = username[:150]
                    if User.objects.filter(username=username).exists():
                        username = f'{username[:140]}-{remote_id[:8]}'
                    first_name = metadata.get('first_name', '')
                    last_name = metadata.get('last_name', '')
                    if not isinstance(first_name, str):
                        first_name = ''
                    if not isinstance(last_name, str):
                        last_name = ''
                    email = remote_user.get('email') or identity
                    if not isinstance(email, str):
                        email = identity
                    with transaction.atomic():
                        user = User.objects.create(
                            username=username,
                            email=email[:254],
                            first_name=first_name[:150],
                            last_name=last_name[:150],
                        )
                        user.set_unusable_password()
                        user.save(update_fields=['password'])
                        role = metadata.get('role', MarketplaceProfile.Role.BOTH)
                        if not isinstance(role, str):
                            role = MarketplaceProfile.Role.BOTH
                        valid_roles = {choice for choice, _label in MarketplaceProfile.Role.choices}
                        if role not in valid_roles:
                            role = MarketplaceProfile.Role.BOTH
                        phone = metadata.get('phone', '')
                        organization = metadata.get('organization', '')
                        location = metadata.get('location', '')
                        MarketplaceProfile.objects.create(
                            user=user,
                            supabase_uid=remote_id,
                            role=role,
                            phone=phone[:30] if isinstance(phone, str) else '',
                            organization=organization[:120] if isinstance(organization, str) else '',
                            location=location[:100] if isinstance(location, str) else '',
                        )
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                destination = request.POST.get('next') or request.GET.get('next')
                if destination and url_has_allowed_host_and_scheme(
                    destination,
                    allowed_hosts={request.get_host()},
                    require_https=request.is_secure(),
                ):
                    return redirect(destination)
                messages.success(request, f'Welcome back, {user.get_full_name() or user.username}.')
                return redirect('marketplace:dashboard')
    return render(request, 'marketplace/login.html', {'form': form})


@login_required(login_url='marketplace:login')
def dashboard(request):
    profile, _ = MarketplaceProfile.objects.get_or_create(
        user=request.user,
        defaults={'role': MarketplaceProfile.Role.BOTH},
    )
    listings = Listing.objects.filter(seller=profile).order_by('-created_at')
    offers_received = BuyerOffer.objects.filter(listing__seller=profile).select_related(
        'listing', 'buyer__user'
    )
    offers_sent = BuyerOffer.objects.filter(buyer=profile).select_related('listing', 'listing__seller__user')
    orders = Order.objects.filter(
        Q(offer__listing__seller=profile) | Q(offer__buyer=profile)
    ).select_related('offer__listing', 'offer__listing__seller__user', 'offer__buyer__user')
    return render(
        request,
        'marketplace/dashboard.html',
        {
            'profile': profile,
            'listings': listings,
            'offers_received': offers_received,
            'offers_sent': offers_sent,
            'orders': orders,
        },
    )


@login_required(login_url='marketplace:login')
def listing_create(request):
    profile = getattr(request.user, 'marketplace_profile', None)
    if profile is None:
        profile = MarketplaceProfile.objects.create(user=request.user, role=MarketplaceProfile.Role.BOTH)
    if not profile.can_sell:
        return HttpResponseForbidden('Your marketplace profile is registered as a buyer only.')
    form = ListingForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        listing = form.save(commit=False)
        listing.seller = profile
        listing.save()
        messages.success(request, 'Your product is now listed in the marketplace.')
        return redirect('marketplace:listing_detail', pk=listing.pk)
    return render(request, 'marketplace/listing_form.html', {'form': form})


@login_required(login_url='marketplace:login')
@require_POST
def offer_create(request, pk):
    listing = get_object_or_404(Listing, pk=pk)
    profile = getattr(request.user, 'marketplace_profile', None)
    if profile is None or not profile.can_buy:
        return HttpResponseForbidden('A buyer marketplace profile is required to make an offer.')
    form = BuyerOfferForm(request.POST, listing=listing, buyer=profile)
    if form.is_valid():
        offer = form.save(commit=False)
        offer.listing = listing
        offer.buyer = profile
        offer.save()
        messages.success(request, 'Your purchase offer has been sent to the farmer.')
        return redirect('marketplace:dashboard')
    messages.error(request, 'Please correct the offer details and try again.')
    for error in form.non_field_errors():
        messages.error(request, error)
    for field in form:
        for error in field.errors:
            messages.error(request, f'{field.label}: {error}')
    return redirect('marketplace:listing_detail', pk=pk)


@login_required(login_url='marketplace:login')
@require_POST
def offer_decide(request, pk, decision):
    profile = getattr(request.user, 'marketplace_profile', None)
    offer = get_object_or_404(
        BuyerOffer.objects.select_related('listing'),
        pk=pk,
        listing__seller__user=request.user,
    )
    if profile is None or offer.listing.seller_id != profile.pk:
        return HttpResponseForbidden('Only the farmer who listed this produce can respond.')
    if offer.status != BuyerOffer.Status.PENDING:
        messages.error(request, 'This offer has already been resolved.')
        return redirect('marketplace:dashboard')
    if decision == 'accept':
        with transaction.atomic():
            listing = Listing.objects.select_for_update().get(pk=offer.listing_id)
            locked_offer = BuyerOffer.objects.select_for_update().get(pk=offer.pk)
            if locked_offer.status != BuyerOffer.Status.PENDING:
                messages.error(request, 'This offer has already been resolved.')
                return redirect('marketplace:dashboard')
            if not listing.is_available or locked_offer.quantity_tonnes > listing.quantity_tonnes:
                messages.error(request, 'There is not enough produce remaining to accept this offer.')
                return redirect('marketplace:dashboard')
            locked_offer.status = BuyerOffer.Status.ACCEPTED
            locked_offer.save(update_fields=['status'])
            listing.quantity_tonnes -= locked_offer.quantity_tonnes
            if listing.quantity_tonnes == Decimal('0'):
                listing.status = Listing.Status.SOLD
            listing.save(update_fields=['quantity_tonnes', 'status'])
            Order.objects.create(offer=locked_offer)
        messages.success(request, 'Offer accepted and order created.')
    elif decision == 'reject':
        offer.status = BuyerOffer.Status.REJECTED
        offer.save(update_fields=['status'])
        messages.info(request, 'Offer declined.')
    else:
        return HttpResponseForbidden('Unknown offer action.')
    return redirect('marketplace:dashboard')


@login_required(login_url='marketplace:login')
@require_POST
def order_update(request, pk):
    profile = getattr(request.user, 'marketplace_profile', None)
    if profile is None:
        return HttpResponseForbidden('Marketplace profile required.')
    order = get_object_or_404(
        Order.objects.select_related('offer__listing'),
        pk=pk,
        offer__listing__seller=profile,
    )
    allowed_transitions = {
        Order.Status.CONFIRMED: Order.Status.PREPARING,
        Order.Status.PREPARING: Order.Status.SHIPPED,
        Order.Status.SHIPPED: Order.Status.DELIVERED,
    }
    if allowed_transitions.get(order.status) == request.POST.get('status'):
        order.status = request.POST['status']
        order.save(update_fields=['status', 'updated_at'])
        messages.success(request, f'Order #{order.pk} status updated.')
    else:
        messages.error(request, 'That order status change is not allowed.')
    return redirect('marketplace:dashboard')
