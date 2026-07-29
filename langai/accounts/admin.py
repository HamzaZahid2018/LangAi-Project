from django.contrib import admin
from .models import UserProfile, OTPVerification


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display  = ('user', 'is_verified', 'created_at')
    list_filter   = ('is_verified',)
    search_fields = ('user__username', 'user__email')


@admin.register(OTPVerification)
class OTPVerificationAdmin(admin.ModelAdmin):
    list_display  = ('user', 'otp', 'is_used', 'created_at')
    list_filter   = ('is_used',)
    search_fields = ('user__username',)
    readonly_fields = ('created_at',)