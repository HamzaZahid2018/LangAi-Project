from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import random
import string
class UserProfile(models.Model):
    user        = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    is_verified = models.BooleanField(default=False)
    bio         = models.TextField(blank=True, null=True, max_length=300)
    avatar      = models.ImageField(upload_to='avatars/', null=True, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} — Profile"

    def get_avatar_url(self):
        if self.avatar:
            return self.avatar.url
        return None
class OTPVerification(models.Model):
    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='otps')
    otp        = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used    = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'OTP Verification'

    def __str__(self):
        return f"OTP({self.otp}) for {self.user.username}"

    def is_valid(self):
        """OTP expires after 1 minute"""
        expiry = self.created_at + timedelta(minutes=1)
        return (not self.is_used) and (timezone.now() < expiry)

    def time_remaining(self):
        expiry = self.created_at + timedelta(minutes=1)
        remaining = expiry - timezone.now()
        return max(int(remaining.total_seconds()), 0)

    @classmethod
    def generate_otp(cls):
        return ''.join(random.choices(string.digits, k=6))

    @classmethod
    def create_for_user(cls, user):
        # Invalidate all previous OTPs
        cls.objects.filter(user=user, is_used=False).update(is_used=True)
        otp_code = cls.generate_otp()
        return cls.objects.create(user=user, otp=otp_code)