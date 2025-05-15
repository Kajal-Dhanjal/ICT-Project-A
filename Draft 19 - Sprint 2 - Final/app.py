import threading
import ssl

from flask import Flask, render_template, request, redirect, g, send_from_directory, Response
from flask import Flask, render_template, request, redirect, g, jsonify, make_response
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from supabase_client.supabaseClient import supabase
from security_protocols.rbac.rbac import get_user_by_email, get_all_users, get_all_residents
from security_protocols.rbac.assign import get_assigned_residents
from security_protocols.rbac.permissions import get_latest_vitals_for_resident
from werkzeug.utils import secure_filename
from security_protocols.rbac.invite import create_invite_token, verify_invite_token, complete_registration

from security_protocols.rbac.email_inviter import send_invite_email

from security_protocols.jwt.auth import jwt_required
from security_protocols.jwt.jwt_handler import generate_jwt
from flask import make_response

from security_protocols.password_reset.email_sender import send_password_reset_email

from datetime import datetime
import os

from threading import Thread

from security_protocols.monitoring.logger import log_activity, get_logs, get_honeypot_logs

from security_protocols.honeypot.honeypot_handler import honeypot

from security_protocols.mfa.mfa import verify_mfa_otp, mfa_required



# Separate honeypot Flask app
from flask import Flask as HoneypotFlask
honeypot_app = HoneypotFlask(__name__)
honeypot_app.register_blueprint(honeypot)

@honeypot_app.route("/", methods=["GET", "POST"])
def honeypot_login():
    if request.method == "POST":
        print("⚠️ Honeypot triggered:", request.form)
    return '''
        <h1>Login</h1>
        <form method="POST">
            Username: <input name="username"><br>
            Password: <input name="password"><br>
            <input type="submit">
        </form>
    '''


from dotenv import load_dotenv
load_dotenv()

app = Flask(
    __name__,
    template_folder='web_interface/templates',
    static_folder='web_interface/static'
)


app.secret_key = os.getenv("FLASK_SECRET_KEY")

csrf = CSRFProtect(app)  # CSRF protection
limiter = Limiter(       # Rate limiting
    app=app,
    key_func=get_remote_address,
    default_limits=["2000 per day", "500 per hour"]
)

secret_key = os.getenv("FLASK_SECRET_KEY")

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route("/admin/invite", methods=["GET", "POST"])
@jwt_required
@mfa_required
def admin_invite():
    if g.role != "admin":
        return "Unauthorized", 403  # ✅ Block non-admins

    invite_link = None
    if request.method == "POST":
        email = request.form.get("email")
        role = request.form.get("role")
        token = create_invite_token(email, role)
        invite_link = f"{request.host_url}register?token={token}"

    return render_template("invite_form.html", invite_link=invite_link)



from flask import render_template, redirect, url_for, request, session
# --- [MFA QR Code Setup for Microsoft Authenticator] ---
import pyotp
import pyqrcode
from flask import send_file

@app.route('/qr/<filename>')
def serve_qr(filename):
    # Construct the full path
    full_path = os.path.join(app.root_path, "security_protocols", "mfa", "static", filename)
    
    # Debug logging
    print(f"Requested QR image: {filename}")
    print(f"Looking for file at: {full_path}")
    print(f"File exists: {os.path.exists(full_path)}")
    
    # Include explicit MIME type
    return send_from_directory(
        os.path.join(app.root_path, "security_protocols", "mfa", "static"),
        filename
    )


# Find the /mfa/setup route
@app.route("/mfa/setup", methods=["GET"])
def mfa_setup():
    pending = session.get("pending_user")
    if not pending:
        return redirect("/login")

    # Only proceed with setup if force=true or user doesn't have MFA set up
    user_id = pending["user_id"]
    email = pending["email"]
    
    # Check if MFA is already set up
    result = supabase.table("users").select("mfa_secret").eq("id", user_id).single().execute()
    
    # If force parameter isn't provided and MFA is set up, redirect to verification
    if request.args.get('force') != 'true' and result.data and result.data.get("mfa_secret"):
        return redirect("/mfa")

    # Rest of your MFA setup code...
    # Generate a new MFA Secret only if needed
    secret = pyotp.random_base32()
    print(f"DEBUG: Generating new MFA secret for {user_id}: {secret}")
    
    # Create otpauth URI
    uri = pyotp.TOTP(secret).provisioning_uri(
        name=email,  # shown in the MFA app
        issuer_name="SecureCareApp"
    )
    
    # Save to Supabase
    supabase.table("users").update({"mfa_secret": secret}).eq("id", user_id).execute()
    log_activity(user_id, "MFA secret generated and saved", email=email)
    
    # Save QR as image
    qr_filename = f"qr_{user_id}.png"
    app_root = os.getcwd()
    static_path = os.path.join(app_root, "security_protocols", "mfa", "static")
    os.makedirs(static_path, exist_ok=True)
    qr_path = os.path.join(static_path, qr_filename)
    
    qr = pyqrcode.create(uri)
    qr.png(qr_path, scale=6)

    # Get the MFA secret
    result = supabase.table("users").select("mfa_secret").eq("id", user_id).single().execute()
    secret = result.data.get("mfa_secret")
    qr_filename = f"qr_{user_id}.png"
    
    # Always render the setup page
    return render_template("mfa_setup_code.html", secret=secret, user_id=user_id, qr_filename=qr_filename)

