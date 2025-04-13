import jwt
import os
from flask import request
from dotenv import load_dotenv
from functools import wraps

load_dotenv()
SECRET = os.getenv("SECRET_KEY")

def token_required(role=None):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            token = request.headers.get("Authorization")
            if not token:
                return {"message": "Token missing"}, 401
            try:
                payload = jwt.decode(token.split()[1], SECRET, algorithms=["HS256"])
                if role and payload.get("role") != role:
                    return {"message": "Forbidden"}, 403
                return f(*args, **kwargs)
            except jwt.ExpiredSignatureError:
                return {"message": "Token expired"}, 401
            except jwt.InvalidTokenError:
                return {"message": "Invalid token"}, 400
        return wrapper
    return decorator

def generate_token(username, role):
    return jwt.encode({"user": username, "role": role}, SECRET, algorithm="HS256")
