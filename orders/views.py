from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.http import HttpResponse
from django.db import transaction
from django.db.models import Q
from cart.models import Cart, CartItem
from user_profile.models import Address
from products.models import ProductVariant
from .models import Order, OrderItem

# PDF invoice generation imports
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import io

@login_required(login_url='/login/')
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
    
    # Calculate discounts if products have original prices
    total_discount = 0.00
    for item in cart_items:
        if item.product.original_price and item.product.original_price > item.product.price:
            savings = (item.product.original_price - item.product.price) * item.quantity
            total_discount += float(savings)
            
    # GST Included representation (18% GST)
    tax = float(subtotal) * 0.18 / 1.18

    # Flat shipping fee: free above 3000, else 99
    shipping_fee = 0.00 if subtotal >= 3000 else 99.00
    final_price = float(subtotal) + shipping_fee

    if request.method == 'POST':
        address_id = request.POST.get('address_id')
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
                    payment_method='COD',
                    payment_status='pending',
                    status='pending',
                    subtotal=subtotal,
                    discount=total_discount,
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
                        price=item.product.price,
                        item_total=item.total_price
                    )

                    # Deduct stock
                    if item.variant:
                        item.variant.stock -= item.quantity
                        item.variant.save()

                # Clear user's cart items
                cart.items.all().delete()
                
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
        'tax': tax,
        'shipping_fee': shipping_fee,
        'final_price': final_price,
    }
    return render(request, 'orders/checkout.html', context)

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
    
    try:
        with transaction.atomic():
            item.is_cancelled = True
            item.cancel_reason = reason
            item.save()

            # Restore variant stock
            if item.variant:
                item.variant.stock += item.quantity
                item.variant.save()

            # Recalculate order totals based on remaining non-cancelled items
            active_items = order.items.filter(is_cancelled=False)
            if active_items.exists():
                new_subtotal = sum(i.item_total for i in active_items)
                
                new_discount = 0.00
                for i in active_items:
                    if i.product and i.product.original_price and i.product.original_price > i.product.price:
                        savings = (i.product.original_price - i.product.price) * i.quantity
                        new_discount += float(savings)

                new_tax = float(new_subtotal) * 0.18 / 1.18
                new_shipping = 0.00 if new_subtotal >= 3000 else 99.00
                new_final = float(new_subtotal) + new_shipping

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
                order.subtotal = 0.00
                order.discount = 0.00
                order.tax = 0.00
                order.shipping_fee = 0.00
                order.final_price = 0.00
                order.save()

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
            order.status = 'returned'
            order.return_reason = reason
            order.save()

            # Restore stocks of all active (non-cancelled) items
            for item in order.items.filter(is_cancelled=False):
                if item.variant:
                    item.variant.stock += item.quantity
                    item.variant.save()

            messages.success(request, "Order returned successfully. Refund initiated.")
    except Exception as e:
        messages.error(request, f"Could not return order: {str(e)}")

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
        cancelled_label = " (CANCELLED)" if item.is_cancelled else ""
        table_data.append([
            Paragraph(f"<b>{item.product_name}</b>{cancelled_label}", body_style),
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