@app.route("/mfa", methods=["GET"])
def mfa_page():
    pending = session.get("pending_user")
    if not pending:
        return redirect("/login")

    user_id = pending["user_id"]

    # Check if user has completed MFA setup
    result = supabase.table("users").select("mfa_secret").eq("id", user_id).single().execute()
    
    # Let the user continue to verification even if not set up yet
    # They can set up from the MFA page if needed
    return render_template("mfa.html", user_id=user_id)
@app.route("/mfa/validate", methods=["POST"])
def mfa_validate():
    data = request.form
    user_id = data.get("user_id")
    otp = data.get("otp").strip()

    if not user_id or not otp:
        log_activity(None, "MFA validation failed: Missing user ID or OTP")
        return render_template("mfa.html", error="Missing user ID or OTP", user_id=user_id)

    result, status_code = verify_mfa_otp(user_id, otp)

    if result["status"] == "success":
        user_info = supabase.table("users").select("email, role").eq("id", user_id).single().execute().data

        log_activity(user_id, "MFA verification successful", email=user_info["email"])

        new_token = generate_jwt(user_id, user_info["role"], mfa_verified=True)
        log_activity(user_id, "JWT generated after MFA verification", email=user_info["email"])

        resp = make_response(redirect(url_for("dashboard")))
        resp.set_cookie("access_token", new_token, httponly=True)
        return resp
    else:
        # Log failed MFA attempts
        try:
            user_info = supabase.table("users").select("email").eq("id", user_id).single().execute().data
            email = user_info["email"] if user_info else None
        except Exception:
            email = None
            
        log_activity(user_id, f"MFA verification failed: {result['message']}", email=email)
        return render_template("mfa.html", error=result["message"], user_id=user_id)
# Add these routes to app.py near other MFA-related routes
from flask import jsonify
from security_protocols.mfa.email_sender import send_qr_code_email

@app.route("/mfa/email-qr/<user_id>", methods=["POST"])
def email_qr_code(user_id):
    # Get user's email from database
    user = supabase.table("users").select("email").eq("id", user_id).single().execute()
    if not user.data:
        return jsonify({"success": False, "message": "User not found"}), 404
    
    email = user.data["email"]
    qr_filename = f"qr_{user_id}.png"
    qr_path = os.path.join(app.root_path, "security_protocols", "mfa", "static", qr_filename)
    
    # Generate a temporary link to view the QR code
    qr_link = url_for('serve_qr_link', user_id=user_id, _external=True)
    
    # Send email with QR code as attachment
    success = send_qr_code_email(email, qr_path, qr_link)
    
    if success:
        return jsonify({"success": True, "message": "QR code sent to your email"})
    else:
        return jsonify({"success": False, "message": "Failed to send email"}), 500

@app.route("/qr-link/<user_id>")
def serve_qr_link(user_id):
    # This route serves the QR code as a standalone page
    # Security check to verify user has access to this QR code
    pending = session.get("pending_user")
    if not pending or pending["user_id"] != user_id:
        return "Unauthorized", 403
        
    return render_template("qr_code_view.html", user_id=user_id)

# In app.py, replace the login route with this version:

