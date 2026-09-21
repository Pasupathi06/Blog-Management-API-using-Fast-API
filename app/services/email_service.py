import os
import smtplib
from email.message import EmailMessage

from dotenv import load_dotenv

load_dotenv()


# ============================================================
# SMTP SETTINGS
# ============================================================

# # ALREADY CORRECT
SMTP_HOST = os.getenv("SMTP_HOST", "live.smtp.mailtrap.io")

# # ALREADY CORRECT
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))

# # ADDED - Mailtrap username
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "api")

# # ALREADY CORRECT - Sender email
SMTP_EMAIL = os.getenv("SMTP_EMAIL")

# # ALREADY CORRECT - Mailtrap API token from .env
# # DO NOT PUT THE ACTUAL TOKEN HERE
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")


def send_email(
    recipient: str,
    subject: str,
    body: str
):
    """
    Send an email using SMTP.
    """

    # # CHANGED - SMTP_USERNAME added to validation
    if not SMTP_USERNAME or not SMTP_EMAIL or not SMTP_PASSWORD:
        print("Email settings are not configured.")
        return

    message = EmailMessage()

    # # ALREADY CORRECT
    message["From"] = SMTP_EMAIL
    message["To"] = recipient
    message["Subject"] = subject

    # # ALREADY CORRECT
    message.set_content(body)

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:

            # # ALREADY CORRECT
            server.starttls()

            # # CHANGED - Mailtrap uses api + API token
            server.login(
                SMTP_USERNAME,
                SMTP_PASSWORD
            )

            # # ALREADY CORRECT
            server.send_message(message)

        print(f"Email sent successfully to {recipient}")

    except Exception as e:
        # # ALREADY CORRECT
        print(f"Email sending failed: {e}")
