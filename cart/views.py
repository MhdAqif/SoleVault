from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from products.models import Product, ProductVariant
from .models import Cart, CartItem, Wishlist, WishlistItem

def _get_or_create_cart(request):
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
        return cart
    else:
        # Session based cart
        if not request.session.session_key:
            request.session.create()
        session_id = request.session.session_key
        cart, created = Cart.objects.get_or_create(user=None, session_id=session_id)
        return cart

def cart_detail(request):
    cart = _get_or_create_cart(request)
    context = {
        'cart': cart,
    }
    return render(request, 'cart/cart_detail.html', context)

@require_POST
def cart_add(request, product_id):
    cart = _get_or_create_cart(request)
    product = get_object_or_404(Product, id=product_id, is_active=True)
    
    quantity = int(request.POST.get('quantity', 1))
    size_name = request.POST.get('size', '').strip()

    # Try to find variant if size is matching
    variant = product.variants.filter(size__name=size_name).first() if size_name else None

    # Check if this exact product+size is already in cart
    cart_item = cart.items.filter(product=product, size=size_name).first()
    
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
        
    # Redirect to where they came from or cart
    return redirect(request.META.get('HTTP_REFERER', 'cart:detail'))

@require_POST
def cart_update(request, item_id):
    cart = _get_or_create_cart(request)
    cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
    
    action = request.POST.get('action') # 'increase' or 'decrease'
    if action == 'increase':
        cart_item.quantity += 1
        cart_item.save()
    elif action == 'decrease' and cart_item.quantity > 1:
        cart_item.quantity -= 1
        cart_item.save()
        
    return redirect('cart:detail')

@require_POST
def cart_remove(request, item_id):
    cart = _get_or_create_cart(request)
    cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
    cart_item.delete()
    messages.success(request, "Item removed from cart.")
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
