from flask import Blueprint, request
from security_protocols.logging_and_monitoring.logger import log_activity
from .email_alert import send_alert_email

honeypot = Blueprint("honeypot", __name__)

@honeypot.route("/admin-panel")
def fake_admin_panel():
    ip = request.remote_addr
    ua = request.headers.get("User-Agent", "Unknown")
    message = f"[HONEYPOT] Accessed fake admin panel - IP: {ip}, UA: {ua}"
    log_activity("HONEYPOT", message, ip)
    send_alert_email("Honeypot Triggered: /admin-panel", message)
    return "Access Denied. This activity has been logged.", 403

@honeypot.route("/login-trap", methods=["GET", "POST"])
def login_trap():
    ip = request.remote_addr
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        message = f"[HONEYPOT] Login trap attempt - Email: {email}, Password: {password}, IP: {ip}"
        log_activity("HONEYPOT", message, ip)
        send_alert_email("Honeypot Triggered: /login-trap", message)
        return "Incorrect credentials. This attempt has been logged.", 403
    return '''
        <h2>Legacy Login</h2>
        <form method="post">
            Email: <input name="email" type="text" /><br>
            Password: <input name="password" type="password" /><br>
            <input type="submit" value="Login" />
        </form>
    '''

@honeypot.route("/secret-files/backup.zip")
def trap_file():
    ip = request.remote_addr
    message = f"[HONEYPOT] Attempted to download trap file from /secret-files/backup.zip - IP: {ip}"
    log_activity("HONEYPOT", message, ip)
    send_alert_email("Honeypot Triggered: /secret-files/backup.zip", message)
    return "Access Denied. This action has been logged.", 403
