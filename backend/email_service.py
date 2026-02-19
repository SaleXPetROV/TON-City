"""
Email Service for TON City Builder
Handles sending password reset codes via SMTP
"""
import os
import smtplib
import random
import string
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone, timedelta
import logging

logger = logging.getLogger(__name__)

# In-memory storage for reset codes (in production, use Redis or DB)
reset_codes = {}

# In-memory storage for email verification codes
email_verification_codes = {}

def generate_reset_code() -> str:
    """Generate 8-character code with uppercase, lowercase letters and digits"""
    characters = string.ascii_uppercase + string.ascii_lowercase + string.digits
    return ''.join(random.choice(characters) for _ in range(8))

def generate_verification_code() -> str:
    """Generate 6-digit verification code"""
    return ''.join(random.choice(string.digits) for _ in range(6))

def store_verification_code(email: str, code: str, username: str, password_hash: str):
    """Store email verification code with user data"""
    email_verification_codes[email.lower()] = {
        "code": code,
        "username": username,
        "password_hash": password_hash,
        "expires_at": datetime.now(timezone.utc) + timedelta(minutes=15),
        "attempts": 0
    }

def verify_email_code(email: str, code: str) -> tuple[bool, str, dict]:
    """
    Verify email verification code
    Returns (success, message, user_data)
    """
    email_lower = email.lower()
    
    if email_lower not in email_verification_codes:
        return False, "no_code_requested", {}
    
    stored = email_verification_codes[email_lower]
    
    # Check expiration
    if datetime.now(timezone.utc) > stored["expires_at"]:
        del email_verification_codes[email_lower]
        return False, "code_expired", {}
    
    # Check attempts (max 5)
    if stored["attempts"] >= 5:
        del email_verification_codes[email_lower]
        return False, "too_many_attempts", {}
    
    # Verify code
    if stored["code"] != code:
        stored["attempts"] += 1
        return False, "invalid_code", {}
    
    # Success - get user data and remove code
    user_data = {
        "username": stored["username"],
        "password_hash": stored["password_hash"]
    }
    del email_verification_codes[email_lower]
    return True, "success", user_data

def store_reset_code(email: str, code: str):
    """Store reset code with 15 minute expiration"""
    reset_codes[email.lower()] = {
        "code": code,
        "expires_at": datetime.now(timezone.utc) + timedelta(minutes=15),
        "attempts": 0
    }

def verify_reset_code(email: str, code: str) -> tuple[bool, str]:
    """
    Verify reset code for email
    Returns (success, message)
    """
    email_lower = email.lower()
    
    if email_lower not in reset_codes:
        return False, "no_code_requested"
    
    stored = reset_codes[email_lower]
    
    # Check expiration
    if datetime.now(timezone.utc) > stored["expires_at"]:
        del reset_codes[email_lower]
        return False, "code_expired"
    
    # Check attempts (max 5)
    if stored["attempts"] >= 5:
        del reset_codes[email_lower]
        return False, "too_many_attempts"
    
    # Verify code
    if stored["code"] != code:
        stored["attempts"] += 1
        return False, "invalid_code"
    
    # Success - remove code
    del reset_codes[email_lower]
    return True, "success"

def send_reset_email(to_email: str, code: str, language: str = "en") -> bool:
    """Send password reset email with code"""
    return send_email_with_code(to_email, code, language, "reset")

def send_verification_email(to_email: str, code: str, language: str = "en") -> bool:
    """Send email verification code"""
    return send_email_with_code(to_email, code, language, "verification")

def send_email_with_code(to_email: str, code: str, language: str = "en", email_type: str = "reset") -> bool:
    """Send email with code (reset or verification)"""
    smtp_host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = os.environ.get("SMTP_USER")
    smtp_password = os.environ.get("SMTP_PASSWORD")
    from_email = os.environ.get("SMTP_FROM_EMAIL", smtp_user)
    from_name = os.environ.get("SMTP_FROM_NAME", "TON City Builder")
    
    if not smtp_user or not smtp_password:
        logger.error("SMTP credentials not configured")
        return False
    
    # Email content based on language
    subjects = {
        "en": "Password Reset Code - TON City Builder",
        "ru": "Код восстановления пароля - TON City Builder",
        "zh": "密码重置代码 - TON City Builder",
        "es": "Código de restablecimiento de contraseña - TON City Builder",
        "de": "Passwort-Reset-Code - TON City Builder",
        "fr": "Code de réinitialisation du mot de passe - TON City Builder",
        "ja": "パスワードリセットコード - TON City Builder",
        "ko": "비밀번호 재설정 코드 - TON City Builder"
    }
    
    bodies = {
        "en": f"""
<html>
<body style="font-family: Arial, sans-serif; background-color: #0a0a0f; color: #ffffff; padding: 20px;">
    <div style="max-width: 500px; margin: 0 auto; background: linear-gradient(135deg, #1a1a2e 0%, #0f0f1a 100%); border-radius: 16px; padding: 30px; border: 1px solid rgba(0,255,255,0.2);">
        <h1 style="color: #00ffff; margin-bottom: 20px;">🏙️ TON City Builder</h1>
        <p>You requested a password reset. Use the code below:</p>
        <div style="background: rgba(0,255,255,0.1); border-radius: 8px; padding: 20px; text-align: center; margin: 20px 0;">
            <span style="font-size: 32px; font-weight: bold; letter-spacing: 4px; color: #00ffff;">{code}</span>
        </div>
        <p style="color: #888;">This code will expire in 15 minutes.</p>
        <p style="color: #888;">If you didn't request this, please ignore this email.</p>
    </div>
</body>
</html>
""",
        "ru": f"""
<html>
<body style="font-family: Arial, sans-serif; background-color: #0a0a0f; color: #ffffff; padding: 20px;">
    <div style="max-width: 500px; margin: 0 auto; background: linear-gradient(135deg, #1a1a2e 0%, #0f0f1a 100%); border-radius: 16px; padding: 30px; border: 1px solid rgba(0,255,255,0.2);">
        <h1 style="color: #00ffff; margin-bottom: 20px;">🏙️ TON City Builder</h1>
        <p>Вы запросили сброс пароля. Используйте код ниже:</p>
        <div style="background: rgba(0,255,255,0.1); border-radius: 8px; padding: 20px; text-align: center; margin: 20px 0;">
            <span style="font-size: 32px; font-weight: bold; letter-spacing: 4px; color: #00ffff;">{code}</span>
        </div>
        <p style="color: #888;">Код действителен 15 минут.</p>
        <p style="color: #888;">Если вы не запрашивали сброс пароля, проигнорируйте это письмо.</p>
    </div>
</body>
</html>
"""
    }
    
    subject = subjects.get(language, subjects["en"])
    body = bodies.get(language, bodies["en"])
    
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{from_name} <{from_email}>"
        msg["To"] = to_email
        
        html_part = MIMEText(body, "html")
        msg.attach(html_part)
        
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(from_email, to_email, msg.as_string())
        
        logger.info(f"Password reset email sent to {to_email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return False
