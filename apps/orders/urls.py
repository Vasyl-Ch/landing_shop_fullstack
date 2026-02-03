from django.urls import path
from apps.orders import views

app_name = "orders"

urlpatterns = [
    path("checkout/", views.CheckoutView.as_view(), name="checkout"),
    path("my-orders/", views.OrderListView.as_view(), name="order_list"),
    path(
        "order/<str:order_number>/",
        views.OrderDetailView.as_view(),
        name="order_detail",
    ),
    path(
        "order/<str:order_number>/cancel/",
        views.OrderCancelView.as_view(),
        name="order_cancel",
    ),
    path("track/", views.TrackOrderView.as_view(), name="track_order"),
]
