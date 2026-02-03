import uuid
from django.conf import settings
from apps.cart.models import Cart


def generate_guest_token():
    """Generates a unique token for the guest."""
    return str(uuid.uuid4())


def get_or_create_cart(request):
    """
    Receives or creates a cart for the current request.

    Logic:
    1. If the user is authorized - search/create a cart by user
    2. If a guest - search/create a cart by guest_token from cookies
    3. If guest_token not, generate a new one and set a cookie

    Returns: (cart, guest_token_to_set)
    - cart: Cart object
    - guest_token_to_set: Token to set in the cookie (or None)
    """

    guest_token_to_set = None

    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)

        guest_token = request.COOKIES.get(settings.GUEST_TOKEN_COOKIE_NAME)
        if guest_token:
            try:
                guest_cart = Cart.objects.get(guest_token=guest_token)
                cart.merge_with(guest_cart)
            except Cart.DoesNotExist:
                pass
    else:
        guest_token = request.COOKIES.get(settings.GUEST_TOKEN_COOKIE_NAME)

        if guest_token:
            cart, created = Cart.objects.get_or_create(guest_token=guest_token)
        else:
            guest_token = generate_guest_token()
            cart = Cart.objects.create(guest_token=guest_token)
            guest_token_to_set = guest_token

    return cart, guest_token_to_set


def set_guest_token_cookie(response, guest_token):
    """
    Sets guest_token in the HttpOnly cookie.

    Options:
    - response: Django HttpResponse object
    - guest_token: Token string
    """
    response.set_cookie(
        key=settings.GUEST_TOKEN_COOKIE_NAME,
        value=guest_token,
        max_age=settings.GUEST_TOKEN_COOKIE_AGE,
        httponly=settings.GUEST_TOKEN_COOKIE_HTTPONLY,
        secure=settings.GUEST_TOKEN_COOKIE_SECURE,
        samesite=settings.GUEST_TOKEN_COOKIE_SAMESITE,
    )
