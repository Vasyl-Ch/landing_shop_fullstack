from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.utils.translation import gettext as _
from apps.orders.models import Order
from apps.payments.services import StripeService
from apps.payments.tasks import process_stripe_webhook
import logging

logger = logging.getLogger(__name__)


def create_checkout_session(request, order_id):
    """
    Creates Stripe Checkout Session and redirect to Stripe.
    """
    order = get_object_or_404(Order, id=order_id)

    if order.status == Order.Status.PAID:
        messages.warning(request, _("Этот заказ уже оплачен"))
        return redirect("orders:order_detail", order_number=order.order_number)

    try:
        session = StripeService.create_checkout_session(order, request)

        return redirect(session.url, code=303)

    except Exception as e:
        logger.error(f"Error creating checkout session: {str(e)}")
        messages.error(request, _("Ошибка при создании платёжной сессии"))
        return redirect("orders:order_detail", order_number=order.order_number)


def payment_success(request, order_number):
    """
    Successful payment page.
    """
    order = get_object_or_404(Order, order_number=order_number)

    context = {
        "order": order,
        "title": _("Оплата успешна"),
    }
    return render(request, "payments/success.html", context)


def payment_cancel(request, order_number):
    """
    Payment cancellation page.
    """
    order = get_object_or_404(Order, order_number=order_number)

    context = {
        "order": order,
        "title": _("Оплата отменена"),
    }
    return render(request, "payments/cancel.html", context)


@csrf_exempt
@require_POST
def stripe_webhook(request):
    """
    Webhook endpoint to receive events from Stripe.

    IMPORTANT: @csrf_exempt necessary, because. Stripe can't send a CSRF token.
    Security is provided by webhook secret signature verification.
    """
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")

    if not sig_header:
        logger.warning("Webhook received without signature")
        return HttpResponse("No signature", status=400)

    try:
        event = StripeService.construct_webhook_event(payload, sig_header)

        logger.info(f'Received Stripe webhook: {event["type"]} ({event["id"]})')

        process_stripe_webhook.delay(
            event_id=event["id"], event_type=event["type"], event_data=event
        )

        return HttpResponse("Webhook received", status=200)

    except ValueError as e:
        logger.error(f"Invalid webhook payload: {str(e)}")
        return HttpResponse(f"Invalid payload: {str(e)}", status=400)

    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
        return HttpResponse(f"Webhook error: {str(e)}", status=400)
