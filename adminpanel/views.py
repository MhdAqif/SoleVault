from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.views.decorators.http import require_POST
from django.views.decorators.cache import never_cache  
from functools import wraps
from django.db import transaction

# Hoisted Imports
from products.models import Product, Category, ProductVariant, Brand, Size, ProductImage
from orders.models import Order

User = get_user_model()
 
 
# ─────────────────────────────────────────
#  DECORATOR — Admin only + no-cache
#  @never_cache sets Cache-Control: no-store
#  so the browser never serves a cached admin
#  page when back is pressed after logout
# ─────────────────────────────────────────
def admin_required(view_func):
    @wraps(view_func)
    @never_cache
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_staff:
            return redirect('adminpanel:admin_login')
        return view_func(request, *args, **kwargs)
    return wrapper
 
 

@never_cache 
def admin_login(request):
    """
    Admin sign-in.
    - Looks up by email (CustomUser uses email auth).
    - Only staff/superusers are allowed.
    """
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('adminpanel:dashboard')
 
    error = None
 
    if request.method == 'POST':
        email    = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')
 
        try:
            user_obj = User.objects.get(email=email)
        except User.DoesNotExist:
            error = 'Invalid email or password.'
            return render(request, 'adminpanel/admin_login.html', {'error': error})
 
        # Try email= first (allauth / custom backend)
        user = authenticate(request, email=email, password=password)
 
        # Fallback for backends that use username=
        if user is None:
            user = authenticate(request, username=user_obj.email, password=password)
 
        if user is not None and user.is_staff:
            login(request, user)
            return redirect('adminpanel:dashboard')
        elif user is not None and not user.is_staff:
            error = 'You do not have admin privileges.'
        else:
            error = 'Invalid email or password.'
 
    return render(request, 'adminpanel/admin_login.html', {'error': error})
 
 

def admin_logout(request):
    """
    Log out and redirect to login.
    Response headers prevent the browser from
    caching the redirect, so back button won't
    restore the admin session.
    """
    logout(request)
    messages.success(request, 'Logged out successfully.')
    response = redirect('adminpanel:admin_login')
    response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response['Pragma']        = 'no-cache'
    response['Expires']       = '0'
    return response
 
 

@admin_required
def dashboard(request):
    from django.db.models import Sum
    from django.utils import timezone
    from datetime import datetime, timedelta
    import json
    from orders.models import OrderItem
    from user_profile.models import WalletTransaction
    
    total_users = User.objects.filter(is_staff=False).count()
    total_products = Product.objects.count()
    total_categories = Category.objects.count()

    total_orders = Order.objects.count()
    total_revenue = sum(o.final_price for o in Order.objects.filter(status='delivered'))
    recent_orders = Order.objects.all().order_by('-created_at')[:5]
    low_stock_count = ProductVariant.objects.filter(stock__lt=5).count()

    # 1. Best Selling Lists (Top 10)
    top_products = OrderItem.objects.values('product__name', 'product__image').annotate(
        total_qty=Sum('quantity'),
        total_sales=Sum('item_total')
    ).order_by('-total_qty')[:10]

    top_categories = OrderItem.objects.filter(product__category__isnull=False).values('product__category__name').annotate(
        total_qty=Sum('quantity'),
        total_sales=Sum('item_total')
    ).order_by('-total_qty')[:10]

    top_brands = OrderItem.objects.filter(product__brand__isnull=False).values('product__brand__name').annotate(
        total_qty=Sum('quantity'),
        total_sales=Sum('item_total')
    ).order_by('-total_qty')[:10]

    # 2. Charts Series (aggregate monthly sales for current year)
    now = timezone.now()
    year = now.year
    chart_months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    chart_values = []
    
    for m in range(1, 13):
        # sum of final_price of delivered orders in month m of year
        monthly_sales = sum(
            o.final_price for o in Order.objects.filter(
                created_at__year=year,
                created_at__month=m,
                status='delivered'
            )
        )
        chart_values.append(float(monthly_sales))

    # 3. Cashflow Ledger Book
    ledger_entries = []
    # Paid order inflows
    for o in Order.objects.filter(payment_status='paid')[:30]:
        ledger_entries.append({
            'date': o.created_at,
            'type': 'Order Income',
            'description': f"Payment received for Order {o.order_id}",
            'amount': float(o.final_price)
        })
    # Refund/Referral payouts (Wallet Credit additions)
    for t in WalletTransaction.objects.filter(transaction_type='credit')[:30]:
        ledger_entries.append({
            'date': t.created_at,
            'type': 'Store Payout',
            'description': t.description,
            'amount': -float(t.amount)
        })
    
    # Sort ledger entries descending by date
    ledger_entries = sorted(ledger_entries, key=lambda x: x['date'], reverse=True)[:15]

    context = {
        'total_users'      : total_users,
        'total_products'   : total_products,
        'total_categories' : total_categories,
        'total_orders'     : total_orders,
        'total_revenue'    : total_revenue,
        'recent_orders'    : recent_orders,
        'low_stock_count'  : low_stock_count,
        'top_products'     : top_products,
        'top_categories'   : top_categories,
        'top_brands'       : top_brands,
        'chart_labels_json': json.dumps(chart_months),
        'chart_values_json': json.dumps(chart_values),
        'ledger_entries'   : ledger_entries,
    }
    return render(request, 'adminpanel/admin_dashboard.html', context)
 
 
