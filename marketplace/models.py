from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class MarketplaceProfile(models.Model):
    class Role(models.TextChoices):
        FARMER = 'FARMER', 'Farmer / Seller'
        BUYER = 'BUYER', 'Buyer'
        BOTH = 'BOTH', 'Farmer and buyer'

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='marketplace_profile',
    )
    supabase_uid = models.CharField(max_length=64, unique=True, null=True, blank=True)
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.FARMER)
    phone = models.CharField(max_length=30, blank=True)
    organization = models.CharField(max_length=120, blank=True)
    location = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.get_full_name() or self.user.username} ({self.get_role_display()})'

    @property
    def can_sell(self):
        return self.role in {self.Role.FARMER, self.Role.BOTH}

    @property
    def can_buy(self):
        return self.role in {self.Role.BUYER, self.Role.BOTH}


class Listing(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Available'
        SOLD = 'SOLD', 'Sold'
        INACTIVE = 'INACTIVE', 'Inactive'

    seller = models.ForeignKey(
        MarketplaceProfile,
        on_delete=models.PROTECT,
        related_name='listings',
    )
    crop = models.CharField(max_length=80)
    description = models.TextField(blank=True)
    quantity_tonnes = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
    )
    price_per_tonne = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        null=True,
        blank=True,
        help_text='Optional asking price in ZMW per tonne.',
    )
    location = models.CharField(max_length=100)
    quality = models.CharField(max_length=120, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.quantity_tonnes} tonnes of {self.crop} in {self.location}'

    @property
    def is_available(self):
        return self.status == self.Status.ACTIVE and self.quantity_tonnes > 0


class BuyerOffer(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        ACCEPTED = 'ACCEPTED', 'Accepted'
        REJECTED = 'REJECTED', 'Declined'

    listing = models.ForeignKey(Listing, on_delete=models.PROTECT, related_name='offers')
    buyer = models.ForeignKey(
        MarketplaceProfile,
        on_delete=models.PROTECT,
        related_name='offers',
    )
    quantity_tonnes = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
    )
    price_per_tonne = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        help_text='Your offer in ZMW per tonne.',
    )
    message = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Offer for {self.listing.crop} by {self.buyer}'

    @property
    def total_value(self):
        return self.quantity_tonnes * self.price_per_tonne


class Order(models.Model):
    class Status(models.TextChoices):
        CONFIRMED = 'CONFIRMED', 'Confirmed'
        PREPARING = 'PREPARING', 'Preparing'
        SHIPPED = 'SHIPPED', 'Shipped'
        DELIVERED = 'DELIVERED', 'Delivered'
        CANCELLED = 'CANCELLED', 'Cancelled'

    offer = models.OneToOneField(BuyerOffer, on_delete=models.PROTECT, related_name='order')
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.CONFIRMED)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Order #{self.pk} - {self.offer.listing.crop}'


class MarketPrice(models.Model):
    crop = models.CharField(max_length=80)
    market = models.CharField(max_length=100)
    price_per_tonne = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
    )
    observed_on = models.DateField()
    source = models.CharField(max_length=160, blank=True)

    class Meta:
        ordering = ['-observed_on', 'crop', 'market']

    def __str__(self):
        return f'{self.crop} at {self.market}: ZMW {self.price_per_tonne}/tonne'
