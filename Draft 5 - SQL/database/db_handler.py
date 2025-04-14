import sqlite3
from datetime import datetime

DB_PATH = "database/app.db"

def connect():
    return sqlite3.connect(DB_PATH)

def get_resident_by_id(resident_id):
    with connect() as conn:
        row = conn.execute("SELECT * FROM residents WHERE resident_id = ?", (resident_id,)).fetchone()
        if row:
            return {"id": row[0], "full_name": row[1], "room": row[2]}
    return None

def get_care_plans(resident_id):
    with connect() as conn:
        rows = conn.execute("SELECT * FROM care_plans WHERE resident_id = ? ORDER BY timestamp DESC", (resident_id,)).fetchall()
        return [dict(id=row[0], resident_id=row[1], timestamp=datetime.fromisoformat(row[2]),
                     assessment=row[3], diagnosis=row[4], goals=row[5],
                     interventions=row[6], evaluation=row[7], filename=row[8]) for row in rows]

def get_vitals(resident_id):
    with connect() as conn:
        rows = conn.execute("SELECT * FROM vitals WHERE resident_id = ? ORDER BY timestamp DESC", (resident_id,)).fetchall()
        return [dict(bp=row[2], temp=row[3], hr=row[4], timestamp=datetime.fromisoformat(row[5])) for row in rows]

def get_medications(resident_id):
    with connect() as conn:
        rows = conn.execute("SELECT * FROM medications WHERE resident_id = ? ORDER BY timestamp DESC", (resident_id,)).fetchall()
        return [dict(name=row[2], dose=row[3], time=row[4], route=row[5], timestamp=datetime.fromisoformat(row[6])) for row in rows]

def get_files(resident_id):
    with connect() as conn:
        rows = conn.execute("SELECT * FROM files WHERE resident_id = ? ORDER BY timestamp DESC", (resident_id,)).fetchall()
        return [dict(filename=row[2], timestamp=datetime.fromisoformat(row[3])) for row in rows]

def save_care_entry(resident_id, assessment, diagnosis, goals, interventions, evaluation, filename=None):
    timestamp = datetime.now().isoformat()
    with connect() as conn:
        conn.execute("""
            INSERT INTO care_plans (resident_id, timestamp, assessment, diagnosis, goals, interventions, evaluation, filename)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (resident_id, timestamp, assessment, diagnosis, goals, interventions, evaluation, filename))

        if filename:
            conn.execute("""
                INSERT INTO files (resident_id, filename, timestamp)
                VALUES (?, ?, ?)
            """, (resident_id, filename, timestamp))

def save_vitals(resident_id, bp, temp, hr):
    timestamp = datetime.now().isoformat()
    with connect() as conn:
        conn.execute("""
            INSERT INTO vitals (resident_id, bp, temp, hr, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (resident_id, bp, temp, hr, timestamp))

def save_medication(resident_id, name, dose, time, route):
    timestamp = datetime.now().isoformat()
    with connect() as conn:
        conn.execute("""
            INSERT INTO medications (resident_id, name, dose, time, route, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (resident_id, name, dose, time, route, timestamp))
