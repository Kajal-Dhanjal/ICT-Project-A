# ✅ JWT Creation Logic for session_management/jwt_handler.py
import jwt
import os
from datetime import datetime, timedelta

def generate_jwt(user_id, role, mfa_verified=False):
    payload = {
        "sub": user_id,
        "role": role,
        "mfa_verified": mfa_verified,
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(hours=1),
        "aud": "authenticated"
    }
    secret = os.environ.get("JWT_SECRET")
    token = jwt.encode(payload, secret, algorithm="HS256")
    return token
