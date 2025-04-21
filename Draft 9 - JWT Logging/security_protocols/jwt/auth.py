from functools import wraps
from flask import request, redirect, url_for, g
import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
import os
from supabase_client.supabaseClient import supabase
from security_protocols.monitoring import security_audit

def jwt_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        access_token = request.cookies.get('access_token')
        if not access_token:
            security_audit.logger.warning("No access_token in cookies. Redirecting to login.")
            return redirect(url_for('login'))

        try:
            security_audit.logger.info("JWT received from browser.")
            payload = jwt.decode(
                access_token,
                os.environ.get('JWT_SECRET'),
                algorithms=['HS256'],
                options={"verify_aud": False}
            )
            user_id = payload.get('sub')
            security_audit.logger.info(f"JWT decoded successfully: sub={user_id}")

            user = supabase.table("users").select("id, role").eq("id", user_id).single().execute()
            if not user.data:
                security_audit.logger.warning(f"No user found with ID {user_id}. Redirecting to login.")
                return redirect(url_for('login'))

            g.user_id = user.data['id']
            g.role = user.data['role']
            security_audit.logger.info(f"Auth success — g.user_id={g.user_id}, g.role={g.role}")

        except ExpiredSignatureError:
            security_audit.logger.warning("JWT expired. Redirecting to login.")
            return redirect(url_for('login'))
        except InvalidTokenError as e:
            security_audit.logger.error(f"Invalid JWT: {str(e)}")
            return redirect(url_for('login'))
        except Exception as e:
            security_audit.logger.error(f"Unexpected JWT error: {str(e)}")
            return redirect(url_for('login'))

        return f(*args, **kwargs)
    return decorated_function
