"""
Click (Uzum Bank) to'lov tizimi integratsiyasi.
Hujjat: https://docs.click.uz
"""
import hashlib
from django.conf import settings
from .models import Payment


def make_md5(s: str) -> str:
    return hashlib.md5(s.encode()).hexdigest()


def verify_click_sign(data: dict) -> bool:
    """Click imzosini tekshirish"""
    sign_string = (
        f"{data.get('click_trans_id')}"
        f"{settings.CLICK_SERVICE_ID}"
        f"{settings.CLICK_SECRET_KEY}"
        f"{data.get('merchant_trans_id')}"
        f"{data.get('amount')}"
        f"{data.get('action')}"
        f"{data.get('sign_time')}"
    )
    return make_md5(sign_string) == data.get('sign_string', '')


def click_prepare(data: dict) -> dict:
    """
    Click Prepare - to'lovdan oldin buyurtmani tekshirish.
    Click bu URLni chaqiradi: /api/v1/payments/click/
    """
    if not verify_click_sign(data):
        return {'error': -1, 'error_note': 'SIGN CHECK FAILED!'}

    order_id = data.get('merchant_trans_id')
    amount   = float(data.get('amount', 0))

    try:
        payment = Payment.objects.get(id=order_id, status='pending')
    except Payment.DoesNotExist:
        return {'error': -5, 'error_note': 'User does not exist'}

    if abs(float(payment.amount) - amount) > 0.01:
        return {'error': -2, 'error_note': 'Incorrect parameter amount'}

    return {
        'click_trans_id':    data['click_trans_id'],
        'merchant_trans_id': order_id,
        'merchant_prepare_id': str(payment.id),
        'error':             0,
        'error_note':        'Success',
    }


def click_complete(data: dict) -> dict:
    """
    Click Complete - to'lov muvaffaqiyatli bo'lgandan keyin.
    """
    from django.utils import timezone
    from apps.courses.models import Enrollment

    if not verify_click_sign(data):
        return {'error': -1, 'error_note': 'SIGN CHECK FAILED!'}

    order_id = data.get('merchant_trans_id')
    error    = int(data.get('error', 0))

    try:
        payment = Payment.objects.get(id=order_id)
    except Payment.DoesNotExist:
        return {'error': -5, 'error_note': 'User does not exist'}

    if payment.status == 'completed':
        return {'error': -4, 'error_note': 'Already paid'}

    if error < 0:
        payment.status = 'failed'
        payment.save()
        return {'error': error, 'error_note': 'Transaction cancelled'}

    payment.status         = 'completed'
    payment.transaction_id = data.get('click_trans_id', '')
    payment.paid_at        = timezone.now()
    payment.save()

    # Kursg avtomatik yozish
    Enrollment.objects.get_or_create(student=payment.user, course=payment.course)

    return {
        'click_trans_id':    data['click_trans_id'],
        'merchant_trans_id': order_id,
        'merchant_confirm_id': str(payment.id),
        'error':             0,
        'error_note':        'Success',
    }