@admin_required
def user_list(request):
    """
    List all non-staff users.
    - Search by name / email  (GET ?q=)
    - Sort newest first
    - Paginate 10 per page    (GET ?page=)
    """
    search_query = request.GET.get('q', '').strip()
 
    users = User.objects.filter(is_staff=False).order_by('-date_joined')
 
    if search_query:
        users = users.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)  |
            Q(email__icontains=search_query)
        )
 
    paginator   = Paginator(users, 10)
    page_number = request.GET.get('page', 1)
    page_obj    = paginator.get_page(page_number)
 
    context = {
        'page_obj'    : page_obj,
        'search_query': search_query,
    }
    return render(request, 'adminpanel/admin_user_list.html', context)
 
 

@admin_required
@require_POST
def block_user(request, user_id):
    user = get_object_or_404(User, id=user_id, is_staff=False)
 
    if user.is_active:
        user.is_active = False
        user.save(update_fields=['is_active'])
        messages.success(request, f'User "{user.get_full_name() or user.email}" has been blocked.')
    else:
        messages.info(request, f'User "{user.get_full_name() or user.email}" is already blocked.')
 
    return redirect('adminpanel:user_list')
 
 
@admin_required
@require_POST
def unblock_user(request, user_id):
    user = get_object_or_404(User, id=user_id, is_staff=False)
 
    if not user.is_active:
        user.is_active = True
        user.save(update_fields=['is_active'])
        messages.success(request, f'User "{user.get_full_name() or user.email}" has been unblocked.')
    else:
        messages.info(request, f'User "{user.get_full_name() or user.email}" is already active.')
 
    return redirect('adminpanel:user_list')
 

# --- CATEGORY MANAGEMENT ---
@admin_required
def category_list_admin(request):
    query = request.GET.get('q', '')
    categories = Category.objects.all().order_by('-created_at')
    
    if query:
        categories = categories.filter(
            Q(name__icontains=query) | Q(slug__icontains=query)
        )
    
    paginator = Paginator(categories, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'adminpanel/admin_category_list.html', {
        'page_obj': page_obj, 'query': query
    })

@admin_required
def category_add_admin(request):
    if request.method == 'POST':
        try:
            name = request.POST.get('name', '').strip()
            slug = request.POST.get('slug', '').strip()
            gender = request.POST.get('gender')
            image = request.FILES.get('image')
            is_active = request.POST.get('is_active') == 'on'
            
            if not name or not slug:
                messages.error(request, "Name and Slug are required.")
                return redirect('adminpanel:category_add')
            
            # Case insensitive check for duplicate name
            if Category.objects.filter(name__iexact=name).exists():
                messages.error(request, f"A category with name '{name}' already exists.")
                return redirect('adminpanel:category_add')
                
            # Case insensitive check for duplicate slug
            if Category.objects.filter(slug__iexact=slug).exists():
                messages.error(request, f"A category with slug '{slug}' already exists.")
                return redirect('adminpanel:category_add')
                
            Category.objects.create(
                name=name, slug=slug, gender=gender, image=image, is_active=is_active
            )
            messages.success(request, f"Category {name} created successfully!")
            return redirect('adminpanel:category_list')
        except Exception as e:
            messages.error(request, f"Could not create category: {str(e)}")
            return redirect('adminpanel:category_add')
        
    return render(request, 'adminpanel/admin_category_form.html', {'action': 'Add'})

