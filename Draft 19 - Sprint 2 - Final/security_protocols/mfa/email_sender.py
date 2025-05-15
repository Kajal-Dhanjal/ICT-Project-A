import smtplib
from email.message import EmailMessage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

# Reuse existing email credentials from password_reset/email_sender.py
from security_protocols.rbac.email_inviter import SENDER_EMAIL, SENDER_PASSWORD

def send_qr_code_email(to_email, qr_path, qr_link):
    """
    Send email with QR code as attachment
    
    Args:
        to_email: Email address of the recipient
        qr_path: File path to the QR code image
        qr_link: Link to view the QR code in browser
        
    Returns:
        True if email sent successfully, False otherwise
    """
    msg = MIMEMultipart()
    msg["Subject"] = "ElderSafe Connect - Your MFA Setup QR Code"
    msg["From"] = SENDER_EMAIL
    msg["To"] = to_email
    
    # Create text content
    text = f"""Hello,

Here is your Multi-Factor Authentication (MFA) QR code for ElderSafe Connect.

You can scan this QR code using your authenticator app or view it in your browser using this link:
{qr_link}

If you did not request this QR code, please contact support immediately.

– ElderSafe Connect Team
"""
    msg.attach(MIMEText(text, 'plain'))
    
    # Attach QR code image
    try:
        with open(qr_path, 'rb') as f:
            img_data = f.read()
            image = MIMEImage(img_data, name="mfa_qr_code.png")
            msg.attach(image)
            
        # Send email
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(SENDER_EMAIL, SENDER_PASSWORD)
            smtp.send_message(msg)
            print(f"✅ QR code email sent to {to_email}")
            return True
            
    except Exception as e:
        print(f"❌ Failed to send QR code email to {to_email}: {e}")
        return False