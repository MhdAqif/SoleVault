from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    path('men/',   views.men_page,   name='men'),
    path('women/', views.women_page, name='women'),
    path('new-drops/', views.new_drops_page, name='new_drops'),
    path('sale/', views.sale_page, name='sale'),
    path('search/', views.search_view, name='search'),
    path('<slug:slug>/', views.product_detail, name='detail'),
]