from django.urls import path
from apps.products import views

app_name = "products"

urlpatterns = [
    path("", views.ProductListView.as_view(), name="product_list"),
    path("search/", views.SearchView.as_view(), name="search"),
    path(
        "category/<slug:slug>/",
        views.CategoryDetailView.as_view(),
        name="category_detail",
    ),
    path("<slug:slug>/", views.ProductDetailView.as_view(), name="product_detail"),
]
