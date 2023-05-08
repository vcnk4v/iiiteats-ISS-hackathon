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
        cursor.execute("INSERT INTO UserDetails (contact, email, room_no, hostel, name,password) VALUES (?, ?, ?, ?,?, ?);",
                       (contact, email, room_no, hostel, name,password))
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
            return redirect('/main')
        else:
            message = "Credentials not found. "
            return render_template('login.html', message=message)
    return render_template('login.html')
    # Render the login form without any message
    



@app.route('/take_orders')
def take_orders():
    conn = sqlite3.connect('./iiiteats.db')
    cursor = conn.cursor()
    cursor.execute('''SELECT Orders.order_id, Canteens.name, Orders.location, Users.name, Orders.delivery_status, orderitems.quantity, Orders.user_id
FROM Orders
JOIN Canteens ON Orders.canteen_id = Canteens.canteen_id
JOIN Users ON Orders.user_id = Users.id
JOIN orderitems ON Orders.order_id = orderitems.order_id
WHERE Orders.delivery_status NOT LIKE 'delivered';
''')
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
            else:
                cursor.execute("INSERT INTO Deliveries (order_id, user_id, status) VALUES (?, ?, ?)", (order_id, user_id, 'in progress'))
                cursor.execute("UPDATE Orders SET delivery_status='in progress' WHERE order_id=?", (order_id,))
            # Insert the delivery details into the Deliveries table
           
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

@app.route('/ratings')
def ratings():
    # Retrieve ratings from the database
    conn = sqlite3.connect('iiiteats.db')
    cursor = conn.cursor()
    cursor.execute("""SELECT Rating.rating_id, Users.name, Canteens.name, Rating.rating, Rating.review
        FROM Rating
        JOIN Users ON Rating.user_id = Users.id
        JOIN Canteens ON Rating.canteen_id = Canteens.canteen_id""")
    ratings = cursor.fetchall()
    conn.close()
    
    # Pass the ratings data to the template
    return render_template('ratings.html', ratings=ratings)

@app.route('/submit-rating', methods=['POST'])
def submit_rating():
    # Retrieve the submitted data from the form
    canteen_id = request.form['canteen_id']
    rating = request.form['rate']
    review = request.form['review']
    user_id = session['user_id']

    # Connect to the database
    conn = sqlite3.connect('iiiteats.db')
    cursor = conn.cursor()

    # Insert the rating into the Rating table
    cursor.execute("INSERT INTO Rating (user_id, canteen_id, rating,review) VALUES (?, ?, ?,?);",
                   (user_id, canteen_id, rating,review))
    conn.commit()

    # Close the database connection
    conn.close()

    # Redirect to a confirmation page or any other desired page
    return redirect('/ratings')


@app.route('/profile')
def profile():
    user_id = session['user_id']
    
    conn = sqlite3.connect('iiiteats.db')
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM UserDetails WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    
        # Assuming the column order is: id, contact, email, room_no, hostel, name, password
    user = {
        'id': user[0],
        'contact': user[1],
        'email': user[2],
        'room_no': user[3],
        'hostel': user[4],
        'name': user[5],
        'password': user[6]
    }
    # Retrieve user details from the database

    cursor.execute("""
    SELECT orders.order_id, orders.user_id, orders.order_total, orders.delivery_status, canteens.name, orders.location
    FROM orders
    JOIN canteens ON orders.canteen_id = canteens.canteen_id
    WHERE orders.user_id = ?""", (user_id,))

    orders = cursor.fetchall()
    old_orders = []
    old_deliveries = []
    for order in orders:
        old_orders.append({
            'order_id': order[0],
            'user_id': order[1],
            'order_total': order[2],
            'delivery_status': order[3],
            'canteen_name': order[4],
            'location': order[5]
        })
    cursor.execute("SELECT * FROM Deliveries WHERE user_id = ?", (user_id,))
    deliveries = cursor.fetchall()
        
    for delivery in deliveries:
        # Assuming the column order is: delivery_id, order_id, user_id, status
        old_deliveries.append({
            'delivery_id': delivery[0],
            'order_id': delivery[1],
            'user_id': delivery[2],
            'status': delivery[3]
        })
  
    # Close the database connection
    conn.commit()
    conn.close()

    
    return render_template('profile.html', user=user, old_orders=old_orders, old_deliveries=old_deliveries)

