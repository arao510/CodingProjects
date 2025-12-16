# ids_backend/email_utils.py

import smtplib
from email.mime.text import MIMEText
from ids_backend.config_email import EMAIL_SENDER, EMAIL_PASSWORD

def send_email_notification(subject: str, message: str, recipient: str = None):
    if recipient is None:
        raise ValueError("Recipient email address not provided.")

    msg = MIMEText(message)
    msg["Subject"] = subject
    msg["From"] = EMAIL_SENDER
    msg["To"] = recipient

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
            smtp.send_message(msg)
            print("✔ Email sent successfully!")
    except Exception as e:
        print("❌ Email sending failed:", e)
        raise
