# security_protocols/logging_and_monitoring/logger.py
from datetime import datetime

#storage for logs
auth_logs = []

def log_activity(user_id, action, email=None):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = {
        "timestamp": timestamp,
        "user_id": user_id,
        "action": action,
        "email": email  # <- add this line
    }
    auth_logs.append(log_entry)
    return log_entry

def get_logs():
    """
    Get all authentication logs
    
    Returns:
        List of log entries
    """
    
    return auth_logs.copy()

honeypot_logs = []

def log_honeypot(ip, action):
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    honeypot_logs.append({
        "timestamp": timestamp,
        "ip": ip,
        "action": action
    })

def get_honeypot_logs():
    return honeypot_logs[::-1]
