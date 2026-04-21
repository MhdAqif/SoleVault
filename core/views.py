from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_control

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def home(request):
    from products.models import Product
    featured_products = Product.objects.filter(is_active=True)[:4]
    return render(request, "core/home.html", {'featured_products': featured_products})