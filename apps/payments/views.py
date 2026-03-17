from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.serializers import ModelSerializer

from apps.courses.models import Course
from .models import Payment
from . import payme_service, click_service


# ── Serializer ───────────────────────────────────────────────────────────────
class PaymentSerializer(ModelSerializer):
    class Meta:
        model  = Payment
        fields = ['id', 'course', 'amount', 'method', 'status', 'created_at', 'paid_at']
        read_only_fields = ['status', 'created_at', 'paid_at']


# ── To'lov boshlash ──────────────────────────────────────────────────────────
class InitiatePaymentView(APIView):
    """
    POST /api/v1/payments/initiate/
    Body: { "course_id": 1, "method": "payme" | "click" }
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        course_id = request.data.get('course_id')
        method    = request.data.get('method', 'payme')

        course = get_object_or_404(Course, id=course_id, is_published=True)

        if course.is_free:
            return Response({'error': 'Bu kurs bepul, to\'lov shart emas'},
                            status=status.HTTP_400_BAD_REQUEST)

        # Mavjud to'lovni tekshirish
        existing = Payment.objects.filter(
            user=request.user, course=course, status='completed'
        ).first()
        if existing:
            return Response({'error': 'Siz bu kursni allaqachon sotib olgansiz'},
                            status=status.HTTP_400_BAD_REQUEST)

        # Yangi to'lov yaratish
        payment = Payment.objects.create(
            user   = request.user,
            course = course,
            amount = course.price,
            method = method,
        )

        # To'lov URL ni qaytarish
        if method == 'payme':
            import base64, json
            params = base64.b64encode(
                json.dumps({'m': settings.PAYME_MERCHANT_ID, 'ac.order_id': payment.id,
                            'a': int(course.price * 100)}).encode()
            ).decode()
            pay_url = f"{settings.PAYME_URL}/{params}"
        else:  # click
            pay_url = (
                f"https://my.click.uz/services/pay?"
                f"service_id={settings.CLICK_SERVICE_ID}"
                f"&merchant_id={settings.CLICK_MERCHANT_ID}"
                f"&amount={course.price}"
                f"&transaction_param={payment.id}"
                f"&return_url={settings.FRONTEND_URL}/payment/success"
            )

        return Response({
            'payment_id': payment.id,
            'amount':     course.price,
            'method':     method,
            'pay_url':    pay_url,
        })


# ── Payme Webhook ────────────────────────────────────────────────────────────
class PaymeWebhookView(APIView):
    """
    POST /api/v1/payments/payme/
    Payme JSON-RPC webhook endpointi
    """
    permission_classes = [permissions.AllowAny]

    METHODS = {
        'CheckPerformTransaction': payme_service.check_perform_transaction,
        'CreateTransaction':       payme_service.create_transaction,
        'PerformTransaction':      payme_service.perform_transaction,
        'CancelTransaction':       payme_service.cancel_transaction,
        'CheckTransaction':        payme_service.check_transaction,
    }

    def post(self, request):
        if not payme_service.check_auth(request):
            return Response(
                payme_service.payme_error_response(None, {'code': -32504, 'message': 'Insufficient privilege'}),
                status=status.HTTP_403_FORBIDDEN
            )

        body      = request.data
        method    = body.get('method')
        params    = body.get('params', {})
        req_id    = body.get('id')

        handler = self.METHODS.get(method)
        if not handler:
            return Response(
                payme_service.payme_error_response(req_id, payme_service.PaymeError.METHOD_NOT_FOUND)
            )

        result = handler(params, req_id)
        return Response(result)


# ── Click Webhook ─────────────────────────────────────────────────────────────
class ClickWebhookView(APIView):
    """
    POST /api/v1/payments/click/
    Click prepare va complete endpointi
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        action = int(request.data.get('action', -1))
        if action == 0:
            result = click_service.click_prepare(request.data)
        elif action == 1:
            result = click_service.click_complete(request.data)
        else:
            result = {'error': -3, 'error_note': 'Action not found'}
        return Response(result)


# ── To'lovlar tarixi ─────────────────────────────────────────────────────────
class MyPaymentsView(generics.ListAPIView):
    """GET /api/v1/payments/history/ — Foydalanuvchi to'lovlari"""
    serializer_class   = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Payment.objects.filter(user=self.request.user).order_by('-created_at')
