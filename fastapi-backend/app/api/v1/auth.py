from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta
import logging

from app.api.deps import get_db, get_current_user, get_client_ip
from app.core.security import (
    verify_password, 
    get_password_hash, 
    create_access_token, 
    create_verification_token,
    verify_token,
    generate_username_from_email,
    rate_limiter
)
from app.core.config import settings
from app.models.user import User
from app.schemas.user import (
    UserCreate, 
    UserLogin, 
    LoginResponse, 
    User as UserSchema,
    PasswordResetRequest,
    PasswordResetConfirm,
    EmailVerificationRequest,
    EmailVerificationConfirm,
    MessageResponse,
    GoogleAuthRequest,
    PasswordChange
)
from app.services.email_service import EmailService
from app.services.google_auth_service import GoogleAuthService

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize services
email_service = EmailService()
google_auth_service = GoogleAuthService()


@router.post("/register", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new user.
    """
    client_ip = get_client_ip(request)
    
    # Rate limiting
    if rate_limiter.is_rate_limited(
        f"register_{client_ip}", 
        settings.REGISTRATION_RATE_LIMIT, 
        settings.RATE_LIMIT_PERIOD
    ):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many registration attempts. Please try again later."
        )
    
    try:
        # Check if user already exists
        result = await db.execute(
            select(User).where(User.email == user_data.email)
        )
        if result.scalar_one_or_none():
            rate_limiter.record_attempt(f"register_{client_ip}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this email already exists"
            )
        
        # Generate username if not provided
        username = user_data.username or generate_username_from_email(user_data.email)
        
        # Ensure username is unique
        result = await db.execute(
            select(User).where(User.username == username)
        )
        if result.scalar_one_or_none():
            username = generate_username_from_email(user_data.email)
        
        # Create user
        hashed_password = get_password_hash(user_data.password)
        verification_token = create_verification_token(user_data.email, "email_verification")
        
        db_user = User(
            email=user_data.email,
            username=username,
            hashed_password=hashed_password,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            email_verification_token=verification_token,
            email_verification_sent_at=datetime.utcnow()
        )
        
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        
        # Send verification email
        await email_service.send_verification_email(
            email=user_data.email,
            first_name=user_data.first_name or username,
            token=verification_token
        )
        
        logger.info(f"User registered: {user_data.email}")
        return MessageResponse(
            message="Registration successful. Please check your email to verify your account."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed. Please try again."
        )


@router.post("/login", response_model=LoginResponse)
async def login(
    user_credentials: UserLogin,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Login user and return access token.
    """
    client_ip = get_client_ip(request)
    
    # Rate limiting
    if rate_limiter.is_rate_limited(
        f"login_{client_ip}", 
        settings.LOGIN_RATE_LIMIT, 
        settings.RATE_LIMIT_PERIOD
    ):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again later."
        )
    
    try:
        # Get user
        result = await db.execute(
            select(User).where(User.email == user_credentials.email)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            rate_limiter.record_attempt(f"login_{client_ip}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Check if account is locked
        if user.is_locked:
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail="Account is temporarily locked due to too many failed login attempts"
            )
        
        # Verify password
        if not verify_password(user_credentials.password, user.hashed_password):
            # Increment login attempts
            user.increment_login_attempts()
            
            # Lock account if too many attempts
            if user.login_attempts >= settings.ACCOUNT_LOCKOUT_ATTEMPTS:
                user.locked_until = datetime.utcnow() + timedelta(
                    seconds=settings.ACCOUNT_LOCKOUT_DURATION
                )
                await db.commit()
                raise HTTPException(
                    status_code=status.HTTP_423_LOCKED,
                    detail="Account locked due to too many failed login attempts"
                )
            
            await db.commit()
            rate_limiter.record_attempt(f"login_{client_ip}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Check if user is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is deactivated"
            )
        
        # Clear login attempts and update last login
        user.clear_login_attempts()
        user.last_login = datetime.utcnow()
        user.last_login_ip = client_ip
        await db.commit()
        await db.refresh(user)  # Refresh to ensure all attributes are loaded
        
        # Create access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        if user_credentials.remember_me:
            access_token_expires = timedelta(days=30)  # 30 days for remember me
        
        access_token = create_access_token(
            subject=str(user.id),
            expires_delta=access_token_expires
        )
        
        # Clear rate limiting for successful login
        rate_limiter.clear_attempts(f"login_{client_ip}")
        
        logger.info(f"User logged in: {user.email}")
        
        # Create user dict to avoid greenlet issues
        user_dict = {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "avatar_url": user.avatar_url,
            "email_verified": user.email_verified,
            "is_active": user.is_active,
            "created_at": user.created_at,
            "updated_at": user.updated_at,
            "last_login": user.last_login,
            "full_name": user.full_name
        }
        
        return LoginResponse(
            access_token=access_token,
            user=UserSchema.model_validate(user_dict)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed. Please try again."
        )


@router.post("/verify-email", response_model=MessageResponse)
async def verify_email(
    verification_data: EmailVerificationConfirm,
    db: AsyncSession = Depends(get_db)
):
    """
    Verify user email with token.
    """
    try:
        # Verify token
        email = verify_token(verification_data.token, "email_verification")
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired verification token"
            )
        
        # Get user
        result = await db.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        if user.email_verified:
            return MessageResponse(message="Email already verified")
        
        # Verify email
        user.email_verified = True
        user.email_verification_token = None
        user.email_verification_sent_at = None
        await db.commit()
        
        logger.info(f"Email verified: {user.email}")
        return MessageResponse(message="Email verified successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Email verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Email verification failed. Please try again."
        )


