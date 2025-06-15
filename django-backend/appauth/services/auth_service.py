import logging
from typing import Optional, Dict, Any, Tuple
from django.contrib.auth import authenticate
from django.utils import timezone
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
from django.db import transaction
from rest_framework.exceptions import AuthenticationFailed

from ..models import AppUser
from .email_service import EmailService, EmailError
from .rate_limit_service import RateLimitService
from .google_auth_service import GoogleAuthService, GoogleAuthError

logger = logging.getLogger(__name__)

class AuthenticationError(Exception):
    """Base exception for authentication errors."""
    pass

class RegistrationError(AuthenticationError):
    """Exception for registration-related errors."""
    pass

class AuthService:
    """Service for handling authentication operations."""

    def __init__(self):
        """Initialize auth service with required dependencies."""
        self.email_service = EmailService()
        self.rate_limiter = RateLimitService()
        self.google_auth_service = GoogleAuthService()

    @transaction.atomic
    def register_user(
        self,
        email: str,
        password: str,
        ip_address: Optional[str] = None,
        **extra_fields
    ) -> AppUser:
        """
        Register a new user with email and password.
        
        Args:
            email: User's email address
            password: User's password
            ip_address: Optional IP address for rate limiting
            **extra_fields: Additional fields for user creation
            
        Returns:
            AppUser: Created user instance
            
        Raises:
            RegistrationError: If registration fails
            ValidationError: If data validation fails
        """
        try:
            # Check rate limit
            if ip_address and self.rate_limiter.is_rate_limited(
                ip_address,
                'registration',
                max_attempts=5,
                period=3600  # 1 hour
            ):
                raise RegistrationError(
                    _("Too many registration attempts. Please try again later.")
                )

            # Validate email
            if not email or '@' not in email:
                raise ValidationError(_("Invalid email address"))

            # Validate password
            if not password or len(password) < 8:
                raise ValidationError(_("Password must be at least 8 characters long"))

            # Normalize email
            email = email.lower().strip()

            with transaction.atomic():
                # Create user
                user = AppUser.objects.create_user(
                    email=email,
                    password=password,
                    **extra_fields
                )

                # Send verification email
                try:
                    self.email_service.send_verification_email(user)
                except EmailError as e:
                    logger.error(
                        f"Failed to send verification email: {str(e)}",
                        extra={'user_id': str(user.id)},
                        exc_info=True
                    )
                    # Don't raise - user is still created but unverified

                # Record successful registration
                if ip_address:
                    self.rate_limiter.record_attempt(ip_address, 'registration')

                logger.info(
                    f"User registered successfully: {email}",
                    extra={
                        'user_id': str(user.id),
                        'ip_address': ip_address
                    }
                )

                return user

        except ValidationError:
            raise
        except Exception as e:
            logger.error(
                f"Registration failed for {email}: {str(e)}",
                extra={'ip_address': ip_address},
                exc_info=True
            )
            raise RegistrationError(_("Registration failed. Please try again."))

    def login_user(
    self,
    email: str,
    password: str,
    ip_address: Optional[str] = None,
    device_info: Optional[str] = None
) -> Tuple[AppUser, bool]:
        """Authenticate a user with email and password."""
        try:
            # Check rate limit first
            if ip_address and self.rate_limiter.is_rate_limited(
                ip_address,
                'login',
                max_attempts=5,
                period=300
            ):
                raise AuthenticationFailed(
                    _("Too many login attempts. Please try again later.")
                )

            # Normalize email
            email = email.lower().strip()

            try:
                user = AppUser.objects.get(email=email)
            except AppUser.DoesNotExist:
                if ip_address:
                    self.rate_limiter.record_attempt(ip_address, 'login')
                raise AuthenticationFailed(_("Invalid email or password"))

            # Check if account is locked
            if user.is_locked():
                raise AuthenticationFailed(
                    _("Account is temporarily locked. Please try again later.")
                )

            # Authenticate
            authenticated_user = authenticate(email=email, password=password)
            if not authenticated_user:
                # Record failed attempt
                user.record_login_attempt(False, ip_address)
                if ip_address:
                    self.rate_limiter.record_attempt(ip_address, 'login')
                raise AuthenticationFailed(_("Invalid email or password"))

            # Record successful login
            user.record_login_attempt(True, ip_address)

            # Return tuple of (user, requires_verification)
            return user, not user.email_verified

        except AuthenticationFailed:
            raise
        except Exception as e:
            logger.error(
                f"Login failed for {email}",
                extra={'ip_address': ip_address},
                exc_info=True
            )
            raise AuthenticationFailed(_("Authentication failed"))
    
    def _is_suspicious_login(
        self,
        user: AppUser,
        ip_address: Optional[str],
        device_info: Optional[str]
    ) -> bool:
        """
        Check if login attempt is suspicious.
        
        Args:
            user: AppUser instance
            ip_address: IP address of login attempt
            device_info: Device/browser information
            
        Returns:
            bool: True if login appears suspicious
        """
        if not ip_address:
            return False

        # Check if this is first login from this IP
        if user.last_login_ip and user.last_login_ip != ip_address:
            # If location drastically different, might be suspicious
            if not self._is_ip_in_same_region(user.last_login_ip, ip_address):
                return True

        # Check login time pattern
        current_time = timezone.now().hour
        if not self._is_normal_login_time(current_time):
            return True

        # Additional checks could be added:
        # - Multiple failed attempts before success
        # - Multiple logins from different locations in short time
        # - Unusual device/browser combination
        # - Known malicious IP addresses
        
        return False

    def _is_ip_in_same_region(self, ip1: str, ip2: str) -> bool:
        """
        Check if two IPs are from the same geographic region.
        This is a placeholder - in production, use a proper IP geolocation service.
        
        Args:
            ip1: First IP address
            ip2: Second IP address
            
        Returns:
            bool: True if IPs are in same region
        """
        # Implement IP geolocation logic here
        # For now, just check first two octets as example
        return ip1.split('.')[:2] == ip2.split('.')[:2]

    def _is_normal_login_time(self, hour: int) -> bool:
        """
        Check if login time is within normal hours.
        
        Args:
            hour: Hour of day (0-23)
            
        Returns:
            bool: True if login time is normal
        """
        # Consider 1am-5am suspicious
        return not (1 <= hour <= 5)

    def logout_user(
        self,
        user: AppUser,
        all_sessions: bool = False,
        ip_address: Optional[str] = None
    ) -> bool:
        """
        Log out a user.
        
        Args:
            user: AppUser instance
            all_sessions: Whether to log out all sessions
            ip_address: Optional IP address
            
        Returns:
            bool: True if logout successful
        """
        try:
            # Handle token invalidation if using token auth
            if all_sessions:
                # Delete all auth tokens for user
                from knox.models import AuthToken
                AuthToken.objects.filter(user=user).delete()
            
            logger.info(
                f"User logged out successfully{' (all sessions)' if all_sessions else ''}",
                extra={
                    'user_id': str(user.id),
                    'ip_address': ip_address
                }
            )
            
            return True

        except Exception as e:
            logger.error(
                "Logout failed",
                extra={
                    'user_id': str(user.id),
                    'ip_address': ip_address,
                    'error': str(e)
                },
                exc_info=True
            )
            return False

    def resend_verification_email(
        self,
        email: str,
        ip_address: Optional[str] = None
    ) -> bool:
        """
        Resend verification email.
        
        Args:
            email: User's email
            ip_address: Optional IP address for rate limiting
            
        Returns:
            bool: True if email sent successfully
            
        Raises:
            ValidationError: If process fails
        """
        try:
            # Check rate limit
            if ip_address and self.rate_limiter.is_rate_limited(
                ip_address,
                'verification_email',
                max_attempts=3,
                period=3600  # 1 hour
            ):
                raise ValidationError(
                    _("Too many verification email requests. Please try again later.")
                )

            email = email.lower().strip()
            user = AppUser.objects.get(email=email)
            
            if user.email_verified:
                raise ValidationError(_("Email is already verified"))

            # Send verification email
            self.email_service.send_verification_email(user)
            
            if ip_address:
                self.rate_limiter.record_attempt(ip_address, 'verification_email')

            logger.info(
                f"Verification email resent to {email}",
                extra={
                    'user_id': str(user.id),
                    'ip_address': ip_address
                }
            )
            
            return True

        except AppUser.DoesNotExist:
            raise ValidationError(_("User not found"))
        except ValidationError:
            raise
        except Exception as e:
            logger.error(
                f"Failed to resend verification email: {str(e)}",
                extra={'ip_address': ip_address},
                exc_info=True
            )
            raise ValidationError(_("Failed to resend verification email"))

        except AuthenticationFailed:
            raise
        except Exception as e:
            logger.error(
                f"Login failed for {email}: {str(e)}",
                extra={'ip_address': ip_address},
                exc_info=True
            )
            raise AuthenticationFailed(_("Authentication failed"))

    def verify_email(self, email: str, token: str) -> bool:
        """
        Verify a user's email address.
        
        Args:
            email: User's email
            token: Verification token
            
        Returns:
            bool: True if verification successful
            
        Raises:
            ValidationError: If verification fails
        """
        try:
            email = email.lower().strip()
            user = AppUser.objects.get(email=email)
            
            if user.email_verified:
                return True

            if user.verify_token(token, 'email_verification'):
                user.email_verified = True
                user.clear_token('email_verification')
                user.save()
                
                logger.info(
                    f"Email verified successfully: {email}",
                    extra={'user_id': str(user.id)}
                )
                return True
            
            raise ValidationError(_("Invalid or expired verification token"))

        except AppUser.DoesNotExist:
            raise ValidationError(_("User not found"))
        except Exception as e:
            logger.error(
                f"Email verification failed for {email}: {str(e)}",
                exc_info=True
            )
            raise ValidationError(_("Email verification failed"))

    def initiate_password_reset(
        self,
        email: str,
        ip_address: Optional[str] = None
    ) -> bool:
        """
        Start password reset process.
        
        Args:
            email: User's email
            ip_address: Optional IP address for rate limiting
            
        Returns:
            bool: True if reset email sent successfully
            
        Raises:
            ValidationError: If process fails
        """
        try:
            # Check rate limit
            if ip_address and self.rate_limiter.is_rate_limited(
                ip_address,
                'password_reset',
                max_attempts=3,
                period=3600  # 1 hour
            ):
                raise ValidationError(
                    _("Too many password reset attempts. Please try again later.")
                )

            email = email.lower().strip()
            user = AppUser.objects.get(email=email)
            
            # Send password reset email
            self.email_service.send_password_reset_email(user)
            
            if ip_address:
                self.rate_limiter.record_attempt(ip_address, 'password_reset')

            logger.info(
                f"Password reset initiated for {email}",
                extra={
                    'user_id': str(user.id),
                    'ip_address': ip_address
                }
            )
            
            return True

        except AppUser.DoesNotExist:
            # Don't reveal user existence, but log the attempt
            logger.info(
                f"Password reset attempted for non-existent user: {email}",
                extra={'ip_address': ip_address}
            )
            return True
        except Exception as e:
            logger.error(
                f"Password reset initiation failed for {email}: {str(e)}",
                extra={'ip_address': ip_address},
                exc_info=True
            )
            raise ValidationError(_("Failed to initiate password reset"))

    def reset_password(
        self,
        email: str,
        token: str,
        new_password: str,
        ip_address: Optional[str] = None
    ) -> bool:
        """
        Complete password reset process.
        
        Args:
            email: User's email
            token: Reset token
            new_password: New password
            ip_address: Optional IP address
            
        Returns:
            bool: True if password reset successful
            
        Raises:
            ValidationError: If reset fails
        """
        try:
            email = email.lower().strip()
            user = AppUser.objects.get(email=email)

            if not user.verify_token(token, 'password_reset'):
                raise ValidationError(_("Invalid or expired reset token"))

            # Validate new password
            if len(new_password) < 8:
                raise ValidationError(_("Password must be at least 8 characters long"))

            # Update password
            user.set_password(new_password)
            user.clear_token('password_reset')
            user.save()

            # Send confirmation email
            try:
                self.email_service.send_password_change_notification(user)
            except EmailError:
                logger.warning(
                    "Failed to send password change notification",
                    extra={
                        'user_id': str(user.id),
                        'ip_address': ip_address
                    }
                )

            logger.info(
                f"Password reset successful for {email}",
                extra={
                    'user_id': str(user.id),
                    'ip_address': ip_address
                }
            )
            
            return True

        except AppUser.DoesNotExist:
            raise ValidationError(_("Invalid reset request"))
        except ValidationError:
            raise
        except Exception as e:
            logger.error(
                f"Password reset failed for {email}: {str(e)}",
                extra={'ip_address': ip_address},
                exc_info=True
            )
            raise ValidationError(_("Failed to reset password"))

    def change_password(
        self,
        user: AppUser,
        current_password: str,
        new_password: str,
        ip_address: Optional[str] = None
    ) -> bool:
        """
        Change user's password.
        
        Args:
            user: AppUser instance
            current_password: Current password
            new_password: New password
            ip_address: Optional IP address
            
        Returns:
            bool: True if password changed successfully
            
        Raises:
            ValidationError: If password change fails
        """
        try:
            # Verify current password
            if not user.check_password(current_password):
                raise ValidationError(_("Current password is incorrect"))

            # Validate new password
            if len(new_password) < 8:
                raise ValidationError(_("Password must be at least 8 characters long"))

            if current_password == new_password:
                raise ValidationError(_("New password must be different from current password"))

            # Update password
            user.set_password(new_password)
            user.save()

            # Send notification
            try:
                self.email_service.send_password_change_notification(user)
            except EmailError:
                logger.warning(
                    "Failed to send password change notification",
                    extra={
                        'user_id': str(user.id),
                        'ip_address': ip_address
                    }
                )

            logger.info(
                "Password changed successfully",
                extra={
                    'user_id': str(user.id),
                    'ip_address': ip_address
                }
            )
            
            return True

        except ValidationError:
            raise
        except Exception as e:
            logger.error(
                "Password change failed",
                extra={
                    'user_id': str(user.id),
                    'ip_address': ip_address,
                    'error': str(e)
                },
                exc_info=True
            )
            raise ValidationError(_("Failed to change password"))

    def authenticate_google(
        self,
        access_token: str,
        id_token: Optional[str] = None,
        device_info: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None
    ) -> Tuple[AppUser, bool]:
        """
        Authenticate or create user using Google OAuth.
        
        Args:
            access_token: Google OAuth access token
            id_token: Optional ID token from Google
            device_info: Optional device information
            ip_address: Optional IP address
            
        Returns:
            Tuple of (user, created) where created indicates new user
            
        Raises:
            AuthenticationError: If authentication fails
        """
        try:
            # Check rate limit for social auth attempts
            if ip_address and self.rate_limiter.is_rate_limited(
                ip_address,
                'social_auth',
                max_attempts=10,
                period=300  # 5 minutes
            ):
                raise AuthenticationError(
                    _("Too many authentication attempts. Please try again later.")
                )

            # Authenticate with Google
            user, created = self.google_auth_service.authenticate_google(
                access_token=access_token,
                ip_address=ip_address
            )

            # Record successful authentication
            if ip_address:
                user.record_login_attempt(True, ip_address)

            # Check for suspicious activity
            if self._is_suspicious_login(user, ip_address, device_info):
                try:
                    self.email_service.send_suspicious_login_notification(
                        user,
                        ip_address,
                        device_info=device_info
                    )
                except EmailError:
                    # Log but don't prevent login
                    logger.warning(
                        "Failed to send suspicious login notification",
                        extra={
                            'user_id': str(user.id),
                            'ip_address': ip_address
                        }
                    )

            logger.info(
                f"{'New' if created else 'Existing'} user authenticated via Google",
                extra={
                    'user_id': str(user.id),
                    'ip_address': ip_address,
                    'created': created
                }
            )

            return user, created

        except GoogleAuthError as e:
            if ip_address:
                self.rate_limiter.record_attempt(ip_address, 'social_auth')
            raise AuthenticationError(str(e))
        except Exception as e:
            logger.error(
                "Google authentication failed",
                extra={
                    'error': str(e),
                    'ip_address': ip_address
                },
                exc_info=True
            )
            raise AuthenticationError(
                _("Authentication failed. Please try again later.")
            )

    def _is_suspicious_login(
        self,
        user: AppUser,
        ip_address: Optional[str],
        device_info: Optional[str]
    ) -> bool:
        """
        Check if login attempt is suspicious.
        """
        if not ip_address:
            return False

        # Check if this is first login from this IP
        if user.last_login_ip and user.last_login_ip != ip_address:
            # If location drastically different, might be suspicious
            if not self._is_ip_in_same_region(user.last_login_ip, ip_address):
                return True

        # Check login time pattern
        current_time = timezone.now().hour
        if not self._is_normal_login_time(current_time):
            return True

        # Additional checks could be added:
        # - Multiple failed attempts before success
        # - Multiple logins from different locations in short time
        # - Unusual device/browser combination
        # - Known malicious IP addresses
        
        return False

    def _is_ip_in_same_region(self, ip1: str, ip2: str) -> bool:
        """
        Check if two IPs are from the same geographic region.
        This is a placeholder - in production, use a proper IP geolocation service.
        """
        # Implement IP geolocation logic here
        # For now, just check first two octets as example
        return ip1.split('.')[:2] == ip2.split('.')[:2]

    def _is_normal_login_time(self, hour: int) -> bool:
        """
        Check if login time is within normal hours.
        """
        # Consider 1am-5am suspicious
        return not (1 <= hour <= 5)

    def logout_user(
        self,
        user: AppUser,
        all_sessions: bool = False,
        ip_address: Optional[str] = None
    ) -> bool:
        """
        Log out a user.
        """
        try:
            # Handle token invalidation if using token auth
            if all_sessions:
                # Delete all auth tokens for user
                from knox.models import AuthToken
                AuthToken.objects.filter(user=user).delete()
            
            logger.info(
                f"User logged out successfully{' (all sessions)' if all_sessions else ''}",
                extra={
                    'user_id': str(user.id),
                    'ip_address': ip_address
                }
            )
            
            return True

        except Exception as e:
            logger.error(
                "Logout failed",
                extra={
                    'user_id': str(user.id),
                    'ip_address': ip_address,
                    'error': str(e)
                },
                exc_info=True
            )
            return False

    def resend_verification_email(
        self,
        email: str,
        ip_address: Optional[str] = None
    ) -> bool:
        """
        Resend verification email.
        """
        try:
            # Check rate limit
            if ip_address and self.rate_limiter.is_rate_limited(
                ip_address,
                'verification_email',
                max_attempts=3,
                period=3600  # 1 hour
            ):
                raise ValidationError(
                    _("Too many verification email requests. Please try again later.")
                )

            email = email.lower().strip()
            user = AppUser.objects.get(email=email)
            
            if user.email_verified:
                raise ValidationError(_("Email is already verified"))

            # Send verification email
            self.email_service.send_verification_email(user)
            
            if ip_address:
                self.rate_limiter.record_attempt(ip_address, 'verification_email')

            logger.info(
                f"Verification email resent to {email}",
                extra={
                    'user_id': str(user.id),
                    'ip_address': ip_address
                }
            )
            
            return True

        except AppUser.DoesNotExist:
            raise ValidationError(_("User not found"))
        except ValidationError:
            raise
        except Exception as e:
            logger.error(
                f"Failed to resend verification email: {str(e)}",
                extra={'ip_address': ip_address},
                exc_info=True
            )
            raise ValidationError(_("Failed to resend verification email"))