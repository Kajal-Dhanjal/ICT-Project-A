from flask import Blueprint, request, render_template
from security_protocols.monitoring.logger import log_honeypot
from .email_alert import send_alert_email

#honeypot = Blueprint("honeypot", __name__, template_folder="hp_web_interfaces")
app = Flask(__name__, template_folder="hp_web_interfaces")

@honeypot.route("/admin", methods=["GET", "POST"])
def fake_admin_panel():
    ip = request.remote_addr
    ua = request.headers.get("User-Agent", "Unknown")
    message = f"[HONEYPOT] Accessed fake admin panel - IP: {ip}, UA: {ua}"
    log_honeypot(ip, "[HONEYPOT] Accessed fake admin panel")
    send_alert_email("Honeypot Triggered: /admin", message)
    return render_template("admin.html"), 403

@honeypot.route("/login", methods=["GET", "POST"])
def login_trap():
    ip = request.remote_addr
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        message = f"[HONEYPOT] Login trap attempt - Email: {email}, Password: {password}, IP: {ip}"
        log_honeypot(ip, f"[HONEYPOT] Login trap attempt by {email}")
        send_alert_email("Honeypot Triggered: /login", message)
        return render_template("login.html"), 403
    return render_template("login.html")

@honeypot.route("/top-secrets", methods=["GET", "POST"])
def trap_file():
    ip = request.remote_addr
    message = f"[HONEYPOT] Tried accessing /top-secrets - IP: {ip}"
    log_honeypot(ip, "[HONEYPOT] Tried accessing /top-secrets")
    send_alert_email("Honeypot Triggered: /top-secrets", message)
    return render_template("top-secrets.html"), 403
