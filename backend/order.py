from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.platypus import Table
from reportlab.lib.units import inch
from .models import Order


def create_order_report(order_obj: Order):
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
