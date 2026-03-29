from django.urls import path
from . import views

app_name = 'user_profile' 

urlpatterns = [
    path('', views.user_profile, name='profile'),
    path('edit/',         views.profile_edit,   name='profile_edit'),
    path('address/',      views.manage_address,     name='manage_address'),
    path('address/add/',  views.add_address,    name='add_address'),
    path('address/edit/<int:pk>/', views.edit_address, name='edit_address'),
    path('address/delete/<int:pk>/', views.delete_address, name='delete_address'),
]