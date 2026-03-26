from django.urls import path
from . import views

urlpatterns = [
    path('signup/', views.signup, name='signup'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('verify/', views.verify_otp, name='verify'),
    path('forget/', views.forget_password, name='forget_password'),
    path('forget-otp/', views.forget_otp, name='forget_otp'),
    path('reset/', views.reset_password, name='reset_password')
]