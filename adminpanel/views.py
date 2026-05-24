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
    total_users = User.objects.filter(is_staff=False).count()
    total_products = Product.objects.count()
    total_categories = Category.objects.count()

    total_orders = Order.objects.count()
    total_revenue = sum(o.final_price for o in Order.objects.filter(status='delivered'))
    recent_orders = Order.objects.all().order_by('-created_at')[:5]
    low_stock_count = ProductVariant.objects.filter(stock__lt=5).count()

    context = {
        'total_users'      : total_users,
        'total_products'   : total_products,
        'total_categories' : total_categories,
        'total_orders'     : total_orders,
        'total_revenue'    : total_revenue,
        'recent_orders'    : recent_orders,
        'low_stock_count'  : low_stock_count,
        'top_product_count': 0,
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
 