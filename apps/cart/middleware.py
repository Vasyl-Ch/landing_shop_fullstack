from apps.cart.utils import get_or_create_cart, set_guest_token_cookie


class CartMiddleware:
    """
    Middleware to automatically attach the cart to the request.
    Also sets a cookie guest_token if necessary.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        cart, guest_token_to_set = get_or_create_cart(request)
        request.cart = cart

        response = self.get_response(request)

        if guest_token_to_set:
            set_guest_token_cookie(response, guest_token_to_set)

        return response