@admin_required
def category_edit_admin(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    
    if request.method == 'POST':
        try:
            name = request.POST.get('name', '').strip()
            slug = request.POST.get('slug', '').strip()
            gender = request.POST.get('gender')
            is_active = request.POST.get('is_active') == 'on'
            
            if not name or not slug:
                messages.error(request, "Name and Slug are required.")
                return redirect('adminpanel:category_edit', category_id=category.id)
                
            # Case insensitive check for duplicate name (excluding this category)
            if Category.objects.filter(name__iexact=name).exclude(id=category_id).exists():
                messages.error(request, f"A category with name '{name}' already exists.")
                return redirect('adminpanel:category_edit', category_id=category.id)
                
            # Case insensitive check for duplicate slug (excluding this category)
            if Category.objects.filter(slug__iexact=slug).exclude(id=category_id).exists():
                messages.error(request, f"A category with slug '{slug}' already exists.")
                return redirect('adminpanel:category_edit', category_id=category.id)
            
            category.name = name
            category.slug = slug
            category.gender = gender
            category.is_active = is_active
            
            if request.FILES.get('image'):
                category.image = request.FILES.get('image')
                
            category.save()
            messages.success(request, f"Category {category.name} updated successfully!")
            return redirect('adminpanel:category_list')
        except Exception as e:
            messages.error(request, f"Could not update category: {str(e)}")
            return redirect('adminpanel:category_edit', category_id=category.id)
        
    return render(request, 'adminpanel/admin_category_form.html', {'category': category, 'action': 'Edit'})

@admin_required
@require_POST
def category_delete_admin(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    category.is_active = False
    category.save()
    messages.success(request, "Category soft deleted successfully.")
    return redirect('adminpanel:category_list')


# --- CATALOG MANAGEMENT ---
@admin_required
def product_list_admin(request):
    query = request.GET.get('q', '')
    cat_id = request.GET.get('category', '')
    brand_id = request.GET.get('brand', '')
    size_id = request.GET.get('size', '')
    color = request.GET.get('color', '')

    products = Product.objects.all().order_by('-created_at')
    
    if query:
        products = products.filter(
            Q(name__icontains=query) | 
            Q(brand__name__icontains=query) | 
            Q(slug__icontains=query)
        )
    
    if cat_id:
        products = products.filter(category_id=cat_id)
    if brand_id:
        products = products.filter(brand_id=brand_id)
    if size_id:
        products = products.filter(variants__size_id=size_id).distinct()
    if color:
        products = products.filter(variants__color=color).distinct()

    # Get options for filters
    categories = Category.objects.filter(is_active=True).order_by('name')
    brands = Brand.objects.all().order_by('name')
    sizes = Size.objects.all().order_by('name')
    colors = ProductVariant.objects.exclude(color='').values_list('color', flat=True).distinct().order_by('color')
    
    paginator = Paginator(products, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'query': query,
        'cat_id': cat_id,
        'brand_id': brand_id,
        'size_id': size_id,
        'selected_color': color,
        'categories': categories,
        'brands': brands,
        'sizes': sizes,
        'colors': colors,
    }
    
    return render(request, 'adminpanel/admin_product_list.html', context)

@admin_required
def product_add_admin(request):
    try:
        brands = Brand.objects.all()
        categories = Category.objects.filter(is_active=True)
        all_sizes = Size.objects.all()
        
        if request.method == 'POST':
            name = request.POST.get('name')
            slug = request.POST.get('slug')
            price = request.POST.get('price')
            cropped_images = request.FILES.getlist('cropped_images')
            brand_id = request.POST.get('brand')
            category_id = request.POST.get('category')
            
            # Simple validation
            if not name or not slug or not price:
                messages.error(request, "Name, Slug, and Price are required.")
                return redirect('adminpanel:product_add')
            
            if len(cropped_images) < 3:
                messages.error(request, f"Minimum 3 images are required. You provided {len(cropped_images)}.")
                return redirect('adminpanel:product_add')
                
            main_image = cropped_images.pop(0)
                
            product = Product.objects.create(
                name=name,
                slug=slug,
                price=price,
                image=main_image,
                brand_id=brand_id if brand_id else None,
                category_id=category_id if category_id else None,
                occasion=request.POST.get('occasion', 'casual'),
                material=request.POST.get('material', 'mesh'),
                description=request.POST.get('description', ''),
                original_price=request.POST.get('original_price') or None,
                is_new=request.POST.get('is_new') == 'on',
                is_active=request.POST.get('is_active') == 'on',
            )

            # Save Variants
            v_sizes  = request.POST.getlist('v_size[]')
            v_colors = request.POST.getlist('v_color[]')
            v_stocks = request.POST.getlist('v_stock[]')

            for i in range(len(v_sizes)):
                if i < len(v_colors) and i < len(v_stocks):
                    ProductVariant.objects.create(
                        product=product,
                        size_id=v_sizes[i],
                        color=v_colors[i],
                        stock=v_stocks[i]
                    )
            
            for img in cropped_images:
                ProductImage.objects.create(product=product, image=img)
                
            messages.success(request, f"Product {name} created!")
            return redirect('adminpanel:product_list')
    except Exception as e:
        messages.error(request, f"Error adding product: {str(e)}")
        return redirect('adminpanel:product_list')
        
    return render(request, 'adminpanel/admin_product_form.html', {
        'brands': brands, 
        'categories': categories, 
        'all_sizes': all_sizes, 
        'occasion_choices': Product.OCCASION_CHOICES,
        'material_choices': Product.MATERIAL_CHOICES,
        'action': 'Add'
    })

@admin_required
def product_edit_admin(request, product_id):
    try:
        product = get_object_or_404(Product, id=product_id)
        brands = Brand.objects.all()
        categories = Category.objects.filter(is_active=True)
        all_sizes = Size.objects.all()
        
        if request.method == 'POST':
            product.name = request.POST.get('name')
            product.slug = request.POST.get('slug')
            product.price = request.POST.get('price')
            
            cropped_images = request.FILES.getlist('cropped_images')
            existing_img_count = product.images.count() + (1 if product.image else 0)
            
            if existing_img_count + len(cropped_images) < 3:
                messages.error(request, f"Minimum 3 total images are required. You have {existing_img_count + len(cropped_images)}.")
                return redirect('adminpanel:product_edit', product_id=product.id)
                
            # If product doesn't have a main image but we got new ones
            if not product.image and cropped_images:
                product.image = cropped_images.pop(0)
                
            brand_id = request.POST.get('brand')
            category_id = request.POST.get('category')
            product.brand_id = brand_id if brand_id else None
            product.category_id = category_id if category_id else None
            
            product.occasion = request.POST.get('occasion', 'casual')
            product.material = request.POST.get('material', 'mesh')
            product.description = request.POST.get('description', '')
            product.original_price = request.POST.get('original_price') or None
            product.is_new = request.POST.get('is_new') == 'on'
            product.is_active = request.POST.get('is_active') == 'on'
            
            product.save()

            # Update Variants (Simple approach: delete and recreate)
            product.variants.all().delete()
            v_sizes  = request.POST.getlist('v_size[]')
            v_colors = request.POST.getlist('v_color[]')
            v_stocks = request.POST.getlist('v_stock[]')

            for i in range(len(v_sizes)):
                if i < len(v_colors) and i < len(v_stocks):
                    ProductVariant.objects.create(
                        product=product,
                        size_id=v_sizes[i],
                        color=v_colors[i],
                        stock=v_stocks[i]
                    )
            
            for img in cropped_images:
                ProductImage.objects.create(product=product, image=img)
                
            messages.success(request, f"Product {product.name} updated!")
            return redirect('adminpanel:product_list')
    except Exception as e:
        messages.error(request, f"Error editing product: {str(e)}")
        return redirect('adminpanel:product_list')
        
    return render(request, 'adminpanel/admin_product_form.html', {
        'product': product, 
        'brands': brands, 
        'categories': categories, 
        'all_sizes': all_sizes, 
        'occasion_choices': Product.OCCASION_CHOICES,
        'material_choices': Product.MATERIAL_CHOICES,
        'action': 'Edit'
    })

@admin_required
@require_POST
def product_delete_admin(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    product.is_active = False
    product.save()
    messages.success(request, "Product soft deleted successfully.")
    return redirect('adminpanel:product_list')


# --- ORDER MANAGEMENT ---

@admin_required
def order_list_admin(request):
    """
    List all orders in the admin panel.
    - Default sorting: descending order by order date
    - Search by order ID, customer name, or email
    - Sort by date (descending/ascending), price (descending/ascending)
    - Filter by status
    - Clear functionality
    - Pagination
    """
    query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '').strip()
    sort_order = request.GET.get('sort', '-created_at').strip()

    orders = Order.objects.all()

    # Search
    if query:
        orders = orders.filter(
            Q(order_id__icontains=query) |
            Q(full_name__icontains=query) |
            Q(user__email__icontains=query)
        )

    # Filter
    if status_filter:
        orders = orders.filter(status=status_filter)

    # Sort
    if sort_order == 'date_asc':
        orders = orders.order_by('created_at')
    elif sort_order == 'date_desc':
        orders = orders.order_by('-created_at')
    elif sort_order == 'price_asc':
        orders = orders.order_by('final_price')
    elif sort_order == 'price_desc':
        orders = orders.order_by('-final_price')
    else:
        orders = orders.order_by('-created_at')

    # Pagination: 10 per page
    paginator = Paginator(orders, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    all_statuses = Order.STATUS_CHOICES

    context = {
        'page_obj': page_obj,
        'query': query,
        'status_filter': status_filter,
        'sort_order': sort_order,
        'all_statuses': all_statuses,
    }
    return render(request, 'adminpanel/admin_order_list.html', context)


@admin_required
def order_detail_admin(request, order_id):
    """
    View details of a specific order.
    """
    order = get_object_or_404(Order, id=order_id)
    all_statuses = Order.STATUS_CHOICES
    
    context = {
        'order': order,
        'all_statuses': all_statuses,
    }
    return render(request, 'adminpanel/admin_order_detail.html', context)


@admin_required
@require_POST
def order_update_status_admin(request, order_id):
    """
    Change order status.
    """

    order = get_object_or_404(Order, id=order_id)
    new_status = request.POST.get('status', '').strip()

    valid_statuses = [choice[0] for choice in Order.STATUS_CHOICES]
    if new_status not in valid_statuses:
        messages.error(request, "Invalid status choice.")
        return redirect('adminpanel:order_detail', order_id=order.id)

    old_status = order.status
    if old_status == new_status:
        messages.info(request, f"Order status is already '{order.get_status_display()}'.")
        return redirect('adminpanel:order_detail', order_id=order.id)

    try:
        with transaction.atomic():
            order.status = new_status
            
            if new_status == 'delivered':
                order.payment_status = 'paid'

            if new_status in ['cancelled', 'returned'] and old_status not in ['cancelled', 'returned']:
                for item in order.items.filter(is_cancelled=False):
                    if item.variant:
                        item.variant.stock += item.quantity
                        item.variant.save()
                
                if new_status == 'cancelled':
                    order.cancel_reason = "Cancelled by Administrator"
                else:
                    order.return_reason = "Returned by Administrator"

                # Direct Refund to Wallet for Cancellations / Returns if the order was paid
                if order.payment_status == 'paid' and order.final_price > 0:
                    from user_profile.models import Wallet, WalletTransaction
                    import decimal
                    wallet_obj, _ = Wallet.objects.get_or_create(user=order.user)
                    wallet_decimal = decimal.Decimal(str(wallet_obj.balance))
                    order_final = decimal.Decimal(str(order.final_price))
                    wallet_obj.balance = wallet_decimal + order_final
                    wallet_obj.save()
                    
                    description = f"Refund for Order {order.order_id} ({new_status.title()})"
                    WalletTransaction.objects.create(
                        wallet=wallet_obj,
                        transaction_type='credit',
                        amount=order.final_price,
                        description=description,
                        order=order
                    )

            order.save()
            messages.success(request, f"Order status successfully updated to '{order.get_status_display()}'.")
    except Exception as e:
        messages.error(request, f"Could not update status: {str(e)}")

    return redirect('adminpanel:order_detail', order_id=order.id)


# --- INVENTORY MANAGEMENT ---

@admin_required
def inventory_list_admin(request):
    """
    List all product variants for easy stock and inventory management.
    - Search by product name
    - Filter by 'low stock' (stock < 5)
    - Paginate 15 items per page
    """
    query = request.GET.get('q', '').strip()
    low_stock_only = request.GET.get('low_stock', '') == '1'

    variants = ProductVariant.objects.all().select_related('product', 'size').order_by('product__name', 'size__name')

    if query:
        variants = variants.filter(
            Q(product__name__icontains=query) |
            Q(product__brand__name__icontains=query)
        )

    if low_stock_only:
        variants = variants.filter(stock__lt=5)

    paginator = Paginator(variants, 15)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'query': query,
        'low_stock_only': low_stock_only,
    }
    return render(request, 'adminpanel/admin_inventory_list.html', context)


@admin_required
@require_POST
def inventory_update_stock_admin(request, variant_id):
    """
    Quickly update stock count for a variant.
    """
    variant = get_object_or_404(ProductVariant, id=variant_id)
    try:
        new_stock = int(request.POST.get('stock', 0))
        if new_stock < 0:
            messages.error(request, "Stock cannot be negative.")
        else:
            variant.stock = new_stock
            variant.save(update_fields=['stock'])
            messages.success(request, f"Stock updated for {variant.product.name} (Size: {variant.size.name}, Color: {str(variant.color).title()}) to {new_stock}!")
    except (ValueError, TypeError):
        messages.error(request, "Invalid stock value.")

    # Redirect back to where we came from, or defaults to inventory list
    next_url = request.META.get('HTTP_REFERER') or redirect('adminpanel:inventory_list')
    return redirect(next_url)


# ────────────────────────────────────────────────────────
#  COUPON MANAGEMENT
# ────────────────────────────────────────────────────────

@admin_required
def coupon_list_admin(request):
    from orders.models import Coupon
    coupons = Coupon.objects.all().order_by('-valid_from')
    return render(request, 'adminpanel/admin_coupon_list.html', {'coupons': coupons})


@admin_required
def coupon_add_admin(request):
    from orders.models import Coupon
    from django.utils import timezone
    import decimal
    
    if request.method == 'POST':
        code = request.POST.get('code', '').strip().upper()
        discount_type = request.POST.get('discount_type', 'percentage')
        discount_value = request.POST.get('discount_value', '0')
        min_spend = request.POST.get('min_spend', '0')
        max_discount = request.POST.get('max_discount', '')
        active = request.POST.get('active') == 'true'
        valid_from = request.POST.get('valid_from')
        valid_to = request.POST.get('valid_to')
        
        # Validations
        errors = []
        if not code:
            errors.append("Coupon code is required.")
        elif Coupon.objects.filter(code=code).exists():
            errors.append("A coupon with this code already exists.")
            
        try:
            val_discount = decimal.Decimal(discount_value)
            if val_discount <= 0:
                errors.append("Discount value must be greater than zero.")
        except (ValueError, decimal.InvalidOperation):
            errors.append("Invalid discount value.")
            
        try:
            val_min = decimal.Decimal(min_spend)
            if val_min < 0:
                errors.append("Minimum spend cannot be negative.")
        except (ValueError, decimal.InvalidOperation):
            errors.append("Invalid minimum spend value.")
            
        val_max = None
        if max_discount:
            try:
                val_max = decimal.Decimal(max_discount)
                if val_max < 0:
                    errors.append("Maximum discount cannot be negative.")
            except (ValueError, decimal.InvalidOperation):
                errors.append("Invalid maximum discount value.")
                
        if not valid_from or not valid_to:
            errors.append("Validity dates are required.")
        else:
            try:
                from django.utils.dateparse import parse_datetime
                dt_from = parse_datetime(valid_from)
                dt_to = parse_datetime(valid_to)
                if not dt_from or not dt_to:
                    from datetime import datetime
                    dt_from = timezone.make_aware(datetime.strptime(valid_from, '%Y-%m-%d'))
                    dt_to = timezone.make_aware(datetime.strptime(valid_to, '%Y-%m-%d'))
                
                if dt_from >= dt_to:
                    errors.append("Valid from date must be strictly before valid to date.")
            except Exception:
                errors.append("Invalid date format.")
                
        if errors:
            for err in errors:
                messages.error(request, err)
        else:
            Coupon.objects.create(
                code=code,
                discount_type=discount_type,
                discount_value=val_discount,
                min_spend=val_min,
                max_discount=val_max,
                active=active,
                valid_from=dt_from,
                valid_to=dt_to
            )
            messages.success(request, f"Coupon '{code}' created successfully!")
            return redirect('adminpanel:coupon_list')
            
    return render(request, 'adminpanel/admin_coupon_form.html')


@admin_required
@require_POST
def coupon_delete_admin(request, coupon_id):
    from orders.models import Coupon
    coupon = get_object_or_404(Coupon, id=coupon_id)
    coupon.delete()
    messages.success(request, f"Coupon '{coupon.code}' deleted successfully.")
    return redirect('adminpanel:coupon_list')


# ────────────────────────────────────────────────────────
#  OFFER MANAGEMENT
# ────────────────────────────────────────────────────────

@admin_required
def offer_list_admin(request):
    from products.models import ProductOffer, CategoryOffer
    p_offers = ProductOffer.objects.all().select_related('product')
    c_offers = CategoryOffer.objects.all().select_related('category')
    
    products = Product.objects.filter(is_active=True).order_by('name')
    categories = Category.objects.filter(is_active=True).order_by('name')
    
    context = {
        'product_offers': p_offers,
        'category_offers': c_offers,
        'products': products,
        'categories': categories,
    }
    return render(request, 'adminpanel/admin_offer_list.html', context)


@admin_required
@require_POST
def product_offer_add_admin(request):
    from products.models import ProductOffer
    product_id = request.POST.get('product_id')
    discount_percentage = request.POST.get('discount_percentage')
    
    try:
        pct = int(discount_percentage)
        if pct <= 0 or pct > 100:
            messages.error(request, "Discount must be between 1% and 100%.")
        else:
            product = get_object_or_404(Product, id=product_id)
            offer, created = ProductOffer.objects.get_or_create(product=product, defaults={'discount_percentage': pct})
            if not created:
                offer.discount_percentage = pct
                offer.is_active = True
                offer.save()
            messages.success(request, f"Product offer added successfully for '{product.name}'!")
    except (ValueError, TypeError):
        messages.error(request, "Invalid discount percentage.")
        
    return redirect('adminpanel:offer_list')


@admin_required
@require_POST
def product_offer_delete_admin(request, offer_id):
    from products.models import ProductOffer
    offer = get_object_or_404(ProductOffer, id=offer_id)
    offer.delete()
    messages.success(request, f"Product offer for '{offer.product.name}' deleted successfully.")
    return redirect('adminpanel:offer_list')


@admin_required
@require_POST
def category_offer_add_admin(request):
    from products.models import CategoryOffer
    category_id = request.POST.get('category_id')
    discount_percentage = request.POST.get('discount_percentage')
    
    try:
        pct = int(discount_percentage)
        if pct <= 0 or pct > 100:
            messages.error(request, "Discount must be between 1% and 100%.")
        else:
            category = get_object_or_404(Category, id=category_id)
            offer, created = CategoryOffer.objects.get_or_create(category=category, defaults={'discount_percentage': pct})
            if not created:
                offer.discount_percentage = pct
                offer.is_active = True
                offer.save()
            messages.success(request, f"Category offer added successfully for '{category.name}'!")
    except (ValueError, TypeError):
        messages.error(request, "Invalid discount percentage.")
        
    return redirect('adminpanel:offer_list')


@admin_required
@require_POST
def category_offer_delete_admin(request, offer_id):
    from products.models import CategoryOffer
    offer = get_object_or_404(CategoryOffer, id=offer_id)
    offer.delete()
    messages.success(request, f"Category offer for '{offer.category.name}' deleted successfully.")
    return redirect('adminpanel:offer_list')


# ────────────────────────────────────────────────────────
#  VERIFY RETURN REQUESTS: REJECT FLOW
# ────────────────────────────────────────────────────────

@admin_required
@require_POST
def order_reject_return_admin(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if order.status == 'return_requested':
        order.status = 'delivered'
        order.save()
        messages.success(request, f"Return request for Order {order.order_id} has been rejected. Order status set to Delivered.")
    else:
        messages.error(request, "This order has no active return request.")
    return redirect('adminpanel:order_detail', order_id=order.id)


# ────────────────────────────────────────────────────────
#  SALES REPORTS
# ────────────────────────────────────────────────────────

@admin_required
def sales_report_admin(request):
    from django.utils import timezone
    from datetime import timedelta, datetime
    
    filter_type = request.GET.get('filter_type', 'daily')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    now = timezone.now()
    today = now.date()
    
    if filter_type == 'daily':
        q_start = timezone.make_aware(datetime.combine(today, datetime.min.time()))
        q_end = timezone.make_aware(datetime.combine(today, datetime.max.time()))
    elif filter_type == 'weekly':
        start_of_week = today - timedelta(days=today.weekday())
        q_start = timezone.make_aware(datetime.combine(start_of_week, datetime.min.time()))
        q_end = now
    elif filter_type == 'yearly':
        start_of_year = today.replace(month=1, day=1)
        q_start = timezone.make_aware(datetime.combine(start_of_year, datetime.min.time()))
        q_end = now
    elif filter_type == 'custom' and start_date and end_date:
        try:
            dt_s = datetime.strptime(start_date, '%Y-%m-%d')
            dt_e = datetime.strptime(end_date, '%Y-%m-%d')
            q_start = timezone.make_aware(datetime.combine(dt_s.date(), datetime.min.time()))
            q_end = timezone.make_aware(datetime.combine(dt_e.date(), datetime.max.time()))
        except ValueError:
            q_start = timezone.make_aware(datetime.combine(today, datetime.min.time()))
            q_end = timezone.make_aware(datetime.combine(today, datetime.max.time()))
            filter_type = 'daily'
    else:
        q_start = timezone.make_aware(datetime.combine(today, datetime.min.time()))
        q_end = timezone.make_aware(datetime.combine(today, datetime.max.time()))
        filter_type = 'daily'
        
    orders = Order.objects.filter(
        created_at__range=(q_start, q_end)
    ).exclude(status='cancelled').order_by('-created_at')
    
    sales_count = orders.count()
    overall_order_amount = sum(o.final_price for o in orders)
    overall_discount = sum(o.discount for o in orders)
    
    context = {
        'orders': orders,
        'sales_count': sales_count,
        'overall_order_amount': overall_order_amount,
        'overall_discount': overall_discount,
        'filter_type': filter_type,
        'start_date': start_date,
        'end_date': end_date,
    }
    return render(request, 'adminpanel/admin_sales_report.html', context)


@admin_required
def sales_report_pdf(request):
    from django.utils import timezone
    from datetime import timedelta, datetime
    from django.http import HttpResponse
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    
    filter_type = request.GET.get('filter_type', 'daily')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    now = timezone.now()
    today = now.date()
    
    if filter_type == 'daily':
        q_start = timezone.make_aware(datetime.combine(today, datetime.min.time()))
        q_end = timezone.make_aware(datetime.combine(today, datetime.max.time()))
    elif filter_type == 'weekly':
        start_of_week = today - timedelta(days=today.weekday())
        q_start = timezone.make_aware(datetime.combine(start_of_week, datetime.min.time()))
        q_end = now
    elif filter_type == 'yearly':
        start_of_year = today.replace(month=1, day=1)
        q_start = timezone.make_aware(datetime.combine(start_of_year, datetime.min.time()))
        q_end = now
    elif filter_type == 'custom' and start_date and end_date:
        try:
            dt_s = datetime.strptime(start_date, '%Y-%m-%d')
            dt_e = datetime.strptime(end_date, '%Y-%m-%d')
            q_start = timezone.make_aware(datetime.combine(dt_s.date(), datetime.min.time()))
            q_end = timezone.make_aware(datetime.combine(dt_e.date(), datetime.max.time()))
        except ValueError:
            q_start = timezone.make_aware(datetime.combine(today, datetime.min.time()))
            q_end = timezone.make_aware(datetime.combine(today, datetime.max.time()))
    else:
        q_start = timezone.make_aware(datetime.combine(today, datetime.min.time()))
        q_end = timezone.make_aware(datetime.combine(today, datetime.max.time()))
        
    orders = Order.objects.filter(
        created_at__range=(q_start, q_end)
    ).exclude(status='cancelled').order_by('-created_at')
    
    sales_count = orders.count()
    overall_order_amount = sum(o.final_price for o in orders)
    overall_discount = sum(o.discount for o in orders)
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="SoleVault_Sales_Report_{filter_type}.pdf"'
    
    doc = SimpleDocTemplate(response, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    story = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=24,
        textColor=colors.HexColor('#1e3a8a'),
        spaceAfter=12
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        textColor=colors.HexColor('#4b5563'),
        spaceAfter=20
    )
    
    story.append(Paragraph("SoleVault Sales Report", title_style))
    story.append(Paragraph(f"Generated on {now.strftime('%Y-%m-%d %H:%M:%S')} | Scope: {filter_type.upper()}", subtitle_style))
    story.append(Spacer(1, 10))
    
    summary_data = [
        ["Metric", "Value"],
        ["Overall Sales Count", str(sales_count)],
        ["Overall Discount Deducted", f"INR {overall_discount:.2f}"],
        ["Overall Net Sales Amount", f"INR {overall_order_amount:.2f}"]
    ]
    summary_table = Table(summary_data, colWidths=[200, 200])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (1, 0), colors.HexColor('#1e3a8a')),
        ('TEXTCOLOR', (0, 0), (1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e5e7eb')),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f9fafb')),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 20))
    
    detail_data = [
        ["Order ID", "Customer", "Date", "Subtotal (INR)", "Discount (INR)", "Grand Total (INR)", "Status"]
    ]
    for o in orders:
        detail_data.append([
            o.order_id,
            o.user.email if o.user else "Guest",
            o.created_at.strftime('%Y-%m-%d'),
            f"{o.subtotal:.2f}",
            f"{o.discount:.2f}",
            f"{o.final_price:.2f}",
            o.get_status_display()
        ])
        
    detail_table = Table(detail_data, colWidths=[90, 110, 70, 70, 75, 75, 50])
    detail_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3b82f6')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d1d5db')),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
    ]))
    story.append(detail_table)
    
    doc.build(story)
    return response


