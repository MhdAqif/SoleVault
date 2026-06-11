from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.views.decorators.cache import never_cache
from django.http import HttpResponse, JsonResponse
from django.db import transaction
from django.db.models import Q
from cart.models import Cart, CartItem
from user_profile.models import Address
from products.models import ProductVariant
from .models import Order, OrderItem, Coupon
import razorpay
from django.conf import settings

# PDF invoice generation imports
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import io

@login_required(login_url='/login/')
@never_cache
def checkout_page(request):
    try:
        cart = Cart.objects.get(user=request.user)
    except Cart.DoesNotExist:
        messages.error(request, "Your cart is empty.")
        return redirect('products:men')

    cart_items = cart.items.all()
    if not cart_items.exists():
        messages.error(request, "Your cart is empty.")
        return redirect('products:men')

    addresses = Address.objects.filter(user=request.user)
    default_address = addresses.filter(is_default=True).first()
    if not default_address and addresses.exists():
        default_address = addresses.first()

    # Checkout Math
    subtotal = cart.total_price
    
    # Calculate product-level informational discounts if products have original prices
    total_discount = 0.00
    for item in cart_items:
        if item.product.original_price and item.product.original_price > item.product.price:
            savings = (item.product.original_price - item.product.price) * item.quantity
            total_discount += float(savings)

    #  Coupon Management integration
    coupon_code = request.session.get('coupon_code')
    coupon = None
    coupon_discount = 0.00
    if coupon_code:
        try:
            coupon = Coupon.objects.get(code=coupon_code)
            import decimal
            decimal_subtotal = decimal.Decimal(str(subtotal))
            valid, _ = coupon.is_valid(decimal_subtotal)
            if valid:
                coupon_discount = float(coupon.calculate_discount(decimal_subtotal, cart_items=cart_items))
            else:
                # Remove invalid coupon if conditions are no longer met
                request.session.pop('coupon_code', None)
                coupon_code = None
                coupon = None
        except Coupon.DoesNotExist:
            request.session.pop('coupon_code', None)
            coupon_code = None
            coupon = None

    # GST Included representation (18% GST on the discounted total)
    discounted_subtotal = float(subtotal) - coupon_discount
    tax = discounted_subtotal * 0.18 / 1.18

    # Flat shipping fee: free above 3000, else 99
    shipping_fee = 0.00 if discounted_subtotal >= 3000 else 99.00
    final_price = discounted_subtotal + shipping_fee

    from user_profile.models import Wallet
    wallet, _ = Wallet.objects.get_or_create(user=request.user)
    wallet_balance = float(wallet.balance)

    if request.method == 'POST':
        address_id = request.POST.get('address_id')
        payment_method = request.POST.get('payment_method', 'COD')
        if payment_method not in ['COD', 'Razorpay', 'Wallet']:
            payment_method = 'COD'

        if not address_id:
            messages.error(request, "Please select or add a delivery address.")
            return redirect('orders:checkout')

        selected_address = get_object_or_404(Address, id=address_id, user=request.user)

        # Transaction safety for stock checking and deduction
        try:
            with transaction.atomic():
                # Re-fetch items inside atomic block for safety
                items_to_check = cart.items.all()
                for item in items_to_check:
                    if item.variant:
                        if item.quantity > item.variant.stock:
                            raise ValueError(f"Insufficient stock for {item.product.name} ({item.variant.size.name}/{item.variant.color}). Only {item.variant.stock} units available.")
                    else:
                        raise ValueError(f"Product variant not found for {item.product.name}.")

                # If stock check passes, create Order
                order = Order.objects.create(
                    user=request.user,
                    full_name=selected_address.full_name,
                    phone=selected_address.phone,
                    address=selected_address.address,
                    district=selected_address.district,
                    state=selected_address.state,
                    city=selected_address.city,
                    pincode=selected_address.pincode,
                    landmark=selected_address.landmark,
                    payment_method=payment_method,
                    payment_status='pending',
                    status='pending',
                    subtotal=subtotal,
                    discount=coupon_discount,
                    tax=tax,
                    shipping_fee=shipping_fee,
                    final_price=final_price
                )

                # Create OrderItems and decrement stock
                for item in items_to_check:
                    # Snapshot size and color
                    size_val = item.variant.size.name if item.variant and item.variant.size else item.size
                    color_val = item.variant.color if item.variant else ''
                    
                    OrderItem.objects.create(
                        order=order,
                        product=item.product,
                        variant=item.variant,
                        product_name=item.product.name,
                        size=size_val,
                        color=color_val,
                        quantity=item.quantity,
                        price=item.product.offer_price,
                        item_total=item.total_price
                    )

                    # Deduct stock
                    if item.variant:
                        item.variant.stock -= item.quantity
                        item.variant.save()

                if payment_method == 'Wallet':
                    from user_profile.models import Wallet, WalletTransaction
                    import decimal
                    wallet_obj, created = Wallet.objects.get_or_create(user=request.user)
                    decimal_final = decimal.Decimal(str(final_price))
                    wallet_decimal = decimal.Decimal(str(wallet_obj.balance))
                    if wallet_decimal < decimal_final:
                        raise ValueError(f"Insufficient wallet balance. You need ₹{decimal_final} but only have ₹{wallet_decimal}.")
                    
                    wallet_obj.balance = wallet_decimal - decimal_final
                    wallet_obj.save()
                    
                    WalletTransaction.objects.create(
                        wallet=wallet_obj,
                        transaction_type='debit',
                        amount=decimal_final,
                        description=f"Payment for Order {order.order_id}",
                        order=order
                    )
                    
                    order.payment_status = 'paid'
                    order.status = 'processing'
                    order.save()

                # Clear user's cart items
                cart.items.all().delete()
                
                # Clear coupon code session since order is placed successfully
                request.session.pop('coupon_code', None)
                
                if payment_method == 'Razorpay':
                    messages.success(request, "Order created! Proceeding to secure payment.")
                    return redirect('orders:payment_page', order_id=order.order_id)
                elif payment_method == 'Wallet':
                    messages.success(request, f"Successfully paid ₹{final_price} using your Wallet! Order placed successfully.")
                    return redirect('orders:success', order_id=order.order_id)
                else:
                    messages.success(request, "Order placed successfully!")
                    return redirect('orders:success', order_id=order.order_id)

        except ValueError as val_err:
            messages.error(request, str(val_err))
            return redirect('orders:checkout')
        except Exception as e:
            messages.error(request, f"An unexpected error occurred during order placement: {str(e)}")
            return redirect('orders:checkout')

    context = {
        'cart_items': cart_items,
        'addresses': addresses,
        'default_address': default_address,
        'subtotal': subtotal,
        'total_discount': total_discount,
        'coupon': coupon,
        'coupon_discount': coupon_discount,
        'tax': tax,
        'shipping_fee': shipping_fee,
        'final_price': final_price,
        'wallet_balance': wallet_balance,
    }
    return render(request, 'orders/checkout.html', context)

