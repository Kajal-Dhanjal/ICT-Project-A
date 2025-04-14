from flask import Flask, render_template, request, redirect, session, send_from_directory
from datetime import datetime
import os

# Security Modules
from security_protocols.web_perimeter_security.session_handler import (
    login_user, logout_user, get_user_from_session
)
from security_protocols.mfa.mfa_handler import verify_code
from security_protocols.rbac.rbac import (
    users, residents, assignments,
    get_user_by_email, get_user_by_id, get_role,
    get_accessible_residents, can_nurse_write,
    create_user, create_resident, assign_access,
    delete_user, delete_resident
)
from security_protocols.encryption.encryption_handler import verify_password

from security_protocols.database.db_handler import (
    get_resident_by_id, get_care_plans, get_vitals, get_medications, get_files,
    save_care_entry, save_medication, save_vitals
)
from security_protocols.logging_and_monitoring.logger import (
    log_activity, get_logs
)

app = Flask(__name__)
app.secret_key = 'demo-secret'
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["user"]
        password = request.form["password"]

        user = get_user_by_email(email)
        if user and verify_password(email, password):
            session["temp_user"] = user["user_id"]
            return redirect("/mfa")

    return render_template("login.html", users=users)


@app.route("/mfa", methods=["GET", "POST"])
def mfa():
    if request.method == "POST" and verify_code(request.form["code"]):
        login_user(session.pop("temp_user"))
        return redirect("/dashboard")
    return render_template("mfa.html")


@app.route("/dashboard")
def dashboard():
    user = get_user_from_session()
    if not user:
        return redirect("/")
    role = get_role(user)
    visible = get_accessible_residents(user)
    logs = get_logs() if role == "admin" else []
    return render_template("dashboard.html",
        user=user,
        role=role,
        residents=visible,
        logs=logs,
        all_users=users,
        assignments=assignments
    )


@app.route("/create_user", methods=["POST"])
def create_user_route():
    user = get_user_from_session()
    if user and get_role(user) == "admin":
        create_user(request.form["full_name"], request.form["email"], request.form["role"])
    return redirect("/dashboard")


@app.route("/create_resident", methods=["POST"])
def create_resident_route():
    user = get_user_from_session()
    if user and get_role(user) == "admin":
        create_resident(request.form["resident_name"], request.form["room_number"])
    return redirect("/dashboard")


@app.route("/assign_access", methods=["POST"])
def assign_access_route():
    user = get_user_from_session()
    if user and get_role(user) == "admin":
        assign_access(
            request.form["staff_email"],
            request.form["resident_name"],
            request.form["access_level"]
        )
    return redirect("/dashboard")


@app.route("/delete_user", methods=["POST"])
def delete_user_route():
    user = get_user_from_session()
    if user and get_role(user) == "admin":
        delete_user(request.form["user_id"])
    return redirect("/dashboard")


@app.route("/delete_resident", methods=["POST"])
def delete_resident_route():
    user = get_user_from_session()
    if user and get_role(user) == "admin":
        delete_resident(request.form["resident_id"])
    return redirect("/dashboard")


@app.route("/care_plan/<resident_id>", methods=["GET", "POST"])
def care_plan(resident_id):
    user = get_user_from_session()
    if not user:
        return redirect("/")

    resident = get_resident_by_id(resident_id)
    if not resident:
        return "Resident not found", 404

    role = get_role(user)
    has_write_access = can_nurse_write(user["user_id"], resident_id)

    if request.method == "POST":
        if role != "nurse" or not has_write_access:
            return "Unauthorized", 403

        save_care_entry(
            resident_id,
            request.form["assessment"],
            request.form["diagnosis"],
            request.form["goals"],
            request.form["interventions"],
            request.form["evaluation"],
            filename=handle_file_upload(request.files.get("file"))
        )

        if any([request.form.get("bp"), request.form.get("temp"), request.form.get("hr")]):
            save_vitals(resident_id, request.form["bp"], request.form["temp"], request.form["hr"])

        if request.form.get("med_name"):
            save_medication(
                resident_id,
                request.form["med_name"],
                request.form["dose"],
                request.form["time"],
                request.form["route"]
            )

        return redirect(f"/care_plan/{resident_id}")

    return render_template("care_plan_view.html",
        resident=resident,
        care_plans=get_care_plans(resident_id),
        vitals=get_vitals(resident_id),
        medications=get_medications(resident_id),
        files=get_files(resident_id),
        role=role,
        has_write_access=has_write_access,
        can_write=has_write_access  # alias for HTML
    )


def handle_file_upload(file):
    if file and file.filename:
        filename = file.filename
        path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(path)
        return filename
    return None


@app.route("/uploads/<filename>")
def serve_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


@app.route("/logout")
def logout():
    logout_user()
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)

