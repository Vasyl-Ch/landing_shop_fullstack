from decimal import Decimal
from django.db import transaction
from apps.orders.models import Order, OrderItem


def calculate_shipping_cost(order_data):
    """
    Calculates shipping costs.
    Returns 0 for free shipping threshold, otherwise returns 0 as well
    (actual cost determined by carrier).
    """
    return Decimal("0.00")


def get_shipping_text(subtotal):
    """
    Returns shipping cost text based on order amount.
    Free shipping for orders >= 1000 rubles.
    """
    if isinstance(subtotal, (str, int, float)):
        subtotal = Decimal(str(subtotal))

    if subtotal >= Decimal("1000.00"):
        return "Бесплатно"
    return "В соответствии с тарифами перевозчика"


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
        product = cart_item.product

        if not product.is_in_stock():
            raise ValueError(f'Товар "{product.name}" недоступен для заказа')

        if product.track_inventory:
            if cart_item.quantity > product.stock:
                raise ValueError(
                    f'Недостаточно товара "{product.name}" на складе. '
                    f"Доступно: {product.stock} шт., в корзине: {cart_item.quantity} шт."
                )

        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=cart_item.quantity,
        )

        if product.track_inventory:
            success = product.reduce_stock(cart_item.quantity)
            if not success:
                raise ValueError(
                    f'Ошибка при резервировании товара "{product.name}". '
                    f"Возможно, другой пользователь только что приобрел последние экземпляры."
                )

    cart.clear()

    return order