@login_required(login_url='/login/')
@never_cache
def payment_page(request, order_id):
    order = get_object_or_404(Order, order_id=order_id, user=request.user)
    
    # If already paid, go to success directly
    if order.payment_status == 'paid':
        messages.info(request, "This order is already paid.")
        return redirect('orders:success', order_id=order.order_id)
        
    # If payment method is not Razorpay, they shouldn't be here
    if order.payment_method != 'Razorpay':
        messages.error(request, "Invalid payment request.")
        return redirect('orders:detail', order_id=order.order_id)

    # Initialize Razorpay Client
    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    
    error_msg = None
    razorpay_order_id = order.razorpay_order_id
    
    # If there is no Razorpay order yet, create it
    if not razorpay_order_id:
        try:
            amount_in_paise = int(order.final_price * 100)
            if settings.DEBUG and settings.RAZORPAY_KEY_ID.startswith('rzp_test_') and amount_in_paise > 3000000:
                amount_in_paise = 3000000
            razorpay_order = client.order.create({
                "amount": amount_in_paise,
                "currency": "INR",
                "receipt": str(order.order_id),
                "payment_capture": 1
            })
            razorpay_order_id = razorpay_order['id']
            order.razorpay_order_id = razorpay_order_id
            order.save()
        except Exception as e:
            error_msg = f"Failed to initialize Razorpay checkout: {str(e)}"

    amount_in_paise = int(order.final_price * 100)
    if settings.DEBUG and settings.RAZORPAY_KEY_ID.startswith('rzp_test_') and amount_in_paise > 3000000:
        amount_in_paise = 3000000

    context = {
        'order': order,
        'razorpay_order_id': razorpay_order_id,
        'razorpay_key_id': settings.RAZORPAY_KEY_ID,
        'amount': amount_in_paise,
        'error_msg': error_msg,
    }
    return render(request, 'orders/payment.html', context)

