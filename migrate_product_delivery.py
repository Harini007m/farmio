import sqlite3
import os

DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database.db')

def migrate():
    print("Starting Product Delivery migration...")
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    cursor = db.cursor()

    try:
        # 1. Update delivery_tasks to include product_order_id and order_type
        # In SQLite we can't easily make a column nullable if it isn't, 
        # but order_id is already nullable by default unless specified NOT NULL.
        # Let's check the schema.
        cursor.execute("PRAGMA table_info(delivery_tasks)")
        columns = [row['name'] for row in cursor.fetchall()]
        
        if 'product_order_id' not in columns:
            print("Adding product_order_id to delivery_tasks...")
            cursor.execute("ALTER TABLE delivery_tasks ADD COLUMN product_order_id INTEGER")
            
        if 'order_type' not in columns:
            print("Adding order_type to delivery_tasks...")
            cursor.execute("ALTER TABLE delivery_tasks ADD COLUMN order_type TEXT DEFAULT 'milk'")

        # 2. Update existing tasks to be 'milk' type
        cursor.execute("UPDATE delivery_tasks SET order_type = 'milk' WHERE order_type IS NULL")

        # 3. Add order_status to product_orders for consistency with orders
        cursor.execute("PRAGMA table_info(product_orders)")
        columns = [row['name'] for row in cursor.fetchall()]
        if 'order_status' not in columns:
            print("Adding order_status to product_orders...")
            cursor.execute("ALTER TABLE product_orders ADD COLUMN order_status TEXT DEFAULT 'Confirmed'")

        db.commit()
        print("Migration successful!")
    except Exception as e:
        print(f"Migration failed: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    migrate()