@router.post("/resend-verification", response_model=MessageResponse)
async def resend_verification(
    request_data: EmailVerificationRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Resend email verification link.
    """
    client_ip = get_client_ip(request)
    
    # Rate limiting
    if rate_limiter.is_rate_limited(
        f"verification_{client_ip}", 
        3,  # 3 attempts per hour
        settings.RATE_LIMIT_PERIOD
    ):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many verification requests. Please try again later."
        )
    
    try:
        # Get user
        result = await db.execute(
            select(User).where(User.email == request_data.email)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            # Don't reveal if email exists
            return MessageResponse(
                message="If the email exists, a verification link has been sent."
            )
        
        if user.email_verified:
            return MessageResponse(message="Email is already verified")
        
        # Generate new token
        verification_token = create_verification_token(user.email, "email_verification")
        user.email_verification_token = verification_token
        user.email_verification_sent_at = datetime.utcnow()
        await db.commit()
        
        # Send verification email
        await email_service.send_verification_email(
            email=user.email,
            first_name=user.first_name or user.username,
            token=verification_token
        )
        
        rate_limiter.record_attempt(f"verification_{client_ip}")
        logger.info(f"Verification email resent: {user.email}")
        return MessageResponse(
            message="If the email exists, a verification link has been sent."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Resend verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send verification email. Please try again."
        )


@router.post("/password-reset", response_model=MessageResponse)
async def request_password_reset(
    request_data: PasswordResetRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Request password reset link.
    """
    client_ip = get_client_ip(request)
    
    # Rate limiting
    if rate_limiter.is_rate_limited(
        f"password_reset_{client_ip}", 
        settings.PASSWORD_RESET_RATE_LIMIT, 
        settings.RATE_LIMIT_PERIOD
    ):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many password reset requests. Please try again later."
        )
    
    try:
        # Get user
        result = await db.execute(
            select(User).where(User.email == request_data.email)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            # Don't reveal if email exists
            return MessageResponse(
                message="If the email exists, a password reset link has been sent."
            )
        
        # Generate reset token
        reset_token = create_verification_token(user.email, "password_reset")
        user.password_reset_token = reset_token
        user.password_reset_sent_at = datetime.utcnow()
        await db.commit()
        
        # Send password reset email
        await email_service.send_password_reset_email(
            email=user.email,
            first_name=user.first_name or user.username,
            token=reset_token
        )
        
        rate_limiter.record_attempt(f"password_reset_{client_ip}")
        logger.info(f"Password reset requested: {user.email}")
        return MessageResponse(
            message="If the email exists, a password reset link has been sent."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password reset request error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send password reset email. Please try again."
        )


@router.post("/password-reset/confirm", response_model=MessageResponse)
async def confirm_password_reset(
    reset_data: PasswordResetConfirm,
    db: AsyncSession = Depends(get_db)
):
    """
    Confirm password reset with token and new password.
    """
    try:
        # Verify token
        email = verify_token(reset_data.token, "password_reset")
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token"
            )
        
        # Get user
        result = await db.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Update password
        user.hashed_password = get_password_hash(reset_data.new_password)
        user.password_reset_token = None
        user.password_reset_sent_at = None
        user.clear_login_attempts()  # Clear any login attempts
        await db.commit()
        
        # Send password change notification
        await email_service.send_password_change_notification(
            email=user.email,
            first_name=user.first_name or user.username
        )
        
        logger.info(f"Password reset completed: {user.email}")
        return MessageResponse(message="Password reset successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password reset confirmation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset failed. Please try again."
        )


@router.post("/password-change", response_model=MessageResponse)
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Change password for authenticated user.
    """
    try:
        # Verify current password
        if not verify_password(password_data.current_password, current_user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Update password
        current_user.hashed_password = get_password_hash(password_data.new_password)
        await db.commit()
        
        # Send password change notification
        await email_service.send_password_change_notification(
            email=current_user.email,
            first_name=current_user.first_name or current_user.username
        )
        
        logger.info(f"Password changed: {current_user.email}")
        return MessageResponse(message="Password changed successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password change error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password change failed. Please try again."
        )


@router.post("/google", response_model=LoginResponse)
async def google_auth(
    auth_data: GoogleAuthRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Authenticate with Google OAuth.
    """
    try:
        # Verify Google token and get user info
        user_info = await google_auth_service.verify_token(auth_data.access_token)
        
        if not user_info:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid Google access token"
            )
        
        # Check if user exists
        result = await db.execute(
            select(User).where(User.email == user_info["email"])
        )
        user = result.scalar_one_or_none()
        
        if not user:
            # Create new user
            username = generate_username_from_email(user_info["email"])
            user = User(
                email=user_info["email"],
                username=username,
                first_name=user_info.get("given_name"),
                last_name=user_info.get("family_name"),
                avatar_url=user_info.get("picture"),
                email_verified=True,  # Google emails are pre-verified
                hashed_password=get_password_hash(""),  # No password for OAuth users
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
            logger.info(f"New Google user created: {user.email}")
        else:
            # Update last login
            user.last_login = datetime.utcnow()
            user.last_login_ip = get_client_ip(request)
            await db.commit()
        
        # Create access token
        access_token = create_access_token(subject=str(user.id))
        
        logger.info(f"Google auth successful: {user.email}")
        return LoginResponse(
            access_token=access_token,
            user=UserSchema.model_validate(user)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Google auth error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google authentication failed. Please try again."
        ) 