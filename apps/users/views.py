from django.shortcuts import render, redirect
from django.views import View
from django.views.generic import TemplateView, UpdateView
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.utils.translation import gettext_lazy
from django.urls import reverse_lazy
from django.conf import settings
from apps.users.models import User, UserProfile
from apps.cart.models import Cart


class RegisterView(View):
    """
    User registration.
    """

    template_name = "users/register.html"

    def get(self, request):
        if request.user.is_authenticated:
            return redirect("core:home")

        context = {"title": "Регистрация"}
        return render(request, self.template_name, context)

    def post(self, request):
        email = request.POST.get("email")
        username = request.POST.get("username")
        password1 = request.POST.get("password1")  # Изменено с "password"
        password2 = request.POST.get("password2")  # Изменено с "password_confirm"
        first_name = request.POST.get("first_name", "")
        last_name = request.POST.get("last_name", "")
        phone = request.POST.get("phone", "")

        if not all([email, username, password1, password2]):
            messages.error(request, gettext_lazy("Заполните все обязательные поля"))
            return redirect("users:register")

        if password1 != password2:
            messages.error(request, gettext_lazy("Пароли не совпадают"))
            return redirect("users:register")

        if len(password1) < 8:
            messages.error(
                request, gettext_lazy("Пароль должен содержать минимум 8 символов")
            )
            return redirect("users:register")

        if User.objects.filter(email=email).exists():
            messages.error(
                request, gettext_lazy("Пользователь с таким email уже существует")
            )
            return redirect("users:register")

        if User.objects.filter(username=username).exists():
            messages.error(request, gettext_lazy("Это имя пользователя уже занято"))
            return redirect("users:register")

        try:
            user = User.objects.create_user(
                email=email,
                username=username,
                password=password1,
                first_name=first_name,
                last_name=last_name,
                phone=phone,
            )

            guest_token = request.COOKIES.get("guest_token")
            if guest_token:
                try:
                    guest_cart = Cart.objects.get(guest_token=guest_token)
                    user_cart, _ = Cart.objects.get_or_create(user=user)
                    user_cart.merge_with(guest_cart)
                except Cart.DoesNotExist:
                    pass

            login(request, user)

            messages.success(
                request, gettext_lazy("Регистрация успешна! Добро пожаловать!")
            )
            return redirect("core:home")

        except Exception as e:
            messages.error(request, gettext_lazy(f"Ошибка при регистрации: {str(e)}"))
            return redirect("users:register")


class LoginView(View):
    """
    User login.
    """

    template_name = "users/login.html"

    def get(self, request):
        if request.user.is_authenticated:
            return redirect("core:home")

        context = {"title": "Вход"}
        return render(request, self.template_name, context)

    def post(self, request):
        email = request.POST.get("email")
        password = request.POST.get("password")
        remember_me = request.POST.get("remember_me")

        if not email or not password:
            messages.error(request, gettext_lazy("Введите email и пароль"))
            return redirect("users:login")

        user = authenticate(request, username=email, password=password)

        if user is not None:
            login(request, user)

            if not remember_me:
                request.session.set_expiry(0)  # Browser close

            # Merge guest cart with user cart
            guest_token = request.COOKIES.get(settings.GUEST_TOKEN_COOKIE_NAME)
            if guest_token:
                try:
                    guest_cart = Cart.objects.get(guest_token=guest_token)
                    user_cart, _ = Cart.objects.get_or_create(user=user)
                    user_cart.merge_with(guest_cart)
                except Cart.DoesNotExist:
                    pass

            messages.success(
                request,
                gettext_lazy(f"Добро пожаловать, {user.first_name or user.email}!"),
            )

            next_url = request.GET.get("next") or request.POST.get("next")
            if next_url:
                return redirect(next_url)
            return redirect("core:home")
        else:
            messages.error(request, gettext_lazy("Неверный email или пароль"))
            return redirect("users:login")


class LogoutView(LoginRequiredMixin, View):
    """
    User logout.
    """

    def post(self, request):
        logout(request)
        messages.success(request, gettext_lazy("Вы вышли из системы"))
        return redirect("core:home")


class ProfileView(LoginRequiredMixin, TemplateView):
    """
    User profile overview.
    """

    template_name = "users/profile.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Мой профиль"

        context["recent_orders"] = self.request.user.orders.prefetch_related(
            "items__product"
        ).order_by("-created_at")[:5]

        return context


class ProfileEditView(LoginRequiredMixin, UpdateView):
    """
    Edit user profile.
    """

    model = UserProfile
    template_name = "users/profile_edit.html"
    fields = [
        "address_line1",
        "address_line2",
        "city",
        "state",
        "postal_code",
        "country",
        "date_of_birth",
        "avatar",
    ]
    success_url = reverse_lazy("users:profile")

    def get_object(self, queryset=None):
        return self.request.user.profile

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Редактировать профиль"
        return context

    def form_valid(self, form):
        messages.success(self.request, gettext_lazy("Профиль успешно обновлён"))
        return super().form_valid(form)


class AccountSettingsView(LoginRequiredMixin, View):
    """
    Account settings - change email, password, etc.
    """

    template_name = "users/account_settings.html"

    def get(self, request):
        context = {"title": "Настройки аккаунта"}
        return render(request, self.template_name, context)

    def post(self, request):
        action = request.POST.get("action")

        if action == "update_personal_info":
            user = request.user
            user.first_name = request.POST.get("first_name", user.first_name)
            user.last_name = request.POST.get("last_name", user.last_name)
            user.phone = request.POST.get("phone", user.phone)
            user.save()
            messages.success(request, gettext_lazy("Личные данные обновлены"))

        elif action == "change_password":
            old_password = request.POST.get("old_password")
            new_password = request.POST.get("new_password")
            new_password_confirm = request.POST.get("new_password_confirm")

            if not request.user.check_password(old_password):
                messages.error(request, gettext_lazy("Неверный текущий пароль"))
            elif new_password != new_password_confirm:
                messages.error(request, gettext_lazy("Новые пароли не совпадают"))
            elif len(new_password) < 8:
                messages.error(request, gettext_lazy("Пароль должен содержать минимум 8 символов"))
            else:
                request.user.set_password(new_password)
                request.user.save()
                from django.contrib.auth import update_session_auth_hash

                update_session_auth_hash(request, request.user)
                messages.success(request, gettext_lazy("Пароль успешно изменён"))

        return redirect("users:account_settings")
