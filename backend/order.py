import csv
import datetime
from django.db import IntegrityError
from django.http.response import HttpResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.platypus import Table
from reportlab.lib.units import inch
from .models import Order, ProductItem, OrderStateChoices


def update_ordered_items_quantity(order: Order) -> bool:
    """
    Функция обновляет количество товаров продавца после успешного создания заказа

    Параметры:
        order (Order): Объект заказа
    Возвращает:
        - True, если обновление прошло успешно
        - False, если обновление не удалось
    """
    products_to_update = []
    for ordered_item in order.ordered_items.all():
        updated_quantity = ordered_item.product_item.quantity
        if order.state == OrderStateChoices.CREATED:
            updated_quantity -= ordered_item.quantity
        elif order.state == OrderStateChoices.CANCELED:
            updated_quantity += ordered_item.quantity
        if updated_quantity < 0:
            return False
        ordered_item.product_item.quantity = updated_quantity
        products_to_update.append(ordered_item.product_item)
    try:
        ProductItem.objects.bulk_update(products_to_update, ["quantity"])
    except IntegrityError:
        return False
    return True


def create_order_report(order_obj: Order) -> str | None:
    """
    Функция создает отчет о заказе в формате pdf

    Параметры:
        order_obj (Order): Объект заказа
    Возвращает:
        - Путь к файлу отчета, если создание прошло успешно
        - None, если создание не удалось
    """
    try:
        filename = f"order_{order_obj.id}.pdf"
        path = f"data/{filename}"
        doc = canvas.Canvas(path, pagesize=letter)
        doc.setFont("Helvetica", 12)
        text_x, text_y = 4 * inch, 10 * inch

        doc.drawString(text_x, text_y, f"Order #{order_obj.id}")
        doc.drawString(text_x + 1 * inch, text_y - 0.5 * inch, f"Date: {order_obj.created_at}")

        table_x, table_y = 0.5 * inch, text_y - 2.5 * inch
        table_data = [
            ["Product", "Price", "Quantity", "Cost"],
        ]
        for item in order_obj.ordered_items.all():
            table_data.append([
                item.product_item.product.name,
                item.product_item.price,
                item.quantity,
                item.get_cost()]
            )
        table_data.append(["Total price with discount", "", "", round(order_obj.total_price, 2)])
        table_y -= len(table_data) * 0.15 * inch
        table = Table(table_data, style=[
            ('GRID', (0, 0), (-1, -1), 0.2, "black"),
            ('BOX', (0, 0), (-1, -1), 0, "black"),
            ('FONT', (0, 0), (-1, -1), "Helvetica", 10),
            ('ALIGN', (0, 0), (-1, -1), "CENTER"),
            ('VALIGN', (0, 0), (-1, -1), "MIDDLE"),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('WRAP', (0, 0), (-1, -1), True),
        ])
        table.setStyle([
            ('FONTNAME', (0, 0), (-1, 0), "Helvetica-Bold"),
            ('FONTNAME', (0, -1), (-1, -1), "Helvetica-Bold"),
            ('GRID', (0, -1), (-1, -1), 0, (255, 255, 255)),
        ])
        table.wrapOn(doc, table_x, table_y)
        table.drawOn(doc, table_x, table_y)
        doc.save()
        return path
    except Exception as err:
        return None


def get_mail_attachment(file_path) -> bytes | None:
    try:
        with open(file_path, 'rb') as f:
            return f.read()
    except Exception:
        return None


def export_to_csv(options, queryset):
    """
    Функция административного интерфейса для экспорта данных в CSV-файл

    Параметры:
        - options (Any): Метаданные модели
        - queryset (QuerySet): Запрос на выборку
    """
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
