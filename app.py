import sqlite3
import os
import math
from datetime import date, datetime
from functools import wraps
from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash, g, jsonify
)
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'milk_platform_secret_key_2026'
DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database.db')


# ─── Database helpers ───────────────────────────────────────────────────────────
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(DATABASE)
    db.execute("PRAGMA foreign_keys = ON")
    db.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('farmer', 'consumer', 'delivery_partner')),
            location TEXT DEFAULT '',
            latitude REAL DEFAULT 0,
            longitude REAL DEFAULT 0,
            wallet_balance REAL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS farmers (
            farmer_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL UNIQUE,
            farm_name TEXT NOT NULL,
            location TEXT NOT NULL,
            milk_capacity_per_day REAL DEFAULT 0,
            price_per_litre REAL DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        );

        CREATE TABLE IF NOT EXISTS milk_listings (
            listing_id INTEGER PRIMARY KEY AUTOINCREMENT,
            farmer_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            total_quantity REAL DEFAULT 0,
            price_per_litre REAL NOT NULL,
            collection_time TEXT DEFAULT '',
            delivery_estimate TEXT DEFAULT '',
            is_closed INTEGER DEFAULT 0,
            FOREIGN KEY (farmer_id) REFERENCES farmers(farmer_id)
        );

        CREATE TABLE IF NOT EXISTS orders (
            order_id INTEGER PRIMARY KEY AUTOINCREMENT,
            consumer_id INTEGER NOT NULL,
            farmer_id INTEGER NOT NULL,
            listing_id INTEGER NOT NULL,
            quantity REAL NOT NULL,
            order_date TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            FOREIGN KEY (consumer_id) REFERENCES users(user_id),
            FOREIGN KEY (farmer_id) REFERENCES farmers(farmer_id),
            FOREIGN KEY (listing_id) REFERENCES milk_listings(listing_id)
        );

        CREATE TABLE IF NOT EXISTS products (
            product_id INTEGER PRIMARY KEY AUTOINCREMENT,
            farmer_id INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            quantity REAL NOT NULL,
            price REAL NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (farmer_id) REFERENCES farmers(farmer_id)
        );

        CREATE TABLE IF NOT EXISTS product_orders (
            product_order_id INTEGER PRIMARY KEY AUTOINCREMENT,
            consumer_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity REAL NOT NULL,
            total_price REAL NOT NULL,
            order_date TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            FOREIGN KEY (consumer_id) REFERENCES users(user_id),
            FOREIGN KEY (product_id) REFERENCES products(product_id)
        );

        CREATE TABLE IF NOT EXISTS subscriptions (
            subscription_id INTEGER PRIMARY KEY AUTOINCREMENT,
            consumer_id INTEGER NOT NULL,
            farmer_id INTEGER NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            quantity REAL NOT NULL,
            price_per_day REAL NOT NULL,
            total_amount REAL NOT NULL,
            status TEXT DEFAULT 'active',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (consumer_id) REFERENCES users(user_id),
            FOREIGN KEY (farmer_id) REFERENCES farmers(farmer_id)
        );

        CREATE TABLE IF NOT EXISTS wallet_transactions (
            transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            type TEXT NOT NULL CHECK(type IN ('recharge', 'payment', 'refund')),
            description TEXT,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        );

        CREATE TABLE IF NOT EXISTS vacation_dates (
            vacation_id INTEGER PRIMARY KEY AUTOINCREMENT,
            consumer_id INTEGER NOT NULL,
            vacation_date TEXT NOT NULL,
            FOREIGN KEY (consumer_id) REFERENCES users(user_id)
        );

        CREATE TABLE IF NOT EXISTS delivery_tasks (
            delivery_id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            pickup_location TEXT NOT NULL,
            pickup_latitude REAL NOT NULL,
            pickup_longitude REAL NOT NULL,
            delivery_address TEXT NOT NULL,
            delivery_latitude REAL NOT NULL,
            delivery_longitude REAL NOT NULL,
            quantity REAL NOT NULL,
            delivery_partner_id INTEGER,
            status TEXT DEFAULT 'Pending',
            delivery_time TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (order_id) REFERENCES orders(order_id),
            FOREIGN KEY (delivery_partner_id) REFERENCES users(user_id)
        );
    ''')
    db.commit()
    db.close()


# ─── Haversine distance (km) ────────────────────────────────────────────────────
def haversine(lat1, lon1, lat2, lon2):
    """Return distance in km between two lat/lng points."""
    R = 6371  # Earth radius in km
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (math.sin(d_lat / 2) ** 2 +
         math.cos(math.radians(lat1)) *
         math.cos(math.radians(lat2)) *
         math.sin(d_lon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


# ─── Auth decorator ─────────────────────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in first.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


def farmer_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get('role') != 'farmer':
            flash('Access denied. Farmer account required.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


def consumer_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get('role') != 'consumer':
            flash('Access denied. Consumer account required.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


def delivery_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get('role') != 'delivery_partner':
            flash('Access denied. Delivery Partner account required.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


# ─── Routes: Home ────────────────────────────────────────────────────────────────
@app.route('/')
def index():
    db = get_db()
    farmer_count = db.execute('SELECT COUNT(*) FROM farmers').fetchone()[0]
    listing_count = db.execute(
        'SELECT COUNT(*) FROM milk_listings WHERE date = ?', (str(date.today()),)
    ).fetchone()[0]
    order_count = db.execute('SELECT COUNT(*) FROM orders').fetchone()[0]
    return render_template('index.html',
                           farmer_count=farmer_count,
                           listing_count=listing_count,
                           order_count=order_count)


# ─── Routes: Auth ────────────────────────────────────────────────────────────────
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name'].strip()
        email = request.form['email'].strip().lower()
        password = request.form['password']
        role = request.form['role']

        # Location fields (common to both roles)
        user_location = request.form.get('user_location', '').strip() or 'Not specified'
        user_lat = float(request.form.get('user_latitude', 0) or 0)
        user_lng = float(request.form.get('user_longitude', 0) or 0)

        if not all([name, email, password, role]):
            flash('All fields are required.', 'danger')
            return redirect(url_for('register'))

        if user_lat == 0 and user_lng == 0:
            flash('Please provide your location by clicking "Detect My Location" or entering coordinates manually.', 'danger')
            return redirect(url_for('register'))

        db = get_db()
        existing = db.execute('SELECT user_id FROM users WHERE email = ?', (email,)).fetchone()
        if existing:
            flash('Email already registered.', 'danger')
            return redirect(url_for('register'))

        hashed = generate_password_hash(password)
        cursor = db.execute(
            'INSERT INTO users (name, email, password, role, location, latitude, longitude) VALUES (?, ?, ?, ?, ?, ?, ?)',
            (name, email, hashed, role, user_location, user_lat, user_lng)
        )
        user_id = cursor.lastrowid

        if role == 'farmer':
            farm_name = request.form.get('farm_name', '').strip() or f"{name}'s Farm"
            farm_location = request.form.get('location', '').strip() or user_location
            capacity = float(request.form.get('milk_capacity', 0) or 0)
            price = float(request.form.get('price_per_litre', 0) or 0)
            db.execute(
                'INSERT INTO farmers (user_id, farm_name, location, milk_capacity_per_day, price_per_litre) VALUES (?, ?, ?, ?, ?)',
                (user_id, farm_name, farm_location, capacity, price)
            )

        db.commit()
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        password = request.form['password']

        db = get_db()
        user = db.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['user_id']
            session['user_name'] = user['name']
            session['role'] = user['role']
            session['user_lat'] = user['latitude']
            session['user_lng'] = user['longitude']
            session['user_location'] = user['location']

            if user['role'] == 'farmer':
                farmer = db.execute(
                    'SELECT farmer_id FROM farmers WHERE user_id = ?', (user['user_id'],)
                ).fetchone()
                if farmer:
                    session['farmer_id'] = farmer['farmer_id']
                return redirect(url_for('farmer_dashboard'))
            elif user['role'] == 'delivery_partner':
                return redirect(url_for('delivery_dashboard'))
            else:
                session['wallet_balance'] = user['wallet_balance']
                return redirect(url_for('consumer_dashboard'))
        else:
            flash('Invalid email or password.', 'danger')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))


# ─── Routes: Farmer Dashboard ───────────────────────────────────────────────────
@app.route('/farmer/dashboard')
@login_required
@farmer_required
def farmer_dashboard():
    db = get_db()
    farmer_id = session.get('farmer_id')
    today = str(date.today())

    farmer = db.execute(
        'SELECT f.*, u.name, u.email FROM farmers f JOIN users u ON f.user_id = u.user_id WHERE f.farmer_id = ?',
        (farmer_id,)
    ).fetchone()

    today_listings = db.execute(
        'SELECT * FROM milk_listings WHERE farmer_id = ? AND date = ?',
        (farmer_id, today)
    ).fetchall()

    total_listed = sum(l['total_quantity'] for l in today_listings)

    today_orders = db.execute('''
        SELECT o.*, u.name as consumer_name
        FROM orders o
        JOIN users u ON o.consumer_id = u.user_id
        WHERE o.farmer_id = ? AND o.order_date = ?
        ORDER BY o.order_id DESC
    ''', (farmer_id, today)).fetchall()

    total_ordered = sum(o['quantity'] for o in today_orders)
    remaining = total_listed - total_ordered

    all_orders = db.execute('''
        SELECT o.*, u.name as consumer_name, ml.date as listing_date
        FROM orders o
        JOIN users u ON o.consumer_id = u.user_id
        JOIN milk_listings ml ON o.listing_id = ml.listing_id
        WHERE o.farmer_id = ?
        ORDER BY o.order_id DESC
        LIMIT 20
    ''', (farmer_id,)).fetchall()

    products = db.execute(
        'SELECT * FROM products WHERE farmer_id = ? ORDER BY created_at DESC',
        (farmer_id,)
    ).fetchall()

    product_orders = db.execute('''
        SELECT po.*, u.name as consumer_name, p.product_name
        FROM product_orders po
        JOIN users u ON po.consumer_id = u.user_id
        JOIN products p ON po.product_id = p.product_id
        WHERE p.farmer_id = ?
        ORDER BY po.product_order_id DESC
        LIMIT 20
    ''', (farmer_id,)).fetchall()

    return render_template('farmer_dashboard.html',
                           farmer=farmer,
                           today_listings=today_listings,
                           total_listed=total_listed,
                           total_ordered=total_ordered,
                           remaining=max(0, remaining),
                           today_orders=today_orders,
                           all_orders=all_orders,
                           products=products,
                           product_orders=product_orders,
                           today=today)


# ─── Routes: Add milk listing ───────────────────────────────────────────────────
@app.route('/farmer/add-milk', methods=['GET', 'POST'])
@login_required
@farmer_required
def add_milk():
    if request.method == 'POST':
        farmer_id = session.get('farmer_id')
        listing_date = request.form['date']
        total_qty = float(request.form.get('total_quantity', 0) or 0)
        price = float(request.form['price_per_litre'])
        collection_time = request.form.get('collection_time', '').strip()
        db = get_db()
        db.execute(
            'INSERT INTO milk_listings (farmer_id, date, total_quantity, price_per_litre, collection_time) VALUES (?, ?, ?, ?, ?)',
            (farmer_id, listing_date, total_qty, price, collection_time)
        )
        db.commit()
        flash('Milk listing added successfully!', 'success')
        return redirect(url_for('farmer_dashboard'))

    return render_template('add_milk.html', today=str(date.today()))


# ─── Routes: Close today's sellings ──────────────────────────────────────────
@app.route('/farmer/toggle-listing/<int:listing_id>', methods=['POST'])
@login_required
@farmer_required
def toggle_listing(listing_id):
    db = get_db()
    farmer_id = session.get('farmer_id')

    listing = db.execute(
        'SELECT * FROM milk_listings WHERE listing_id = ? AND farmer_id = ?',
        (listing_id, farmer_id)
    ).fetchone()

    if not listing:
        flash('Listing not found.', 'danger')
        return redirect(url_for('farmer_dashboard'))

    new_status = 1 if listing['is_closed'] == 0 else 0
    db.execute(
        'UPDATE milk_listings SET is_closed = ? WHERE listing_id = ?',
        (new_status, listing_id)
    )
    db.commit()
    msg = "Selling CLOSED for this listing." if new_status == 1 else "Selling RE-OPENED for this listing."
    flash(msg, 'info')
    return redirect(url_for('farmer_dashboard'))


# ─── Routes: Farmer orders view ─────────────────────────────────────────────────
@app.route('/farmer/orders')
@login_required
@farmer_required
def farmer_orders():
    db = get_db()
    farmer_id = session.get('farmer_id')

    orders = db.execute('''
        SELECT o.*, u.name as consumer_name, ml.date as listing_date, ml.price_per_litre
        FROM orders o
        JOIN users u ON o.consumer_id = u.user_id
        JOIN milk_listings ml ON o.listing_id = ml.listing_id
        WHERE o.farmer_id = ?
        ORDER BY o.order_id DESC
    ''', (farmer_id,)).fetchall()

    product_orders = db.execute('''
        SELECT po.*, u.name as consumer_name, p.product_name
        FROM product_orders po
        JOIN users u ON po.consumer_id = u.user_id
        JOIN products p ON po.product_id = p.product_id
        WHERE p.farmer_id = ?
        ORDER BY po.product_order_id DESC
    ''', (farmer_id,)).fetchall()

    return render_template('orders.html',
                           orders=orders,
                           product_orders=product_orders,
                           role='farmer')


@app.route('/farmer/update-order-status/<int:order_id>', methods=['POST'])
@login_required
@farmer_required
def update_order_status(order_id):
    status = request.form['status']
    db = get_db()
    db.execute('UPDATE orders SET status = ? WHERE order_id = ?', (status, order_id))
    db.commit()
    flash('Order status updated.', 'success')
    return redirect(url_for('farmer_orders'))


@app.route('/farmer/update-product-order-status/<int:order_id>', methods=['POST'])
@login_required
@farmer_required
def update_product_order_status(order_id):
    status = request.form['status']
    db = get_db()
    # Verify this product order belongs to the farmer
    po = db.execute('''
        SELECT po.product_order_id FROM product_orders po
        JOIN products p ON po.product_id = p.product_id
        WHERE po.product_order_id = ? AND p.farmer_id = ?
    ''', (order_id, session.get('farmer_id'))).fetchone()
    if po:
        db.execute('UPDATE product_orders SET status = ? WHERE product_order_id = ?', (status, order_id))
        db.commit()
        flash('Product order status updated.', 'success')
    else:
        flash('Order not found.', 'danger')
    return redirect(url_for('farmer_orders'))


# ─── Routes: Products ───────────────────────────────────────────────────────────
@app.route('/farmer/products', methods=['GET', 'POST'])
@login_required
@farmer_required
def farmer_products():
    db = get_db()
    farmer_id = session.get('farmer_id')

    if request.method == 'POST':
        product_name = request.form['product_name']
        quantity = float(request.form['quantity'])
        price = float(request.form['price'])

        db.execute(
            'INSERT INTO products (farmer_id, product_name, quantity, price) VALUES (?, ?, ?, ?)',
            (farmer_id, product_name, quantity, price)
        )
        db.commit()
        flash(f'{product_name} added successfully!', 'success')
        return redirect(url_for('farmer_products'))

    products = db.execute(
        'SELECT * FROM products WHERE farmer_id = ? ORDER BY created_at DESC',
        (farmer_id,)
    ).fetchall()

    return render_template('products.html', products=products, role='farmer')


@app.route('/farmer/delete-product/<int:product_id>', methods=['POST'])
@login_required
@farmer_required
def delete_product(product_id):
    db = get_db()
    try:
        db.execute('DELETE FROM products WHERE product_id = ? AND farmer_id = ?',
                   (product_id, session.get('farmer_id')))
        db.commit()
        flash('Product removed.', 'success')
    except sqlite3.IntegrityError:
        flash('Cannot delete this product because it has existing orders. Consider setting its quantity to 0 instead.', 'danger')
    
    return redirect(url_for('farmer_products'))


# ─── Routes: Consumer Dashboard ─────────────────────────────────────────────────
@app.route('/consumer/dashboard')
@login_required
@consumer_required
def consumer_dashboard():
    db = get_db()
    today = str(date.today())

    # Consumer's coordinates from session
    consumer_lat = session.get('user_lat', 0)
    consumer_lng = session.get('user_lng', 0)
    max_distance_km = 7  # Show farmers within 7 km

    farmers = db.execute('''
        SELECT f.*, u.name as farmer_name, u.latitude as farmer_lat, u.longitude as farmer_lng,
        (SELECT SUM(ml.total_quantity)
         FROM milk_listings ml WHERE ml.farmer_id = f.farmer_id AND ml.date = ?) as total_available,
        (SELECT COALESCE(SUM(o.quantity), 0)
         FROM orders o WHERE o.farmer_id = f.farmer_id
         AND o.order_date = ?) as total_ordered
        FROM farmers f
        JOIN users u ON f.user_id = u.user_id
    ''', (today, today)).fetchall()

    # Get freshness info for today's listings per farmer
    freshness_map = {}
    all_listings = db.execute('''
        SELECT farmer_id, collection_time
        FROM milk_listings WHERE date = ? AND collection_time != ''
        ORDER BY listing_id DESC
    ''', (today,)).fetchall()
    for fl in all_listings:
        if fl['farmer_id'] not in freshness_map:
            freshness_map[fl['farmer_id']] = {
                'collection_time': fl['collection_time']
            }

    farmer_list = []
    for f in farmers:
        farmer_lat = f['farmer_lat'] or 0
        farmer_lng = f['farmer_lng'] or 0

        # Calculate distance between consumer and farmer
        if consumer_lat != 0 and consumer_lng != 0 and farmer_lat != 0 and farmer_lng != 0:
            dist = haversine(consumer_lat, consumer_lng, farmer_lat, farmer_lng)
        else:
            dist = 0  # If coordinates missing, show by default

        # Only include farmers within the max distance and NOT closed
        if dist <= max_distance_km or consumer_lat == 0 or farmer_lat == 0:
            total_avail = f['total_available'] or 0
            total_ord = f['total_ordered'] or 0
            remaining = total_avail - total_ord
            
            # Check if farmer has any open listing for today
            is_closed = db.execute(
                'SELECT is_closed FROM milk_listings WHERE farmer_id = ? AND date = ?',
                (f['farmer_id'], today)
            ).fetchone()
            
            if not is_closed or is_closed['is_closed'] == 0:
                freshness = freshness_map.get(f['farmer_id'], {})
                farmer_list.append({
                    'farmer_id': f['farmer_id'],
                    'farmer_name': f['farmer_name'],
                    'farm_name': f['farm_name'],
                    'location': f['location'],
                    'milk_capacity_per_day': f['milk_capacity_per_day'],
                    'price_per_litre': f['price_per_litre'],
                    'total_available': total_avail,
                    'remaining': max(0, remaining),
                    'distance_km': round(dist, 1),
                    'collection_time': freshness.get('collection_time', '')
                })

    # Sort by distance (nearest first)
    farmer_list.sort(key=lambda x: x['distance_km'])

    # Sync wallet in session
    user = db.execute('SELECT wallet_balance FROM users WHERE user_id = ?', (session['user_id'],)).fetchone()
    session['wallet_balance'] = user['wallet_balance']

    # Check for active vacation (tomorrow)
    from datetime import timedelta
    tomorrow = (date.today() + timedelta(days=1)).strftime('%Y-%m-%d')
    vacation_active = db.execute('SELECT 1 FROM vacation_dates WHERE consumer_id = ? AND vacation_date = ?', 
                                (session['user_id'], tomorrow)).fetchone()

    my_orders = db.execute('''
        SELECT o.*, f.farm_name, u.name as farmer_name, ml.price_per_litre
        FROM orders o
        JOIN farmers f ON o.farmer_id = f.farmer_id
        JOIN users u ON f.user_id = u.user_id
        JOIN milk_listings ml ON o.listing_id = ml.listing_id
        WHERE o.consumer_id = ?
        ORDER BY o.order_id DESC
        LIMIT 10
    ''', (session['user_id'],)).fetchall()

    return render_template('consumer_dashboard.html',
                           farmers=farmer_list,
                           my_orders=my_orders,
                           today=today,
                           max_distance=max_distance_km,
                           user_location=session.get('user_location', ''),
                           vacation_active=vacation_active)


# ─── Routes: Consumer place order ───────────────────────────────────────────────
@app.route('/consumer/order/<int:farmer_id>', methods=['GET', 'POST'])
@login_required
@consumer_required
def place_order(farmer_id):
    db = get_db()
    today = str(date.today())

    farmer = db.execute('''
        SELECT f.*, u.name as farmer_name
        FROM farmers f JOIN users u ON f.user_id = u.user_id
        WHERE f.farmer_id = ?
    ''', (farmer_id,)).fetchone()

    if not farmer:
        flash('Farmer not found.', 'danger')
        return redirect(url_for('consumer_dashboard'))

    listings = db.execute(
        'SELECT * FROM milk_listings WHERE farmer_id = ? AND date >= ? ORDER BY date ASC',
        (farmer_id, today)
    ).fetchall()

    if request.method == 'POST':
        listing_id_str = request.form.get('listing_id', '')
        if not listing_id_str:
            flash('Please select a delivery date first.', 'warning')
            return redirect(url_for('place_order', farmer_id=farmer_id))
            
        listing_id = int(listing_id_str)
        quantity = float(request.form['quantity'])

        listing = db.execute(
            'SELECT * FROM milk_listings WHERE listing_id = ?', (listing_id,)
        ).fetchone()

        if not listing:
            flash('Listing not found.', 'danger')
            return redirect(url_for('place_order', farmer_id=farmer_id))
            
        if listing['is_closed']:
            flash('This listing is now closed for orders.', 'warning')
            return redirect(url_for('consumer_dashboard'))

        ordered_already = db.execute(
            'SELECT COALESCE(SUM(quantity), 0) FROM orders WHERE listing_id = ?',
            (listing_id,)
        ).fetchone()[0]

        total_available = listing['total_quantity'] - ordered_already

        total_price = quantity * listing['price_per_litre']

        # Wallet check
        user_wallet = db.execute('SELECT wallet_balance FROM users WHERE user_id = ?', (session['user_id'],)).fetchone()['wallet_balance']
        
        if total_price > user_wallet:
            flash(f'Insufficient wallet balance. Total: Rs. {total_price:.2f}, Balance: Rs. {user_wallet:.2f}. Please recharge.', 'danger')
            return redirect(url_for('wallet'))

        if quantity <= 0:
            flash('Please enter a valid quantity.', 'danger')
        elif quantity > total_available:
            flash(f'Not enough milk available. Only {total_available:.1f} litres remaining.', 'danger')
        else:
            # Deduct from wallet
            db.execute('UPDATE users SET wallet_balance = wallet_balance - ? WHERE user_id = ?', (total_price, session['user_id']))
            db.execute('INSERT INTO wallet_transactions (user_id, amount, type, description) VALUES (?, ?, ?, ?)',
                       (session['user_id'], -total_price, 'payment', f"Milk Order - {listing['date']}"))
            
            cursor = db.execute(
                'INSERT INTO orders (consumer_id, farmer_id, listing_id, quantity, order_date, status) VALUES (?, ?, ?, ?, ?, ?)',
                (session['user_id'], farmer_id, listing_id, quantity, listing['date'], 'pending')
            )
            order_id = cursor.lastrowid

            # Create delivery task
            # Get consumer info
            consumer = db.execute('SELECT location, latitude, longitude FROM users WHERE user_id = ?', (session['user_id'],)).fetchone()
            # Get farmer info (from users table via farmer_id)
            farmer_user = db.execute('''
                SELECT u.location, u.latitude, u.longitude 
                FROM users u 
                JOIN farmers f ON u.user_id = f.user_id 
                WHERE f.farmer_id = ?
            ''', (farmer_id,)).fetchone()

            db.execute('''
                INSERT INTO delivery_tasks (
                    order_id, pickup_location, pickup_latitude, pickup_longitude, 
                    delivery_address, delivery_latitude, delivery_longitude, 
                    quantity, delivery_time, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                order_id, 
                farmer_user['location'], farmer_user['latitude'], farmer_user['longitude'],
                consumer['location'], consumer['latitude'], consumer['longitude'],
                quantity, listing['collection_time'], 'Pending'
            ))

            db.commit()
            flash(f'Order placed successfully for {listing["date"]}! A delivery partner will be assigned soon.', 'success')
            return redirect(url_for('consumer_dashboard'))

    listing_data = []
    for l in listings:
        ordered = db.execute(
            'SELECT COALESCE(SUM(quantity), 0) FROM orders WHERE listing_id = ?',
            (l['listing_id'],)
        ).fetchone()[0]
        remaining = l['total_quantity'] - ordered
        listing_data.append({
            'listing_id': l['listing_id'],
            'date': l['date'],
            'total_quantity': l['total_quantity'],
            'price_per_litre': l['price_per_litre'],
            'remaining': max(0, remaining),
            'is_closed': l['is_closed'],
            'collection_time': l['collection_time'] or ''
        })

    return render_template('place_order.html',
                           farmer=farmer,
                           listings=listing_data,
                           today=today)


