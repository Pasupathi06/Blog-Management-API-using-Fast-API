import os
import smtplib
from email.message import EmailMessage

from dotenv import load_dotenv

load_dotenv()



SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_EMAIL = os.getenv("SMTP_EMAIL")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")


def send_email(
    recipient: str,
    subject: str,
    body: str
):
    if not SMTP_EMAIL or not SMTP_PASSWORD:
        print("Email settings are not configured.")
        return

    message = EmailMessage()
    message["From"] = SMTP_EMAIL
    message["To"] = recipient
    message["Subject"] = subject
    message.set_content(body)

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.send_message(message)

        print(f"Email sent successfully to {recipient}")

    except Exception as e:
        print(f"Email sending failed: {e}")