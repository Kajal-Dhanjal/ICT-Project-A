import sqlite3

with open("database/setup.sql", "r") as f:
    sql = f.read()

conn = sqlite3.connect("database/app.db")
conn.executescript(sql)
conn.close()

print("✅ Database initialized successfully.")
