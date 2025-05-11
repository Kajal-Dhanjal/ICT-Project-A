import smtplib
from email.message import EmailMessage

# ⚠️ This uses inline credentials for now — secure in production using .env
SENDER_EMAIL = "careaged66@gmail.com"
SENDER_PASSWORD = "lfjp rdxb ojgr hvhj"

def send_invite_email(to_email, invite_link):
    msg = EmailMessage()
    msg["Subject"] = "Your SecureCare Registration Link"
    msg["From"] = SENDER_EMAIL
    msg["To"] = to_email
    msg.set_content(
        f"""Hello,

You've been invited to join SecureCare.

Please complete your registration by clicking the link below:

{invite_link}

If you didn't request this, you can safely ignore it.

– SecureCare Team
"""
    )

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(SENDER_EMAIL, SENDER_PASSWORD)
            smtp.send_message(msg)
            print(f"✅ Invite sent to {to_email}")
    except Exception as e:
        print(f"❌ Failed to send invite to {to_email}: {e}")
