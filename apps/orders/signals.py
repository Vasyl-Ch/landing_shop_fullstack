from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from apps.orders.models import Order, OrderStatusHistory


@receiver(pre_save, sender=Order)
def track_status_change(sender, instance, **kwargs):
    """
    Tracks changes in order status and creates a record in the history.
    """
    if instance.pk:
        try:
            old_order = Order.objects.get(pk=instance.pk)
            if old_order.status != instance.status:
                instance._status_changed = True
                instance._old_status = old_order.status
        except Order.DoesNotExist:
            pass


@receiver(post_save, sender=Order)
def log_status_change(sender, instance, created, **kwargs):
    """
    Logs the status change in OrderStatusHistory.
    """
    if created:
        OrderStatusHistory.objects.create(
            order=instance,
            old_status="",
            new_status=instance.status,
            note="Заказ создан",
        )
    elif hasattr(instance, "_status_changed") and instance._status_changed:
        OrderStatusHistory.objects.create(
            order=instance,
            old_status=instance._old_status,
            new_status=instance.status,
            note=f"Статус изменён: {instance.get_old_status_display()} → {instance.get_status_display()}",
        )
        delattr(instance, "_status_changed")
        delattr(instance, "_old_status")


def get_old_status_display(self):
    """Helper to get the display name of the old status."""
    if hasattr(self, "_old_status"):
        return dict(Order.Status.choices).get(self._old_status, self._old_status)
    return ""


Order.get_old_status_display = get_old_status_display
