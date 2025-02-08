from celery import shared_task
from django.core.mail import EmailMultiAlternatives


@shared_task
def send_email(subject, message, from_email, to_email: list[str]):
    msg = EmailMultiAlternatives(subject, message, from_email, to_email)
    msg.send()
