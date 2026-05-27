from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('checkout/', views.checkout_page, name='checkout'),
    path('payment/verify/', views.payment_verify, name='payment_verify'),
    path('payment/failure/<str:order_id>/', views.payment_failure, name='payment_failure'),
    path('payment/<str:order_id>/', views.payment_page, name='payment_page'),
    path('success/<str:order_id>/', views.order_success, name='success'),
    path('my-orders/', views.order_list, name='list'),
    path('order-detail/<str:order_id>/', views.order_detail, name='detail'),
    path('cancel-item/<str:order_id>/<int:item_id>/', views.cancel_order_item, name='cancel_item'),
    path('return/<str:order_id>/', views.return_order, name='return_order'),
    path('invoice/<str:order_id>/', views.download_invoice, name='invoice'),
    path('coupon/apply/', views.apply_coupon, name='apply_coupon'),
    path('coupon/remove/', views.remove_coupon, name='remove_coupon'),
]
