from django.urls import path
from . import views

urlpatterns = [
    path('initiate/', views.InitiatePaymentView.as_view(), name='payment_initiate'),
    path('payme/',    views.PaymeWebhookView.as_view(),    name='payme_webhook'),
    path('click/',    views.ClickWebhookView.as_view(),    name='click_webhook'),
    path('history/',  views.MyPaymentsView.as_view(),      name='payment_history'),
]
