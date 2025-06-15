import logging
from typing import Tuple, Optional, Dict, Any
from django.conf import settings
from social_core.backends.google import GoogleOAuth2
from social_django.utils import load_strategy, load_backend
from django.contrib.auth import get_user_model
from ..models import AppUser
from .email_service import EmailService

logger = logging.getLogger(__name__)

class GoogleAuthError(Exception):
    """Base exception for Google authentication errors."""
    pass

class GoogleAuthService:
    """Service for handling Google OAuth authentication."""

    def __init__(self):
        self.email_service = EmailService()
        self.User = get_user_model()

    def get_or_create_user(
        self,
        user_data: Dict[str, Any],
        ip_address: Optional[str] = None
    ) -> Tuple[AppUser, bool]:
        """Get existing user or create new one from Google data."""
        try:
            email = user_data.get('email')
            if not email:
                raise GoogleAuthError("Email not provided by Google")

            # Normalize email
            email = email.lower().strip()

            try:
                # Try to get existing user
                user = self.User.objects.get(email=email)
                created = False
                
                logger.info(
                    f"Existing user logged in via Google: {email}",
                    extra={'ip_address': ip_address}
                )
                
            except self.User.DoesNotExist:
                # Create new user without explicitly setting username
                # Let the model's create_user method handle username generation
                user = self.User.objects.create_user(
                    email=email,
                    first_name=user_data.get('given_name', ''),
                    last_name=user_data.get('family_name', ''),
                    password=None  # Password not needed for OAuth
                )
                
                # Set additional fields
                user.email_verified = True  # Google has verified the email
                if 'picture' in user_data:
                    user.avatar = user_data['picture']
                
                user.save()
                created = True
                
                logger.info(
                    f"New user created via Google: {email}",
                    extra={'ip_address': ip_address}
                )

            return user, created

        except Exception as e:
            logger.error(
                "Failed to process Google user data",
                extra={
                    'error': str(e),
                    'email': user_data.get('email'),
                    'ip_address': ip_address
                },
                exc_info=True
            )
            raise GoogleAuthError(
                "Failed to process Google authentication. Please try again."
            )
