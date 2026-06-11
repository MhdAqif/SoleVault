from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from .models import Address
import time
from accounts.views import generate_otp, send_otp

@login_required
def user_profile(request):
    user = request.user

    if request.method == "POST":
        full_name = request.POST.get("full_name")
        email = request.POST.get("email", "").strip()
        phone = request.POST.get("phone")
        photo = request.FILES.get("photo")
        remove_photo = request.POST.get("remove_photo")

        # Save standard fields first immediately
        if full_name:
            name_parts = full_name.split()
            user.first_name = name_parts[0]
            user.last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""

        user.phone_number = phone

        if remove_photo == "1":
            user.profile_image = None
        if photo:
            user.profile_image = photo

        user.save()

        # Check if email is changing
        if email and email != user.email:
            from accounts.models import CustomUser
            if CustomUser.objects.exclude(id=user.id).filter(email=email).exists():
                messages.error(request, "This email is already in use by another account.")
                return render(request, 'user_profile/profile.html')

            # Generate OTP & Store in Session
            otp = generate_otp()
            request.session['new_email_pending'] = email
            request.session['email_change_otp'] = otp
            request.session['email_change_otp_time'] = time.time()

            # Send OTP to new email address
            send_otp(email, otp)
            messages.success(request, f"Verification code sent to {email}. Please enter the OTP to confirm your email change.")
            return redirect('user_profile:verify_email_otp')

        messages.success(request, "Profile updated successfully.")
        return redirect('user_profile:profile')

    return render(request, 'user_profile/profile.html')

@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            messages.success(request, 'Your password was successfully updated!')
            return redirect('user_profile:profile')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'user_profile/change_password.html', {
        'form': form
    })

@login_required
def profile_edit(request):
    return redirect('user_profile:profile')

@login_required
def manage_address(request):
    addresses = Address.objects.filter(user=request.user)

    return render(request, 'user_profile/manage_address.html', {
        'addresses': addresses
    })

@login_required
def add_address(request):
    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        phone = request.POST.get('mobile_number') or request.POST.get('phone')
        address = request.POST.get('address')
        pincode = request.POST.get('pin_code') or request.POST.get('pincode')
        if not full_name or not phone or not address:
            messages.error(request, "Please fill all required fields")
            return redirect('user_profile:add_address')

        is_default = request.POST.get('is_default') == 'on'
        # If this is the user's first address, force it to be default
        if not Address.objects.filter(user=request.user).exists():
            is_default = True
        
        if is_default:
            Address.objects.filter(user=request.user).update(is_default=False)

        Address.objects.create(
            user=request.user,
            full_name=full_name,
            phone=phone,
            address=address,
            district=request.POST.get('district'),
            state=request.POST.get('state'),
            city=request.POST.get('city'),
            pincode=pincode,
            landmark=request.POST.get('landmark'),
            is_default=is_default,
        )

        messages.success(request, "Address added successfully.")
        next_url = request.POST.get('next') or request.GET.get('next')
        if next_url:
            return redirect(next_url)
        return redirect('user_profile:manage_address')

    return render(request, 'user_profile/add_address.html')

from django.http import JsonResponse
from django.views.decorators.http import require_POST

