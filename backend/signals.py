from typing import Type
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.db.models.signals import post_save
from django.dispatch import receiver, Signal
from django_rest_passwordreset.signals import reset_password_token_created

from backend.models import User, EmailTokenConfirm, Order

new_user_registered = Signal()
new_order = Signal()


@receiver(reset_password_token_created)
def password_reset_token_created(sender, instance, reset_password_token, *args, **kwargs):
    msg = EmailMultiAlternatives(
        "Password reset token",
        reset_password_token.key,
        settings.EMAIL_HOST_USER,
        [reset_password_token.email]
    )
    msg.send()


@receiver(post_save, sender=User)
def new_user_registered_signal(sender: Type[User], instance: User, created: bool, **kwargs):
    if created and not instance.is_active:
        token, _ = EmailTokenConfirm.objects.get_or_create(user=instance)
        msg = EmailMultiAlternatives(
            "Password reset token",
            token.key,
            settings.EMAIL_HOST_USER,
            [instance.email]
        )
        msg.send()


@receiver(new_order)
def new_order_signal(user_id, **kwargs):
    user = User.objects.get(pk=user_id)
    msg = EmailMultiAlternatives(
        "Обновление статуса заказа",
        "Заказ сформирован",
        settings.EMAIL_HOST_USER,
        [user.email]
    )
    msg.send()
