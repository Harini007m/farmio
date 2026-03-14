import sqlite3
import os

DATABASE = 'database.db'

def migrate():
    if not os.path.exists(DATABASE):
        print("Database not found.")
        return

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    try:
        print("Starting V2 migration...")
        
        # Feature 1: Milk Freshness Information
        # Add delivery_start_time and delivery_end_time to milk_listings
        cursor.execute("PRAGMA table_info(milk_listings)")
        columns = [c[1] for c in cursor.fetchall()]
        if 'delivery_start_time' not in columns:
            print("Adding delivery_start_time to milk_listings...")
            cursor.execute("ALTER TABLE milk_listings ADD COLUMN delivery_start_time TEXT")
        if 'delivery_end_time' not in columns:
            print("Adding delivery_end_time to milk_listings...")
            cursor.execute("ALTER TABLE milk_listings ADD COLUMN delivery_end_time TEXT")

        # Feature 2: Delivery Status Tracking
        # Add order_status to orders
        cursor.execute("PRAGMA table_info(orders)")
        columns = [c[1] for c in cursor.fetchall()]
        if 'order_status' not in columns:
            print("Adding order_status to orders...")
            cursor.execute("ALTER TABLE orders ADD COLUMN order_status TEXT DEFAULT 'Confirmed'")

        # Feature 3: Farmer Trust Score
        # Add trust_score to farmers
        cursor.execute("PRAGMA table_info(farmers)")
        columns = [c[1] for c in cursor.fetchall()]
        if 'trust_score' not in columns:
            print("Adding trust_score to farmers...")
            cursor.execute("ALTER TABLE farmers ADD COLUMN trust_score REAL DEFAULT 0")

        # Create reviews table for trust score (average buyer rating)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reviews (
                review_id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                consumer_id INTEGER NOT NULL,
                farmer_id INTEGER NOT NULL,
                rating INTEGER NOT NULL,
                comment TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (order_id) REFERENCES orders(order_id),
                FOREIGN KEY (consumer_id) REFERENCES users(user_id),
                FOREIGN KEY (farmer_id) REFERENCES farmers(farmer_id)
            )
        ''')
        print("Ensured reviews table exists.")

        conn.commit()
        print("V2 migration completed successfully!")
        
    except Exception as e:
        conn.rollback()
        print(f"Migration failed: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    migrate()