@login_required(login_url='/login/')
@require_POST
def payment_verify(request):
    razorpay_payment_id = request.POST.get('razorpay_payment_id')
    razorpay_order_id = request.POST.get('razorpay_order_id')
    razorpay_signature = request.POST.get('razorpay_signature')
    order_id = request.POST.get('order_id')

    order = get_object_or_404(Order, order_id=order_id, user=request.user)
    
    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    
    try:
        # Cryptographic verification of payment signature
        client.utility.verify_payment_signature({
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature
        })
        
        # Mark as paid and processing
        with transaction.atomic():
            order.payment_status = 'paid'
            order.status = 'processing'
            order.razorpay_payment_id = razorpay_payment_id
            order.razorpay_signature = razorpay_signature
            order.save()
            
        messages.success(request, "Payment successful! Your order has been placed.")
        return redirect('orders:success', order_id=order.order_id)
    except Exception as e:
        order.payment_status = 'failed'
        order.save()
        messages.error(request, f"Payment verification failed: {str(e)}")
        return redirect('orders:payment_failure', order_id=order.order_id)

@login_required(login_url='/login/')
def order_success(request, order_id):
    order = get_object_or_404(Order, order_id=order_id, user=request.user)
    return render(request, 'orders/success.html', {'order': order})

@login_required(login_url='/login/')
def order_list(request):
    from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

    query = request.GET.get('q', '').strip()
    orders_qs = Order.objects.filter(user=request.user).order_by('-created_at')
    
    if query:
        orders_qs = orders_qs.filter(
            Q(order_id__icontains=query) |
            Q(items__product_name__icontains=query)
        ).distinct()
        
    # Paginate by 5 orders per page
    paginator = Paginator(orders_qs, 5)
    page_number = request.GET.get('page')
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    return render(request, 'orders/order_list.html', {
        'orders': page_obj,
        'search_query': query,
        'page_obj': page_obj
    })

@login_required(login_url='/login/')
def order_detail(request, order_id):
    order = get_object_or_404(Order, order_id=order_id, user=request.user)
    return render(request, 'orders/order_detail.html', {'order': order})

