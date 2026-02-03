from apps.products.models import Category


def cart_context(request):
    """
    Adds cart information to all templates.
    The cart is already available through request.cart thanks to middleware.
    """
    cart = getattr(request, "cart", None)

    if cart:
        return {
            "cart": cart,
            "cart_items_count": cart.get_total_items(),
            "cart_total_price": cart.get_total_price(),
        }

    return {
        "cart": None,
        "cart_items_count": 0,
        "cart_total_price": 0,
    }


def categories_context(request):
    """
    Adds a list of basic categories to navigate.
    """
    return {
        "header_categories": Category.objects.filter(
            is_active=True, parent__isnull=True
        ).order_by("order", "name")[:10]
    }


def site_settings(request):
    """
    Global site settings.
    """
    return {
        "SITE_NAME": "E-Commerce Store",
        "SITE_DESCRIPTION": "Интернет-магазин качественных товаров",
        "SUPPORT_EMAIL": "support@example.com",
        "SUPPORT_PHONE": "+380 000 000 000",
    }
