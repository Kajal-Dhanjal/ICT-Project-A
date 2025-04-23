from flask import Flask, render_template, request, redirect, g
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from supabase_client.supabaseClient import supabase
from security_protocols.rbac.rbac import get_role, get_user_by_email, get_all_users, get_all_residents
from security_protocols.rbac.assign import get_assigned_residents
from security_protocols.rbac.permissions import get_latest_vitals_for_resident
from werkzeug.utils import secure_filename
from security_protocols.rbac.invite import create_invite_token, verify_invite_token, complete_registration
from security_protocols.jwt.auth import jwt_required
from datetime import datetime
import os

from threading import Thread

from security_protocols.monitoring.logger import log_activity, get_logs, get_honeypot_logs

from security_protocols.honeypot.honeypot_handler import honeypot
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

@app.route("/admin/invite", methods=["GET", "POST"])
@jwt_required
def admin_invite():
    if g.role != "admin":
        return "Unauthorized", 403
    
    invite_link = None
    if request.method == "POST":
        email = request.form.get("email")
        role = request.form.get("role")
        token = create_invite_token(email, role)
        invite_link = f"{request.host_url}register?token={token}"
    
    return render_template("invite_form.html", invite_link=invite_link)

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
            user = supabase.table("users").select("id, role").eq("email", email).single().execute()
            
            resp = redirect("/dashboard")
            resp.set_cookie(
                'access_token',
                auth_response.session.access_token,
                httponly=True,
                secure=True,
                samesite='None'
            )
            log_activity(user.data['id'], "Logged in")
            return resp
        else:
            log_activity(None, "Failed login attempt", email=email)  # 👈 Fixed
            return "Invalid credentials", 403

    except Exception as e:
        print(f"Login error: {e}")
        log_activity(None, "Failed login attempt", email=email)  # 👈 Fixed
        return "Invalid credentials", 403
@app.route("/register", methods=["Get","POST"])
@limiter.limit("3600 per hour")  # Add this line
def register():

    if request.method == "GET":
        token = request.args.get("token")
        invite = verify_invite_token(token)
        if not invite:
            return "Invalid or expired invite link", 400
        return render_template("register.html", token=token, email=invite["email"])
    
    elif request.method == "POST":
        token = request.form.get("token")
        password = request.form.get("password")
        try:
            result = complete_registration(token, password)
            return render_template("register_success.html")
        except Exception as e:
            return str(e), 400

@app.route("/dashboard")
@jwt_required
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
    log_activity(g.user_id, "Logged out")
    resp = redirect("/login")
    resp.delete_cookie('access_token')
    return resp

@app.route("/admin_dashboard")
@jwt_required
def admin_dashboard():
    if g.role != "admin":
        return "Unauthorized", 403
    
    user = supabase.table("users").select("*").eq("id", g.user_id).single().execute().data
    users = get_all_users()
    residents = get_all_residents()
    logs = get_logs()
    honeypot_logs = get_honeypot_logs()  # You’ll need to create this
    return render_template("admin_dashboard.html", user=user, users=users, residents=residents, logs=logs, all_users=users, all_residents=residents, all_logs=logs, honeypot_logs=honeypot_logs)

@app.route("/care_plan_dashboard")
@jwt_required
def care_plan_dashboard():
    if g.role not in ["carer", "nurse"]:
        return "Unauthorized", 403
    
    residents = get_assigned_residents(g.user_id, g.role)
    
    for resident in residents:
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
def resident_dashboard():
    if g.role != "resident":
        return "Unauthorized", 403
    
    user = supabase.table("users").select("*").eq("id", g.user_id).single().execute().data
    care_summary = get_latest_vitals_for_resident(g.user_id)
    return render_template("resident_dashboard.html", user=user, care_summary=care_summary)

@app.route("/submit_care_plan", methods=["POST"])
@jwt_required
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