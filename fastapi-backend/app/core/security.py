from datetime import datetime, timedelta
from typing import Optional, Union, Any
from jose import jwt, JWTError
from passlib.context import CryptContext
import secrets
import string
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import hashlib
import uuid

from .config import settings

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Configuration
ALGORITHM = "HS256"


def create_access_token(
    subject: Union[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create JWT access token.
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode = {"exp": expire, "sub": str(subject), "type": "access"}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_verification_token(subject: Union[str, Any], purpose: str) -> str:
    """
    Create verification token for email verification, password reset, etc.
    """
    expire = datetime.utcnow() + timedelta(hours=24)  # 24 hours for verification
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": "verification",
        "purpose": purpose
    }
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str, expected_purpose: Optional[str] = None) -> Optional[str]:
    """
    Verify JWT token and return subject if valid.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        token_type: str = payload.get("type")
        purpose: str = payload.get("purpose")
        
        if user_id is None:
            return None
            
        # Check token type and purpose if specified
        if expected_purpose and purpose != expected_purpose:
            return None
            
        return user_id
    except JWTError:
        return None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify password against hash.
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash password.
    """
    return pwd_context.hash(password)


def generate_secure_token(length: int = 32) -> str:
    """
    Generate cryptographically secure random token.
    """
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def generate_short_id(length: int = 8) -> str:
    """
    Generate short ID using UUID and base64 encoding.
    """
    uid = str(uuid.uuid4())
    hash_object = hashlib.sha256(uid.encode())
    hash_hex = hash_object.hexdigest()
    # Convert to base64-like encoding
    import base64
    encoded = base64.b64encode(bytes.fromhex(hash_hex[:16])).decode('utf-8')
    return encoded[:length].replace('+', '').replace('/', '').replace('=', '')


def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Validate password strength.
    Returns (is_valid, error_message).
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"
    
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"
    
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one digit"
    
    if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        return False, "Password must contain at least one special character"
    
    return True, ""


def generate_username_from_email(email: str) -> str:
    """
    Generate a unique username from email.
    """
    base = email.split('@')[0].lower()
    # Remove non-alphanumeric characters
    base = ''.join(c for c in base if c.isalnum())
    
    # Ensure minimum length
    if len(base) < 3:
        base = base + 'user'
    
    # Add random suffix to ensure uniqueness
    suffix = generate_short_id(4)
    return f"{base}{suffix}"


def create_email_verification_link(token: str) -> str:
    """
    Create email verification link.
    """
    return f"{settings.FRONTEND_URL}/verify-email?token={token}"


def create_password_reset_link(token: str) -> str:
    """
    Create password reset link.
    """
    return f"{settings.FRONTEND_URL}/reset-password?token={token}"


class RateLimiter:
    """
    Simple in-memory rate limiter for authentication attempts.
    In production, this should use Redis.
    """
    
    def __init__(self):
        self.attempts = {}
    
    def is_rate_limited(self, identifier: str, limit: int, period: int) -> bool:
        """
        Check if identifier is rate limited.
        """
        now = datetime.utcnow()
        if identifier not in self.attempts:
            self.attempts[identifier] = []
        
        # Remove old attempts
        self.attempts[identifier] = [
            attempt for attempt in self.attempts[identifier]
            if (now - attempt).total_seconds() < period
        ]
        
        # Check if limit exceeded
        return len(self.attempts[identifier]) >= limit
    
    def record_attempt(self, identifier: str):
        """
        Record an attempt.
        """
        if identifier not in self.attempts:
            self.attempts[identifier] = []
        
        self.attempts[identifier].append(datetime.utcnow())
    
    def clear_attempts(self, identifier: str):
        """
        Clear attempts for identifier.
        """
        if identifier in self.attempts:
            del self.attempts[identifier]


# Global rate limiter instance
rate_limiter = RateLimiter() 