@login_required(login_url='/login/')
@require_POST
def cancel_order_item(request, order_id, item_id):
    order = get_object_or_404(Order, order_id=order_id, user=request.user)
    item = get_object_or_404(OrderItem, id=item_id, order=order)

    if order.status not in ['pending', 'processing']:
        messages.error(request, "This order cannot be cancelled as it is already shipped/delivered.")
        return redirect('orders:detail', order_id=order_id)

    reason = request.POST.get('cancel_reason', '').strip()
    old_final_price = order.final_price
    try:
        with transaction.atomic():
            item.is_cancelled = True
            item.cancel_reason = reason
            item.save()

            # Restore variant stock
            if item.variant:
                item.variant.stock += item.quantity
                item.variant.save()

            import decimal
            # Recalculate order totals based on remaining non-cancelled items
            active_items = order.items.filter(is_cancelled=False).exclude(return_status='approved')
            if active_items.exists():
                new_subtotal = sum(i.item_total for i in active_items)
                
                new_discount = decimal.Decimal('0.00')
                for i in active_items:
                    if i.product and i.product.original_price and i.product.original_price > i.product.price:
                        savings = (i.product.original_price - i.product.price) * i.quantity
                        new_discount += decimal.Decimal(str(savings))

                decimal_subtotal = decimal.Decimal(str(new_subtotal))
                discounted_sub = decimal_subtotal - new_discount
                new_tax = discounted_sub * decimal.Decimal('0.18') / decimal.Decimal('1.18')
                new_shipping = decimal.Decimal('0.00') if discounted_sub >= decimal.Decimal('3000.00') else decimal.Decimal('99.00')
                new_final = discounted_sub + new_shipping

                order.subtotal = new_subtotal
                order.discount = new_discount
                order.tax = new_tax
                order.shipping_fee = new_shipping
                order.final_price = new_final
                order.save()
            else:
                # If all items are cancelled, mark the entire order as cancelled
                order.status = 'cancelled'
                order.cancel_reason = reason or "All items cancelled by user."
                order.subtotal = decimal.Decimal('0.00')
                order.discount = decimal.Decimal('0.00')
                order.tax = decimal.Decimal('0.00')
                order.shipping_fee = decimal.Decimal('0.00')
                order.final_price = decimal.Decimal('0.00')
                order.save()

            # Refund to user's wallet if already paid!
            if order.payment_status == 'paid':
                refund_amount = decimal.Decimal(str(old_final_price)) - decimal.Decimal(str(order.final_price))
                if refund_amount > decimal.Decimal('0.00'):
                    from user_profile.models import Wallet, WalletTransaction
                    wallet_obj, _ = Wallet.objects.get_or_create(user=request.user)
                    wallet_decimal = decimal.Decimal(str(wallet_obj.balance))
                    wallet_obj.balance = wallet_decimal + refund_amount
                    wallet_obj.save()
                    
                    WalletTransaction.objects.create(
                        wallet=wallet_obj,
                        transaction_type='credit',
                        amount=refund_amount,
                        description=f"Refund for cancelled item: {item.product_name}",
                        order=order
                    )
                    messages.success(request, f"Cancelled {item.product_name} successfully. ₹{refund_amount} refunded directly to your Wallet!")
                else:
                    messages.success(request, f"Cancelled {item.product_name} successfully.")
            else:
                messages.success(request, f"Cancelled {item.product_name} successfully.")
    except Exception as e:
        messages.error(request, f"Could not cancel item: {str(e)}")

    return redirect('orders:detail', order_id=order_id)

@login_required(login_url='/login/')
@require_POST
def return_order(request, order_id):
    order = get_object_or_404(Order, order_id=order_id, user=request.user)

    if order.status != 'delivered':
        messages.error(request, "Only delivered orders can be returned.")
        return redirect('orders:detail', order_id=order_id)

    reason = request.POST.get('return_reason', '').strip()
    if not reason:
        messages.error(request, "A reason is mandatory to initiate a return.")
        return redirect('orders:detail', order_id=order_id)

    try:
        with transaction.atomic():
            order.status = 'return_requested'
            order.return_reason = reason
            order.save()

            messages.success(request, "Return request submitted successfully. Awaiting administrator confirmation.")
    except Exception as e:
        messages.error(request, f"Could not submit return request: {str(e)}")

    return redirect('orders:detail', order_id=order_id)