# ─── Routes: Consumer orders ────────────────────────────────────────────────────
@app.route('/consumer/orders')
@login_required
@consumer_required
def consumer_orders():
    db = get_db()

    orders = db.execute('''
        SELECT o.*, f.farm_name, u.name as farmer_name, ml.price_per_litre
        FROM orders o
        JOIN farmers f ON o.farmer_id = f.farmer_id
        JOIN users u ON f.user_id = u.user_id
        JOIN milk_listings ml ON o.listing_id = ml.listing_id
        WHERE o.consumer_id = ?
        ORDER BY o.order_id DESC
    ''', (session['user_id'],)).fetchall()

    product_orders = db.execute('''
        SELECT po.*, p.product_name, f.farm_name, u.name as farmer_name
        FROM product_orders po
        JOIN products p ON po.product_id = p.product_id
        JOIN farmers f ON p.farmer_id = f.farmer_id
        JOIN users u ON f.user_id = u.user_id
        WHERE po.consumer_id = ?
        ORDER BY po.product_order_id DESC
    ''', (session['user_id'],)).fetchall()

    return render_template('orders.html',
                           orders=orders,
                           product_orders=product_orders,
                           role='consumer')


# ─── Routes: Milk Subscription ──────────────────────────────────────────────────
@app.route('/consumer/subscribe/<int:farmer_id>', methods=['GET', 'POST'])
@login_required
@consumer_required
def subscribe(farmer_id):
    db = get_db()
    farmer = db.execute('''
        SELECT f.*, u.name as farmer_name
        FROM farmers f JOIN users u ON f.user_id = u.user_id
        WHERE f.farmer_id = ?
    ''', (farmer_id,)).fetchone()

    if not farmer:
        flash('Farmer not found.', 'danger')
        return redirect(url_for('consumer_dashboard'))

    if request.method == 'POST':
        start_date_str = request.form['start_date']
        quantity = float(request.form['quantity'])  # Quantity in Litres
        
        # Calculate end date (21 days later)
        start_date_dt = datetime.strptime(start_date_str, '%Y-%m-%d')
        from datetime import timedelta
        end_date_dt = start_date_dt + timedelta(days=20) # 21 days total inclusive
        end_date_str = end_date_dt.strftime('%Y-%m-%d')
        
        price_per_500ml = 30.0 # Fixed as per requirement
        price_per_litre = price_per_500ml * 2
        price_per_day = quantity * price_per_litre
        total_amount = price_per_day * 21
        
        db.execute('''
            INSERT INTO subscriptions (consumer_id, farmer_id, start_date, end_date, quantity, price_per_day, total_amount, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (session['user_id'], farmer_id, start_date_str, end_date_str, quantity, price_per_day, total_amount, 'active'))
        db.commit()
        
        flash(f'Subscription successful! 21 days supply starting {start_date_str}. Total: Rs. {total_amount:.2f}', 'success')
        return redirect(url_for('consumer_subscriptions'))

    return render_template('subscribe.html', farmer=farmer, today=str(date.today()))


@app.route('/consumer/subscriptions')
@login_required
@consumer_required
def consumer_subscriptions():
    db = get_db()
    subscriptions = db.execute('''
        SELECT s.*, f.farm_name, u.name as farmer_name
        FROM subscriptions s
        JOIN farmers f ON s.farmer_id = f.farmer_id
        JOIN users u ON f.user_id = u.user_id
        WHERE s.consumer_id = ?
        ORDER BY s.subscription_id DESC
    ''', (session['user_id'],)).fetchall()
    
    return render_template('subscriptions.html', subscriptions=subscriptions, role='consumer')


@app.route('/consumer/edit-subscription/<int:subscription_id>', methods=['GET', 'POST'])
@login_required
@consumer_required
def edit_subscription(subscription_id):
    db = get_db()
    sub = db.execute('SELECT * FROM subscriptions WHERE subscription_id = ? AND consumer_id = ?', 
                    (subscription_id, session['user_id'])).fetchone()
    
    if not sub:
        flash('Subscription not found.', 'danger')
        return redirect(url_for('consumer_subscriptions'))
    
    if request.method == 'POST':
        quantity = float(request.form['quantity'])
        status = request.form['status']
        
        price_per_500ml = 30.0
        price_per_litre = price_per_500ml * 2
        price_per_day = quantity * price_per_litre
        
        db.execute('''
            UPDATE subscriptions 
            SET quantity = ?, status = ?
            WHERE subscription_id = ?
        ''', (quantity, status, subscription_id))
        db.commit()
        flash('Subscription updated.', 'success')
        return redirect(url_for('consumer_subscriptions'))
        
    return render_template('edit_subscription.html', subscription=sub)


@app.route('/farmer/subscriptions')
@login_required
@farmer_required
def farmer_subscriptions():
    db = get_db()
    subscriptions = db.execute('''
        SELECT s.*, u.name as consumer_name, u.location as consumer_location
        FROM subscriptions s
        JOIN users u ON s.consumer_id = u.user_id
        WHERE s.farmer_id = ?
        ORDER BY s.start_date ASC
    ''', (session['farmer_id'],)).fetchall()
    
    return render_template('subscriptions.html', subscriptions=subscriptions, role='farmer')


# ─── Routes: Consumer products ──────────────────────────────────────────────────
@app.route('/consumer/products')
@login_required
@consumer_required
def consumer_products():
    db = get_db()
    products = db.execute('''
        SELECT p.*, f.farm_name, u.name as farmer_name
        FROM products p
        JOIN farmers f ON p.farmer_id = f.farmer_id
        JOIN users u ON f.user_id = u.user_id
        WHERE p.quantity > 0
        ORDER BY p.created_at DESC
    ''').fetchall()

    return render_template('products.html', products=products, role='consumer')


@app.route('/consumer/buy-product/<int:product_id>', methods=['POST'])
@login_required
@consumer_required
def buy_product(product_id):
    db = get_db()
    quantity = float(request.form['quantity'])
    today = str(date.today())

    product = db.execute('SELECT * FROM products WHERE product_id = ?', (product_id,)).fetchone()

    if not product:
        flash('Product not found.', 'danger')
        return redirect(url_for('consumer_products'))

    if quantity <= 0 or quantity > product['quantity']:
        flash(f'Invalid quantity. Available: {product["quantity"]}', 'danger')
        return redirect(url_for('consumer_products'))

    total_price = quantity * product['price']
    
    # Wallet check
    user_wallet = db.execute('SELECT wallet_balance FROM users WHERE user_id = ?', (session['user_id'],)).fetchone()['wallet_balance']
    
    if total_price > user_wallet:
        flash(f'Insufficient wallet balance. Total: Rs. {total_price:.2f}, Balance: Rs. {user_wallet:.2f}. Please recharge.', 'danger')
        return redirect(url_for('wallet'))

    # Deduct from wallet
    db.execute('UPDATE users SET wallet_balance = wallet_balance - ? WHERE user_id = ?', (total_price, session['user_id']))
    db.execute('INSERT INTO wallet_transactions (user_id, amount, type, description) VALUES (?, ?, ?, ?)',
               (session['user_id'], -total_price, 'payment', f"Bought {product['product_name']}"))

    db.execute(
        'INSERT INTO product_orders (consumer_id, product_id, quantity, total_price, order_date, status) VALUES (?, ?, ?, ?, ?, ?)',
        (session['user_id'], product_id, quantity, total_price, today, 'pending')
    )
    db.execute(
        'UPDATE products SET quantity = quantity - ? WHERE product_id = ?',
        (quantity, product_id)
    )
    db.commit()
    flash(f'Order placed! {quantity} units of {product["product_name"]} for Rs. {total_price:.2f}. Track your delivery in the History tab!', 'success')
    return redirect(url_for('consumer_products'))


@app.route('/consumer/wallet', methods=['GET', 'POST'])
@login_required
@consumer_required
def wallet():
    db = get_db()
    user_id = session['user_id']
    
    if request.method == 'POST':
        amount = float(request.form.get('amount', 0))
        if amount > 0:
            db.execute('UPDATE users SET wallet_balance = wallet_balance + ? WHERE user_id = ?', (amount, user_id))
            db.execute('INSERT INTO wallet_transactions (user_id, amount, type, description) VALUES (?, ?, ?, ?)',
                       (user_id, amount, 'recharge', 'Wallet Recharge'))
            db.commit()
            flash(f'Successfully recharged Rs. {amount:.2f}!', 'success')
            return redirect(url_for('wallet'))

    user = db.execute('SELECT wallet_balance FROM users WHERE user_id = ?', (user_id,)).fetchone()
    transactions = db.execute('''
        SELECT * FROM wallet_transactions 
        WHERE user_id = ? 
        ORDER BY timestamp DESC
    ''', (user_id,)).fetchall()
    
    return render_template('wallet.html', balance=user['wallet_balance'], transactions=transactions)


@app.route('/consumer/vacation', methods=['GET', 'POST'])
@login_required
@consumer_required
def vacation():
    db = get_db()
    user_id = session['user_id']
    
    if request.method == 'POST':
        v_date = request.form['vacation_date']
        # Check if already exists
        exists = db.execute('SELECT 1 FROM vacation_dates WHERE consumer_id = ? AND vacation_date = ?', (user_id, v_date)).fetchone()
        if not exists:
            db.execute('INSERT INTO vacation_dates (consumer_id, vacation_date) VALUES (?, ?)', (user_id, v_date))
            db.commit()
            flash(f'Vacation set for {v_date}. Delivery will be paused.', 'info')
        else:
            flash('Date already set as vacation.', 'warning')
        return redirect(url_for('vacation'))

    dates = db.execute('SELECT * FROM vacation_dates WHERE consumer_id = ? ORDER BY vacation_date ASC', (user_id,)).fetchall()
    return render_template('vacation.html', vacation_dates=dates)


@app.route('/consumer/vacation/delete/<int:vacation_id>', methods=['POST'])
@login_required
@consumer_required
def delete_vacation(vacation_id):
    db = get_db()
    db.execute('DELETE FROM vacation_dates WHERE vacation_id = ? AND consumer_id = ?', (vacation_id, session['user_id']))
    db.commit()
    flash('Vacation date removed.', 'success')
    return redirect(url_for('vacation'))


# ─── Routes: Delivery Partner ──────────────────────────────────────────────────
@app.route('/delivery/dashboard')
@login_required
@delivery_required
def delivery_dashboard():
    db = get_db()
    user_id = session['user_id']
    
    # Available tasks (Pending)
    available_tasks = db.execute('SELECT * FROM delivery_tasks WHERE status = "Pending"').fetchall()
    
    # My tasks (Accepted, Picked Up)
    my_tasks = db.execute('''
        SELECT * FROM delivery_tasks 
        WHERE delivery_partner_id = ? AND status IN ("Accepted", "Picked Up")
        ORDER BY status ASC
    ''', (user_id,)).fetchall()
    
    # Completed tasks
    completed_tasks = db.execute('''
        SELECT * FROM delivery_tasks 
        WHERE delivery_partner_id = ? AND status = "Delivered"
        ORDER BY created_at DESC LIMIT 10
    ''', (user_id,)).fetchall()
    
    # Simple Route Optimization for "My Tasks"
    optimized_tasks = []
    if my_tasks:
        # Convert to list of dicts for sorting
        task_list = [dict(t) for t in my_tasks]
        
        # Simple heuristic: Group by pickup location coordinates
        # Then sort by delivery location coordinates
        # This keeps nearby pickups together and optimizes delivery sequence
        task_list.sort(key=lambda x: (x['pickup_latitude'], x['pickup_longitude'], x['delivery_latitude'], x['delivery_longitude']))
        optimized_tasks = task_list
    else:
        optimized_tasks = my_tasks

    return render_template('delivery_dashboard.html', 
                           available_tasks=[dict(t) for t in available_tasks],
                           my_tasks=[dict(t) for t in optimized_tasks],
                           completed_tasks=completed_tasks)


@app.route('/delivery/accept/<int:delivery_id>', methods=['POST'])
@login_required
@delivery_required
def accept_delivery(delivery_id):
    db = get_db()
    db.execute('''
        UPDATE delivery_tasks 
        SET status = "Accepted", delivery_partner_id = ? 
        WHERE delivery_id = ? AND status = "Pending"
    ''', (session['user_id'], delivery_id))
    db.commit()
    flash('Delivery task accepted!', 'success')
    return redirect(url_for('delivery_dashboard'))


@app.route('/delivery/picked-up/<int:delivery_id>', methods=['POST'])
@login_required
@delivery_required
def picked_up(delivery_id):
    db = get_db()
    db.execute('''
        UPDATE delivery_tasks 
        SET status = "Picked Up" 
        WHERE delivery_id = ? AND delivery_partner_id = ?
    ''', (delivery_id, session['user_id']))
    
    task = db.execute('SELECT order_id FROM delivery_tasks WHERE delivery_id = ?', (delivery_id,)).fetchone()
    if task:
        # Also update the main order status
        db.execute('UPDATE orders SET status = "Out for Delivery" WHERE order_id = ?', (task['order_id'],))
        
    db.commit()
    flash('Task marked as Picked Up! Consumer has been notified via order status.', 'info')
    return redirect(url_for('delivery_dashboard'))


@app.route('/delivery/delivered/<int:delivery_id>', methods=['POST'])
@login_required
@delivery_required
def delivered(delivery_id):
    db = get_db()
    db.execute('''
        UPDATE delivery_tasks 
        SET status = "Delivered" 
        WHERE delivery_id = ? AND delivery_partner_id = ?
    ''', (delivery_id, session['user_id']))
    
    task = db.execute('SELECT order_id FROM delivery_tasks WHERE delivery_id = ?', (delivery_id,)).fetchone()
    if task:
        # Also update the main order status
        db.execute('UPDATE orders SET status = "Delivered" WHERE order_id = ?', (task['order_id'],))
        
    db.commit()
    flash('Delivery completed successfully! Order status updated for consumer.', 'success')
    return redirect(url_for('delivery_dashboard'))


# ─── Init and run ────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
