from datetime import datetime

logs = []

def log_activity(user_id, action):
    logs.append({
        "user_id": user_id,
        "action": action,
        "timestamp": datetime.now()
    })

def get_logs():
    return logs
