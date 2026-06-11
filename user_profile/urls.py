from django.urls import path
from . import views

app_name = 'user_profile' 

urlpatterns = [
    path('', views.user_profile, name='profile'),
    path('edit/',         views.profile_edit,   name='profile_edit'),
    path('address/',      views.manage_address,     name='manage_address'),
    path('address/add/',  views.add_address,    name='add_address'),
    path('address/add/ajax/', views.add_address_ajax, name='add_address_ajax'),
    path('address/edit/ajax/<int:pk>/', views.edit_address_ajax, name='edit_address_ajax'),
    path('address/edit/<int:pk>/', views.edit_address, name='edit_address'),
    path('address/delete/<int:pk>/', views.delete_address, name='delete_address'),
    path('address/default/<int:pk>/', views.set_default_address, name='set_default_address'),
    path('change-password/', views.change_password, name='change_password'),
    path('verify-email-otp/', views.verify_email_otp, name='verify_email_otp'),
    path('coupons/', views.user_coupons, name='coupons'),
    path('wallet/', views.user_wallet, name='wallet'),
    path('wallet/topup/init/', views.wallet_topup_init, name='wallet_topup_init'),
    path('wallet/topup/verify/', views.wallet_topup_verify, name='wallet_topup_verify'),
    path('referral/', views.user_referral, name='referral'),
]