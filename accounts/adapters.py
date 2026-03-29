# adapters.py
from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth import get_user_model

class MyAccountAdapter(DefaultAccountAdapter):
    def populate_username(self, request, user):
        user.username = user.email.split('@')[0]



User = get_user_model()

class MySocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        if sociallogin.user.email:
            try:
                user = User.objects.get(email=sociallogin.user.email)
                sociallogin.connect(request, user)
            except User.DoesNotExist:
                pass        