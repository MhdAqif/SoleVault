from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Product, Brand, Category
from django.db import models

# ─────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────
def _apply_filters(queryset, request):
    """
    Apply common GET filters to a product queryset.
    Supported params: brand, color, size, occasion, material, q (search)
    """
    brand     = request.GET.get('brand', '').strip()
    color     = request.GET.get('color', '').strip()
    size      = request.GET.get('size', '').strip()
    occasion  = request.GET.get('occasion', '').strip()
    material  = request.GET.get('material', '').strip()
    search    = request.GET.get('q', '').strip()

    if brand:
        queryset = queryset.filter(brand__slug=brand)
    if color:
        queryset = queryset.filter(variants__color__iexact=color).distinct()
    if size:
        queryset = queryset.filter(variants__size__name=size).distinct()
    if occasion:
        queryset = queryset.filter(occasion__iexact=occasion)
    if material:
        queryset = queryset.filter(material__iexact=material)
    if search:
        queryset = queryset.filter(
            Q(name__icontains=search) |
            Q(brand__name__icontains=search) |
            Q(description__icontains=search)
        )

    # Price Range Filter
    min_price = request.GET.get('min_price', '').strip()
    max_price = request.GET.get('max_price', '').strip()
    if min_price.isdigit():
        queryset = queryset.filter(price__gte=int(min_price))
    if max_price.isdigit():
        queryset = queryset.filter(price__lte=int(max_price))

    # Sort
    sort = request.GET.get('sort', '')
    if sort == 'price_asc':
        queryset = queryset.order_by('price')
    elif sort == 'price_desc':
        queryset = queryset.order_by('-price')
    elif sort == 'a_z':
        queryset = queryset.order_by('name')
    elif sort == 'z_a':
        queryset = queryset.order_by('-name')
    elif sort == 'newest':
        queryset = queryset.order_by('-created_at')
    else:
        queryset = queryset.order_by('-created_at')

    return queryset


def _get_filter_context():
    """Return shared filter data for both men/women pages."""
    return {
        'brands'    : Brand.objects.all(),
        'sizes'     : ['5','6','7','8','9','10','11','12','13','14'],
        'colors'    : [
            {'name': 'Red',   'hex': '#ef4444'},
            {'name': 'Blue',  'hex': '#3b82f6'},
            {'name': 'Black', 'hex': '#111827'},
            {'name': 'White', 'hex': '#f3f4f6'},
            {'name': 'Navy',  'hex': '#1e3a5f'},
        ],
        'occasions' : [choice[1] for choice in Product.OCCASION_CHOICES],
        'materials' : [choice[1] for choice in Product.MATERIAL_CHOICES],
    }


# ─────────────────────────────────────────
#  MEN'S PAGE
# ─────────────────────────────────────────
def men_page(request):
    """
    Men's product listing page.
    - Filters: brand, color, size, search
    - Category tab: new_arrivals / best_sellers / sale
    - Pagination: 9 per page
    """
    try:
        tab = request.GET.get('tab', 'all')
        category_slug = request.GET.get('category')

        products = Product.objects.filter(
            gender__in=['men', 'unisex'],
            is_active=True,
        ).select_related('brand', 'category')

        if category_slug:
            products = products.filter(category__slug=category_slug)

        # Tab filter
        if tab == 'new':
            products = products.filter(is_new=True)
        elif tab == 'sale':
            products = products.filter(original_price__isnull=False)

        products = _apply_filters(products, request)

        # Category cards
        men_categories = Category.objects.filter(gender='men', is_active=True)

        # Pagination
        paginator   = Paginator(products, 9)
        page_number = request.GET.get('page', 1)
        page_obj    = paginator.get_page(page_number)

        context = {
            'page_obj'      : page_obj,
            'products'      : page_obj,
            'active_tab'    : tab,
            'men_categories': men_categories,
            'search_query'  : request.GET.get('q', ''),
            'active_brand'  : request.GET.get('brand', ''),
            'active_color'  : request.GET.get('color', ''),
            'active_size'   : request.GET.get('size', ''),
            'active_occasion' : request.GET.get('occasion', ''),
            'active_material' : request.GET.get('material', ''),
            'min_price'     : request.GET.get('min_price', ''),
            'max_price'     : request.GET.get('max_price', ''),
            **_get_filter_context(),
        }
        return render(request, 'products/men.html', context)
    except Exception as e:
        from django.contrib import messages
        messages.error(request, f"An error occurred while loading products: {str(e)}")
        return render(request, 'products/men.html', {'products': [], 'men_categories': []})


# ─────────────────────────────────────────
#  WOMEN'S PAGE
# ─────────────────────────────────────────
def women_page(request):
    """
    Women's product listing page.
    - Same filters as men's page
    - Accent colour is purple (handled in template/CSS)
    """
    try:
        tab = request.GET.get('tab', 'all')
        category_slug = request.GET.get('category')

        products = Product.objects.filter(
            gender__in=['women', 'unisex'],
            is_active=True,
        ).select_related('brand', 'category')

        if category_slug:
            products = products.filter(category__slug=category_slug)

        if tab == 'new':
            products = products.filter(is_new=True)
        elif tab == 'sale':
            products = products.filter(original_price__isnull=False)

        products = _apply_filters(products, request)

        women_categories = Category.objects.filter(gender='women', is_active=True)

        paginator   = Paginator(products, 9)
        page_number = request.GET.get('page', 1)
        page_obj    = paginator.get_page(page_number)

        context = {
            'page_obj'        : page_obj,
            'products'        : page_obj,
            'active_tab'      : tab,
            'women_categories': women_categories,
            'search_query'    : request.GET.get('q', ''),
            'active_brand'    : request.GET.get('brand', ''),
            'active_color'    : request.GET.get('color', ''),
            'active_size'     : request.GET.get('size', ''),
            'active_occasion' : request.GET.get('occasion', ''),
            'active_material' : request.GET.get('material', ''),
            'min_price'       : request.GET.get('min_price', ''),
            'max_price'       : request.GET.get('max_price', ''),
            **_get_filter_context(),
        }
        return render(request, 'products/women.html', context)
    except Exception as e:
        from django.contrib import messages
        messages.error(request, f"An error occurred while loading products: {str(e)}")
        return render(request, 'products/women.html', {'products': [], 'women_categories': []})


# ─────────────────────────────────────────
#  GLOBAL SEARCH
# ─────────────────────────────────────────
def search_view(request):
    """
    Search across all products.
    """
    query = request.GET.get('q', '').strip()
    products = Product.objects.filter(is_active=True).select_related('brand', 'category')
    
    if query:
        products = _apply_filters(products, request)
    else:
        products = products.none()
        
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj'    : page_obj,
        'search_query': query,
    }
    return render(request, 'products/search_results.html', context)


def product_detail(request, slug):
    """
    Single product detail page.
    Tabs: description / manufacturer / review — all on same page, JS-switched.
    """
    product = Product.objects.filter(
        slug=slug
    ).select_related('brand', 'category').prefetch_related('images', 'variants__size').first()

    if not product or not product.is_active:
        from django.contrib import messages
        from django.shortcuts import redirect
        messages.error(request, "This product is currently unavailable.")
        return redirect('products:men')

    # Similar products: same category or brand, exclude current
    similar_products = Product.objects.filter(
        is_active=True
    ).filter(
        models.Q(category=product.category) | models.Q(brand=product.brand)
    ).exclude(id=product.id)[:4]

    context = {
        'product'         : product,
        'similar_products': similar_products,
    }
    return render(request, 'products/product_detail.html', context)