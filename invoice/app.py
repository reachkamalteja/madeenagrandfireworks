from flask import Flask, render_template, request, make_response, redirect, url_for, session
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from PIL import Image
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Secure session key

# ------------------------ PDF Generation ------------------------

def generate_invoice_pdf(data):
    """Generates PDF invoice using ReportLab."""
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Background template
    template_path = "static/PROFORMA.JPG"
    c.drawImage(template_path, 0, 0, width=width, height=height)

    # Header Info
    c.setFont("Helvetica-Bold", 13)
    formatted_date = datetime.strptime(data['date'], "%Y-%m-%d").strftime("%d/%m/%Y")
    c.drawString(50, height - 170, f"To: {data['to_name']}")
    c.drawString(width - 140, height - 170, f"Date: {formatted_date}")
    c.drawString(50, height - 190, f"Address: {data['to_address']}")

    # Table Headers
    c.setFont("Helvetica-Bold", 12)
    c.drawString(70, height - 230, "S.No")
    c.drawString(150, height - 230, "Item")
    c.drawString(300, height - 230, "Quantity")
    c.drawString(400, height - 230, "Price")
    c.drawString(500, height - 230, "Total")

    # Table Data
    y = height - 250
    total = 0

    for i, item in enumerate(data['items'], start=1):
        total_item = item['quantity'] * item['price']
        total += total_item

        c.setFont("Helvetica-Bold", 10)
        c.drawString(80, y, str(i))
        c.drawString(145, y, item['name'])
        c.drawString(320, y, str(item['quantity']))
        c.drawString(400, y, str(item['price']))
        c.drawString(500, y, str(total_item))
        y -= 20

    # Totals
    advance = float(data['advance_paid'])
    balance = total - advance

    c.setFont("Helvetica-Bold", 10)
    c.drawString(400, y - 10, "Total Amount:")
    c.drawString(500, y - 10, f"Rs. {total:.2f}")
    c.drawString(400, y - 30, "Advance Paid:")
    c.drawString(500, y - 30, f"Rs. {advance:.2f}")
    c.drawString(400, y - 50, "Due Amount:")
    c.drawString(500, y - 50, f"Rs. {balance:.2f}")

    # Terms
    c.setFillColorRGB(1, 0, 0)
    c.drawString(40, 80, "Terms & Conditions:")
    c.drawString(40, 65, "1. 50% advance must be paid upon order placement.")
    c.drawString(40, 50, "2. The balance must be paid upon delivery.")
    c.drawString(40, 35, "3. No Exchange & No Returns.")
    c.drawString(40, 20, "4. If any wrong firing, we are not responsible.")
    c.setFillColorRGB(0, 0, 0)

    # Signature
    c.setFont("Helvetica-Bold", 12)
    c.drawString(400, 100, "MADEENA GRAND FIREWORKS")
    c.drawString(450, 50, "PROPRIETOR")

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer

# ------------------------ Routes ------------------------

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # Gather form data
        num_items = int(request.form['num_items'])
        items = [
            {
                'name': request.form[f"item_name_{i}"],
                'quantity': int(request.form[f"quantity_{i}"]),
                'price': float(request.form[f"price_{i}"])
            }
            for i in range(num_items)
        ]

        invoice_data = {
            'to_name': request.form['to_name'],
            'to_address': request.form['to_address'],
            'date': request.form['date'],
            'advance_paid': float(request.form['advance_paid']),
            'items': items
        }

        pdf = generate_invoice_pdf(invoice_data)

        response = make_response(pdf.read())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = 'inline; filename=invoice.pdf'
        return response

    return render_template("index.html")

# ------------------------ Entry Point ------------------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