@login_required
@require_POST
def add_address_ajax(request):
    try:
        full_name = request.POST.get('full_name')
        phone = request.POST.get('phone') or request.POST.get('mobile_number')
        address = request.POST.get('address')
        city = request.POST.get('city')
        district = request.POST.get('district')
        state = request.POST.get('state')
        pincode = request.POST.get('pincode') or request.POST.get('pin_code')
        landmark = request.POST.get('landmark')
        is_default = request.POST.get('is_default') == 'on' or request.POST.get('is_default') == 'true'

        if not all([full_name, phone, address, city, district, state, pincode]):
            return JsonResponse({'success': False, 'error': 'All required fields must be filled.'})

        if not Address.objects.filter(user=request.user).exists():
            is_default = True

        if is_default:
            Address.objects.filter(user=request.user).update(is_default=False)

        new_addr = Address.objects.create(
            user=request.user,
            full_name=full_name,
            phone=phone,
            address=address,
            district=district,
            state=state,
            city=city,
            pincode=pincode,
            landmark=landmark,
            is_default=is_default
        )

        return JsonResponse({
            'success': True,
            'address': {
                'id': new_addr.id,
                'full_name': new_addr.full_name,
                'phone': new_addr.phone,
                'address': new_addr.address,
                'city': new_addr.city,
                'district': new_addr.district,
                'state': new_addr.state,
                'pincode': new_addr.pincode,
                'landmark': new_addr.landmark or '',
                'is_default': new_addr.is_default
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@require_POST
def edit_address_ajax(request, pk):
    try:
        address_obj = get_object_or_404(Address, id=pk, user=request.user)
        full_name = request.POST.get('full_name')
        phone = request.POST.get('phone') or request.POST.get('mobile_number')
        address = request.POST.get('address')
        city = request.POST.get('city')
        district = request.POST.get('district')
        state = request.POST.get('state')
        pincode = request.POST.get('pincode') or request.POST.get('pin_code')
        landmark = request.POST.get('landmark')
        is_default = request.POST.get('is_default') == 'on' or request.POST.get('is_default') == 'true'

        if not all([full_name, phone, address, city, district, state, pincode]):
            return JsonResponse({'success': False, 'error': 'All required fields must be filled.'})

        if not Address.objects.filter(user=request.user).exclude(id=pk).exists():
            is_default = True

        if is_default:
            Address.objects.filter(user=request.user).update(is_default=False)

        address_obj.full_name = full_name
        address_obj.phone = phone
        address_obj.address = address
        address_obj.city = city
        address_obj.district = district
        address_obj.state = state
        address_obj.pincode = pincode
        address_obj.landmark = landmark
        address_obj.is_default = is_default
        address_obj.save()

        return JsonResponse({
            'success': True,
            'address': {
                'id': address_obj.id,
                'full_name': address_obj.full_name,
                'phone': address_obj.phone,
                'address': address_obj.address,
                'city': address_obj.city,
                'district': address_obj.district,
                'state': address_obj.state,
                'pincode': address_obj.pincode,
                'landmark': address_obj.landmark or '',
                'is_default': address_obj.is_default
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def edit_address(request, pk):
    address = get_object_or_404(Address, id=pk, user=request.user)

    if request.method == 'POST':
        is_default = request.POST.get('is_default') == 'on'
        # If it is the only address, force it to remain default
        if not Address.objects.filter(user=request.user).exclude(id=pk).exists():
            is_default = True

        if is_default:
            Address.objects.filter(user=request.user).update(is_default=False)

        address.full_name = request.POST.get('full_name')
        address.phone = request.POST.get('phone') or request.POST.get('mobile_number')
        address.address = request.POST.get('address')
        address.district = request.POST.get('district')
        address.state = request.POST.get('state')
        address.city = request.POST.get('city')
        address.pincode = request.POST.get('pincode') or request.POST.get('pin_code')
        address.landmark = request.POST.get('landmark')
        address.is_default = is_default
        address.save()

        messages.success(request, "Address updated successfully.")
        next_url = request.POST.get('next') or request.GET.get('next')
        if next_url:
            return redirect(next_url)
        return redirect('user_profile:manage_address')

    return render(request, 'user_profile/edit_address.html', {
        'address': address
    })

@login_required
def delete_address(request, pk):
    address = get_object_or_404(Address, id=pk, user=request.user)

    if request.method == 'POST':
        was_default = address.is_default
        address.delete()
        
        # If we deleted the default address, set another address as default
        if was_default:
            first_addr = Address.objects.filter(user=request.user).first()
            if first_addr:
                first_addr.is_default = True
                first_addr.save()
                
        messages.success(request, "Address deleted successfully.")
        return redirect('user_profile:manage_address')

    return render(request, 'user_profile/delete_address.html', {
        'address': address
    })

@login_required
def set_default_address(request, pk):
    address = get_object_or_404(Address, id=pk, user=request.user)
    Address.objects.filter(user=request.user).update(is_default=False)
    address.is_default = True
    address.save()
    messages.success(request, f"Set {address.full_name}'s address as default.")
    
    referer = request.META.get('HTTP_REFERER', '')
    if 'checkout' in referer:
        return redirect('orders:checkout')
    return redirect('user_profile:manage_address')

@login_required
def verify_email_otp(request):
    new_email = request.session.get('new_email_pending')
    actual_otp = request.session.get('email_change_otp')
    otp_time = request.session.get('email_change_otp_time')

    if not new_email or not actual_otp or not otp_time:
        messages.error(request, "No pending email change request found.")
        return redirect('user_profile:profile')

    if request.method == 'POST':
        entered_otp = ''.join([
            request.POST.get('otp_1', ''),
            request.POST.get('otp_2', ''),
            request.POST.get('otp_3', ''),
            request.POST.get('otp_4', ''),
            request.POST.get('otp_5', ''),
            request.POST.get('otp_6', ''),
        ])

        # Expiry check (5 mins)
        if time.time() - otp_time > 300:
            messages.error(request, "OTP expired. Please try updating your email again.")
            request.session.pop('new_email_pending', None)
            request.session.pop('email_change_otp', None)
            request.session.pop('email_change_otp_time', None)
            return redirect('user_profile:profile')

        if entered_otp == actual_otp:
            user = request.user
            user.email = new_email
            user.username = new_email
            user.save()

            messages.success(request, f"Email updated successfully to {new_email}!")
            request.session.pop('new_email_pending', None)
            request.session.pop('email_change_otp', None)
            request.session.pop('email_change_otp_time', None)
            return redirect('user_profile:profile')
        else:
            messages.error(request, "Invalid OTP. Please try again.")

    return render(request, 'user_profile/verify_email_otp.html', {'new_email': new_email})

@login_required
def user_coupons(request):
    from django.utils import timezone
    from orders.models import Coupon
    now = timezone.now()
    active_coupons = Coupon.objects.filter(
        active=True,
        valid_from__lte=now,
        valid_to__gte=now
    )
    return render(request, 'user_profile/coupons.html', {
        'coupons': active_coupons
    })

@login_required
def user_wallet(request):
    from .models import Wallet
    wallet, created = Wallet.objects.get_or_create(user=request.user)
    transactions = wallet.transactions.all().order_by('-created_at')
    return render(request, 'user_profile/wallet.html', {
        'wallet': wallet,
        'transactions': transactions
    })


@login_required
def user_referral(request):
    import uuid
    user = request.user
    if not user.referral_code:
        new_user_ref = f"SV-REF-{uuid.uuid4().hex[:6].upper()}"
        while user.__class__.objects.filter(referral_code=new_user_ref).exists():
            new_user_ref = f"SV-REF-{uuid.uuid4().hex[:6].upper()}"
        user.referral_code = new_user_ref
        user.save()
    
    # Construct full referral link
    base_url = request.build_absolute_uri('/signup/')
    referral_link = f"{base_url}?ref={user.referral_code}"
    
    return render(request, 'user_profile/referral.html', {
        'referral_code': user.referral_code,
        'referral_link': referral_link,
    })


@login_required
def wallet_topup_init(request):
    import razorpay
    import decimal
    from django.conf import settings
    
    if request.method != 'POST':
        return redirect('user_profile:wallet')
        
    amount_str = request.POST.get('amount', '').strip()
    try:
        amount = decimal.Decimal(amount_str)
        if amount <= 0:
            messages.error(request, "Amount must be greater than zero.")
            return redirect('user_profile:wallet')
    except (ValueError, decimal.InvalidOperation):
        messages.error(request, "Please enter a valid deposit amount.")
        return redirect('user_profile:wallet')
        
    # Initialize Razorpay client
    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    
    # Amount in paisa
    amount_paisa = int(amount * 100)
    if settings.DEBUG and settings.RAZORPAY_KEY_ID.startswith('rzp_test_') and amount_paisa > 3000000:
        amount_paisa = 3000000
        
    try:
        razorpay_order = client.order.create({
            'amount': amount_paisa,
            'currency': 'INR',
            'payment_capture': 1
        })
        
        # Save amount and Razorpay order ID in session
        request.session['topup_amount'] = str(amount)
        request.session['topup_razorpay_order_id'] = razorpay_order['id']
        
        context = {
            'razorpay_order_id': razorpay_order['id'],
            'razorpay_key_id': settings.RAZORPAY_KEY_ID,
            'amount': amount,
            'amount_paisa': amount_paisa,
            'user': request.user,
        }
        return render(request, 'user_profile/wallet_payment.html', context)
        
    except Exception as e:
        messages.error(request, f"Failed to initialize payment gateway: {str(e)}")
        return redirect('user_profile:wallet')


@login_required
def wallet_topup_verify(request):
    import razorpay
    import decimal
    from django.conf import settings
    from django.db import transaction
    from .models import Wallet, WalletTransaction
    
    if request.method != 'POST':
        return redirect('user_profile:wallet')
        
    razorpay_payment_id = request.POST.get('razorpay_payment_id')
    razorpay_order_id = request.POST.get('razorpay_order_id')
    razorpay_signature = request.POST.get('razorpay_signature')
    
    session_order_id = request.session.get('topup_razorpay_order_id')
    amount_str = request.session.get('topup_amount')
    
    if not session_order_id or not amount_str or razorpay_order_id != session_order_id:
        messages.error(request, "Session expired or transaction mismatch.")
        return redirect('user_profile:wallet')
        
    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    
    try:
        # Verify payment signature
        client.utility.verify_payment_signature({
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature
        })
        
        # Atomically credit wallet
        amount = decimal.Decimal(amount_str)
        with transaction.atomic():
            wallet, created = Wallet.objects.get_or_create(user=request.user)
            wallet.balance += amount
            wallet.save()
            
            WalletTransaction.objects.create(
                wallet=wallet,
                transaction_type='credit',
                amount=amount,
                description=f"Deposited funds via Razorpay (Ref: {razorpay_payment_id})"
            )
            
        # Clear sessions
        request.session.pop('topup_amount', None)
        request.session.pop('topup_razorpay_order_id', None)
        
        messages.success(request, f"Successfully deposited ₹{amount:.2f} to your wallet!")
        
    except Exception as e:
        messages.error(request, "Payment signature verification failed. Deposit unsuccessful.")
        
    return redirect('user_profile:wallet')
