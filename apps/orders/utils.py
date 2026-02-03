from decimal import Decimal
from django.db import transaction
from apps.orders.models import Order, OrderItem


def calculate_shipping_cost(order_data):
    """
    Calculates shipping costs.

    In the future project, there will be a complex logic:
    - By weight of goods
    - By delivery address
    - By order amount (free delivery from X rubles)

    So far, we are returning a fixed amount.
    """
    subtotal = order_data.get("subtotal", 0)
    if subtotal >= 30:
        return Decimal("0.00")
    return Decimal("5.00")


@transaction.atomic
def create_order_from_cart(cart, order_data):
    """
    Creates an order from the cart.

    Options:
    - cart: Cart object
    - order_data: dict with order data {
        'email': str,
        'first_name': str,
        'last_name': str,
        'phone': str,
        'address_line1': str,
        'address_line2': str (optional),
        'city': str,
        'state': str (optional),
        'postal_code': str,
        'country': str,
        'customer_note': str (optional),
        'user': User object or None
      }

    Returns: Order object

    Important: Uses transaction.atomic for the atomicity of the operation.
    """

    if not cart.items.exists():
        raise ValueError("Корзина пуста")

    subtotal = cart.get_total_price()

    order_data["subtotal"] = subtotal
    shipping_cost = calculate_shipping_cost(order_data)

    total = subtotal + shipping_cost

    order = Order.objects.create(
        user=order_data.get("user"),
        email=order_data["email"],
        first_name=order_data["first_name"],
        last_name=order_data["last_name"],
        phone=order_data["phone"],
        address_line1=order_data["address_line1"],
        address_line2=order_data.get("address_line2", ""),
        city=order_data["city"],
        state=order_data.get("state", ""),
        postal_code=order_data["postal_code"],
        country=order_data.get("country", "Россия"),
        subtotal=subtotal,
        shipping_cost=shipping_cost,
        total=total,
        customer_note=order_data.get("customer_note", ""),
        status=Order.Status.PENDING,
    )

    for cart_item in cart.items.select_related("product"):
        if not cart_item.product.is_in_stock():
            raise ValueError(f'Товар "{cart_item.product.name}" недоступен')

        OrderItem.objects.create(
            order=order,
            product=cart_item.product,
            quantity=cart_item.quantity,
        )

        success = cart_item.product.reduce_stock(cart_item.quantity)
        if not success:
            raise ValueError(
                f'Недостаточно товара "{cart_item.product.name}" на складе'
            )

    cart.clear()

    return order
