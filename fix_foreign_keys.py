import sqlite3
import os

DATABASE = 'database.db'

def full_migration():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    try:
        print("Starting full database migration to fix broken foreign keys...")
        
        # 1. Disable foreign keys temporarily
        cursor.execute("PRAGMA foreign_keys = OFF")
        
        # List of tables to recreate and their new definitions
        # These are based on app.py init_db
        tables = {
            "farmers": '''
                CREATE TABLE farmers (
                    farmer_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL UNIQUE,
                    farm_name TEXT NOT NULL,
                    location TEXT NOT NULL,
                    milk_capacity_per_day REAL DEFAULT 0,
                    price_per_litre REAL DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            ''',
            "orders": '''
                CREATE TABLE orders (
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
                )
            ''',
            "product_orders": '''
                CREATE TABLE product_orders (
                    product_order_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    consumer_id INTEGER NOT NULL,
                    product_id INTEGER NOT NULL,
                    quantity REAL NOT NULL,
                    total_price REAL NOT NULL,
                    order_date TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    FOREIGN KEY (consumer_id) REFERENCES users(user_id),
                    FOREIGN KEY (product_id) REFERENCES products(product_id)
                )
            ''',
            "subscriptions": '''
                CREATE TABLE subscriptions (
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
                )
            ''',
            "wallet_transactions": '''
                CREATE TABLE wallet_transactions (
                    transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    amount REAL NOT NULL,
                    type TEXT NOT NULL CHECK(type IN ('recharge', 'payment', 'refund')),
                    description TEXT,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            ''',
            "vacation_dates": '''
                CREATE TABLE vacation_dates (
                    vacation_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    consumer_id INTEGER NOT NULL,
                    vacation_date TEXT NOT NULL,
                    FOREIGN KEY (consumer_id) REFERENCES users(user_id)
                )
            ''',
            "delivery_tasks": '''
                CREATE TABLE delivery_tasks (
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
                )
            '''
        }
        
        for table_name, schema in tables.items():
            print(f"Recreating table: {table_name}")
            # Get existing data
            cursor.execute(f"SELECT * FROM {table_name}")
            data = cursor.fetchall()
            
            # Get column names
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [c[1] for c in cursor.fetchall()]
            
            # Drop and recreate
            cursor.execute(f"DROP TABLE {table_name}")
            cursor.execute(schema)
            
            # Restore data
            if data:
                placeholders = ",".join(["?"] * len(columns))
                cursor.executemany(f"INSERT INTO {table_name} ({','.join(columns)}) VALUES ({placeholders})", data)

        conn.commit()
        print("Migration and foreign key repair successful!")
        
    except Exception as e:
        conn.rollback()
        print(f"Migration failed: {e}")
    finally:
        cursor.execute("PRAGMA foreign_keys = ON")
        conn.close()

if __name__ == '__main__':
    full_migration()
