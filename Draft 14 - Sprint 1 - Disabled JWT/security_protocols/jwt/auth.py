from functools import wraps
from flask import request, redirect, url_for, g
import jwt
from jwt.exceptions import InvalidTokenError
import os
from supabase_client.supabaseClient import supabase

from security_protocols.monitoring.logger import log_activity

def jwt_required(f):
    from functools import wraps
    from flask import request, g

    @wraps(f)
    def decorated_function(*args, **kwargs):
        print("🔕 JWT disabled — simulating user context for testing")

        # Simulate roles based on route
        path = request.path

        if "/admin_dashboard" in path or "/admin" in path:
            g.user_id = "fbaaf8a8-134e-4d18-8cf2-89387778ffc6"  # admin
            g.role = "admin"
        elif "/care_plan_dashboard" in path or "/submit_care_plan" in path:
            g.user_id = "d8fa56e0-37ae-4f34-8adf-05b2b32baa04"  # nurse
            g.role = "nurse"
        elif "/resident_dashboard" in path:
            g.user_id = "f6533a7c-42e6-4f3b-8a63-67fa1d915837"  # carer
            g.role = "carer"
        else:
            # fallback to admin role
            g.user_id = "edf3c908-799e-4562-b5bd-591807de03a1"
            g.role = "admin"

        return f(*args, **kwargs)

    return decorated_function



#def jwt_required(f):
    #@wraps(f)
    #def decorated_function(*args, **kwargs):
        #access_token = request.cookies.get('access_token')
        #if not access_token:
            #log_activity(None, "Unauthorized: No JWT presented")
            #print("❌ No access_token in cookies.")
            #return redirect(url_for('login'))
        
        #try:
            #secret = os.environ.get('JWT_SECRET')
            #print("✅ Using JWT_SECRET:", secret)

            #payload = jwt.decode(
                #access_token,
                #os.environ.get('JWT_SECRET'),
                #algorithms=['HS256'],
                #audience='authenticated'
            #)

            #print("✅ Decoded JWT payload:", payload)

            #user_id = payload.get('sub')
            #print("🔍 Looking up user ID:", user_id)

            #user = supabase.table("users").select("id, role, email").eq("id", user_id).single().execute()

            #print("🔍 Supabase user query result:", user.data)

            #if not user.data:
                #print("❌ No user found with ID from JWT.")
                #return redirect(url_for('login'))

            #g.user_id = user.data['id']
            #g.role = user.data['role']
            #print("✅ Auth success: g.user_id =", g.user_id, "g.role =", g.role)

 #       except Exception as e:
 #           log_activity(None, f"Unauthorized: Invalid JWT - {str(e)}")
 #           print("❌ JWT validation or DB lookup failed:", str(e))
 #           return redirect(url_for('login'))
        
  #      log_activity(g.user_id, "JWT validated", email=user.data["email"])
        
  #      return f(*args, **kwargs)
  #  return decorated_function