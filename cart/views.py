from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from products.models import Product, ProductVariant
from .models import Cart, CartItem, Wishlist, WishlistItem

def _get_or_create_cart(request):
    """Only authenticated users have a persistent cart."""
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
        return cart
    return None

def cart_detail(request):
    if not request.user.is_authenticated:
        messages.info(request, "Please log in to view your cart.")
        return redirect(f"{reverse('login')}?next={request.path}")
    cart = _get_or_create_cart(request)
    context = {
        'cart': cart,
    }
    return render(request, 'cart/cart_detail.html', context)

@require_POST
def cart_add(request, product_id):
    # Guests cannot add to cart — send them to login
    if not request.user.is_authenticated:
        messages.info(request, "Please log in to add items to your cart.")
        next_url = request.META.get('HTTP_REFERER', '/')
        return redirect(f"{reverse('login')}?next={next_url}")
    try:
        cart = _get_or_create_cart(request)
        product = get_object_or_404(Product, id=product_id, is_active=True)
        
        quantity = int(request.POST.get('quantity', 1))
        size_name = request.POST.get('size', '').strip()
        color_name = request.POST.get('color', '').strip()

        # Try to find variant if size and color are matching
        variant = None
        if size_name and color_name:
            variant = product.variants.filter(size__name=size_name, color__iexact=color_name).first()
        if not variant and size_name:
            variant = product.variants.filter(size__name=size_name).first()

        max_limit = 5
        
        # Check stock availability
        if variant:
            if variant.stock <= 0:
                messages.error(request, f"Sorry, {product.name} (Size: {variant.size.name}, Color: {variant.color|title}) is out of stock.")
                return redirect(request.META.get('HTTP_REFERER', 'cart:detail'))
            
            # Check if this exact product+variant is already in cart
            cart_item = cart.items.filter(product=product, variant=variant).first()
            current_qty = cart_item.quantity if cart_item else 0
            
            if current_qty + quantity > variant.stock:
                messages.error(request, f"Only {variant.stock} units are available in stock. You already have {current_qty} in your cart.")
                return redirect(request.META.get('HTTP_REFERER', 'cart:detail'))
            
            if current_qty + quantity > max_limit:
                messages.error(request, f"Maximum limit of {max_limit} items reached for this product. You already have {current_qty} in your cart.")
                return redirect(request.META.get('HTTP_REFERER', 'cart:detail'))
        else:
            if not product.is_in_stock:
                messages.error(request, f"Sorry, {product.name} is out of stock.")
                return redirect(request.META.get('HTTP_REFERER', 'cart:detail'))
                
            cart_item = cart.items.filter(product=product, size=size_name).first()
            current_qty = cart_item.quantity if cart_item else 0
            if current_qty + quantity > max_limit:
                messages.error(request, f"Maximum limit of {max_limit} items reached for this product. You already have {current_qty} in your cart.")
                return redirect(request.META.get('HTTP_REFERER', 'cart:detail'))

        if cart_item:
            cart_item.quantity += quantity
            cart_item.save()
            messages.success(request, f"Updated {product.name} quantity in your cart.")
        else:
            CartItem.objects.create(
                cart=cart,
                product=product,
                variant=variant,
                size=size_name,
                quantity=quantity
            )
            messages.success(request, f"Added {product.name} to your cart.")
            
        # Remove from wishlist if it exists
        if request.user.is_authenticated:
            WishlistItem.objects.filter(wishlist__user=request.user, product=product).delete()
            
    except Exception as e:
        messages.error(request, f"Could not add item to cart: {str(e)}")
        
    return redirect(request.META.get('HTTP_REFERER', 'cart:detail'))

from django.http import JsonResponse

@require_POST
def cart_update(request, item_id):
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    try:
        cart = _get_or_create_cart(request)
        cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
        
        action = request.POST.get('action') # 'increase' or 'decrease'
        variant = cart_item.variant
        max_limit = 5
        success = True
        
        if action == 'increase':
            if variant and cart_item.quantity >= variant.stock:
                messages.error(request, f"Cannot increase quantity. Only {variant.stock} units available in stock.")
                success = False
            elif cart_item.quantity >= max_limit:
                messages.error(request, f"Maximum limit of {max_limit} items reached for this product.")
                success = False
            else:
                cart_item.quantity += 1
                cart_item.save()
                messages.success(request, "Cart quantity updated.")
        elif action == 'decrease' and cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
            messages.success(request, "Cart quantity updated.")
            
        if is_ajax:
            storage = messages.get_messages(request)
            msg_list = [{'message': msg.message, 'tags': msg.tags} for msg in storage]
            return JsonResponse({
                'success': success,
                'quantity': cart_item.quantity,
                'item_total_price': float(cart_item.total_price),
                'cart_total_price': float(cart.total_price),
                'messages': msg_list
            })
    except Exception as e:
        messages.error(request, f"Error updating cart: {str(e)}")
        if is_ajax:
            storage = messages.get_messages(request)
            msg_list = [{'message': msg.message, 'tags': msg.tags} for msg in storage]
            return JsonResponse({'success': False, 'messages': msg_list})
        
    return redirect('cart:detail')

@require_POST
def cart_remove(request, item_id):
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    try:
        cart = _get_or_create_cart(request)
        cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
        cart_item.delete()          
        messages.success(request, "Item removed from cart.")
        
        if is_ajax:
            storage = messages.get_messages(request)
            msg_list = [{'message': msg.message, 'tags': msg.tags} for msg in storage]
            return JsonResponse({
                'success': True,
                'cart_total_price': float(cart.total_price),
                'cart_is_empty': not cart.items.exists(),
                'messages': msg_list
            })
    except Exception as e:
        messages.error(request, f"Error removing item: {str(e)}")
        if is_ajax:
            storage = messages.get_messages(request)
            msg_list = [{'message': msg.message, 'tags': msg.tags} for msg in storage]
            return JsonResponse({'success': False, 'messages': msg_list})
        
    return redirect('cart:detail')

@login_required(login_url='/login/')
def wishlist_detail(request):
    wishlist, created = Wishlist.objects.get_or_create(user=request.user)
    return render(request, 'cart/wishlist_detail.html', {'wishlist': wishlist})

@login_required(login_url='/login/')
@require_POST
def wishlist_toggle(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    wishlist, created = Wishlist.objects.get_or_create(user=request.user)
    
    item = wishlist.items.filter(product=product).first()
    if item:
        item.delete()
        messages.success(request, f"Removed {product.name} from wishlist.")
    else:
        WishlistItem.objects.create(wishlist=wishlist, product=product)
        messages.success(request, f"Added {product.name} to wishlist.")
        
    return redirect(request.META.get('HTTP_REFERER', 'products:men'))
