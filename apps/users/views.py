import random
from django.core.mail import send_mail
from django.conf import settings
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import User, OTPCode
from .serializers import (
    RegisterSerializer, UserProfileSerializer,
    ChangePasswordSerializer, PublicUserSerializer,
)


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access':  str(refresh.access_token),
    }


class RegisterView(generics.CreateAPIView):
    """POST /api/v1/auth/register/ — Ro'yxatdan o'tish"""
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # OTP yuborish
        code = str(random.randint(100000, 999999))
        OTPCode.objects.create(user=user, code=code)
        send_mail(
            'EduZen — Email tasdiqlash',
            f'Tasdiqlash kodingiz: {code}\n\nKod 10 daqiqa davomida amal qiladi.',
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=True,
        )

        tokens = get_tokens_for_user(user)
        return Response({
            'message': 'Ro\'yxatdan o\'tdingiz. Email tasdiqlang.',
            'user': UserProfileSerializer(user).data,
            **tokens,
        }, status=status.HTTP_201_CREATED)


class VerifyEmailView(APIView):
    """POST /api/v1/auth/verify-email/ — Email tasdiqlash"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        code = request.data.get('code')
        otp  = OTPCode.objects.filter(
            user=request.user, code=code, is_used=False
        ).order_by('-created_at').first()

        if not otp:
            return Response({'error': 'Kod noto\'g\'ri yoki muddati o\'tgan'},
                            status=status.HTTP_400_BAD_REQUEST)

        otp.is_used = True
        otp.save()
        request.user.is_verified = True
        request.user.save()
        return Response({'message': 'Email tasdiqlandi ✓'})


class LoginView(TokenObtainPairView):
    """POST /api/v1/auth/login/ — Kirish (JWT)"""
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            email = request.data.get('email')
            user  = User.objects.get(email=email)
            response.data['user'] = UserProfileSerializer(user).data
        return response


class LogoutView(APIView):
    """POST /api/v1/auth/logout/ — Chiqish"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            token = RefreshToken(request.data['refresh'])
            token.blacklist()
        except Exception:
            pass
        return Response({'message': 'Chiqildingiz'})


class ProfileView(generics.RetrieveUpdateAPIView):
    """GET/PATCH /api/v1/auth/profile/ — Profil"""
    serializer_class   = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class ChangePasswordView(APIView):
    """POST /api/v1/auth/change-password/ — Parol o'zgartirish"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()
        return Response({'message': 'Parol o\'zgartirildi'})


class PublicProfileView(generics.RetrieveAPIView):
    """GET /api/v1/auth/users/<id>/ — Boshqa foydalanuvchi profili"""
    queryset           = User.objects.filter(is_active=True)
    serializer_class   = PublicUserSerializer
    permission_classes = [permissions.AllowAny]
