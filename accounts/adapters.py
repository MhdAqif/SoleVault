# adapters.py
from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()

def generate_unique_username(email, first_name="", last_name=""):
    base = ""
    if email:
        base = email.split('@')[0]
    elif first_name:
        base = f"{first_name}{last_name}".lower()
    
    base = "".join(c for c in base if c.isalnum())
    if not base:
        base = "user"
        
    username = base
    counter = 1
    while User.objects.filter(username=username).exists():
        username = f"{base}{counter}"
        counter += 1
    return username

def generate_unique_referral_code():
    code = f"SV-REF-{uuid.uuid4().hex[:6].upper()}"
    while User.objects.filter(referral_code=code).exists():
        code = f"SV-REF-{uuid.uuid4().hex[:6].upper()}"
    return code

class MyAccountAdapter(DefaultAccountAdapter):
    def populate_username(self, request, user):
        user.username = generate_unique_username(user.email, user.first_name, user.last_name)

class MySocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        if sociallogin.user.email:
            try:
                user = User.objects.get(email=sociallogin.user.email)
                sociallogin.connect(request, user)
            except User.DoesNotExist:
                pass

    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)
        user.username = generate_unique_username(user.email, user.first_name, user.last_name)
        if not user.referral_code:
            user.referral_code = generate_unique_referral_code()
        return user