from flask import session
from security_protocols.rbac.rbac import get_user_by_id

def login_user(user_id):
    session["user_id"] = user_id

def logout_user():
    session.clear()

def get_user_from_session():
    from security_protocols.rbac.rbac import get_user_by_id
    return get_user_by_id(session.get("user_id"))

