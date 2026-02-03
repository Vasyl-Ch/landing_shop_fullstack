from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView
from django.db.models import Q, Prefetch
from apps.products.models import Product, Category, ProductImage
from django.core.paginator import Paginator


class ProductListView(ListView):
    """
    List of all products with filtering and sorting.
    """

    model = Product
    template_name = "products/product_list.html"
    context_object_name = "products"
    paginate_by = 12

    def get_queryset(self):
        queryset = Product.objects.filter(is_active=True).select_related("category")

        search_query = self.request.GET.get("q")
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) | Q(description__icontains=search_query)
            )

        sort_by = self.request.GET.get("sort", "-created_at")
        allowed_sorts = [
            "price",
            "-price",
            "name",
            "-name",
            "-created_at",
            "created_at",
        ]
        if sort_by in allowed_sorts:
            queryset = queryset.order_by(sort_by)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Каталог товаров"
        context["search_query"] = self.request.GET.get("q", "")
        context["current_sort"] = self.request.GET.get("sort", "-created_at")
        context["categories"] = Category.objects.filter(is_active=True)
        return context


class ProductDetailView(DetailView):
    """
    Product detail page.
    """

    model = Product
    template_name = "products/product_detail.html"
    context_object_name = "product"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_queryset(self):
        return (
            Product.objects.filter(is_active=True)
            .select_related("category")
            .prefetch_related(
                Prefetch("images", queryset=ProductImage.objects.order_by("order"))
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.object

        context["title"] = product.name

        context["related_products"] = (
            Product.objects.filter(
                category=product.category, is_active=True
            )
            .exclude(id=product.id)
            .select_related("category")[:4]
        )

        return context


class CategoryDetailView(DetailView):
    """
    Category page with products in this category.
    """

    model = Category
    template_name = "products/category_detail.html"
    context_object_name = "category"
    slug_field = "slug"
    slug_url_kwarg = "slug"
    paginate_by = 12

    def get_queryset(self):
        return Category.objects.filter(is_active=True).prefetch_related("children")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category = self.object

        all_category_ids = [category.id]
        all_category_ids.extend([child.id for child in category.get_all_children()])

        products = (
            Product.objects.filter(
                is_active=True, category_id__in=all_category_ids
            )
            .select_related("category")
            .order_by("-created_at")
        )

        sort_by = self.request.GET.get("sort", "-created_at")
        allowed_sorts = [
            "price",
            "-price",
            "name",
            "-name",
            "-created_at",
            "created_at",
        ]
        if sort_by in allowed_sorts:
            products = products.order_by(sort_by)

        paginator = Paginator(products, self.paginate_by)
        page_number = self.request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        context["products"] = page_obj
        context["page_obj"] = page_obj
        context["is_paginated"] = page_obj.has_other_pages()
        context["title"] = category.name
        context["current_sort"] = sort_by

        return context


class SearchView(ListView):
    """
    Product search.
    """

    model = Product
    template_name = "products/search_results.html"
    context_object_name = "products"
    paginate_by = 12

    def get_queryset(self):
        query = self.request.GET.get("q", "")

        if not query:
            return Product.objects.none()

        return (
            Product.objects.filter(
                Q(name__icontains=query)
                | Q(description__icontains=query)
                | Q(category__name__icontains=query),
                is_active=True,
            )
            .select_related("category")
            .order_by("-created_at")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.get("q", "")
        context["title"] = f'Результаты поиска: "{query}"'
        context["search_query"] = query
        context["total_results"] = self.get_queryset().count()
        return context
