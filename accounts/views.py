from django.shortcuts import render, redirect
from django.contrib import messages
from .models import CustomUser
from django.contrib.auth.hashers import make_password
from django.contrib.auth import authenticate, login ,logout
import re
import random
from django.core.mail import send_mail
import time
from django.template.loader import render_to_string


def generate_otp():
    return str(random.randint(100000, 999999))

def send_otp(email, otp):
    subject = 'Your SoleVault Verification Code'
    message = f'Your OTP is {otp}'

    html_message = render_to_string('accounts/otp_email.html', {
        'otp': otp
    })

    send_mail(
        subject,
        message,
        'your_email@gmail.com',
        [email],
        html_message=html_message,
        fail_silently=False,
    )

def resend_otp(request):
    if 'signup_data' in request.session:
        email = request.session['signup_data']['email']
        otp = generate_otp()
        request.session['otp'] = otp
        request.session['otp_time'] = time.time()
        send_otp(email, otp)
        messages.success(request, "Verification code has been resent to your email.")
        return redirect('verify_otp')
    elif 'reset_email' in request.session:
        email = request.session['reset_email']
        otp = generate_otp()
        request.session['reset_otp'] = otp
        send_otp(email, otp)
        messages.success(request, "Password reset code has been resent to your email.")
        return redirect('forget_otp')
    else:
        messages.error(request, "Session expired. Please start the process again.")
        return redirect('signup') 
    
def signup(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        referral = request.POST.get('referral', '').strip()

        errors = []
        
        # Name validation
        if not first_name:
            errors.append("First name is required.")
        elif not first_name.isalpha():
            errors.append("First name must contain only letters.")
        elif len(first_name) < 2 or len(first_name) > 50:
            errors.append("First name must be between 2 and 50 characters.")

        if not last_name:
            errors.append("Last name is required.")
        elif not last_name.isalpha():
            errors.append("Last name must contain only letters.")
        elif len(last_name) < 2 or len(last_name) > 50:
            errors.append("Last name must be between 2 and 50 characters.")

        # Email validation
        if not email:
            errors.append("Email address is required.")
        else:
            email_pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
            if not re.match(email_pattern, email):
                errors.append("Invalid email address format.")
            elif CustomUser.objects.filter(email=email).exists():
                errors.append("An account with this email address already exists.")

        # Phone validation
        if not phone:
            errors.append("Phone number is required.")
        else:
            phone_pattern = r'^[6-9]\d{9}$'
            if not re.match(phone_pattern, phone):
                errors.append("Phone number must be a valid 10-digit number starting with 6-9.")

        # Password validation
        if not password:
            errors.append("Password is required.")
        else:
            password_pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&]).{8,}$'
            if not re.match(password_pattern, password):
                errors.append("Password must be at least 8 characters long and contain at least one uppercase letter, one lowercase letter, one digit, and one special character (@$!%*?&).")
            elif password != confirm_password:
                errors.append("Passwords do not match.")

        # Referral validation
        if referral:
            if not CustomUser.objects.filter(referral_code=referral).exists():
                errors.append("Invalid referral code.")

        if errors:
            for err in errors:
                messages.error(request, err)
            return render(request, 'accounts/signup.html', {
                'form_data': request.POST,
                'ref_code': referral
            }, status=400)

        # STORE DATA (NOT SAVE USER)
        request.session['signup_data'] = {
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'phone': phone,
            'password': password,
            'referral': referral,
        }

        # OTP
        otp = generate_otp()
        request.session['otp'] = otp
        request.session['otp_time'] = time.time()

        send_otp(email, otp)

        return redirect('verify_otp')

    ref_code = request.GET.get('ref', '')
    return render(request, 'accounts/signup.html', {'ref_code': ref_code})


def user_login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        user = authenticate(request, username=email, password=password)

        if user is not None:
            if user.is_blocked:
                messages.error(request, "Your account has been blocked.")
                return render(request, 'accounts/login.html', status=403)

            login(request, user)
            return redirect('/')  # home page

        else:
            messages.error(request, "Invalid credentials")
            return render(request, 'accounts/login.html', status=400)

    return render(request, 'accounts/login.html')

def user_logout(request):
    logout(request)
    request.session.flush()
    return redirect('login')

