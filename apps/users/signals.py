from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.users.models import User, UserProfile


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Automatically creates a profile when you create a user.
    """
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    Automatically saves the profile when the user is saved.
    """
    if hasattr(instance, "profile"):
        instance.profile.save()
