import os

import stripe
from django.conf import settings
from django.urls import reverse
from decimal import Decimal
from dotenv import load_dotenv

load_dotenv()

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")


class StripeService:
    """
    Service for working with Stripe API.
    """

    @staticmethod
    def create_checkout_session(order, request):
        """
        Creates a Stripe Checkout Session for the order.

        Options:
        - order: Order object
        - request: Django request (to build the URL)

        Returns: Stripe Session object
        """

        line_items = []
        for item in order.items.all():
            line_items.append(
                {
                    "price_data": {
                        "currency": "rub",
                        "product_data": {
                            "name": item.product_name,
                            "description": f"Товар из заказа #{order.order_number}",
                        },
                        "unit_amount": int(item.product_price * 100),
                    },
                    "quantity": item.quantity,
                }
            )

        if order.shipping_cost > 0:
            line_items.append(
                {
                    "price_data": {
                        "currency": "rub",
                        "product_data": {
                            "name": "Доставка",
                        },
                        "unit_amount": int(order.shipping_cost * 100),
                    },
                    "quantity": 1,
                }
            )

        success_url = request.build_absolute_uri(
            reverse(
                "payments:payment_success", kwargs={"order_number": order.order_number}
            )
        )
        cancel_url = request.build_absolute_uri(
            reverse(
                "payments:payment_cancel", kwargs={"order_number": order.order_number}
            )
        )

        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=line_items,
            mode="payment",
            success_url=success_url,
            cancel_url=cancel_url,
            customer_email=order.email,
            client_reference_id=str(order.id),
            metadata={
                "order_id": str(order.id),
                "order_number": order.order_number,
            },
        )

        order.stripe_checkout_session_id = session.id
        order.save(update_fields=["stripe_checkout_session_id"])

        return session

    @staticmethod
    def retrieve_checkout_session(session_id):
        """
        Retrieves session data from Stripe.
        """
        return stripe.checkout.Session.retrieve(session_id)

    @staticmethod
    def construct_webhook_event(payload, sig_header):
        """
        Validates and constructs a webhook event from Stripe.

        Options:
        - payload: raw body request (bytes)
        - sig_header: Stripe-Signature header value

        Returns: Stripe Event object
        Raises: ValueError, stripe.error.SignatureVerificationError
        """
        webhook_secret = settings.STRIPE_WEBHOOK_SECRET

        try:
            event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
            return event
        except ValueError as e:
            raise ValueError(f"Invalid payload: {str(e)}")
        except stripe.error.SignatureVerificationError as e:
            raise stripe.error.SignatureVerificationError(
                f"Invalid signature: {str(e)}", sig_header
            )
