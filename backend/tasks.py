from celery import shared_task
from django.core.mail import EmailMultiAlternatives
from io import BytesIO
from django.template.loader import render_to_string
from django.conf import settings
from .models import Order



@shared_task
def send_email(subject: str, message: str, from_email: str, to_email: list[str]):
    msg = EmailMultiAlternatives(subject, message, from_email, to_email)
    msg.send()


# @shared_task
# def order_created(order_id, message: str, from_email: str, to_email: list[str]):
#     order = Order.objects.get(id=order_id)
#     subject = f'Order nr. {order.id}'
#     email = EmailMultiAlternatives(subject, message, from_email, to_email)
#     html = render_to_string('backend/orders/pdf.html', {'order': order})
#     out = BytesIO()
#     stylesheets = [weasyprint.CSS(settings.STATIC_ROOT + 'css/pdf.css')]
#     weasyprint.HTML(string=html).write_pdf(out, stylesheets=stylesheets)
#     email.attach(f'order_{order.id}.pdf', out.getvalue(), 'application/pdf')
#     email.send()
