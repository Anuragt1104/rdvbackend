from django.urls import path
from . import views

urlpatterns = [
    path('', views.mailer, name='mailer'),
    path('past/', views.past_mails, name='past_mails'),
    path('login/', views.login, name='mailer_login'),
    path('confirm/<int:id>/', views.confirm_mail, name='confirm_mail'),
]