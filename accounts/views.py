from django.shortcuts import render, redirect
from django.contrib import messages
from .models import CustomUser
from django.contrib.auth.hashers import make_password
from django.contrib.auth import authenticate, login ,logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
import re


def signup(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        referral = request.POST.get('referral')

        #PASSWORD VALIDATION
        if password != confirm_password:
            messages.error(request, "Passwords do not match")
            return redirect('signup')
        
        pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&]).{8,}$'
        if not re.match(pattern, password):
            messages.error(request, "Password must be strong ")
            return redirect('signup')
        
        # E-MAIL VALIDATION
        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, "Email already exists")
            return redirect('signup')
        if not email or not password:
            messages.error(request, "All fields are required ")
            return redirect('signup')

        # CREATE USER
        user = CustomUser.objects.create(
            username=email,
            email=email,
            first_name=first_name,
            last_name=last_name,
            phone_number=phone,
            referral_code=referral,
            password=make_password(password)
        )

        messages.success(request, "Account created successfully")
        return redirect('login')

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
    return redirect('login')

def verify_otp(request):
    return render(request,'accounts/verify_otp.html')

def forget_password(request):
    return render(request,'accounts/forget_password.html')

def forget_otp(request):
    return render(request,'accounts/forget_otp.html')

def reset_password(request):
    return render(request,'accounts/reset_password.html')