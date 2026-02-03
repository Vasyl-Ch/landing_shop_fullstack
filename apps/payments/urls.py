from django.urls import path
from apps.payments import views

app_name = "payments"

urlpatterns = [
    path(
        "create-checkout/<int:order_id>/",
        views.create_checkout_session,
        name="create_checkout",
    ),
    path("success/<str:order_number>/", views.payment_success, name="payment_success"),
    path("cancel/<str:order_number>/", views.payment_cancel, name="payment_cancel"),
    path("webhook/", views.stripe_webhook, name="stripe_webhook"),
]
