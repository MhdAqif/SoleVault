from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('checkout/', views.checkout_page, name='checkout'),
    path('success/<str:order_id>/', views.order_success, name='success'),
    path('my-orders/', views.order_list, name='list'),
    path('order-detail/<str:order_id>/', views.order_detail, name='detail'),
    path('cancel-item/<str:order_id>/<int:item_id>/', views.cancel_order_item, name='cancel_item'),
    path('return/<str:order_id>/', views.return_order, name='return_order'),
    path('invoice/<str:order_id>/', views.download_invoice, name='invoice'),
]
