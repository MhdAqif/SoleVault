from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    path('men/',   views.men_page,   name='men'),
    path('women/', views.women_page, name='women'),
    path('<slug:slug>/', views.product_detail, name='detail'),
]