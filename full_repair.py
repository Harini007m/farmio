import sqlite3
import os

DATABASE = 'database.db'

def full_repair():
    if not os.path.exists(DATABASE):
        print("Database not found.")
        return

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    try:
        print("Starting comprehensive database repair...")
        cursor.execute("PRAGMA foreign_keys = OFF")
        
        # 1. Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        all_tables = [row[0] for row in cursor.fetchall()]
        
        # 2. Store data for each table
        table_data = {}
        for table in all_tables:
            cursor.execute(f"PRAGMA table_info({table})")
            columns = [c[1] for c in cursor.fetchall()]
            cursor.execute(f"SELECT * FROM {table}")
            data = cursor.fetchall()
            table_data[table] = (columns, data)
            print(f"Backed up {len(data)} rows from {table}")

        # 3. Drop all tables
        for table in all_tables:
            cursor.execute(f"DROP TABLE {table}")
        
        # 4. Re-create all tables using the latest schema from app.py
        # I'll define them here clearly.
        schema_scripts = [
            '''CREATE TABLE users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('farmer', 'consumer', 'delivery_partner')),
                location TEXT DEFAULT '',
                latitude REAL DEFAULT 0,
                longitude REAL DEFAULT 0,
                wallet_balance REAL DEFAULT 0
            )''',
            '''CREATE TABLE farmers (
                farmer_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL UNIQUE,
                farm_name TEXT NOT NULL,
                location TEXT NOT NULL,
                milk_capacity_per_day REAL DEFAULT 0,
                price_per_litre REAL DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )''',
            '''CREATE TABLE milk_listings (
                listing_id INTEGER PRIMARY KEY AUTOINCREMENT,
                farmer_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                total_quantity REAL DEFAULT 0,
                price_per_litre REAL NOT NULL,
                collection_time TEXT DEFAULT '',
                delivery_estimate TEXT DEFAULT '',
                is_closed INTEGER DEFAULT 0,
                FOREIGN KEY (farmer_id) REFERENCES farmers(farmer_id)
            )''',
            '''CREATE TABLE orders (
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
            )''',
            '''CREATE TABLE products (
                product_id INTEGER PRIMARY KEY AUTOINCREMENT,
                farmer_id INTEGER NOT NULL,
                product_name TEXT NOT NULL,
                quantity REAL NOT NULL,
                price REAL NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (farmer_id) REFERENCES farmers(farmer_id)
            )''',
            '''CREATE TABLE product_orders (
                product_order_id INTEGER PRIMARY KEY AUTOINCREMENT,
                consumer_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity REAL NOT NULL,
                total_price REAL NOT NULL,
                order_date TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                FOREIGN KEY (consumer_id) REFERENCES users(user_id),
                FOREIGN KEY (product_id) REFERENCES products(product_id)
            )''',
            '''CREATE TABLE subscriptions (
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
            )''',
            '''CREATE TABLE wallet_transactions (
                transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                type TEXT NOT NULL CHECK(type IN ('recharge', 'payment', 'refund')),
                description TEXT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )''',
            '''CREATE TABLE vacation_dates (
                vacation_id INTEGER PRIMARY KEY AUTOINCREMENT,
                consumer_id INTEGER NOT NULL,
                vacation_date TEXT NOT NULL,
                FOREIGN KEY (consumer_id) REFERENCES users(user_id)
            )''',
            '''CREATE TABLE delivery_tasks (
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
            )'''
        ]
        
        for script in schema_scripts:
            cursor.execute(script)
        
        # 5. Restore data
        for table, (columns, data) in table_data.items():
            if data:
                # Filter out columns that might have changed (though we kept them same)
                # Ensure we only insert into tables that exist in new schema
                cursor.execute(f"PRAGMA table_info({table})")
                new_cols = [c[1] for c in cursor.fetchall()]
                if not new_cols:
                    print(f"Skipping restore for {table} as it doesn't exist in new schema.")
                    continue
                
                # Intersection of columns
                common_cols = [c for c in columns if c in new_cols]
                indices = [columns.index(c) for c in common_cols]
                
                insert_data = []
                for row in data:
                    insert_data.append(tuple(row[i] for i in indices))
                
                placeholders = ",".join(["?"] * len(common_cols))
                cursor.executemany(f"INSERT INTO {table} ({','.join(common_cols)}) VALUES ({placeholders})", insert_data)
                print(f"Restored {len(insert_data)} rows to {table}")

        conn.commit()
        print("Database fully repaired and foreign keys synchronized!")
        
    except Exception as e:
        conn.rollback()
        print(f"Repair failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cursor.execute("PRAGMA foreign_keys = ON")
        conn.close()

if __name__ == '__main__':
    full_repair()
