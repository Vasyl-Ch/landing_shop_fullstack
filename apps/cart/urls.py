from django.urls import path
from apps.cart import views

app_name = "cart"

urlpatterns = [
    # Основные страницы
    path("", views.CartDetailView.as_view(), name="cart_detail"),
    # Действия с корзиной (обычные POST запросы с редиректом)
    path("add/<int:product_id>/", views.AddToCartView.as_view(), name="add_to_cart"),
    path(
        "update/<int:item_id>/",
        views.UpdateCartItemView.as_view(),
        name="update_cart_item",
    ),
    path(
        "remove/<int:item_id>/",
        views.RemoveFromCartView.as_view(),
        name="remove_from_cart",
    ),
    path("clear/", views.ClearCartView.as_view(), name="clear_cart"),
    # AJAX endpoints (возвращают JSON)
    path("ajax/get/", views.CartAjaxGetView.as_view(), name="ajax_get"),
    path("ajax/add/", views.CartAjaxAddView.as_view(), name="ajax_add"),
    path("ajax/update/", views.CartAjaxUpdateView.as_view(), name="ajax_update"),
    path("ajax/remove/", views.CartAjaxRemoveView.as_view(), name="ajax_remove"),
    path("ajax/clear/", views.CartAjaxClearView.as_view(), name="ajax_clear"),
]
