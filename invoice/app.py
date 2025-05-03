from flask import Flask, render_template, request, make_response, redirect, url_for, session
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from PIL import Image
from datetime import datetime
import os
from functools import wraps

app = Flask(__name__)
app.secret_key = os.urandom(24)  # For session management

# Admin credentials (in production, use environment variables or a database)
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "mujjubhai123"  # Change this to a secure password

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error="Invalid credentials")
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

# Generate Invoice PDF
def generate_invoice_pdf(invoice_data):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Load the Photoshop template
    template_path = "invoice/static/PROFORMA.JPG"
    img = Image.open(template_path)

    # Draw the template as background
    c.drawImage(template_path, 0, 0, width=width, height=height)

    c.setFont("Helvetica-Bold", 13)
    c.drawString(50, height - 170, f"To: {invoice_data['to_name']}")  
    # c.drawString(width - 140, height - 170, f"Date: {invoice_data['date']}")  # Lowered slightly
    # Convert date format to DD/MM/YYYY before drawing it
    formatted_date = datetime.strptime(invoice_data['date'], "%Y-%m-%d").strftime("%d/%m/%Y")
    c.drawString(width - 140, height - 170, f"Date: {formatted_date}")
    c.drawString(50, height - 190, f"Address: {invoice_data['to_address']}")






# Table headers
    c.setFont("Helvetica-Bold", 12)
    c.drawString(70, height - 230, "S.No")
    c.drawString(150, height - 230, "Item")
    c.drawString(300, height - 230, "Quantity")
    c.drawString(400, height - 230, "Price")
    c.drawString(500, height - 230, "Total")

    # Items data with serial numbers
    y_position = height - 250
    total_amount = 0

    for serial_no, item in enumerate(invoice_data['items'], start=1):
        c.setFont("Helvetica-Bold", 10)
        c.drawString(80, y_position, str(serial_no))  # Serial Number
        c.drawString(145, y_position, item['name'])
        c.drawString(320, y_position, str(item['quantity']))
        c.drawString(400, y_position, str(item['price']))
        
        total_item_cost = item['quantity'] * item['price']
        c.drawString(500, y_position, str(total_item_cost))

        total_amount += total_item_cost
        y_position -= 20  # Move to the next row

    # ✅ **Fixed Advance Calculation**
    advance_paid = float(invoice_data['advance_paid'])  # Get user input
    balance_due = total_amount - advance_paid  # Subtract advance from total

    # Draw total, advance, and balance
    c.setFont("Helvetica-Bold", 10)

    c.drawString(400, y_position - 10, "Total Amount:")
    c.drawString(500, y_position - 10, "Rs. {:.2f}".format(total_amount))  # ✅ Fix

    c.drawString(400, y_position - 30, "Advance Paid:")
    c.drawString(500, y_position - 30, "Rs. {:.2f}".format(advance_paid))  # ✅ Fix

    c.drawString(400, y_position - 50, "Due Amount:")
    c.drawString(500, y_position - 50, "Rs. {:.2f}".format(balance_due))  # ✅ Fix


    # Terms & Conditions
    c.setFont("Helvetica-Bold", 10)
    c.setFillColorRGB(1, 0, 0)  # Set text color to Red (RGB: 1, 0, 0)

    c.drawString(40, 80, "Terms & Conditions:")
    c.drawString(40, 65, "1. 50% advance must be paid upon order placement.")
    c.drawString(40, 50, "2. The balance must be paid upon delivery.")
    c.drawString(40, 35, "3. No Exchange & No Returns.")
    c.drawString(40, 20, "4. If any wrong firing, we are not responsible.")

    c.setFillColorRGB(0, 0, 0)  # Reset text color to black



   # Signature (Right Side)
    signature_x = 400  # Shift to the right
    signature_y = 100  # Adjust vertical position

    c.setFont("Helvetica-Bold", 12)
    c.drawString(signature_x, signature_y, "MADEENA GRAND FIREWORKS")  # First Line (Above)
    c.drawString(signature_x + 50, signature_y - 50, "PROPRIETOR")  # Shift "PROPRIETOR" a bit right and below




    c.showPage()
    c.save()

    buffer.seek(0)
    return buffer

@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    if request.method == "POST":
        # Retrieve form data
        items = []
        num_items = int(request.form['num_items'])

        for i in range(num_items):
            name = request.form[f"item_name_{i}"]
            quantity = int(request.form[f"quantity_{i}"])
            price = float(request.form[f"price_{i}"])
            items.append({'name': name, 'quantity': quantity, 'price': price})

        to_name = request.form['to_name']
        to_address = request.form['to_address']
        date = request.form['date']
        advance_paid = float(request.form['advance_paid'])  # ✅ Get advance input

        # Invoice data dictionary
        invoice_data = {
            'to_name': to_name,
            'to_address': to_address,
            'date': date,
            'advance_paid': advance_paid,  # ✅ Pass user-inputted advance
            'items': items
        }

        # Generate the invoice PDF
        pdf_buffer = generate_invoice_pdf(invoice_data)

        # Return the PDF
        response = make_response(pdf_buffer.read())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = 'inline; filename=invoice.pdf'
        return response

    return render_template('index.html')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)

