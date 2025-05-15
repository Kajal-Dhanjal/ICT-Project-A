import re
import hashlib
import requests
from functools import wraps
from flask import request, jsonify, redirect, flash

def validate_password(password):
    """
    Validates a password against the system's password policy.
    
    Returns:
        tuple: (is_valid, list of violations)
    """
    violations = []

    # Length check
    if len(password) < 8:
        violations.append("Password must be at least 8 characters long")
    
    # Complexity checks
    if not re.search(r'[A-Z]', password):
        violations.append("Password must contain at least one uppercase letter")
    
    if not re.search(r'[a-z]', password):
        violations.append("Password must contain at least one lowercase letter")
    
    if not re.search(r'[0-9]', password):
        violations.append("Password must contain at least one digit")
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        violations.append("Password must contain at least one special character")
    
    # Only check against HIBP if no policy violations
    if not violations and check_pwned_password(password):
        violations.append("Password has been found in a known data breach")
    
    return (len(violations) == 0, violations)

def check_pwned_password(password):
    """
    Returns True if password has been pwned, else False.
    Implements k-Anonymity using SHA-1 hashing (safe, no full password ever leaves the server).
    """
    sha1 = hashlib.sha1(password.encode('utf-8')).hexdigest().upper()
    prefix, suffix = sha1[:5], sha1[5:]

    try:
        response = requests.get(f"https://api.pwnedpasswords.com/range/{prefix}", timeout=5)
        if response.status_code != 200:
            raise ConnectionError("Failed to fetch data from HIBP API")

        hashes = (line.split(":") for line in response.text.splitlines())
        return any(stored_suffix == suffix for stored_suffix, _ in hashes)

    except Exception as e:
        print(f"HIBP check error: {e}")
        return False  # Fallback to allow registration if HIBP API is unavailable

def enforce_password_policy(password):
    """
    Enforces the password policy, raising an exception if the password doesn't comply.
    
    Args:
        password: The password to validate
        
    Raises:
        ValueError: If the password doesn't meet the policy requirements
    """
    is_valid, violations = validate_password(password)
    
    if not is_valid:
        error_message = "Password policy violations:\n- " + "\n- ".join(violations)
        raise ValueError(error_message)
    
    return True

def password_policy_required(route_function):
    """
    Decorator to enforce password policy on routes that handle password setting/changing
    """
    @wraps(route_function)
    def decorated_function(*args, **kwargs):
        if request.method == "POST":
            password = request.form.get("password")
            if password:
                try:
                    enforce_password_policy(password)
                except ValueError as e:
                    # Flash the error message (if using Flask-Flash)
                    if hasattr(request, 'app') and 'flash' in dir():
                        flash(str(e), 'error')
                    
                    # For API endpoints, return JSON error
                    if request.path.startswith('/api/'):
                        return jsonify({"success": False, "error": str(e)}), 400
                    
                    # Otherwise assume it's a form submission and redirect back
                    return redirect(request.url)
        
        return route_function(*args, **kwargs)
    
    return decorated_function