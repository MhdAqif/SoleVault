from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    phone_number = models.CharField(max_length=15)
    profile_image = models.ImageField(upload_to='profile_images/', blank=True, null=True)
    is_blocked = models.BooleanField(default=False)
    referral_code = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return self.username