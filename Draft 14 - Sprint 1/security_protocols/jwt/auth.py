from functools import wraps
from flask import request, redirect, url_for, g
import jwt
from jwt.exceptions import InvalidTokenError
import os
from supabase_client.supabaseClient import supabase

def jwt_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        access_token = request.cookies.get('access_token')
        if not access_token:
            print("❌ No access_token in cookies.")
            return redirect(url_for('login'))
        
        try:
            secret = os.environ.get('JWT_SECRET')
            print("✅ Using JWT_SECRET:", secret)

            payload = jwt.decode(
                access_token,
                os.environ.get('JWT_SECRET'),
                algorithms=['HS256'],
                audience='authenticated'
            )

            print("✅ Decoded JWT payload:", payload)

            user_id = payload.get('sub')
            print("🔍 Looking up user ID:", user_id)

            user = supabase.table("users").select("id, role").eq("id", user_id).single().execute()
            print("🔍 Supabase user query result:", user.data)

            if not user.data:
                print("❌ No user found with ID from JWT.")
                return redirect(url_for('login'))

            g.user_id = user.data['id']
            g.role = user.data['role']
            print("✅ Auth success: g.user_id =", g.user_id, "g.role =", g.role)

        except Exception as e:
            print("❌ JWT validation or DB lookup failed:", str(e))
            return redirect(url_for('login'))
        
        return f(*args, **kwargs)
    return decorated_function
