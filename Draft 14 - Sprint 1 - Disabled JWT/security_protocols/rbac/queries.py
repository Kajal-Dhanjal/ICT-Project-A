from supabase_client.supabaseClient import supabase

def get_user_by_email(email):
    res = supabase.table("users").select("*").eq("email", email).single().execute()
    return res.data

def get_resident_by_id(resident_id):
    res = supabase.table("residents").select("*").eq("id", resident_id).single().execute()
    return res.data

def get_assignments_for_user(user_id):
    res = supabase.table("assignments").select("*").eq("staff_id", user_id).execute()
    return res.data
