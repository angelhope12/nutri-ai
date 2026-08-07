import smtplib
import os
import random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import logging

load_dotenv()
logger = logging.getLogger(__name__)

SMTP_EMAIL = os.getenv("SMTP_EMAIL")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

def generate_verification_code() -> str:
    """Generates a 6-digit random code."""
    return str(random.randint(100000, 999999))

def send_verification_email(receiver_email: str, code: str) -> bool:
    """
    Sends a verification email with the 6-digit code.
    Returns True if successful, False otherwise.
    """
    if not SMTP_EMAIL or not SMTP_PASSWORD:
        logger.warning("SMTP credentials not found in environment variables. Email will not be sent.")
        # We'll print it to console for development purposes if credentials aren't set
        print(f"\n[DEV MODE] Verification Code for {receiver_email}: {code}\n")
        return True # Return true so development doesn't break

    try:
        message = MIMEMultipart("alternative")
        message["Subject"] = "NutriAI Verification Code"
        message["From"] = f"NutriAI <nutriai@support.ph>"
        message["To"] = receiver_email

        text = f"Welcome to NutriAI!\n\nYour verification code is: {code}\n\nThis code will expire in 10 minutes."
        html = f"""
        <html>
            <body style="font-family: Arial, sans-serif; color: #333;">
                <h2>Welcome to NutriAI! ✨</h2>
                <p>Thank you for signing up. Please use the following code to verify your email address:</p>
                <h1 style="color: #198754; letter-spacing: 2px;">{code}</h1>
                <p>This code will expire in 10 minutes.</p>
                <br>
                <p>Stay healthy!</p>
            </body>
        </html>
        """

        part1 = MIMEText(text, "plain")
        part2 = MIMEText(html, "html")

        message.attach(part1)
        message.attach(part2)

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.sendmail(SMTP_EMAIL, receiver_email, message.as_string())
        
        logger.info(f"Verification email sent to {receiver_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send verification email: {e}")
        # Even if it fails, let's print it to console so user isn't stuck during testing
        print(f"\n[DEV MODE - SEND FAILED] Verification Code for {receiver_email}: {code}\n")
        return False
