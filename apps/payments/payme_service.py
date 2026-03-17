"""
Payme (PayCom) to'lov tizimi integratsiyasi.
Hujjat: https://developer.paycom.uz/docs
"""
import base64
import time
from django.conf import settings
from .models import Payment, PaymeTransaction


# ── Xato kodlari ────────────────────────────────────────────────────────────
class PaymeError:
    PARSE_ERROR          = {'code': -32700, 'message': {'ru': 'Ошибка разбора JSON'}}
    METHOD_NOT_FOUND     = {'code': -32601, 'message': {'ru': 'Метод не найден'}}
    INVALID_PARAMS       = {'code': -32602, 'message': {'ru': 'Неверные параметры'}}
    INTERNAL_ERROR       = {'code': -32603, 'message': {'ru': 'Внутренняя ошибка'}}
    INSUFFICIENT_FUNDS   = {'code': -31001, 'message': {'ru': 'Недостаточно средств'}}
    TRANSACTION_NOT_FOUND= {'code': -31003, 'message': {'ru': 'Транзакция не найдена'}}
    ALREADY_DONE         = {'code': -31060, 'message': {'ru': 'Транзакция уже завершена'}}
    ORDER_NOT_FOUND      = {'code': -31050, 'message': {'ru': 'Заказ не найден'}}
    CANT_PERFORM         = {'code': -31008, 'message': {'ru': 'Не возможно выполнить операцию'}}


def check_auth(request) -> bool:
    """Basic Auth tekshiruvi"""
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Basic '):
        return False
    try:
        decoded = base64.b64decode(auth_header[6:]).decode('utf-8')
        _, key  = decoded.split(':', 1)
        return key == settings.PAYME_SECRET_KEY
    except Exception:
        return False


def payme_error_response(request_id, error: dict):
    return {
        'jsonrpc': '2.0',
        'id':      request_id,
        'error':   error,
    }


def payme_success_response(request_id, result: dict):
    return {
        'jsonrpc': '2.0',
        'id':      request_id,
        'result':  result,
    }


# ── Asosiy metodlar ──────────────────────────────────────────────────────────

def check_perform_transaction(params, request_id):
    """Buyurtma mavjudligini tekshirish"""
    account = params.get('account', {})
    order_id = account.get('order_id')
    amount   = params.get('amount')

    try:
        payment = Payment.objects.get(id=order_id, status='pending')
    except Payment.DoesNotExist:
        return payme_error_response(request_id, PaymeError.ORDER_NOT_FOUND)

    # Miqdorni tekshirish (Payme tiyinda yuboradi)
    expected = int(payment.amount * 100)
    if amount != expected:
        return payme_error_response(request_id, PaymeError.INVALID_PARAMS)

    return payme_success_response(request_id, {'allow': True})


def create_transaction(params, request_id):
    """Tranzaksiya yaratish"""
    payme_id = params.get('id')
    account  = params.get('account', {})
    amount   = params.get('amount')
    time_ms  = params.get('time')
    order_id = account.get('order_id')

    # Mavjud tranzaksiyani tekshirish
    existing = PaymeTransaction.objects.filter(payme_id=payme_id).first()
    if existing:
        if existing.state != 1:
            return payme_error_response(request_id, PaymeError.CANT_PERFORM)
        return payme_success_response(request_id, {
            'create_time': existing.created_time,
            'transaction': str(existing.id),
            'state':       existing.state,
        })

    try:
        payment = Payment.objects.get(id=order_id, status='pending')
    except Payment.DoesNotExist:
        return payme_error_response(request_id, PaymeError.ORDER_NOT_FOUND)

    expected = int(payment.amount * 100)
    if amount != expected:
        return payme_error_response(request_id, PaymeError.INVALID_PARAMS)

    txn = PaymeTransaction.objects.create(
        payment      = payment,
        payme_id     = payme_id,
        account      = account,
        amount       = amount,
        state        = 1,
        created_time = time_ms,
    )

    return payme_success_response(request_id, {
        'create_time': txn.created_time,
        'transaction': str(txn.id),
        'state':       txn.state,
    })


def perform_transaction(params, request_id):
    """To'lovni amalga oshirish"""
    from django.utils import timezone
    from apps.courses.models import Enrollment

    payme_id = params.get('id')
    try:
        txn = PaymeTransaction.objects.get(payme_id=payme_id)
    except PaymeTransaction.DoesNotExist:
        return payme_error_response(request_id, PaymeError.TRANSACTION_NOT_FOUND)

    if txn.state == 2:
        return payme_success_response(request_id, {
            'perform_time': txn.perform_time,
            'transaction':  str(txn.id),
            'state':        txn.state,
        })

    if txn.state != 1:
        return payme_error_response(request_id, PaymeError.CANT_PERFORM)

    now_ms = int(time.time() * 1000)
    txn.state        = 2
    txn.perform_time = now_ms
    txn.save()

    # To'lov va Enrollment yangilash
    payment = txn.payment
    payment.status = 'completed'
    payment.paid_at = timezone.now()
    payment.save()

    Enrollment.objects.get_or_create(student=payment.user, course=payment.course)

    return payme_success_response(request_id, {
        'perform_time': now_ms,
        'transaction':  str(txn.id),
        'state':        2,
    })


def cancel_transaction(params, request_id):
    """Tranzaksiyani bekor qilish"""
    payme_id = params.get('id')
    reason   = params.get('reason')

    try:
        txn = PaymeTransaction.objects.get(payme_id=payme_id)
    except PaymeTransaction.DoesNotExist:
        return payme_error_response(request_id, PaymeError.TRANSACTION_NOT_FOUND)

    now_ms = int(time.time() * 1000)

    if txn.state == 1:
        txn.state       = -1
        txn.cancel_time = now_ms
        txn.reason      = reason
        txn.save()
        if txn.payment:
            txn.payment.status = 'cancelled'
            txn.payment.save()

    elif txn.state == 2:
        # To'langan bo'lsa va qaytarish mumkin bo'lsa
        txn.state       = -2
        txn.cancel_time = now_ms
        txn.reason      = reason
        txn.save()
        if txn.payment:
            txn.payment.status = 'cancelled'
            txn.payment.save()

    return payme_success_response(request_id, {
        'cancel_time': txn.cancel_time,
        'transaction': str(txn.id),
        'state':       txn.state,
    })


def check_transaction(params, request_id):
    payme_id = params.get('id')
    try:
        txn = PaymeTransaction.objects.get(payme_id=payme_id)
    except PaymeTransaction.DoesNotExist:
        return payme_error_response(request_id, PaymeError.TRANSACTION_NOT_FOUND)

    return payme_success_response(request_id, {
        'create_time':  txn.created_time,
        'perform_time': txn.perform_time,
        'cancel_time':  txn.cancel_time,
        'transaction':  str(txn.id),
        'state':        txn.state,
        'reason':       txn.reason,
    })
