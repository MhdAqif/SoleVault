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
    email = request.session.get('email')
    otp = generate_otp()

    request.session['otp'] = otp

    send_otp(email, otp)
    # logic to resend OTP
    messages.success(request, "OTP has been resent.")

    return redirect('verify-otp') 
    
def signup(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        referral = request.POST.get('referral')

        # validations
        if password != confirm_password:
            messages.error(request, "Passwords do not match")
            return redirect('signup')

        pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&]).{8,}$'
        if not re.match(pattern, password):
            messages.error(request, "Password must be strong")
            return redirect('signup')

        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, "Email already exists")
            return redirect('signup')

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

    return render(request, 'accounts/signup.html')


def user_login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        user = authenticate(request, username=email, password=password)

        if user is not None:
            if user.is_blocked:
                messages.error(request, "Your account is blocked")
                return redirect('login')

            login(request, user)
            return redirect('/')  # home page

        else:
            messages.error(request, "Invalid credentials")

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
        if time.time() - otp_time > 300:
            messages.error(request, "OTP expired")
            return redirect('signup')

        if entered_otp == actual_otp:
            data = request.session.get('signup_data')

            CustomUser.objects.create(
                username=data['email'],
                email=data['email'],
                first_name=data['first_name'],
                last_name=data['last_name'],
                phone_number=data['phone'],
                referral_code=data['referral'],
                password=make_password(data['password'])
            )

            messages.success(request, "OTP verified successfully! Please login.")

            # clear session
            request.session.flush()

            return redirect('login')

        else:
            messages.error(request, "Invalid OTP")
            return redirect('verify_otp')

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