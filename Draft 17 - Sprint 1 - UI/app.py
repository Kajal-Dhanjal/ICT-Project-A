from flask import Flask, render_template, request, redirect, g, send_from_directory, Response
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
from flask import url_for



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




from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__, template_folder="web_interface/templates")
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


@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email")

        user = get_user_by_email(email)
        if not user:
            return render_template("forgot_password.html", message="No user found.")

        from itsdangerous import URLSafeTimedSerializer
        s = URLSafeTimedSerializer(secret_key)
        token = s.dumps(email, salt="password-reset")

        reset_link = url_for("reset_password", token=token, _external=True)
        send_invite_email(email, reset_link)  # reuse function for sending the reset link

        return render_template("forgot_password.html", message="Reset link sent to your email.")

    return render_template("forgot_password.html")

@app.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
    s = URLSafeTimedSerializer(secret_key)

    try:
        email = s.loads(token, salt="password-reset", max_age=3600)
    except (SignatureExpired, BadSignature):
        return "Invalid or expired token", 400

    if request.method == "POST":
        new_password = request.form.get("password")
        # Call Supabase password reset logic or update directly if allowed
        user = get_user_by_email(email)
        if not user:
            return "User not found", 404

        supabase.auth.admin.update_user_by_id(user["id"], {"password": new_password})
        return redirect("/login")

    return render_template("reset_password.html", token=token)


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
    return send_from_directory(os.path.join(app.root_path, "security_protocols", "mfa", "static"), filename)


@app.route("/mfa/setup", methods=["GET"])
def mfa_setup():
    pending = session.get("pending_user")
    if not pending:
        return redirect("/login")

    user_id = pending["user_id"]
    email = pending["email"]

    # --- Generate MFA Secret ---
    secret = pyotp.random_base32()

    # --- Create otpauth URI (used by Microsoft/Google Authenticator) ---
    uri = pyotp.TOTP(secret).provisioning_uri(
        name=email,  # shown in the MFA app
        issuer_name="SecureCareApp"
    )

    # --- Save to Supabase ---
    supabase.table("users").update({"mfa_secret": secret}).eq("id", user_id).execute()

    # --- Save QR to /security_protocols/mfa/static/qr_<user_id>.png ---
    qr_filename = f"qr_{user_id}.png"
    app_root = os.getcwd()
    static_path = os.path.join(app_root, "security_protocols", "mfa", "static")
    os.makedirs(static_path, exist_ok=True)
    qr_path = os.path.join(static_path, qr_filename)

    qr = pyqrcode.create(uri)
    qr.png(qr_path, scale=6)

    # --- Render page with code and optional QR ---
    return render_template("mfa_setup_code.html", secret=secret, uri=uri, user_id=user_id)

@app.route("/mfa", methods=["GET"])
def mfa_page():
    pending = session.get("pending_user")
    if not pending:
        return redirect("/login")

    user_id = pending["user_id"]

    # --- Check if user has MFA secret ---
    result = supabase.table("users").select("mfa_secret").eq("id", user_id).single().execute()
    if not result.data.get("mfa_secret"):
        return redirect("/mfa/setup")  # 👈 Send to QR setup if none

    return render_template("mfa.html", user_id=pending["user_id"])  # 👈 Just render the form



@app.route("/mfa/validate", methods=["POST"])
def mfa_validate():
    data = request.form
    user_id = data.get("user_id")
    otp = data.get("otp").strip()

    if not user_id or not otp:
        return render_template("mfa.html", error="Missing user ID or OTP", user_id=user_id)

    result, status_code = verify_mfa_otp(user_id, otp)

    if result["status"] == "success":
        user_info = supabase.table("users").select("email, role").eq("id", user_id).single().execute().data

        log_activity(user_id, "Successful login", email=user_info["email"])  # ✅ Log AFTER MFA


        new_token = generate_jwt(user_id, user_info["role"], mfa_verified=True)

        resp = make_response(redirect(url_for("dashboard")))
        resp.set_cookie("access_token", new_token, httponly=True)
        return resp

    return render_template("mfa.html", error=result["message"], user_id=user_id)



@app.route("/login", methods=["GET", "POST"])
@limiter.limit("500 per minute")
def login():
    if request.method == "GET":
        return render_template("login.html")

    email = request.form.get("email")
    password = request.form.get("password")

    try:
        auth_response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })

        if auth_response.session and auth_response.session.access_token:
            user = supabase.table("users").select("id, role, mfa_secret").eq("email", email).single().execute()
              # 👈 Include mfa_secret

            if not user.data:
                return "User not registered in system", 403
            
            log_activity(user.data["id"], "Successful login", email=email)  # ✅ Add this line

            # --- [MFA Trigger] ---
            session["pending_user"] = {
                "email": email,
                "user_id": user.data["id"],
                "access_token": auth_response.session.access_token
            }
            
            if not user.data.get("mfa_secret"):  # 👈 NEW: Check for secret here
                return redirect("/mfa/setup")  # 👈 Direct to setup if missing
            else:
                return redirect("/mfa")

        else:
            log_activity(None, "Failed login attempt", email=email)
            return "Invalid credentials", 403

    except Exception as e:
        print(f"Login error: {e}")
        log_activity(None, "Failed login attempt", email=email)
        return "Invalid credentials", 403

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
@mfa_required
def logout():
    log_activity(g.user_id, "Logged out")
    resp = redirect("/login")
    resp.delete_cookie('access_token')
    return resp

@app.route("/admin_dashboard", methods=["GET", "POST"])

@jwt_required
@mfa_required
def admin_dashboard():
    if g.role != "admin":
        return "Unauthorized", 403
    
    invite_link = None
    if request.method == "POST":
        email = request.form.get("email")
        role = request.form.get("role")
        token = create_invite_token(email, role)
        invite_link = f"{request.host_url}register?token={token}"

        send_invite_email(email, invite_link)
    
    user = supabase.table("users").select("*").eq("id", g.user_id).single().execute().data
    user = supabase.table("users").select("*").eq("id", g.user_id).single().execute().data
    if not user or "email" not in user:
        user = {"email": "Unknown"}


    users = get_all_users()
    residents = get_all_residents()
    logs = get_logs()
    honeypot_logs = get_honeypot_logs()  # You’ll need to create this
    #return render_template("admin_dashboard.html", user=user, users=users, residents=residents, logs=logs, all_users=users, all_residents=residents, all_logs=logs, honeypot_logs=honeypot_logs)
    return render_template("admin_dashboard.html",
        user=user,
        users=users,
        residents=residents,
        logs=logs,
        all_users=users,
        all_residents=residents,
        all_logs=logs,
        honeypot_logs=honeypot_logs,
        invite_link=invite_link  # 👈 Pass this to the template
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

def run_main():
    app.run(port=5000, debug=True, use_reloader=False)  # 👈 reloader off

def run_honeypot():
    honeypot_app.run(port=3000, debug=True, use_reloader=False)  # 👈 reloader off


if __name__ == "__main__":
    Thread(target=run_main).start()
    Thread(target=run_honeypot).start()