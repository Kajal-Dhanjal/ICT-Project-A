from supabase_client.supabaseClient import supabase

def get_assigned_residents(user_id, role):
    if role not in ["nurse", "carer"]:
        return []

    response = supabase.table("assignments").select("resident_id").eq("staff_id", user_id).execute()
    
    # 👇 Return empty list instead of error if no assignments
    if not response.data:
        return []

    resident_ids = [entry["resident_id"] for entry in response.data]
    resident_response = supabase.table("residents").select("*").in_("id", resident_ids).execute()
    return resident_response.data if resident_response.data else []

