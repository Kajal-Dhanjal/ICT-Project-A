import pyotp
from datetime import datetime
from supabase_client.supabaseClient import supabase

from functools import wraps
from flask import redirect, url_for, request, g
import jwt
import os

def generate_mfa_secret(user_id):
    secret = pyotp.random_base32()
    uri = pyotp.totp.TOTP(secret).provisioning_uri(
        name=f"user_{user_id}",
        issuer_name="SecureCareApp"  # Customize this
    )

    # Save the secret in Supabase
    supabase.table("users").update({"mfa_secret": secret}).eq("id", user_id).execute()
    return {"secret": secret, "uri": uri}

def verify_mfa_otp(user_id, otp_code):
    #result = supabase.table("users").select("totp_secret").eq("id", user_id).single().execute()
    result = supabase.table("users").select("mfa_secret").eq("id", user_id).single().execute()

    user = result.data

    if not user or "mfa_secret" not in user:
        return {"status": "error", "message": "User or secret not found"}, 404

    totp = pyotp.TOTP(user["mfa_secret"])

    if not totp.verify(otp_code, valid_window=2):
        return {"status": "fail", "message": "Invalid OTP"}, 401

    supabase.table("users").update({
        "mfa_last_used": datetime.utcnow().isoformat()
    }).eq("id", user_id).execute()

    return {"status": "success", "message": "OTP verified"}, 200

def mfa_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        access_token = request.cookies.get("access_token")
        if not access_token:
            return redirect(url_for("login"))

        try:
            decoded = jwt.decode(
                access_token,
                os.environ.get("JWT_SECRET"),
                algorithms=["HS256"],
                audience="authenticated"
            )
            if not decoded.get("mfa_verified"):
                return "MFA not completed", 403
        except Exception as e:
            print(f"MFA error: {e}")
            return redirect(url_for("login"))

        return f(*args, **kwargs)
    return decorated_function