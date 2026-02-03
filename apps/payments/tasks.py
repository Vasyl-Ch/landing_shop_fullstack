from celery import shared_task
from django.utils import timezone
from apps.orders.models import Order
from apps.payments.models import StripePayment
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def process_stripe_webhook(self, event_id, event_type, event_data):
    """
    Handles the Stripe webhook asynchronously.

    Options:
    - event_id: Stripe Event ID
    - event_type: Event type (e.g. 'checkout.session.completed')
    - event_data: Event Data (dict)
    """

    logger.info(f"Processing Stripe webhook: {event_type} ({event_id})")

    try:
        if StripePayment.objects.filter(stripe_event_id=event_id).exists():
            logger.warning(f"Event {event_id} already processed, skipping")
            return

        payment = StripePayment.objects.create(
            stripe_event_id=event_id,
            event_type=map_event_type(event_type),
            event_data=event_data,
        )

        if event_type == "checkout.session.completed":
            handle_checkout_session_completed(payment, event_data)
        elif event_type == "payment_intent.succeeded":
            handle_payment_intent_succeeded(payment, event_data)
        elif event_type == "payment_intent.payment_failed":
            handle_payment_intent_failed(payment, event_data)
        else:
            logger.info(f"Unhandled event type: {event_type}")

        payment.processed = True
        payment.processed_at = timezone.now()
        payment.save(update_fields=["processed", "processed_at"])

        logger.info(f"Successfully processed webhook: {event_id}")

    except Exception as exc:
        logger.error(f"Error processing webhook {event_id}: {str(exc)}")

        if "payment" in locals():
            payment.error_message = str(exc)
            payment.save(update_fields=["error_message"])

        raise self.retry(exc=exc, countdown=60)


def map_event_type(stripe_event_type):
    """Mape Stripe event type to our enum."""
    mapping = {
        "checkout.session.created": StripePayment.EventType.CHECKOUT_SESSION_CREATED,
        "checkout.session.completed": StripePayment.EventType.CHECKOUT_SESSION_COMPLETED,
        "payment_intent.succeeded": StripePayment.EventType.PAYMENT_INTENT_SUCCEEDED,
        "payment_intent.payment_failed": StripePayment.EventType.PAYMENT_INTENT_FAILED,
        "charge.succeeded": StripePayment.EventType.CHARGE_SUCCEEDED,
        "charge.failed": StripePayment.EventType.CHARGE_FAILED,
    }
    return mapping.get(stripe_event_type, StripePayment.EventType.OTHER)


def handle_checkout_session_completed(payment, event_data):
    """
    Handles the Checkout Session success event.
    """
    session = event_data.get("data", {}).get("object", {})

    payment.stripe_checkout_session_id = session.get("id")
    payment.stripe_payment_intent_id = session.get("payment_intent")
    payment.save(
        update_fields=["stripe_checkout_session_id", "stripe_payment_intent_id"]
    )

    order_id = session.get("metadata", {}).get("order_id")
    if not order_id:
        logger.error("No order_id in session metadata")
        return

    try:
        order = Order.objects.get(id=order_id)
        payment.order = order
        payment.save(update_fields=["order"])

        order.stripe_payment_intent_id = session.get("payment_intent")
        order.mark_as_paid()

        logger.info(f"Order {order.order_number} marked as paid")

        # Тут реализуем отправку email о подтверждении заказа
        # send_order_confirmation_email.delay(order.id)

    except Order.DoesNotExist:
        logger.error(f"Order with id {order_id} not found")


def handle_payment_intent_succeeded(payment, event_data):
    """
    Processes a successful payment (duplication for reliability).
    """
    intent = event_data.get("data", {}).get("object", {})
    payment.stripe_payment_intent_id = intent.get("id")
    payment.save(update_fields=["stripe_payment_intent_id"])

    logger.info(f'Payment intent succeeded: {intent.get("id")}')


def handle_payment_intent_failed(payment, event_data):
    """
    Processes an unsuccessful payment.
    """
    intent = event_data.get("data", {}).get("object", {})
    payment.stripe_payment_intent_id = intent.get("id")
    payment.save(update_fields=["stripe_payment_intent_id"])

    try:
        order = Order.objects.get(stripe_payment_intent_id=intent.get("id"))
        payment.order = order
        payment.save(update_fields=["order"])

        order.mark_as_failed()
        logger.warning(f"Order {order.order_number} marked as failed")

    except Order.DoesNotExist:
        logger.warning(f'Order not found for payment_intent {intent.get("id")}')
