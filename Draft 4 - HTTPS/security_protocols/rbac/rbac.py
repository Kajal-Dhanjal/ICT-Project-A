from uuid import uuid4

users = []
residents = []
assignments = []

# Default Admin User
users.append({
    "user_id": "admin_admin",
    "full_name": "Admin",
    "email": "admin@example.com",
    "role": "admin"
})

# -------------------------------
# User and Resident Management
# -------------------------------

def create_user(full_name, email, role):
    user_id = f"{full_name.lower().replace(' ', '_')}_{role}"
    users.append({
        "user_id": user_id,
        "full_name": full_name,
        "email": email,
        "role": role
    })

def create_resident(name, room_number):
    resident_id = f"{name.lower().replace(' ', '_')}_res"
    residents.append({
        "resident_id": resident_id,
        "full_name": name,
        "room": room_number
    })

# -------------------------------
# Access Management
# -------------------------------

def assign_access(email, resident_name, access_level):
    user = next((u for u in users if u["email"] == email), None)
    resident = next((r for r in residents if r["full_name"] == resident_name), None)
    if user and resident:
        assignments.append({
            "staff_id": user["user_id"],
            "resident_id": resident["resident_id"],
            "access": access_level
        })

def can_nurse_write(uid, rid):
    for a in assignments:
        if a["staff_id"] == uid and a["resident_id"] == rid:
            return a["access"] == "write"
    return False

# -------------------------------
# Retrieval Functions
# -------------------------------

def get_user_by_email(email):
    return next((u for u in users if u["email"] == email), None)

def get_user_by_id(uid):
    return next((u for u in users if u["user_id"] == uid), None)

def get_role(user):
    return user["role"]

def get_accessible_residents(user):
    if user["role"] == "admin":
        return residents
    accessible_ids = [
        a["resident_id"] for a in assignments if a["staff_id"] == user["user_id"]
    ]
    return [r for r in residents if r["resident_id"] in accessible_ids]

def get_all_users():
    return users

def get_all_residents():
    return residents

def get_assignments_for_user(user_id):
    return [a for a in assignments if a["staff_id"] == user_id]

def get_assignments_for_resident(resident_id):
    return [a for a in assignments if a["resident_id"] == resident_id]

# -------------------------------
# Deletion
# -------------------------------

def delete_user(email):
    global users, assignments
    target = next((u for u in users if u["email"] == email), None)
    if target:
        users = [u for u in users if u["email"] != email]
        assignments = [a for a in assignments if a["staff_id"] != target["user_id"]]

def delete_resident(name):
    global residents, assignments
    target = next((r for r in residents if r["full_name"] == name), None)
    if target:
        residents = [r for r in residents if r["full_name"] != name]
        assignments = [a for a in assignments if a["resident_id"] != target["resident_id"]]
