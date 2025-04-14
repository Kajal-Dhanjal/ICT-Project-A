import sqlite3

DB_PATH = "database/app.db"

def connect():
    return sqlite3.connect(DB_PATH)

# -------------------------------
# User and Resident Management
# -------------------------------

def create_user(full_name, email, role):
    user_id = f"{full_name.lower().replace(' ', '_')}_{role}"
    with connect() as conn:
        exists = conn.execute("SELECT 1 FROM users WHERE email = ?", (email,)).fetchone()
        if not exists:
            conn.execute("""
                INSERT INTO users (user_id, full_name, email, role)
                VALUES (?, ?, ?, ?)
            """, (user_id, full_name, email, role))

def create_resident(name, room_number):
    resident_id = f"{name.lower().replace(' ', '_')}_res"
    with connect() as conn:
        conn.execute("""
            INSERT INTO residents (resident_id, full_name, room)
            VALUES (?, ?, ?)
        """, (resident_id, name, room_number))

# -------------------------------
# Access Management
# -------------------------------

def assign_access(email, resident_name, access_level):
    with connect() as conn:
        user = conn.execute("SELECT user_id FROM users WHERE email = ?", (email,)).fetchone()
        resident = conn.execute("SELECT resident_id FROM residents WHERE full_name = ?", (resident_name,)).fetchone()
        if user and resident:
            conn.execute("""
                INSERT INTO assignments (staff_id, resident_id, access)
                VALUES (?, ?, ?)
            """, (user[0], resident[0], access_level))

def can_nurse_write(uid, rid):
    user = get_user_by_id(uid)
    if not user or user["role"] != "nurse":
        return False

    with connect() as conn:
        row = conn.execute("""
            SELECT access FROM assignments
            WHERE staff_id = ? AND resident_id = ?
        """, (uid, rid)).fetchone()
        return row and row[0] == "write"


# -------------------------------
# Retrieval Functions
# -------------------------------

def get_user_by_email(email):
    if email == "admin@example.com":
        return {
            "user_id": "admin_admin",
            "full_name": "Admin",
            "email": "admin@example.com",
            "role": "admin"
        }

    with connect() as conn:
        row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        if row:
            return dict(user_id=row[0], full_name=row[1], email=row[2], role=row[3])
    return None

def get_user_by_id(uid):
    if uid == "admin_admin":
        return {
            "user_id": "admin_admin",
            "full_name": "Admin",
            "email": "admin@example.com",
            "role": "admin"
        }

    with connect() as conn:
        row = conn.execute("SELECT * FROM users WHERE user_id = ?", (uid,)).fetchone()
        if row:
            return dict(user_id=row[0], full_name=row[1], email=row[2], role=row[3])
    return None


def get_role(user):
    return user["role"]

def get_accessible_residents(user):
    with connect() as conn:
        if user["role"] == "admin":
            rows = conn.execute("SELECT * FROM residents").fetchall()
            return [dict(resident_id=row[0], full_name=row[1], room=row[2]) for row in rows]

        rows = conn.execute("""
            SELECT r.resident_id, r.full_name, r.room
            FROM residents r
            JOIN assignments a ON r.resident_id = a.resident_id
            WHERE a.staff_id = ?
        """, (user["user_id"],)).fetchall()
        return [dict(resident_id=row[0], full_name=row[1], room=row[2]) for row in rows]

def get_all_users():
    admin = {
        "user_id": "admin_admin",
        "full_name": "Admin",
        "email": "admin@example.com",
        "role": "admin"
    }

    with connect() as conn:
        rows = conn.execute("SELECT * FROM users").fetchall()
        users = [dict(user_id=row[0], full_name=row[1], email=row[2], role=row[3]) for row in rows]

    return [admin] + users


def get_all_residents():
    with connect() as conn:
        rows = conn.execute("SELECT * FROM residents").fetchall()
        return [dict(resident_id=row[0], full_name=row[1], room=row[2]) for row in rows]

def get_assignments_for_user(user_id):
    with connect() as conn:
        rows = conn.execute("SELECT * FROM assignments WHERE staff_id = ?", (user_id,)).fetchall()
        return [dict(staff_id=row[1], resident_id=row[2], access=row[3]) for row in rows]

def get_assignments_for_resident(resident_id):
    with connect() as conn:
        rows = conn.execute("SELECT * FROM assignments WHERE resident_id = ?", (resident_id,)).fetchall()
        return [dict(staff_id=row[1], resident_id=row[2], access=row[3]) for row in rows]

# -------------------------------
# Deletion
# -------------------------------

def delete_user(user_id):
    with connect() as conn:
        conn.execute("DELETE FROM assignments WHERE staff_id = ?", (user_id,))
        conn.execute("DELETE FROM users WHERE user_id = ?", (user_id,))

def delete_resident(resident_id):
    with connect() as conn:
        conn.execute("DELETE FROM assignments WHERE resident_id = ?", (resident_id,))
        conn.execute("DELETE FROM residents WHERE resident_id = ?", (resident_id,))
