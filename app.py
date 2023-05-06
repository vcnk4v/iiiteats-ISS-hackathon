from flask import Flask, render_template, redirect, session, request, flash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

db_name = './iiiteats.db'

@app.route('/')
def home():
    return render_template('home.html')
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        room_no = request.form['room_no']
        email = request.form['email']
        password = request.form['password']
        contact = request.form['contact']
        hostel = request.form['hostel']

        # Connect to the database
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()

        # Insert user details into "UserDetails" table
        cursor.execute("INSERT INTO UserDetails (contact, email, room_no, hostel, password) VALUES (?, ?, ?, ?, ?);",
                       (contact, email, room_no, hostel, password))
        conn.commit()

        # Get the user ID after inserting into "UserDetails" table
        user_id = cursor.lastrowid

        # Insert user name into "Users" table
        cursor.execute("INSERT INTO Users (id, name) VALUES (?, ?);", (user_id, name))
        conn.commit()

        # Close the database connection
        conn.close()

        # Store the user ID in the session
        session['user_id'] = user_id

        # Redirect to the login page or any other desired page
        return redirect('/login')

    # Render the sign-up form
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Connect to the database
        conn = sqlite3.connect('iiiteats.db')
        cursor = conn.cursor()

        # Check if the credentials exist in the "UserDetails" table
        cursor.execute("SELECT * FROM UserDetails WHERE email = ? AND password = ?", (email, password))
        user = cursor.fetchone()

        # Close the database connection
        conn.close()

        if user:
            user_id = user[0]

            # Store the user ID in the session
            session['user_id'] = user_id

            # Redirect to the canteen page or any other desired page
            return redirect('/delivery-dashboard')
        else:
            message = "Credentials not found. "
            return render_template('login.html', message=message)
    return render_template('login.html')
    # Render the login form without any message
    



@app.route('/take_orders')
def take_orders():
    conn = sqlite3.connect('./iiiteats.db')
    cursor = conn.cursor()
    cursor.execute('''SELECT Orders.order_id, Canteens.name, Orders.location, Users.name, Orders.delivery_status
                      FROM Orders
                      JOIN Canteens ON Orders.canteen_id = Canteens.canteen_id
                      JOIN Users ON Orders.user_id = Users.id AND orders.delivery_status not like "delivered"''')
    orders_data = cursor.fetchall()
    conn.close()
    return render_template('take_orders.html', orders=orders_data)

@app.route('/order_items/<order_id>')
def order_items(order_id):
    conn = sqlite3.connect('iiiteats.db')
    cursor = conn.cursor()
    cursor.execute('''
    SELECT Menu.item_name, OrderItems.quantity, Menu.item_price
    FROM OrderItems
    JOIN Menu ON OrderItems.menu_id = Menu.menu_id
    JOIN Orders ON OrderItems.order_id = Orders.order_id
    WHERE OrderItems.order_id = ? AND orders.delivery_status not like 'delivered'
''', (order_id,))
    order_items_data = cursor.fetchall()
    conn.close()
    return render_template('order_items.html', order_items=order_items_data)



@app.route('/deliver', methods=['GET', 'POST'])
def deliver():
    if request.method == 'POST':
        order_id = request.form['order_id']
        status = 'in progress'
        
        # Retrieve the logged-in user's ID from the session
        user_id = session['user_id']
       

        # Check if the order_id already exists in the Deliveries table
        with sqlite3.connect('./iiiteats.db') as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT delivery_id FROM Deliveries WHERE order_id=?", (order_id,))
            delivery = cursor.fetchone()
            if delivery:
                # Order already exists in Deliveries table, do nothing
                flash('Order is already being delivered')
                cursor.execute("UPDATE Orders SET delivery_status='in progress' WHERE order_id=?", (order_id,))
                return redirect('/take_orders')

            # Insert the delivery details into the Deliveries table
            cursor.execute("INSERT INTO Deliveries (order_id, user_id, status) VALUES (?, ?, ?)", (order_id, user_id, status))
            cursor.execute("UPDATE Orders SET delivery_status='in progress' WHERE order_id=?", (order_id,))
            conn.commit()
        flash('Delivery accepted!')
        return redirect('/take_orders')

    return redirect('/take_orders')


@app.route('/delivery-dashboard')
def delivery_dashboard():
    user_id = session.get('user_id')  # Use session.get() to avoid KeyError if user_id is not set

    # Check if user_id is not set in session or the user is not logged in
    if user_id is None:
        return redirect('/login')  # Redirect to the login page or any other desired page

    # Connect to the SQLite database
    conn = sqlite3.connect('./iiiteats.db')
    cursor = conn.cursor()

    # Fetch the relevant orders assigned to the current user from the database
    cursor.execute("""
        SELECT deliveries.order_id, users.name, deliveries.status
        FROM deliveries
        JOIN orders ON deliveries.order_id = orders.order_id
        JOIN users ON orders.user_id = users.id
        WHERE deliveries.user_id = ?

        """, (user_id,))
    assigned_orders = cursor.fetchall()
    conn.commit()

    # Close the database connection
    conn.close()

    # Render the delivery dashboard template with the retrieved orders
    return render_template('delivery_dashboard.html', orders=assigned_orders)



@app.route('/mark-delivered/<int:order_id>', methods=['POST'])
def mark_delivered(order_id):
    # Update the order status in the database to 'Delivered' for the specified order_id
    conn = sqlite3.connect('./iiiteats.db')
    cursor = conn.cursor()

    cursor.execute("DELETE FROM deliveries WHERE order_id=?", (order_id,))
    cursor.execute("UPDATE orders SET delivery_status='Delivered' WHERE order_id=?", (order_id,))

    conn.commit()
    # Close the database connection
    conn.close()
    # Redirect the delivery personnel back to the delivery dashboard
    return redirect('/delivery-dashboard')

@app.route('/search-menu', methods=['GET'])
def search_menu():
    # Retrieve the search query, canteen selection, and price range from the request parameters
    conn = sqlite3.connect('./iiiteats.db')
    cursor = conn.cursor()
    query = request.args.get('query', '')
    canteen = request.args.get('canteen', '')
    min_price = request.args.get('min_price', '')
    max_price = request.args.get('max_price', '')

    # Construct the SQL query based on the provided filters
    sql = """
        SELECT Menu.item_name, Menu.item_price, Canteens.name
        FROM Menu
        JOIN Canteens ON Menu.canteen_id = Canteens.canteen_id
        WHERE Menu.item_name LIKE ? 
        AND (Canteens.name LIKE ? OR ? = '')
        AND (Menu.item_price >= ? OR ? = '') AND (Menu.item_price <= ? OR ? = '')
    """
    params = [f"%{query}%", f"%{canteen}%", canteen, min_price, min_price, max_price, max_price]

    # Execute the SQL query on the Menu and Canteens tables
    cursor.execute(sql, params)
    menu_items = cursor.fetchall()

    # Retrieve the list of all canteens for the dropdown and extract the canteen names
    cursor.execute("SELECT DISTINCT name FROM Canteens")
    canteens = [canteen[0] for canteen in cursor.fetchall()]
    conn.commit()
    conn.close()
    # Render the menu page template with the filtered menu items and form values
    return render_template('search.html', menu_items=menu_items, query=query, canteens=canteens, min_price=min_price, max_price=max_price)

if __name__ == '__main__':
    app.run(debug=True)