@app.route("/login", methods=["GET", "POST"])
@limiter.limit("500 per minute")
def login():
    if request.method == "GET":
        return render_template("login.html")

    email = request.form.get("email")
    password = request.form.get("password")
    
    # Log the login attempt (without recording the password)
    client_ip = request.remote_addr
    user_agent = request.headers.get("User-Agent", "Unknown")
    log_message = f"Login attempt from IP: {client_ip}, User-Agent: {user_agent}"
    
    try:
        auth_response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })

        if auth_response.session and auth_response.session.access_token:
            user = supabase.table("users").select("id, role, mfa_secret").eq("email", email).single().execute()
              
            if not user.data:
                log_activity(None, f"Failed login: User not registered in system", email=email)
                return "User not registered in system", 403
            
            log_activity(user.data["id"], f"{log_message} - Successful login", email=email)

            # Store user info in session for MFA verification
            session["pending_user"] = {
                "email": email,
                "user_id": user.data["id"],
                "access_token": auth_response.session.access_token
            }
            
            # Always redirect to MFA verification regardless of setup status
            log_activity(user.data["id"], "Redirecting to MFA verification", email=email)
            return redirect("/mfa")  # Always redirect to MFA verification

        else:
            log_activity(None, f"{log_message} - Failed login: Invalid credentials", email=email)
            return "Invalid credentials", 403

    except Exception as e:
        error_message = str(e)
        log_activity(None, f"{log_message} - Failed login: {error_message}", email=email)
        return "Invalid credentials", 403

@app.route("/forgot-password", methods=["GET", "POST"])
@limiter.limit("5 per minute")  # Prevent abuse
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email")
        
        # First, check if user exists
        user = get_user_by_email(email)
        if not user:
            # We don't reveal if user exists or not for security
            return render_template("forgot_password.html", 
                                message="If your email is registered, you'll receive a password reset link.")

        # Generate secure token using itsdangerous
        from itsdangerous import URLSafeTimedSerializer
        s = URLSafeTimedSerializer(secret_key)
        token = s.dumps(email, salt="password-reset")
        
        # Create reset link with token
        reset_link = url_for("reset_password", token=token, _external=True)
        
        # Import the password reset email function
        from security_protocols.password_reset.email_sender import send_password_reset_email
        
        # Send the reset email
        send_success = send_password_reset_email(email, reset_link)
        
        # For security reasons, always show the same message whether the email exists or not
        message = "If your email is registered, you'll receive a password reset link."
        if not send_success:
            # Log the failure but don't reveal to user
            print(f"Failed to send password reset email to {email}")
            log_activity(None, "Failed to send password reset email", email=email)
        else:
            log_activity(None, "Password reset requested", email=email)
            
        return render_template("forgot_password.html", message=message)

    # GET request - show the form
    return render_template("forgot_password.html")

