from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseAdmin
from .models import User, OTPCode


@admin.register(User)
class UserAdmin(BaseAdmin):
    list_display  = ['email', 'full_name', 'role', 'is_verified', 'is_active', 'date_joined']
    list_filter   = ['role', 'is_verified', 'is_active']
    search_fields = ['email', 'full_name', 'phone']
    ordering      = ['-date_joined']

    fieldsets = (
        ('Asosiy',    {'fields': ('email', 'password')}),
        ('Ma\'lumot', {'fields': ('full_name', 'phone', 'avatar', 'bio', 'role')}),
        ('Holat',     {'fields': ('is_active', 'is_verified', 'is_staff', 'is_superuser')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'full_name', 'password1', 'password2', 'role'),
        }),
    )


@admin.register(OTPCode)
class OTPAdmin(admin.ModelAdmin):
    list_display = ['user', 'code', 'is_used', 'created_at']
    list_filter  = ['is_used']
