from cart.models import Cart

class MergeCartMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        guest_session_key = None
        was_authenticated = request.user.is_authenticated
        
        if not was_authenticated:
            guest_session_key = request.session.session_key

        response = self.get_response(request)

        # Check if the user logged in during this request
        if request.user.is_authenticated and not was_authenticated and guest_session_key:
            try:
                guest_cart = Cart.objects.filter(user=None, session_id=guest_session_key).first()
                if guest_cart:
                    user_cart, created = Cart.objects.get_or_create(user=request.user)
                    for item in guest_cart.items.all():
                        existing_item = user_cart.items.filter(product=item.product, size=item.size).first()
                        if existing_item:
                            existing_item.quantity += item.quantity
                            existing_item.save()
                            item.delete()
                        else:
                            item.cart = user_cart
                            item.save()
                    # Clean up guest cart
                    guest_cart.delete()
            except Exception as e:
                pass

        return response
