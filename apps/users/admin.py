from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from apps.users.models import User, UserProfile


class UserProfileInline(admin.StackedInline):
    """Inline to edit the profile directly in the user form."""

    model = UserProfile
    can_delete = False
    verbose_name = "Профиль"
    verbose_name_plural = "Профиль"
    fields = (
        "address_line1",
        "address_line2",
        "city",
        "state",
        "postal_code",
        "country",
        "date_of_birth",
        "avatar",
    )


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom admin for the User model."""

    inlines = [UserProfileInline]

    list_display = (
        "email",
        "username",
        "role",
        "first_name",
        "last_name",
        "is_active",
        "date_joined",
    )
    list_filter = ("role", "is_active", "is_staff", "date_joined")
    search_fields = ("email", "username", "first_name", "last_name", "phone")
    ordering = ("-date_joined",)

    fieldsets = (
        (None, {"fields": ("email", "username", "password")}),
        (
            _("Персональная информация"),
            {"fields": ("first_name", "last_name", "phone")},
        ),
        (
            _("Права доступа"),
            {
                "fields": (
                    "role",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (_("Важные даты"), {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "username", "password1", "password2", "role"),
            },
        ),
    )

    readonly_fields = ("last_login", "date_joined")


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin for profiles (in case of direct access)."""

    list_display = ("user", "city", "country", "created_at")
    search_fields = ("user__email", "user__username", "city", "country")
    list_filter = ("country", "created_at")
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        (_("Пользователь"), {"fields": ("user",)}),
        (
            _("Адрес"),
            {
                "fields": (
                    "address_line1",
                    "address_line2",
                    "city",
                    "state",
                    "postal_code",
                    "country",
                )
            },
        ),
        (_("Дополнительно"), {"fields": ("date_of_birth", "avatar")}),
        (
            _("Метаданные"),
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )
