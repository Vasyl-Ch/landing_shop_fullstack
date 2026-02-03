from django.shortcuts import render
from django.views.generic import TemplateView
from apps.products.models import Product, Category


class HomeView(TemplateView):
    """
    Main homepage.
    Displays featured products and active categories.
    """

    template_name = "core/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["featured_products"] = Product.objects.filter(
            is_active=True, is_featured=True
        ).select_related("category")[:8]

        context["new_arrivals"] = Product.objects.filter(is_active=True).order_by(
            "-created_at"
        )[:8]

        context["categories"] = Category.objects.filter(
            is_active=True, parent__isnull=True
        ).prefetch_related("children")[:6]

        context["title"] = "Главная"

        return context


class AboutView(TemplateView):
    """About us page."""

    template_name = "core/about.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "О нас"
        return context


class ContactView(TemplateView):
    """Contact page."""

    template_name = "core/contact.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Контакты"
        return context