@login_required(login_url='/login/')
@require_POST
def return_order_item(request, order_id, item_id):
    order = get_object_or_404(Order, order_id=order_id, user=request.user)
    item = get_object_or_404(OrderItem, id=item_id, order=order)

    if order.status != 'delivered':
        messages.error(request, "Only items from delivered orders can be returned.")
        return redirect('orders:detail', order_id=order_id)

    if item.is_cancelled:
        messages.error(request, "Cannot return a cancelled item.")
        return redirect('orders:detail', order_id=order_id)

    if item.return_status != 'none':
        messages.error(request, "A return request has already been initiated or processed for this item.")
        return redirect('orders:detail', order_id=order_id)

    reason = request.POST.get('return_reason', '').strip()
    if not reason:
        messages.error(request, "A reason is mandatory to initiate an item return.")
        return redirect('orders:detail', order_id=order_id)

    try:
        with transaction.atomic():
            item.return_status = 'requested'
            item.return_reason = reason
            item.save()

            # If all active non-cancelled items are now requested/approved for return, update overall order status
            active_items = order.items.filter(is_cancelled=False)
            all_returned_or_requested = True
            for active_item in active_items:
                if active_item.return_status not in ['requested', 'approved']:
                    all_returned_or_requested = False
                    break
            
            if all_returned_or_requested:
                order.status = 'return_requested'
                order.save()

            messages.success(request, f"Return request for {item.product_name} submitted successfully. Awaiting administrator confirmation.")
    except Exception as e:
        messages.error(request, f"Could not submit return request: {str(e)}")

    return redirect('orders:detail', order_id=order_id)

