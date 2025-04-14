import sqlite3

conn = sqlite3.connect("database/app.db")
cur = conn.cursor()

cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cur.fetchall()

print("📋 Tables found in database:")
for t in tables:
    print("-", t[0])

conn.close()
