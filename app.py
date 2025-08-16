from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
from db_connect import conn  # Ensure this connects to the correct database

app = Flask(__name__)
app.secret_key = "Internet@123"  # Use a strong secret key for production

# Route for the main login page
@app.route('/')
def login():
    return render_template('login.html')

# Route for signup page
@app.route('/signup')
def signup():
    return render_template('signup.html')

# Process signup form submission
@app.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    password = request.form['password']
    role = request.form['role']

    if role not in ['Admin', 'Analyst']:
        flash("Invalid role. Only Admin or Analyst can sign up.")
        return redirect(url_for('signup'))

    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO User (username, password, role) VALUES (%s, %s, %s)", 
                       (username, password, role))
        conn.commit()
        flash(f"{role} account created successfully. You can now log in.")
        return redirect(url_for('login'))
    except mysql.connector.Error as err:
        flash(f"Error: {err}")
        return redirect(url_for('signup'))
    finally:
        cursor.close()

# Authentication endpoint for login
@app.route('/login', methods=['POST'])
def authenticate():
    username = request.form['username']
    password = request.form['password']
    role = request.form['role']

    cursor = conn.cursor()
    cursor.execute("SELECT * FROM User WHERE username = %s AND password = %s AND role = %s",
                   (username, password, role))
    user = cursor.fetchone()
    if user:
        session['user_id'] = user[0]
        session['role'] = role
        if role == 'Admin':
            return redirect(url_for('admin_dashboard'))
        elif role == 'Analyst':
            return redirect(url_for('analytics_dashboard'))
        elif role == 'Employee':
            return redirect(url_for('employee_dashboard'))
    else:
        flash("Invalid credentials")
        return redirect(url_for('login'))

# Route for Admin Dashboard
@app.route('/admin_dashboard', methods=['GET', 'POST'])
def admin_dashboard():
    if request.method == 'POST':
        # Process new employee registration
        username = request.form['username']
        password = request.form['password']
        phone_number = request.form['phone_number']

        cursor = conn.cursor()
        try:
            # Insert new user as Employee
            cursor.execute("INSERT INTO User (username, password, role) VALUES (%s, %s, %s)", 
                           (username, password, 'Employee'))
            conn.commit()
            user_id = cursor.lastrowid  # Get the new user ID

            # Now insert into Employee table
            cursor.execute("INSERT INTO Employee (user_id, phone_number) VALUES (%s, %s)", 
                           (user_id, phone_number))
            conn.commit()
            flash("New employee added successfully.")
        except mysql.connector.Error as err:
            flash(f"Error: {err}")
        finally:
            cursor.close()

    # Fetch employee data for display
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT e.employee_id, u.username, COUNT(DISTINCT c.customer_id) AS customer_count, 
                   COUNT(DISTINCT p.purchase_id) AS product_count
            FROM Employee e
            JOIN User u ON e.user_id = u.user_id
            LEFT JOIN Customer c ON c.added_by_employee_id = e.employee_id
            LEFT JOIN Purchase p ON p.customer_id = c.customer_id
            GROUP BY e.employee_id, u.username
        """)
        employees_data = cursor.fetchall()
    except mysql.connector.Error as err:
        flash(f"Error: {err}")
        employees_data = []
    finally:
        cursor.close()

    return render_template('admin_dashboard.html', employees=employees_data)

# Route for Analytics Dashboard
@app.route('/analytics_dashboard')
def analytics_dashboard():
    return render_template('analytics_dashboard.html')

@app.route('/employee_dashboard', methods=['GET', 'POST'])
def employee_dashboard():
    if request.method == 'POST':
        # Process new sale
        customer_name = request.form['customer_name']
        customer_phone = request.form['customer_phone']
        product_name = request.form['product']
        amount = request.form['amount']
        location = request.form['place']
        purchase_date = request.form['purchase_date']
        purchase_time = request.form['purchase_time']
        payment_method = request.form['payment_method']

        cursor = conn.cursor()
        try:
            # First, try to get the product ID
            cursor.execute("SELECT product_id FROM Product WHERE product_name = %s", (product_name,))
            product = cursor.fetchone()

            if product is None:
                # Product does not exist, so we add it to the Product table
                cursor.execute("INSERT INTO Product (product_name) VALUES (%s)", (product_name,))
                conn.commit()
                product_id = cursor.lastrowid  # Get the newly created product_id
                flash(f"New product '{product_name}' added successfully.")
            else:
                product_id = product[0]  # Get the existing product_id

            # Insert into Purchase table
            cursor.execute(
                "INSERT INTO Purchase (customer_name, phone_number, product_id, amount, location, payment_method, purchase_date, purchase_time) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                (customer_name, customer_phone, product_id, amount, location, payment_method, purchase_date, purchase_time)
            )
            conn.commit()
            flash("Sale added successfully.")
        except mysql.connector.Error as err:
            flash(f"Error: {err}")
            conn.rollback()  # Rollback in case of error
        finally:
            cursor.close()

    return render_template('employee_dashboard.html')
# Route for logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
