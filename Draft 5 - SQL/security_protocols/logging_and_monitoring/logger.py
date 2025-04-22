from datetime import datetime

logs = []

def log_activity(subject, action, ip=None):
    """Subject can be user_id or 'HONEYPOT' or 'SYSTEM'."""
    logs.append({
        "user_id": subject,
        "action": action,
        "ip": ip,
        "timestamp": datetime.now()
    })

def get_logs():
    return logs
