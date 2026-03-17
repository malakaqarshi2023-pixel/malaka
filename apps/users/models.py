from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra):
        if not email:
            raise ValueError('Email majburiy')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra):
        extra.setdefault('is_staff', True)
        extra.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra)


class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [
        ('student',    'O\'quvchi'),
        ('instructor', 'O\'qituvchi'),
        ('admin',      'Admin'),
    ]

    email        = models.EmailField(unique=True)
    full_name    = models.CharField(max_length=150)
    phone        = models.CharField(max_length=20, blank=True)
    avatar       = models.ImageField(upload_to='avatars/', null=True, blank=True)
    role         = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    bio          = models.TextField(blank=True)
    is_active    = models.BooleanField(default=True)
    is_staff     = models.BooleanField(default=False)
    is_verified  = models.BooleanField(default=False)
    date_joined  = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS = ['full_name']

    class Meta:
        db_table = 'users'
        verbose_name = 'Foydalanuvchi'
        verbose_name_plural = 'Foydalanuvchilar'

    def __str__(self):
        return f'{self.full_name} <{self.email}>'

    @property
    def is_instructor(self):
        return self.role == 'instructor'


class OTPCode(models.Model):
    """Email tasdiqlash kodi"""
    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='otp_codes')
    code       = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used    = models.BooleanField(default=False)

    class Meta:
        db_table = 'otp_codes'

    def __str__(self):
        return f'{self.user.email} — {self.code}'
