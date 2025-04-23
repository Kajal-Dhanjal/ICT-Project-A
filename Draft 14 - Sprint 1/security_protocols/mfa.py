import pyotp
from datetime import datetime
from supabase_client.supabaseClient import supabase

def generate_mfa_secret(user_id):
    secret = pyotp.random_base32()
    uri = pyotp.totp.TOTP(secret).provisioning_uri(name=user_id, issuer_name="SecureCare")

    supabase.table("users").update({
        "totp_secret": secret,
        "mfa_enabled": True
    }).eq("id", user_id).execute()

    return {"secret": secret, "otpauth_url": uri}

def verify_mfa_otp(user_id, otp_code):
    result = supabase.table("users").select("totp_secret").eq("id", user_id).single().execute()
    user = result.data

    if not user or "totp_secret" not in user:
        return {"status": "error", "message": "User or secret not found"}, 404

    totp = pyotp.TOTP(user["totp_secret"])

    if not totp.verify(otp_code, valid_window=1):
        return {"status": "fail", "message": "Invalid OTP"}, 401

    supabase.table("users").update({
        "mfa_last_used": datetime.utcnow().isoformat()
    }).eq("id", user_id).execute()

    return {"status": "success", "message": "OTP verified"}