@admin_required
def sales_report_excel(request):
    from django.utils import timezone
    from datetime import timedelta, datetime
    from django.http import HttpResponse
    import csv
    
    filter_type = request.GET.get('filter_type', 'daily')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    now = timezone.now()
    today = now.date()
    
    if filter_type == 'daily':
        q_start = timezone.make_aware(datetime.combine(today, datetime.min.time()))
        q_end = timezone.make_aware(datetime.combine(today, datetime.max.time()))
    elif filter_type == 'weekly':
        start_of_week = today - timedelta(days=today.weekday())
        q_start = timezone.make_aware(datetime.combine(start_of_week, datetime.min.time()))
        q_end = now
    elif filter_type == 'yearly':
        start_of_year = today.replace(month=1, day=1)
        q_start = timezone.make_aware(datetime.combine(start_of_year, datetime.min.time()))
        q_end = now
    elif filter_type == 'custom' and start_date and end_date:
        try:
            dt_s = datetime.strptime(start_date, '%Y-%m-%d')
            dt_e = datetime.strptime(end_date, '%Y-%m-%d')
            q_start = timezone.make_aware(datetime.combine(dt_s.date(), datetime.min.time()))
            q_end = timezone.make_aware(datetime.combine(dt_e.date(), datetime.max.time()))
        except ValueError:
            q_start = timezone.make_aware(datetime.combine(today, datetime.min.time()))
            q_end = timezone.make_aware(datetime.combine(today, datetime.max.time()))
    else:
        q_start = timezone.make_aware(datetime.combine(today, datetime.min.time()))
        q_end = timezone.make_aware(datetime.combine(today, datetime.max.time()))
        
    orders = Order.objects.filter(
        created_at__range=(q_start, q_end)
    ).exclude(status='cancelled').order_by('-created_at')
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="SoleVault_Sales_Report_{filter_type}.csv"'
    
    writer = csv.writer(response)
    writer.writerow(["Order ID", "Customer Email", "Date", "Subtotal (INR)", "Discount Deductions (INR)", "Grand Paid Total (INR)", "Status"])
    
    for o in orders:
        writer.writerow([
            o.order_id,
            o.user.email if o.user else "Guest",
            o.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            f"{o.subtotal:.2f}",
            f"{o.discount:.2f}",
            f"{o.final_price:.2f}",
            o.get_status_display()
        ])
        
    return response
 