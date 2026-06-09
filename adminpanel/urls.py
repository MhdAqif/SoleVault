from django.urls import path
from . import views
 
app_name = 'adminpanel'
 
urlpatterns = [
 
    # Auth
    path('login/',  views.admin_login,  name='admin_login'),
    path('logout/', views.admin_logout, name='admin_logout'),
 
    # Dashboard
    path('', views.dashboard, name='dashboard'),
 
    # Users
    path('users/',                      views.user_list,   name='user_list'),
    path('users/<int:user_id>/block/',  views.block_user,  name='block_user'),
    path('users/<int:user_id>/unblock/',views.unblock_user,name='unblock_user'),

    # Catalog
    path('categories/', views.category_list_admin, name='category_list'),
    path('categories/add/', views.category_add_admin, name='category_add'),
    path('categories/<int:category_id>/edit/', views.category_edit_admin, name='category_edit'),
    path('categories/<int:category_id>/delete/', views.category_delete_admin, name='category_delete'),

    path('products/', views.product_list_admin, name='product_list'),
    path('products/add/', views.product_add_admin, name='product_add'),
    path('products/<int:product_id>/edit/', views.product_edit_admin, name='product_edit'),
    path('products/<int:product_id>/delete/', views.product_delete_admin, name='product_delete'),

    # Orders
    path('orders/', views.order_list_admin, name='order_list'),
    path('orders/<int:order_id>/', views.order_detail_admin, name='order_detail'),
    path('orders/<int:order_id>/status/', views.order_update_status_admin, name='order_update_status'),

    # Inventory
    path('inventory/', views.inventory_list_admin, name='inventory_list'),
    path('inventory/<int:variant_id>/update-stock/', views.inventory_update_stock_admin, name='inventory_update_stock'),

    # Coupons
    path('coupons/', views.coupon_list_admin, name='coupon_list'),
    path('coupons/add/', views.coupon_add_admin, name='coupon_add'),
    path('coupons/<int:coupon_id>/delete/', views.coupon_delete_admin, name='coupon_delete'),

    # Offers
    path('offers/', views.offer_list_admin, name='offer_list'),
    path('offers/product/add/', views.product_offer_add_admin, name='product_offer_add'),
    path('offers/product/<int:offer_id>/delete/', views.product_offer_delete_admin, name='product_offer_delete'),
    path('offers/category/add/', views.category_offer_add_admin, name='category_offer_add'),
    path('offers/category/<int:offer_id>/delete/', views.category_offer_delete_admin, name='category_offer_delete'),

    # Returns Reject Flow
    path('orders/<int:order_id>/reject-return/', views.order_reject_return_admin, name='order_reject_return'),
    path('orders/<int:order_id>/item/<int:item_id>/approve-return/', views.order_item_approve_return_admin, name='order_item_approve_return'),
    path('orders/<int:order_id>/item/<int:item_id>/reject-return/', views.order_item_reject_return_admin, name='order_item_reject_return'),

    # Sales Reports & Downloads
    path('sales-report/', views.sales_report_admin, name='sales_report'),
    path('sales-report/pdf/', views.sales_report_pdf, name='sales_report_pdf'),
    path('sales-report/excel/', views.sales_report_excel, name='sales_report_excel'),
]