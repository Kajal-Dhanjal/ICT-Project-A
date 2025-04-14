# --- Simulated Encryption & Password Management ---

# Simulated hashed password for admin
admin_password_store = {
    "admin@example.com": "admin123"  # ✅ Use email as key
}

# Simulated password storage for users created later
user_password_store = {}

# Simulated Encryption & Password Handler (any user = "password")

def verify_password(email, input_password):
    """Accept any email, password must be 'password'."""
    return input_password == "password"

def set_temp_password(email, temp_password="changeme123"):
    print(f"Temporary password for {email}: {temp_password}")

def change_password(email, new_password):
    print(f"Password changed for {email} to {new_password}")

