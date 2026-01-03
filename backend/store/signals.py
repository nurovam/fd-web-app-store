from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from .image_tasks import queue_resize
from .models import Product, Profile

User = get_user_model()

@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.get_or_create(user=instance)


@receiver(post_save, sender=Product)
def resize_product_image(sender, instance, **kwargs):
    if not instance.image:
        return
    update_fields = kwargs.get('update_fields')
    if update_fields and 'image' not in update_fields:
        return
    try:
        image_path = instance.image.path
    except (ValueError, AttributeError):
        return
    transaction.on_commit(lambda: queue_resize(image_path, async_=settings.ASYNC_IMAGE_RESIZE))
