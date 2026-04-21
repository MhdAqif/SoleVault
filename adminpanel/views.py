from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.views.decorators.http import require_POST
from django.views.decorators.cache import never_cache  
from functools import wraps
 
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
    from products.models import Product, Category
    total_products = Product.objects.count()
    total_categories = Category.objects.count()

    context = {
        'total_users'      : total_users,
        'total_products'   : total_products,
        'total_categories' : total_categories,
        'total_orders'     : 0,
        'total_revenue'    : 0,
        'recent_orders'    : [],
        'low_stock_count'  : 0,
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
    from products.models import Category
    from django.db.models import Q
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
    from products.models import Category
    if request.method == 'POST':
        name = request.POST.get('name')
        slug = request.POST.get('slug')
        gender = request.POST.get('gender')
        image = request.FILES.get('image')
        is_active = request.POST.get('is_active') == 'on'
        
        if not name or not slug:
            messages.error(request, "Name and Slug are required.")
            return redirect('adminpanel:category_add')
            
        Category.objects.create(
            name=name, slug=slug, gender=gender, image=image, is_active=is_active
        )
        messages.success(request, f"Category {name} created!")
        return redirect('adminpanel:category_list')
        
    return render(request, 'adminpanel/admin_category_form.html', {'action': 'Add'})

@admin_required
def category_edit_admin(request, category_id):
    from products.models import Category
    category = get_object_or_404(Category, id=category_id)
    
    if request.method == 'POST':
        category.name = request.POST.get('name')
        category.slug = request.POST.get('slug')
        category.gender = request.POST.get('gender')
        category.is_active = request.POST.get('is_active') == 'on'
        
        if request.FILES.get('image'):
            category.image = request.FILES.get('image')
            
        category.save()
        messages.success(request, f"Category {category.name} updated!")
        return redirect('adminpanel:category_list')
        
    return render(request, 'adminpanel/admin_category_form.html', {'category': category, 'action': 'Edit'})

@admin_required
@require_POST
def category_delete_admin(request, category_id):
    from products.models import Category
    category = get_object_or_404(Category, id=category_id)
    category.is_active = False
    category.save()
    messages.success(request, "Category soft deleted successfully.")
    return redirect('adminpanel:category_list')


# --- CATALOG MANAGEMENT ---
@admin_required
def product_list_admin(request):
    from products.models import Product
    from django.db.models import Q
    query = request.GET.get('q', '')
    products = Product.objects.all().order_by('-created_at')
    
    if query:
        products = products.filter(
            Q(name__icontains=query) | 
            Q(brand__name__icontains=query) | 
            Q(slug__icontains=query)
        )
    
    paginator = Paginator(products, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'adminpanel/admin_product_list.html', {'page_obj': page_obj})

@admin_required
def product_add_admin(request):
    try:
        from products.models import Product, Brand, Category, Size
        brands = Brand.objects.all()
        categories = Category.objects.all()
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
            from products.models import ProductVariant
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
            
            from products.models import ProductImage
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
        from products.models import Product, Brand, Category, Size
        product = get_object_or_404(Product, id=product_id)
        brands = Brand.objects.all()
        categories = Category.objects.all()
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
            from products.models import ProductVariant
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
            
            from products.models import ProductImage
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
    from products.models import Product
    product = get_object_or_404(Product, id=product_id)
    product.is_active = False
    product.save()
    messages.success(request, "Product soft deleted successfully.")
    return redirect('adminpanel:product_list')
 