from django.urls import path
from . import views

urlpatterns = [
    path('', views.norway, name='norway'),
    path('login/', views.norway_login, name='norway_login'),
    path('add_ca/', views.add_ca, name='add_ca'),
    path('add_event/', views.add_event, name='add_event'),
]