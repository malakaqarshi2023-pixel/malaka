from django.contrib import admin
from .models import Payment, PaymeTransaction


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display  = ['user', 'course', 'amount', 'method', 'status', 'created_at', 'paid_at']
    list_filter   = ['status', 'method']
    search_fields = ['user__full_name', 'course__title', 'transaction_id']
    readonly_fields = ['created_at', 'paid_at']


@admin.register(PaymeTransaction)
class PaymeTransactionAdmin(admin.ModelAdmin):
    list_display  = ['payme_id', 'payment', 'amount', 'state', 'created_time']
    list_filter   = ['state']
    readonly_fields = ['payme_id', 'account', 'amount', 'created_time', 'perform_time', 'cancel_time']
