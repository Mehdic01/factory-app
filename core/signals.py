from django.conf import settings
from django.core.mail import send_mail
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

User = get_user_model()

@receiver(pre_save, sender=User, dispatch_uid="core_user_normalize_v1")
def normalize_user_fields(sender, instance, **kwargs):
    if instance.username:
        instance.username = instance.username.strip()
    if instance.email:
        instance.email = instance.email.strip().lower()