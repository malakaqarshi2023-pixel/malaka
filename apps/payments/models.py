from django.db import models
from django.conf import settings


class Payment(models.Model):
    STATUS_CHOICES = [
        ('pending',   'Kutilmoqda'),
        ('completed', 'To\'landi'),
        ('failed',    'Xato'),
        ('cancelled', 'Bekor qilindi'),
    ]
    METHOD_CHOICES = [
        ('payme', 'Payme'),
        ('click', 'Click'),
    ]

    user       = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payments')
    course     = models.ForeignKey('courses.Course', on_delete=models.CASCADE, related_name='payments')
    amount     = models.DecimalField(max_digits=12, decimal_places=2)
    method     = models.CharField(max_length=20, choices=METHOD_CHOICES)
    status     = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # To'lov tizimi ID lari
    transaction_id = models.CharField(max_length=100, blank=True)
    provider_order_id = models.CharField(max_length=100, blank=True, unique=True, null=True)

    created_at  = models.DateTimeField(auto_now_add=True)
    paid_at     = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'payments'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.full_name} | {self.course.title} | {self.amount} so\'m | {self.status}'


class PaymeTransaction(models.Model):
    """Payme webhook lari uchun log"""
    STATE_CHOICES = [
        (1,  'Yaratildi'),
        (2,  'To\'landi'),
        (-1, 'Bekor qilindi (to\'lovdan oldin)'),
        (-2, 'Bekor qilindi (to\'lovdan keyin)'),
    ]

    payment        = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='payme_transactions', null=True, blank=True)
    payme_id       = models.CharField(max_length=255, unique=True)
    account        = models.JSONField()
    amount         = models.BigIntegerField()   # tiyinda
    state          = models.SmallIntegerField(choices=STATE_CHOICES, default=1)
    created_time   = models.BigIntegerField()
    perform_time   = models.BigIntegerField(default=0)
    cancel_time    = models.BigIntegerField(default=0)
    reason         = models.SmallIntegerField(null=True, blank=True)

    class Meta:
        db_table = 'payme_transactions'

    def __str__(self):
        return f'Payme {self.payme_id} | state={self.state}'
