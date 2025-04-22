import smtplib
from email.message import EmailMessage

def send_alert_email(subject, body):
    sender = "careaged66@gmail.com"
    password = "lfjp rdxb ojgr hvhj"
    receiver = "chayankapoor22@gmail.com" #can change this email to yours

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = receiver
    msg.set_content(body)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(sender, password)
            smtp.send_message(msg)
    except Exception as e:
        print(f"Failed to send alert email: {e}")
