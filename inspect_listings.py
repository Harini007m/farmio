import sqlite3
conn = sqlite3.connect('database.db')
cursor = conn.cursor()
cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='milk_listings'")
row = cursor.fetchone()
print(row[0] if row else "Table not found")
conn.close()
