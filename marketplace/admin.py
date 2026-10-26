from django.contrib import admin

from .models import BuyerOffer, Listing, MarketPrice, MarketplaceProfile, Order


@admin.register(MarketplaceProfile)
class MarketplaceProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'phone', 'location')
    list_filter = ('role',)
    search_fields = ('user__username', 'user__email', 'organization', 'location')


@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = ('crop', 'seller', 'quantity_tonnes', 'location', 'status', 'created_at')
    list_filter = ('status', 'crop', 'location')
    search_fields = ('crop', 'description', 'seller__user__username')


@admin.register(BuyerOffer)
class BuyerOfferAdmin(admin.ModelAdmin):
    list_display = ('listing', 'buyer', 'quantity_tonnes', 'price_per_tonne', 'status', 'created_at')
    list_filter = ('status',)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'offer', 'status', 'created_at', 'updated_at')
    list_filter = ('status',)


@admin.register(MarketPrice)
class MarketPriceAdmin(admin.ModelAdmin):
    list_display = ('crop', 'market', 'price_per_tonne', 'observed_on', 'source')
    list_filter = ('crop', 'market')
    search_fields = ('crop', 'market', 'source')
