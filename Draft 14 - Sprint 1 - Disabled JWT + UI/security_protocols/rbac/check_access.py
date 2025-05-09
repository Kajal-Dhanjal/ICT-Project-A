from supabase_client.supabaseClient import supabase

def has_read_access(staff_id, resident_id):
    result = supabase.table("assignments") \
        .select("access") \
        .eq("staff_id", staff_id) \
        .eq("resident_id", resident_id) \
        .single().execute()
    return result.data is not None

def has_write_access(staff_id, resident_id):
    result = supabase.table("assignments") \
        .select("access") \
        .eq("staff_id", staff_id) \
        .eq("resident_id", resident_id) \
        .single().execute()
    return result.data and result.data["access"] == "write"
