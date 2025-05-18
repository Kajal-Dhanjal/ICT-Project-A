# Enhanced Logger Module
from datetime import datetime

# In-memory storage for logs
auth_logs = []
honeypot_logs = []

def log_activity(user_id, action, email=None):
    """
    Log an authentication or user activity
    
    Args:
        user_id: ID of the user (can be None for unauthenticated actions)
        action: Description of the action
        email: Email address (optional, useful for login attempts)
        
    Returns:
        The created log entry
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = {
        "timestamp": timestamp,
        "user_id": user_id,
        "action": action,
        "email": email
    }
    
    # Add to the in-memory logs
    auth_logs.append(log_entry)
    
    # For production, you might want to also write to a file
    with open("security_protocols/monitoring/activity_logs.log", "a") as f:
        f.write(f"{timestamp} | User: {user_id} | {action} | {email or ''}\n")
    
    return log_entry

def get_logs(limit=100):
    """
    Get the most recent authentication logs
    
    Args:
        limit: Maximum number of logs to return
        
    Returns:
        List of log entries, newest first
    """
    # Return logs in reverse order (newest first)
    return sorted(auth_logs, key=lambda x: x["timestamp"], reverse=True)[:limit]

def log_honeypot(ip, action, details=None):
    """
    Log a honeypot triggering event
    
    Args:
        ip: IP address that triggered the honeypot
        action: The action or endpoint that was accessed
        details: Additional details (optional, e.g., submitted credentials)
        
    Returns:
        The created log entry
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = {
        "timestamp": timestamp,
        "ip": ip,
        "action": action,
        "details": details
    }
    
    # Add to the in-memory logs
    honeypot_logs.append(log_entry)
    
    # For production, you might want to also write to a file
    # with open("security_protocols/monitoring/honeypot_logs.log", "a") as f:
    #     f.write(f"{timestamp} | IP: {ip} | {action} | {details or ''}\n")
    
    return log_entry

def get_honeypot_logs(limit=50):
    """
    Get the most recent honeypot logs
    
    Args:
        limit: Maximum number of logs to return
        
    Returns:
        List of honeypot log entries, newest first
    """
    # Return logs in reverse order (newest first)
    return sorted(honeypot_logs, key=lambda x: x["timestamp"], reverse=True)[:limit]

# For testing purposes - generate some sample logs
def generate_sample_logs():
    """Generate some sample logs for testing the display"""
    # Clear existing logs
    auth_logs.clear()
    honeypot_logs.clear()
    
    # Sample users
    users = [
        {"id": "user1", "email": "admin@example.com"},
        {"id": "user2", "email": "nurse@example.com"},
        {"id": None, "email": "unknown@example.com"}
    ]
    
    # Sample auth actions
    auth_actions = [
        "Logged in successfully",
        "Failed login attempt",
        "Password reset requested",
        "JWT validated",
        "JWT validation failed: Token expired",
        "Unauthorized attempt to access admin dashboard",
        "Generated invite for user@example.com with role nurse",
        "Logged out"
    ]
    
    # Sample timestamps (for variety)
    timestamps = [
        "2025-05-01 09:15:22",
        "2025-05-05 14:30:45",
        "2025-05-10 08:22:17",
        "2025-05-12 16:05:33",
        "2025-05-13 10:45:12"
    ]
    
    # Generate auth logs
    for i in range(20):
        user = users[i % len(users)]
        action = auth_actions[i % len(auth_actions)]
        timestamp = timestamps[i % len(timestamps)]
        
        auth_logs.append({
            "timestamp": timestamp,
            "user_id": user["id"],
            "action": action,
            "email": user["email"]
        })
    
    # Sample honeypot actions
    honeypot_actions = [
        "[HONEYPOT] Accessed fake admin panel",
        "[HONEYPOT] Login trap attempt by hacker@example.com",
        "[HONEYPOT] Tried accessing /top-secrets",
        "[HONEYPOT] Attempted SQL injection"
    ]
    
    # Sample IPs
    ips = ["192.168.1.100", "10.0.0.5", "172.16.254.1", "8.8.8.8"]
    
    # Generate honeypot logs
    for i in range(10):
        action = honeypot_actions[i % len(honeypot_actions)]
        ip = ips[i % len(ips)]
        timestamp = timestamps[i % len(timestamps)]
        
        honeypot_logs.append({
            "timestamp": timestamp,
            "ip": ip,
            "action": action
        })
    
    print(f"Generated {len(auth_logs)} auth logs and {len(honeypot_logs)} honeypot logs")

# Uncomment to generate sample logs when this module is imported
# generate_sample_logs()