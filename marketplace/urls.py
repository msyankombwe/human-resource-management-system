from django.urls import path

from . import views

app_name = 'marketplace'

urlpatterns = [
    path('', views.home, name='home'),
    path('marketplace/', views.listing_list, name='listing_list'),
    path('marketplace/listing/<int:pk>/', views.listing_detail, name='listing_detail'),
    path('marketplace/listing/new/', views.listing_create, name='listing_create'),
    path('marketplace/listing/<int:pk>/offer/', views.offer_create, name='offer_create'),
    path('marketplace/offers/<int:pk>/<str:decision>/', views.offer_decide, name='offer_decide'),
    path('marketplace/orders/<int:pk>/status/', views.order_update, name='order_update'),
    path('marketplace/dashboard/', views.dashboard, name='dashboard'),
    path('register/', views.register, name='register'),
    path('signin/', views.marketplace_login, name='login'),
]
