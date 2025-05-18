import smtplib
from email.message import EmailMessage
from security_protocols.rbac.email_inviter import SENDER_EMAIL, SENDER_PASSWORD

def send_password_reset_email(to_email, reset_link):
    """
    Send password reset email with the reset link
    Args:
        to_email: Email address of the recipient
        reset_link: Password reset link with token
    """
    msg = EmailMessage()
    msg["Subject"] = "ElderSafe Connect - Password Reset Link"
    msg["From"] = SENDER_EMAIL
    msg["To"] = to_email
    msg.set_content(
        f"""Hello,

You have requested to reset your password for ElderSafe Connect.

Please click the link below to reset your password:

{reset_link}

This link will expire in 60 minutes.

If you didn't request this password reset, you can safely ignore this email.

– ElderSafe Connect Team
"""
    )

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(SENDER_EMAIL, SENDER_PASSWORD)
            smtp.send_message(msg)
            print(f"✅ Password reset email sent to {to_email}")
            return True
    except Exception as e:
        print(f"❌ Failed to send password reset email to {to_email}: {e}")
        return False