@login_required(login_url='/login/')
def download_invoice(request, order_id):
    order = get_object_or_404(Order, order_id=order_id, user=request.user)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )
    story = []

    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'InvoiceTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=colors.HexColor('#0D59F2')
    )
    h2_style = ParagraphStyle(
        'InvoiceH2',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=colors.HexColor('#111111')
    )
    body_style = ParagraphStyle(
        'InvoiceBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#555555')
    )
    header_right_style = ParagraphStyle(
        'HeaderRight',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        alignment=2, # Right aligned
        textColor=colors.HexColor('#555555')
    )

    # 1. Header Section (Two-column layout)
    header_data = [
        [
            Paragraph("SoleVault", title_style),
            Paragraph(f"<b>INVOICE:</b> {order.order_id}<br/><b>Date:</b> {order.created_at.strftime('%d %b %Y %I:%M %p')}<br/><b>Payment:</b> {order.payment_method} ({order.payment_status.upper()})", header_right_style)
        ]
    ]
    header_table = Table(header_data, colWidths=[200, doc.width - 200])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('PADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 20))

    # Divider line
    divider = Table([[""]], colWidths=[doc.width], rowHeights=[2])
    divider.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#EEEEEE')),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(divider)
    story.append(Spacer(1, 15))

    # 2. Addresses Section (Two-column: Company Details vs Shipping Address)
    addr_data = [
        [
            Paragraph("<b>Seller Details:</b><br/>SoleVault India Pvt Ltd<br/>Tech Park, Phase II<br/>Kochi, Kerala, 682030<br/>support@solevault.com", body_style),
            Paragraph(f"<b>Shipping Address:</b><br/>{order.full_name}<br/>{order.address}<br/>{order.city}, {order.district}<br/>{order.state} - {order.pincode}<br/>Phone: {order.phone}", body_style)
        ]
    ]
    addr_table = Table(addr_data, colWidths=[240, doc.width - 240])
    addr_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('PADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(addr_table)
    story.append(Spacer(1, 25))

    # 3. Items Listing Table
    table_data = [
        ["Product Details", "Size", "Color", "Qty", "Unit Price", "Total"]
    ]
    
    for item in order.items.all():
        status_label = ""
        if item.is_cancelled:
            status_label = " (CANCELLED)"
        elif item.return_status == 'approved':
            status_label = " (RETURNED)"
        elif item.return_status == 'requested':
            status_label = " (RETURN REQUESTED)"
        elif item.return_status == 'rejected':
            status_label = " (RETURN REJECTED)"

        table_data.append([
            Paragraph(f"<b>{item.product_name}</b>{status_label}", body_style),
            item.size,
            item.color or "-",
            str(item.quantity),
            f"₹{item.price}",
            f"₹{item.item_total}"
        ])

    items_table = Table(table_data, colWidths=[180, 50, 60, 40, 80, 80])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0D59F2')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 10),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('ALIGN', (3,0), (-1,-1), 'RIGHT'),
        ('BOTTOMPADDING', (0,0), (-1,0), 8),
        ('TOPPADDING', (0,0), (-1,0), 8),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F9FAFB')]),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E5E7EB')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('FONTSIZE', (0,1), (-1,-1), 9),
    ]))
    story.append(items_table)
    story.append(Spacer(1, 20))

    # 4. Summary Totals Section
    summary_data = [
        [Paragraph("", body_style), "Subtotal:", f"₹{order.subtotal}"],
        [Paragraph("", body_style), "Saved Discount:", f"-₹{order.discount}"],
        [Paragraph("", body_style), "GST (18% included):", f"₹{order.tax:.2f}"],
        [Paragraph("", body_style), "Shipping Fee:", f"₹{order.shipping_fee}"],
        [Paragraph("", body_style), "Final Amount:", f"₹{order.final_price}"]
    ]
    
    summary_table = Table(summary_data, colWidths=[200, 180, 110])
    summary_table.setStyle(TableStyle([
        ('ALIGN', (1,0), (1,-1), 'LEFT'),
        ('ALIGN', (2,0), (2,-1), 'RIGHT'),
        ('FONTNAME', (1,-1), (2,-1), 'Helvetica-Bold'),
        ('LINEABOVE', (1,-1), (2,-1), 1.5, colors.HexColor('#0D59F2')),
        ('FONTSIZE', (1,0), (-1,-1), 9),
        ('FONTSIZE', (1,-1), (2,-1), 11),
        ('PADDING', (1,0), (-1,-1), 4),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 40))

    # Footer note
    footer_style = ParagraphStyle(
        'FooterNote',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=9,
        alignment=1, # Centered
        textColor=colors.HexColor('#888888')
    )
    story.append(Paragraph("Thank you for shopping with SoleVault! This is a system-generated electronic tax invoice.", footer_style))

    doc.build(story)
    
    pdf_output = buffer.getvalue()
    buffer.close()

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Invoice_{order.order_id}.pdf"'
    response.write(pdf_output)
    return response

@login_required(login_url='/login/')
@require_POST
def apply_coupon(request):
    code = request.POST.get('coupon_code', '').strip().upper()
    cart = Cart.objects.filter(user=request.user).first()
    if not cart or not cart.items.exists():
        messages.error(request, "Your cart is empty.")
        return redirect('orders:checkout')

    try:
        coupon = Coupon.objects.get(code=code)
        import decimal
        subtotal = decimal.Decimal(str(sum(item.total_price for item in cart.items.all())))
        valid, err_msg = coupon.is_valid(subtotal)
        if not valid:
            messages.error(request, err_msg)
        else:
            request.session['coupon_code'] = code
            messages.success(request, f"Coupon '{code}' applied successfully!")
    except Coupon.DoesNotExist:
        messages.error(request, "Invalid coupon code.")

    return redirect('orders:checkout')

@login_required(login_url='/login/')
@require_POST
def remove_coupon(request):
    request.session.pop('coupon_code', None)
    messages.success(request, "Coupon removed successfully.")
    return redirect('orders:checkout')

@login_required(login_url='/login/')
def payment_failure(request, order_id):
    order = get_object_or_404(Order, order_id=order_id, user=request.user)
    error_msg = request.GET.get('error', 'The transaction was declined by the bank or the modal was closed.')
    return render(request, 'orders/failure.html', {
        'order': order,
        'error_msg': error_msg
    })