@app.route("/reset-password/<token>", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def reset_password(token):
    # Import password policy verification
    from security_protocols.passwords.password_policy import enforce_password_policy
    
    # Verify the token
    from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
    s = URLSafeTimedSerializer(secret_key)
    
    try:
        # Token expires after 1 hour (3600 seconds)
        email = s.loads(token, salt="password-reset", max_age=3600)
    except SignatureExpired:
        return render_template("reset_password_error.html", error="This password reset link has expired.")
    except BadSignature:
        return render_template("reset_password_error.html", error="Invalid reset link.")
    
    # Handle form submission
    if request.method == "POST":
        new_password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")
        
        # Validate password match
        if new_password != confirm_password:
            return render_template("reset_password.html", token=token, error="Passwords do not match.")
        
        try:
            # Enforce password policy
            enforce_password_policy(new_password)
            
            # Get the user
            user = get_user_by_email(email)
            if not user:
                return render_template("reset_password_error.html", error="User not found.")
            
            try:
                # Hash the password using our password hasher
                from security_protocols.passwords.password_hasher import hash_password
                hashed_password = hash_password(new_password)
                
                # Update the hashed password in our users table
                supabase.table("users").update({"hashed_pw": hashed_password}).eq("id", user["id"]).execute()
                
                # Update the password in Supabase Auth
                supabase.auth.admin.update_user_by_id(
                    user["id"],
                    {"password": new_password}
                )
                
                # Log the password reset
                log_activity(user["id"], "Password reset successful", email=email)
                
                # Redirect to success page
                return render_template("reset_password_success.html")
                
            except Exception as e:
                # Log the specific error for debugging
                print(f"Password reset error: {e}")
                log_activity(None, f"Password reset failed: {str(e)}", email=email)
                return render_template("reset_password.html", token=token, 
                                    error=f"An error occurred: {str(e)}")
                                    
        except ValueError as e:
            # Password policy violation
            return render_template("reset_password.html", token=token, error=str(e))
            
        except Exception as outer_e:
            # Log any outer exceptions for debugging
            print(f"Outer password reset error: {outer_e}")
            return render_template("reset_password.html", token=token, 
                                error=f"An error occurred: {str(outer_e)}")
    
    # GET request - show the reset form
    return render_template("reset_password.html", token=token)

@app.route("/register", methods=["GET", "POST"])
@limiter.limit("3600 per hour")
def register():
    token = request.args.get("token") if request.method == "GET" else request.form.get("token")

    invite = verify_invite_token(token)

    # Fix: handle bad or response-type returns
    if not invite or isinstance(invite, Response):
        return "Invalid or expired invite link", 400

    if isinstance(invite, tuple):
        invite_data, status = invite
        if not invite_data or status != 200:
            return "Invalid or expired invite link", status
    else:
        invite_data = invite

    if not invite_data or not isinstance(invite_data, dict):
        return "Invalid token payload", 400

    if request.method == "GET":
        return render_template("register.html", token=token, email=invite_data.get("email"))

    elif request.method == "POST":
        password = request.form.get("password")
        try:
            result = complete_registration(token, password)
            return render_template("register_success.html")
        except Exception as e:
            return str(e), 400

    return "Unexpected error", 500


@app.route("/dashboard")
@jwt_required
@mfa_required
def dashboard():
    print("Dashboard loaded")
    print("g.role:", g.get("role"))
    print("g.user_id:", g.get("user_id"))
    if g.role == "admin":
        return redirect("/admin_dashboard")
    elif g.role in ["nurse", "carer"]:
        return redirect("/care_plan_dashboard")
    elif g.role == "resident":
        return redirect("/resident_dashboard")
    return "Unauthorized", 403

@app.route("/logout")
@jwt_required
def logout():
    user_id = g.user_id
    user_email = None
    
    # Get the user's email for the log
    try:
        user = supabase.table("users").select("email").eq("id", user_id).single().execute().data
        if user and "email" in user:
            user_email = user["email"]
    except Exception:
        pass
    
    log_activity(user_id, "User logged out", email=user_email)
    
    # Clear cookies and redirect
    resp = redirect("/login")
    resp.delete_cookie('access_token')
    return resp


@app.route("/admin_dashboard", methods=["GET", "POST"])
@jwt_required
@mfa_required
def admin_dashboard():
    if g.role != "admin":
        # Log unauthorized access attempts
        log_activity(g.user_id, "Unauthorized attempt to access admin dashboard")
        return "Unauthorized", 403
    
    invite_link = None
    if request.method == "POST":
        email = request.form.get("email")
        role = request.form.get("role")
        
        # Validate user input
        if not email or not role:
            return "Missing required fields", 400
            
        if role not in ["admin", "nurse", "carer", "resident"]:
            return "Invalid role", 400
            
        # Create invite token
        token = create_invite_token(email, role)
        invite_link = f"{request.host_url}register?token={token}"

        # Send email and log the action
        send_invite_email(email, invite_link)
        log_activity(g.user_id, f"Generated invite for {email} with role {role}")
    
    # Get current user information
    user = supabase.table("users").select("*").eq("id", g.user_id).single().execute().data
    if not user or "email" not in user:
        user = {"email": "Unknown"}

    # Get all users, residents, and logs
    users = get_all_users()
    residents = get_all_residents()
    
    # Get the 100 most recent logs for display
    logs = get_logs(100)
    honeypot_logs = get_honeypot_logs(50)
    
    # Pass all necessary data to the template
    return render_template("admin_dashboard.html",
        user=user,
        users=users,
        residents=residents,
        logs=logs,
        all_users=users,
        all_residents=residents,
        honeypot_logs=honeypot_logs,
        invite_link=invite_link
    )


@app.route("/care_plan_dashboard")
@jwt_required
@mfa_required
def care_plan_dashboard():
    if g.role not in ["carer", "nurse"]:
        user = supabase.table("users").select("email").eq("id", g.user_id).single().execute().data
        log_activity(g.user_id, "Unauthorized attempt to access care_plan_dashboard")
        return "Unauthorized", 403
    
    residents = get_assigned_residents(g.user_id, g.role)
    
    for resident in residents:
        print("DEBUG: Resident ID =", resident.get("id"))
        resident["care_plans"] = get_care_plans(resident["id"])
        resident["care_plans"] = sorted(resident["care_plans"], 
                                      key=lambda x: x["timestamp"], 
                                      reverse=True)
    
    user = supabase.table("users").select("*").eq("id", g.user_id).single().execute().data
    return render_template("care_plan_dashboard.html", 
                         user=user, 
                         residents=residents, 
                         role=g.role)

def format_datetime(value, format="%Y-%m-%d %H:%M"):
    if isinstance(value, str):
        value = datetime.fromisoformat(value)
    return value.strftime(format)

app.jinja_env.filters['datetimeformat'] = format_datetime

@app.route("/resident_dashboard")
@jwt_required
@mfa_required
def resident_dashboard():
    if g.role != "resident":
        return "Unauthorized", 403
    
    user = supabase.table("users").select("*").eq("id", g.user_id).single().execute().data
    care_summary = get_latest_vitals_for_resident(g.user_id)
    return render_template("resident_dashboard.html", user=user, care_summary=care_summary)

@app.route("/submit_care_plan", methods=["POST"])
@jwt_required
@mfa_required
def submit_care_plan():
    if g.role != "nurse":
        return "Unauthorized", 403
    
    resident_id = request.form.get("resident_id")
    assessment = request.form.get("assessment")
    bp = request.form.get("bp")
    temp = request.form.get("temp")
    hr = request.form.get("hr")
    medications = request.form.get("medications")
    timestamp = datetime.utcnow().isoformat()

    file_url = None
    file = request.files.get("attachment")
    if file and file.filename:
        filename = secure_filename(file.filename)
        file_path = os.path.join("uploads", filename)
        file.save(file_path)
        file_url = f"/uploads/{filename}"

    supabase.table("care_plans").insert({
        "resident_id": resident_id,
        "nurse_id": g.user_id,
        "assessment": assessment,
        "bp": bp,
        "temp": temp,
        "hr": hr,
        "medications": medications,
        "timestamp": timestamp,
        "attachment": file_url
    }).execute()

    log_activity(g.user_id, f"Submitted care plan for resident {resident_id}")

    return redirect("/care_plan_dashboard")

@app.route("/create_resident", methods=["POST"])
@jwt_required
@mfa_required
def create_resident():
    if g.role != "admin":
        return "Unauthorized", 403
    
    full_name = request.form.get("full_name")
    room = request.form.get("room")
    if not full_name or not room:
        return "Missing fields", 400

    supabase.table("residents").insert({
        "full_name": full_name,
        "room": room
    }).execute()

    log_activity(g.user_id, f"Created resident: {full_name} (Room {room})")

    return redirect("/admin_dashboard")

@app.route("/assign_staff", methods=["POST"])
@jwt_required
@mfa_required
def assign_staff():
    if g.role != "admin":
        return "Unauthorized", 403
    
    staff_id = request.form.get("staff_id")
    resident_id = request.form.get("resident_id")
    access_level = request.form.get("access_level")

    if not staff_id or not resident_id or not access_level:
        return "Incomplete form submission", 400

    existing = supabase.table("assignments").select("*").eq("staff_id", staff_id).eq("resident_id", resident_id).execute()
    if existing.data:
        supabase.table("assignments").update({"access": access_level}).eq("staff_id", staff_id).eq("resident_id", resident_id).execute()
    else:
        supabase.table("assignments").insert({
            "staff_id": staff_id,
            "resident_id": resident_id,
            "access": access_level
        }).execute()

        log_activity(g.user_id, f"Assigned staff {staff_id} to resident {resident_id} ({access_level} access)")

    return redirect("/admin_dashboard")

def get_latest_vitals_for_resident(resident_id):
    response = (
        supabase.table("care_plans")
        .select("*")
        .eq("resident_id", resident_id)
        .order("timestamp", desc=True)
        .limit(1)
        .execute()
    )
    return response.data[0] if response.data else None

def get_care_plans(resident_id):
    response = supabase.table("care_plans").select("*").eq("resident_id", resident_id).order("timestamp", desc=True).execute()
    return response.data if response.data else []

def get_latest_vitals(resident_id):
    return get_latest_vitals_for_resident(resident_id)

def get_medications(resident_id):
    response = supabase.table("care_plans").select("medications").eq("resident_id", resident_id).order("timestamp", desc=True).limit(1).execute()
    return response.data[0]["medications"] if response.data else "N/A"

def get_uploaded_files(resident_id):
    response = supabase.table("care_plans").select("attachment").eq("resident_id", resident_id).order("timestamp", desc=True).limit(1).execute()
    return response.data[0]["attachment"] if response.data else None

@app.after_request
def add_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    return response

app.register_blueprint(honeypot)

context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.load_cert_chain(certfile="security_protocols/TLS/cert/cert.pem",
                             keyfile="security_protocols/TLS/cert/key.pem")

def run_main():
    #app.run(host="192.168.68.1", port=5000, ssl_context=("security_protocols/TLS/cert/cert.pem", "security_protocols/TLS/cert/key.pem"))
    #app.run(host="192.168.68.1", port=5000)
    app.run(host="0.0.0.0", port=5000, debug=False)



def run_honeypot():
    honeypot_app.run(host="0.0.0.0", port=3000, debug=True, use_reloader=False)


if __name__ == "__main__":
        Thread(target=run_main).start()
        Thread(target=run_honeypot).start()