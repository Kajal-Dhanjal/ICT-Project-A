# RBAC using Supabase (replacing SQLite logic)
from supabase_client.supabaseClient import supabase

# -------------------------------
# User and Resident Management
# -------------------------------

def get_user_by_email(email):
    response = supabase.table("users").select("*").eq("email", email).limit(1).execute()
    if response.data and len(response.data) > 0:
        return response.data[0]
    return None


def get_user_by_id(uid):
    response = supabase.table("users").select("*").eq("id", uid).single().execute()
    if response.data:
        return response.data
    return None

def get_role(user):
    return user.get("role")

# -------------------------------
# Access Management
# -------------------------------

def assign_access(user_id, resident_id, access_level):
    supabase.table("assignments").insert({
        "staff_id": user_id,
        "resident_id": resident_id,
        "access": access_level
    }).execute()

def can_nurse_write(user_id, resident_id):
    user = get_user_by_id(user_id)
    if not user or user.get("role") != "nurse":
        return False
    res = supabase.table("assignments").select("access_level").eq("staff_id", user_id).eq("resident_id", resident_id).single().execute()
    return res.data and res.data["access_level"] == "write"

# -------------------------------
# Retrieval Functions
# -------------------------------

def get_all_users():
    res = supabase.table("users").select("*").execute()
    return res.data if res.data else []

def get_all_residents():
    res = supabase.table("residents").select("*").execute()
    return res.data if res.data else []

def get_accessible_residents(user):
    role = user.get("role")
    user_id = user.get("id")

    if role == "admin":
        return get_all_residents()

    res = supabase.from_("assignments")\
        .select("residents (id, full_name, room)")\
        .eq("staff_id", user_id).execute()

    if res.data:
        return [r["residents"] for r in res.data if r.get("residents")]
    return []

def get_assignments_for_user(user_id):
    res = supabase.table("assignments").select("*").eq("staff_id", user_id).execute()
    return res.data if res.data else []

def get_assignments_for_resident(resident_id):
    res = supabase.table("assignments").select("*").eq("resident_id", resident_id).execute()
    return res.data if res.data else []

# -------------------------------
# Resident Self View (Limited Vitals)
# -------------------------------

def get_latest_vitals_for_resident(resident_id):
    res = supabase.table("vitals").select("bp, temp, hr").eq("resident_id", resident_id).order("timestamp", desc=True).limit(1).execute()
    if res.data and len(res.data) > 0:
        return res.data[0]
    return None