@app.route('/update-user-details', methods=['POST'])
def update_user_details():
    conn = sqlite3.connect('iiiteats.db')
    cursor = conn.cursor()
    user_id = session['user_id']
    contact = request.form['contact']
    email = request.form['email']
    room_no = request.form['room_no']
    hostel = request.form['hostel']
    
    # Update user details in the database
    cursor.execute("UPDATE UserDetails SET contact = ?, email = ?, room_no = ?, hostel = ? WHERE id = ?",
                   (contact, email, room_no, hostel, user_id))
    conn.commit()
        # Close the database connection
    conn.close()
    return redirect('/profile')

# Route to handle password change
@app.route('/change-password', methods=['POST'])
def change_password():
    # Check if the user is logged in
    if 'user_id' not in session:
        return redirect('/login')  # Redirect to login if not logged in

    # Retrieve the current and new passwords from the form
    user_id = session['user_id']
    current_password = request.form['current_password']
    new_password = request.form['new_password']
    confirm_password = request.form['confirm_password']

    # Validate the new password and confirm password
    if new_password != confirm_password:
        return "New password and confirm password do not match."

    # Verify the current password against the stored password in the database
    conn = sqlite3.connect('iiiteats.db')
    cursor = conn.cursor()
    cursor.execute("SELECT password FROM UserDetails WHERE id = ?", (user_id,))
    stored_password = cursor.fetchone()[0]
    conn.close()

    if current_password != stored_password:
        return "Incorrect current password."

    # Update the password in the database
    conn = sqlite3.connect('iiiteats.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE UserDetails SET password = ? WHERE id = ?", (new_password, user_id))
    conn.commit()
    conn.close()

    return redirect('/profile')

@app.route('/canteens')
def canteens():
    return render_template("canteens.html")

@app.route('/menu.html', methods=['GET'])
def menu():
    canteen_id = request.args.get('canteenId')
    conn = sqlite3.connect('iiiteats.db')  # Replace 'your_database.db' with your actual database file path
    cursor = conn.cursor()

    # Execute a query to retrieve menu items for the specified canteen_id
    query = "SELECT menu_id, item_name, item_price FROM menu WHERE canteen_id = ?"
    cursor.execute(query, (canteen_id,))
    menu_items = cursor.fetchall()

    conn.close()
    
    return render_template('menu.html', menu_items=menu_items, canteen_id=canteen_id)



@app.route('/place_order', methods=['POST'])
def place_order():
    # Retrieve the order details from the form submission
    menu_id = request.form.get('menuId')
    canteen_id = request.form.get('canteenId')
    location = request.form.get('location')
    quantity = int(request.form.get('quantity'))

    # Connect to the database
    conn = sqlite3.connect('iiiteats.db')
    cursor = conn.cursor()

    try:
        # Insert the order details into the "orders" table
        cursor.execute("INSERT INTO orders (user_id, order_total, delivery_status, canteen_id, location) VALUES (?, ?, ?, ?, ?)",
                       (session['user_id'], 0, 'pending', canteen_id, location))
        order_id = cursor.lastrowid

        # Retrieve the menu item details
        cursor.execute("SELECT item_name, item_price FROM menu WHERE menu_id = ?", (menu_id,))
        menu_item = cursor.fetchone()
        item_price = int(menu_item[1])


        # Insert the order item details into the "orderitems" table
        cursor.execute("INSERT INTO orderitems (order_id, menu_id, quantity) VALUES (?, ?, ?)",
                       (order_id, menu_id, quantity))

        # Calculate the order total
        order_total = (item_price + 20) * quantity

        # Update the order total in the "orders" table
        cursor.execute("UPDATE orders SET order_total = ? WHERE order_id = ?", (order_total, order_id))

        # Commit the changes to the database
        conn.commit()

        flash('Order placed successfully!', 'success')
        return redirect('/canteens')

    except Exception as e:
        conn.rollback()
        flash('Error occurred while placing the order!', 'error')
        print(str(e))

    finally:
        # Close the database connection
        conn.close()

    return redirect('/canteens')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/logout')
def logout():
    # Clear the session
    session.clear()
    return render_template('home.html')

@app.route('/cancel/<order_id>')
def cancel(order_id):
    conn = sqlite3.connect('iiiteats.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM ORDERS WHERE order_id=?",order_id)
    cursor.execute("DELETE FROM orderitems WHERE order_id=?",order_id)
    conn.commit()
    conn.close()
    return redirect('/profile')


@app.route('/main')
def main():
    return render_template('main.html')
if __name__ == '__main__':
    app.run(debug=True)

