from django.db import IntegrityError
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.platypus import Table
from reportlab.lib.units import inch
from .models import Order, ProductItem


def update_ordered_items_quantity(order: Order) -> bool:
    products_to_update = []
    for item in order.ordered_items.all():
        updated_quantity = item.product_item.quantity - item.quantity
        if updated_quantity < 0:
            return False
        item.product_item.quantity = updated_quantity
        products_to_update.append(item.product_item)
    try:
        ProductItem.objects.bulk_update(products_to_update, ["quantity"])
    except IntegrityError:
        return False
    return True


def create_order_report(order_obj: Order) -> str | None:
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
