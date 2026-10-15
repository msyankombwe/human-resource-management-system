from django.urls import path

from . import views

app_name = 'performance'

urlpatterns = [
    path('cycles/', views.cycle_list, name='cycles'),
    path('cycles/add/', views.cycle_create, name='cycle_create'),
    path('reviews/', views.review_list, name='reviews'),
    path('reviews/add/', views.review_create, name='review_create'),
    path('reviews/<int:pk>/edit/', views.review_edit, name='review_edit'),
]
