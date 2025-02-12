import csv
import datetime
from celery import shared_task
from django.core.mail import EmailMultiAlternatives
from django.http import HttpResponse


@shared_task
def send_email(subject: str, message: str, from_email: str, to_email: list[str]):
    msg = EmailMultiAlternatives(subject, message, from_email, to_email)
    msg.send()


@shared_task
def export_to_csv(modeladmin, request, queryset):
    options = modeladmin.model._meta
    content_disposition = f"attachment; filename={options.verbose_name}.csv"
    response = HttpResponse(content_type="text/csv")
    response['Content-Disposition'] = content_disposition
    writer = csv.writer(response)
    fields = [field for field in options.get_fields() if not field.many_to_many and not field.one_to_many]
    writer.writerow([field.verbose_name for field in fields])
    for item in queryset:
        data_row = []
        for field in fields:
            value = getattr(item, field.name)
            if isinstance(value, datetime.datetime):
                value = value.strftime("%Y-%m-%d")
            data_row.append(value)
        writer.writerow(data_row)
    return response