def verify_otp(request):
    if request.method == 'POST':

        entered_otp = ''.join([
            request.POST.get('otp_1', ''),
            request.POST.get('otp_2', ''),
            request.POST.get('otp_3', ''),
            request.POST.get('otp_4', ''),
            request.POST.get('otp_5', ''),
            request.POST.get('otp_6', ''),
        ])

        actual_otp = request.session.get('otp')
        otp_time = request.session.get('otp_time')

        # OTP expiry (5 min)
        if not otp_time or time.time() - otp_time > 300:
            messages.error(request, "OTP has expired. Please click 'Resend OTP' to receive a new one.")
            return render(request, 'accounts/verify_otp.html', status=400)

        if entered_otp == actual_otp:
            data = request.session.get('signup_data')
            if not data:
                messages.error(request, "Registration session data not found. Please sign up again.")
                return redirect('signup')

            import uuid
            import decimal
            from django.db import transaction
            from user_profile.models import Wallet, WalletTransaction

            with transaction.atomic():
                new_user_ref = f"SV-REF-{uuid.uuid4().hex[:6].upper()}"
                while CustomUser.objects.filter(referral_code=new_user_ref).exists():
                    new_user_ref = f"SV-REF-{uuid.uuid4().hex[:6].upper()}"

                from .adapters import generate_unique_username
                unique_uname = generate_unique_username(data['email'], data['first_name'], data['last_name'])

                new_user = CustomUser.objects.create(
                    username=unique_uname,
                    email=data['email'],
                    first_name=data['first_name'],
                    last_name=data['last_name'],
                    phone_number=data['phone'],
                    referral_code=new_user_ref,
                    password=make_password(data['password'])
                )

                ref_code_entered = data.get('referral', '').strip() if data.get('referral') else ''
                if ref_code_entered:
                    referrer = CustomUser.objects.filter(referral_code=ref_code_entered).first()
                    if referrer:
                        # Credit Referrer with ₹200
                        ref_wallet, _ = Wallet.objects.get_or_create(user=referrer)
                        ref_wallet_decimal = decimal.Decimal(str(ref_wallet.balance))
                        ref_wallet.balance = ref_wallet_decimal + decimal.Decimal('200.00')
                        ref_wallet.save()
                        WalletTransaction.objects.create(
                            wallet=ref_wallet,
                            transaction_type='credit',
                            amount=decimal.Decimal('200.00'),
                            description=f"Referral bonus for inviting {new_user.email}"
                        )

                        # Credit Referee (new user) with ₹100
                        new_wallet, _ = Wallet.objects.get_or_create(user=new_user)
                        new_wallet_decimal = decimal.Decimal(str(new_wallet.balance))
                        new_wallet.balance = new_wallet_decimal + decimal.Decimal('100.00')
                        new_wallet.save()
                        WalletTransaction.objects.create(
                            wallet=new_wallet,
                            transaction_type='credit',
                            amount=decimal.Decimal('100.00'),
                            description="Signup referral bonus"
                        )

            messages.success(request, "OTP verified successfully! Please login.")

            # clear session
            request.session.flush()

            return redirect('login')

        else:
            messages.error(request, "Invalid OTP. Please check the code and try again.")
            return render(request, 'accounts/verify_otp.html', status=400)

    return render(request, 'accounts/verify_otp.html')

def forget_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')

        # Check user exists
        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            messages.error(request, "Email not registered")
            return redirect('forget_password')

        # Generate OTP
        otp = generate_otp()

        # Store in session
        request.session['reset_email'] = email
        request.session['reset_otp'] = otp

        # Send email
        send_otp(email, otp)

        messages.success(request, "OTP sent to your email")
        return redirect('forget_otp')

    return render(request, 'accounts/forget_password.html')

def forget_otp(request):
    if request.method == 'POST':
        otp_digits = [
            request.POST.get('otp_1', ''),
            request.POST.get('otp_2', ''),
            request.POST.get('otp_3', ''),
            request.POST.get('otp_4', ''),
            request.POST.get('otp_5', ''),
            request.POST.get('otp_6', ''),
        ]
        entered_otp = ''.join(otp_digits)

        actual_otp = request.session.get('reset_otp')

        if entered_otp == actual_otp:
            messages.success(request, "OTP verified successfully")
            return redirect('reset_password')
        else:
            messages.error(request, "Invalid OTP")
            return redirect('forget_otp')

    return render(request, 'accounts/forget_otp.html')


def reset_password(request):
    if request.method == 'POST':
        password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if not password or not confirm_password:
            messages.error(request, "All fields are required")
            return redirect('reset_password')

        if password != confirm_password:
            messages.error(request, "Passwords do not match")
            return redirect('reset_password')

        email = request.session.get('reset_email')

        if not email:
            messages.error(request, "Session expired. Try again.")
            return redirect('forget_password')

        try:
            user = CustomUser.objects.get(email=email)
            user.set_password(password)
            user.save()

            # clear session
            request.session.flush()

            messages.success(request, "Password reset successful. Please login.")
            return redirect('login')

        except CustomUser.DoesNotExist:
            messages.error(request, "User not found")
            return redirect('forget_password')

    return render(request, 'accounts/reset_password.html')