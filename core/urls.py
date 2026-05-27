from django.urls import path
from . import views

app_name = 'core' 

urlpatterns = [
    path('', views.home, name='home'),   # handles "/"
    path('about/', views.about, name='about'),
    path('philosophy/', views.philosophy, name='philosophy'),
    path('careers/', views.careers, name='careers'),
    path('press/', views.press, name='press'),
    path('contact/', views.contact, name='contact'),
    path('shipping-returns/', views.shipping_returns, name='shipping_returns'),
    path('faq/', views.faq, name='faq'),
    path('size-guide/', views.size_guide, name='size_guide'),
    path('privacy/', views.privacy, name='privacy'),
    path('terms/', views.terms, name='terms'),
    path('blog/', views.blog, name='blog'),
    path('lookbook/', views.lookbook, name='lookbook'),
]