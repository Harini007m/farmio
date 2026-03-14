import os
import sqlite3
from app import init_db

DATABASE = 'database.db'

def reset():
    print("Resetting database...")
    if os.path.exists(DATABASE):
        try:
            os.remove(DATABASE)
            print(f"Deleted existing {DATABASE}")
        except Exception as e:
            print(f"Error deleting database: {e}")
            return

    try:
        init_db()
        print("Database initialized with fresh schema.")
    except Exception as e:
        print(f"Error initializing database: {e}")

if __name__ == "__main__":
    reset()
