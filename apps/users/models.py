from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models
from django.utils.translation import gettext_lazy as _


class CustomUserManager(UserManager):
    """
    Custom manager to ensure `createsuperuser` sets proper flags/role
    when using email as USERNAME_FIELD.
    """

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", User.Role.ADMIN)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return super().create_superuser(
            username=username, email=email, password=password, **extra_fields
        )


class User(AbstractUser):
    """
     Custom user model.

    Roles:
        - admin: full access (is_superuser=True)
        - staff: store managers (is_staff=True)
        - customer: regular customers (default)
    """

    class Role(models.TextChoices):
        ADMIN = "admin", _("Администратор")
        STAFF = "staff", _("Менеджер")
        CUSTOMER = "customer", _("Покупатель")

    email = models.EmailField(
        _("email адрес"),
        unique=True,
        error_messages={
            "unique": _("Пользователь с таким email уже существует."),
        },
    )
    role = models.CharField(
        _("роль"),
        max_length=20,
        choices=Role.choices,
        default=Role.CUSTOMER,
    )
    phone = models.CharField(
        _("телефон"),
        max_length=20,
        blank=True,
        null=True,
    )

    objects = CustomUserManager()

    # Override the USERNAME_FIELD for email login
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        verbose_name = _("Пользователь")
        verbose_name_plural = _("Пользователи")
        ordering = ["-date_joined"]

    def __str__(self):
        return self.email

    def save(self, *args, **kwargs):
        """
        Automatic role-based permissions.
        Priority: explicit flags (is_superuser/is_staff) > role
        """
        # If flags are explicitly set (e.g. via `createsuperuser`),
        # they have priority and role should follow them.
        if self.is_superuser:
            # Superuser always has admin role and staff status
            self.role = self.Role.ADMIN
            self.is_staff = True
        elif self.is_staff:
            # Staff user but not superuser
            if self.role != self.Role.ADMIN:
                self.role = self.Role.STAFF
            self.is_superuser = False
        else:
            # Regular customer - only set role if not already admin/staff
            if self.role not in (self.Role.ADMIN, self.Role.STAFF):
                self.role = self.Role.CUSTOMER
            # Don't override flags if they were explicitly set
            # Only set to False if role is CUSTOMER
            if self.role == self.Role.CUSTOMER:
                self.is_staff = False
                self.is_superuser = False

        super().save(*args, **kwargs)


class UserProfile(models.Model):
    """
    User profile with additional information.
    OneToOne's relationship to User.
    """

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile",
        verbose_name=_("пользователь"),
    )

    address_line1 = models.CharField(
        _("адрес (строка 1)"),
        max_length=255,
        blank=True,
    )
    address_line2 = models.CharField(
        _("адрес (строка 2)"),
        max_length=255,
        blank=True,
    )
    city = models.CharField(
        _("город"),
        max_length=100,
        blank=True,
    )
    state = models.CharField(
        _("регион/область"),
        max_length=100,
        blank=True,
    )
    postal_code = models.CharField(
        _("почтовый индекс"),
        max_length=20,
        blank=True,
    )
    country = models.CharField(
        _("страна"),
        max_length=100,
        blank=True,
        default="Не указана",
    )

    date_of_birth = models.DateField(
        _("дата рождения"),
        blank=True,
        null=True,
    )
    avatar = models.ImageField(
        _("аватар"),
        upload_to="avatars/%Y/%m/%d/",
        blank=True,
        null=True,
    )

    created_at = models.DateTimeField(_("создан"), auto_now_add=True)
    updated_at = models.DateTimeField(_("обновлён"), auto_now=True)

    class Meta:
        verbose_name = _("Профиль пользователя")
        verbose_name_plural = _("Профили пользователей")

    def __str__(self):
        return f"Профиль {self.user.email}"

    def get_full_address(self):
        """Returns the full address in a single string."""
        parts = [
            self.address_line1,
            self.address_line2,
            self.city,
            self.state,
            self.postal_code,
            self.country,
        ]
        return ", ".join(filter(None, parts))
