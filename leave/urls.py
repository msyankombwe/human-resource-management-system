from django.urls import path

from . import views

app_name = 'leave'

urlpatterns = [
    path('', views.leave_list, name='list'),
    path('request/', views.leave_create, name='create'),
    path('<int:pk>/decide/', views.leave_decide, name='decide'),
    path('types/', views.leave_types, name='types'),
]
