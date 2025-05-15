#!/usr/bin/env python3
"""
Test script to generate sample logs for ElderSafe Connect
Run this script to populate your system with test logs for development/testing
"""

import sys
import os
import random
from datetime import datetime, timedelta

# Add the parent directory to path so we can import from the project
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the logger module
from security_protocols.monitoring.logger import log_activity, log_honeypot, clear_logs

# Sample data
SAMPLE_USERS = [
    {"id": "user-001", "email": "admin@example.com", "role": "admin"},
    {"id": "user-002", "email": "nurse1@example.com", "role": "nurse"},
    {"id": "user-003", "email": "nurse2@example.com", "role": "nurse"},
    {"id": "user-004", "email": "carer1@example.com", "role": "carer"},
    {"id": "user-005", "email": "resident1@example.com", "role": "resident"},
]

SAMPLE_IPS = [
    "192.168.1.100",
    "192.168.1.101",
    "192.168.1.102",
    "10.0.0.1",
    "172.16.0.1",
]

UNKNOWN_EMAILS = [
    "unknown1@example.com",
    "hacker@evil.com",
    "test@test.com",
    "admin@otherdomain.com",
]

# Authentication log actions
AUTH_ACTIONS = [
    "Successful login",
    "Failed login attempt",
    "Password reset requested",
    "Account locked due to multiple failed attempts",
    "MFA verification successful",
    "MFA verification failed",
    "JWT validated",
    "JWT validation failed: Token expired",
    "Unauthorized attempt to access admin dashboard",
    "Generated invite for {email} with role {role}",
    "User logged out",
]

# Honeypot actions
HONEYPOT_ACTIONS = [
    "[HONEYPOT] Accessed fake admin panel",
    "[HONEYPOT] Login trap attempt by {email}",
    "[HONEYPOT] Tried accessing /top-secrets",
    "[HONEYPOT] Attempted SQL injection",
    "[HONEYPOT] Attempted XSS attack",
]

def generate_sample_logs(num_auth_logs=50, num_honeypot_logs=15):
    """Generate sample logs for testing"""
    # Clear existing logs
    clear_logs()
    
    print(f"Generating {num_auth_logs} authentication logs...")
    
    # Generate authentication logs
    for i in range(num_auth_logs):
        # Randomly decide if this is a log for a known or unknown user
        if random.random() < 0.8:  # 80% known users
            user = random.choice(SAMPLE_USERS)
            user_id = user["id"]
            email = user["email"]
            
            # Select an action
            action_template = random.choice(AUTH_ACTIONS)
            if "{email}" in action_template and "{role}" in action_template:
                # Handle the invite action
                target_user = random.choice(SAMPLE_USERS)
                action = action_template.format(email=target_user["email"], role=target_user["role"])
            else:
                action = action_template
        else:
            # Unknown user
            user_id = None
            email = random.choice(UNKNOWN_EMAILS)
            # Unknown users mostly generate failed login attempts
            if random.random() < 0.9:
                action = "Failed login attempt"
            else:
                action = random.choice(AUTH_ACTIONS)
        
        # Create the log
        log_activity(user_id, action, email=email)
    
    print(f"Generating {num_honeypot_logs} honeypot logs...")
    
    # Generate honeypot logs
    for i in range(num_honeypot_logs):
        ip = random.choice(SAMPLE_IPS)
        action_template = random.choice(HONEYPOT_ACTIONS)
        
        if "{email}" in action_template:
            action = action_template.format(email=random.choice(UNKNOWN_EMAILS))
        else:
            action = action_template
            
        log_honeypot(ip, action)
    
    print("Sample logs generated successfully!")

if __name__ == "__main__":
    # Allow command line arguments for the number of logs
    auth_logs = 50
    honeypot_logs = 15
    
    if len(sys.argv) > 1:
        try:
            auth_logs = int(sys.argv[1])
        except ValueError:
            print(f"Invalid number for auth logs: {sys.argv[1]}")
    
    if len(sys.argv) > 2:
        try:
            honeypot_logs = int(sys.argv[2])
        except ValueError:
            print(f"Invalid number for honeypot logs: {sys.argv[2]}")
    
    generate_sample_logs(auth_logs, honeypot_logs)