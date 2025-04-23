from supabase_client.supabaseClient import supabase

def get_latest_vitals_for_resident(resident_id: str):
    response = supabase.table("care_plans")\
        .select("*")\
        .eq("resident_id", resident_id)\
        .order("timestamp", desc=True)\
        .limit(1)\
        .execute()

    return response.data[0] if response.data else {}
