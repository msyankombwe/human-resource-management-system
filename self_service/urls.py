from django.urls import path

from . import views

app_name = 'self_service'

urlpatterns = [
    path('', views.home, name='home'),
    path('profile/', views.my_profile, name='profile'),
]
