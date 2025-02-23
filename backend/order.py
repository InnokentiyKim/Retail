from django.db import IntegrityError
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
        if order.state == OrderStateChoices.CONFIRMED:
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
        doc = canvas.Canvas(filename, pagesize=letter)
        doc.setFont("Tahoma", 12)
        doc.drawString(1 * inch, 12 * inch, "Order #{}".format(getattr(order_obj, "id")))
        doc.drawString(1 * inch, 18 * inch, "Date: {}".format(getattr(order_obj, "created_at")))
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
        table_data.append(["Total", "", "", order_obj.total_price])
        table = Table(table_data, style=[
            ('GRID', (0, 0), (-1, -1), 0.5, "black"),
            ('BOX', (0, 0), (-1, -1), 0, "black"),
            ('FONT', (0, 0), (-1, -1), "Tahoma", 12),
            ('ALIGN', (0, 0), (-1, -1), "CENTER"),
            ('VALIGN', (0, 0), (-1, -1), "MIDDLE"),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
        ])
        table.setStyle([
            ('FONTNAME', (0, 0), (-1, 0), "Tahoma-Bold"),
            ('FONTNAME', (0, -1), (-1, -1), "Tahoma-Bold"),
        ])
        table.wrapOn(doc, 1 * inch, 1 * inch)
        table.drawOn(doc, 1 * inch, 10 * inch)
        doc.save()
    except Exception as err:
        return None
    else:
        return filename
