from typing import Type
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver, Signal
from django_rest_passwordreset.signals import reset_password_token_created
from backend.models import User, EmailTokenConfirm
from .tasks import send_email

FROM_EMAIL = settings.EMAIL_HOST_USER

new_user_registered = Signal()
new_order = Signal()


@receiver(reset_password_token_created)
def password_reset_token_created(sender, instance, reset_password_token, *args, **kwargs):
    subject = "Password Reset Token"
    body = reset_password_token.key
    to_email = [reset_password_token.email]
    send_email(subject, body, FROM_EMAIL, to_email)


@receiver(post_save, sender=User)
def new_user_registered_signal(sender: Type[User], instance: User, created: bool, **kwargs):
    if created and not instance.is_active:
        token, _ = EmailTokenConfirm.objects.get_or_create(user=instance)
        subject = "Email confirm token"
        body = token.key
        to_email = [instance.email]
        send_email.delay(subject, body, FROM_EMAIL, to_email)


@receiver(new_order)
def new_order_signal(user_id, **kwargs):
    user = User.objects.get(pk=user_id)
    if user is not None:
        subject = "Обновление статуса заказа"
        body = "Заказ сформирован"
        to_email = [user.email]
        send_email.delay(subject, body, FROM_EMAIL, to_email)
