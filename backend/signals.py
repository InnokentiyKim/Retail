from typing import Type
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver, Signal
from django_rest_passwordreset.signals import reset_password_token_created
from backend.models import User, EmailTokenConfirm, OrderStateChoices
from .tasks import send_email

FROM_EMAIL = settings.EMAIL_HOST_USER

new_user_registered = Signal()
new_order = Signal()


@receiver(reset_password_token_created)
def password_reset_token_created(sender, instance, reset_password_token, *args, **kwargs):
    """
    Сигнал для отправки токена сброса пароля
    """
    subject = "Password Reset Token"
    body = reset_password_token.key
    to_email = [reset_password_token.user.email]
    send_email(subject, body, FROM_EMAIL, to_email)


@receiver(post_save, sender=User)
def new_user_registered_signal(sender: Type[User], instance: User, created: bool, **kwargs):
    """
    Сигнал для отправки токена подтверждения email
    """
    if created and not instance.is_active:
        token, _ = EmailTokenConfirm.objects.get_or_create(user=instance)
        subject = "Email confirm token"
        body = token.key
        to_email = [instance.email]
        send_email.delay(subject, body, FROM_EMAIL, to_email)


@receiver(new_order)
def new_order_signal(user_id, order_id, order_state, report_file=None, **kwargs):
    """
    Сигнал для отправки уведомления о статусе заказа
    """
    user = User.objects.get(pk=user_id)
    if user is not None:
        subject = "Обновление статуса заказа"
        to_email = [user.email]
        body = f"Ваш заказ #{order_id}"
        if order_state == OrderStateChoices.CREATED:
            body = f"Ваш заказ #{order_id} сформирован"
        if order_state == OrderStateChoices.CONFIRMED:
            body = f"Ваш заказ #{order_id} подтвержден. Спасибо за покупку!"
        if order_state == OrderStateChoices.ASSEMBLED:
            body = f"Ваш заказ #{order_id} собран"
        if order_state == OrderStateChoices.DELIVERED:
            body = f"Ваш заказ #{order_id} доставлен"
        if order_state == OrderStateChoices.CANCELED:
            body = f"Ваш заказ #{order_id} отменен"
        if report_file is not None:
            send_email.delay(subject, body, FROM_EMAIL, to_email, report_file)
        else:
            send_email.delay(subject, body, FROM_EMAIL, to_email)
