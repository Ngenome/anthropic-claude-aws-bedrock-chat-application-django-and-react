from django.utils.translation import gettext as _
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError, AuthenticationFailed
from drf_spectacular.utils import extend_schema, OpenApiResponse
from knox.models import AuthToken
from typing import Any
import logging
from .serializers import (
    RegisterSerializer,
    LoginSerializer,
    UserSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    PasswordChangeSerializer,
    EmailVerificationSerializer,
    ResendVerificationSerializer,
    GoogleAuthSerializer
)
from .services.auth_service import (
    AuthService,
    AuthenticationError,
    RegistrationError
)
from .services.rate_limit_service import RateLimitService
from .models import AppUser

from social_django.utils import load_strategy, load_backend
from social_core.backends.oauth import BaseOAuth2
from social_core.exceptions import MissingBackend, AuthTokenError
from knox.models import AuthToken
from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from social_core.backends.oauth import BaseOAuth2
from rest_framework import status
from rest_framework.response import Response
from knox.models import AuthToken
from rest_framework import status
from rest_framework.response import Response
from knox.models import AuthToken
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from knox.models import AuthToken
from .serializers import UserSerializer
import logging

logger = logging.getLogger(__name__)

class RegisterView(generics.CreateAPIView):
    """
    Register a new user account.
    
    Creates a new user account and sends a verification email.
    Rate limited to prevent abuse.
    """
    
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer
    
    def __init__(self, **kwargs: Any) -> None:
        """Initialize view with required services."""
        super().__init__(**kwargs)
        self.auth_service = AuthService()
        self.rate_limiter = RateLimitService()

    @extend_schema(
        responses={
            201: OpenApiResponse(
                description="User registered successfully",
                response=UserSerializer
            ),
            429: OpenApiResponse(
                description="Too many registration attempts"
            )
        }
    )
    def post(self, request, *args: Any, **kwargs: Any) -> Response:
        """Handle user registration."""
        try:
            # Get client IP
            ip_address = request.META.get('REMOTE_ADDR')
            
            # Check rate limit
            if ip_address and self.rate_limiter.is_rate_limited(
                ip_address,
                'registration'
            ):
                return Response(
                    {'detail': _("Too many registration attempts. Please try again later.")},
                    status=status.HTTP_429_TOO_MANY_REQUESTS
                )

            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            # Register user
            user = self.auth_service.register_user(
                ip_address=ip_address,
                **serializer.validated_data
            )

            token = AuthToken.objects.create(user)[1]

            # Return response
            return Response({
                'user': UserSerializer(user).data,
                'token': token
            }, status=status.HTTP_201_CREATED)

        except RegistrationError as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except ValidationError as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception    as e:
            logger.error(
                "Registration failed",
                extra={
                    'error': str(e),
                    'ip_address': ip_address
                },
                exc_info=True
            )
            return Response(
                {'detail': _("Registration failed. Please try again later.")},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
class LoginView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.auth_service = AuthService()
        self.rate_limiter = RateLimitService()

    def post(self, request, *args: Any, **kwargs: Any) -> Response:
        """Handle user login."""
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            # Get client IP
            ip_address = request.META.get('REMOTE_ADDR')

            try:
                # Attempt login
                user, requires_verification = self.auth_service.login_user(
                    email=serializer.validated_data['email'],
                    password=serializer.validated_data['password'],
                    ip_address=ip_address,
                    device_info=serializer.validated_data.get('device_info')
                )

                # Create auth token
                token = AuthToken.objects.create(user)[1]  # Get the token string from the tuple

                response_data = {
                    'user': UserSerializer(user).data,
                    'token': token,
                }

                if requires_verification:
                    response_data.update({
                        'requires_verification': True,
                        'message': str(_("Please verify your email to continue"))
                    })

                return Response(response_data)

            except AuthenticationFailed as e:
                return Response({
                    'error': 'authentication_failed',
                    'detail': str(e)
                }, status=status.HTTP_401_UNAUTHORIZED)

        except ValidationError as e:
            return Response({
                'error': 'validation_error',
                'detail': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(
                "Login failed",
                extra={
                    'error': str(e),
                    'ip_address': ip_address
                },
                exc_info=True
            )
            return Response({
                'error': 'server_error',
                'detail': str(_("An unexpected error occurred"))
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class EmailVerificationView(generics.GenericAPIView):
    """
    Verify user's email address.
    
    Verifies the email using the token sent to user's email.
    """
    
    permission_classes = [AllowAny]
    serializer_class = EmailVerificationSerializer

    def __init__(self, **kwargs: Any) -> None:
        """Initialize view with required services."""
        super().__init__(**kwargs)
        self.auth_service = AuthService()

    @extend_schema(
        responses={
            200: OpenApiResponse(description="Email verified successfully"),
            400: OpenApiResponse(description="Invalid verification token")
        }
    )
    def post(self, request, *args: Any, **kwargs: Any) -> Response:
        """Handle email verification."""
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            # Verify email
            if self.auth_service.verify_email(
                email=serializer.validated_data['email'],
                token=serializer.validated_data['token']
            ):
                return Response({'detail': _("Email verified successfully.")})
            
            return Response(
                {'detail': _("Invalid verification token.")},
                status=status.HTTP_400_BAD_REQUEST
            )

        except ValidationError as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(
                "Email verification failed",
                extra={'error': str(e)},
                exc_info=True
            )
            return Response(
                {'detail': _("Verification failed. Please try again later.")},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class ResendVerificationView(generics.GenericAPIView):
    """
    Resend email verification link.
    
    Sends a new verification email. Rate limited to prevent abuse.
    """
    
    permission_classes = [AllowAny]
    serializer_class = ResendVerificationSerializer

    def __init__(self, **kwargs: Any) -> None:
        """Initialize view with required services."""
        super().__init__(**kwargs)
        self.auth_service = AuthService()
        self.rate_limiter = RateLimitService()

    @extend_schema(
        responses={
            200: OpenApiResponse(description="Verification email sent"),
            429: OpenApiResponse(description="Too many requests")
        }
    )
    def post(self, request, *args: Any, **kwargs: Any) -> Response:
        """Handle resending verification email."""
        try:
            ip_address = request.META.get('REMOTE_ADDR')
            
            # Check rate limit
            if ip_address and self.rate_limiter.is_rate_limited(
                ip_address,
                'verification_email'
            ):
                return Response(
                    {'detail': _("Too many requests. Please try again later.")},
                    status=status.HTTP_429_TOO_MANY_REQUESTS
                )

            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            # Resend verification email
            self.auth_service.resend_verification_email(
                email=serializer.validated_data['email'],
                ip_address=ip_address
            )

            return Response({'detail': _("Verification email sent successfully.")})

        except ValidationError as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(
                "Failed to resend verification email",
                extra={
                    'error': str(e),
                    'ip_address': ip_address
                },
                exc_info=True
            )
            return Response(
                {'detail': _("Failed to send verification email. Please try again later.")},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class PasswordResetRequestView(generics.GenericAPIView):
    """
    Request password reset.
    
    Sends a password reset email. Rate limited to prevent abuse.
    """
    
    permission_classes = [AllowAny]
    serializer_class = PasswordResetRequestSerializer

    def __init__(self, **kwargs: Any) -> None:
        """Initialize view with required services."""
        super().__init__(**kwargs)
        self.auth_service = AuthService()
        self.rate_limiter = RateLimitService()

    @extend_schema(
        responses={
            200: OpenApiResponse(description="Password reset email sent"),
            429: OpenApiResponse(description="Too many requests")
        }
    )
    def post(self, request, *args: Any, **kwargs: Any) -> Response:
        """Handle password reset request."""
        try:
            ip_address = request.META.get('REMOTE_ADDR')
            
            # Check rate limit
            if ip_address and self.rate_limiter.is_rate_limited(
                ip_address,
                'password_reset'
            ):
                return Response(
                    {'detail': _("Too many requests. Please try again later.")},
                    status=status.HTTP_429_TOO_MANY_REQUESTS
                )

            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            # Initiate password reset
            self.auth_service.initiate_password_reset(
                email=serializer.validated_data['email'],
                ip_address=ip_address
            )

            return Response({
                'detail': _("If an account exists with this email, "
                          "a password reset link has been sent.")
            })

        except ValidationError as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(
                "Password reset request failed",
                extra={
                    'error': str(e),
                    'ip_address': ip_address
                },
                exc_info=True
            )
            return Response(
                {'detail': _("Failed to process request. Please try again later.")},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class PasswordResetConfirmView(generics.GenericAPIView):
    """
    Confirm password reset.
    
    Resets the user's password using the token from email.
    """
    
    permission_classes = [AllowAny]
    serializer_class = PasswordResetConfirmSerializer

    def __init__(self, **kwargs: Any) -> None:
        """Initialize view with required services."""
        super().__init__(**kwargs)
        self.auth_service = AuthService()

    @extend_schema(
        responses={
            200: OpenApiResponse(description="Password reset successful"),
            400: OpenApiResponse(description="Invalid reset token")
        }
    )
    def post(self, request, *args: Any, **kwargs: Any) -> Response:
        """Handle password reset confirmation."""
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            # Reset password
            if self.auth_service.reset_password(
                email=serializer.validated_data['email'],
                token=serializer.validated_data['token'],
                new_password=serializer.validated_data['new_password'],
                ip_address=request.META.get('REMOTE_ADDR')
            ):
                return Response({'detail': _("Password reset successful.")})

            return Response(
                {'detail': _("Invalid or expired reset token.")},
                status=status.HTTP_400_BAD_REQUEST
            )

        except ValidationError as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(
                "Password reset confirmation failed",
                exc_info=True
            )
            return Response(
                {'detail': _("Password reset failed. Please try again.")},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class PasswordChangeView(generics.GenericAPIView):
    """
    Change user password.
    
    Changes the password for an authenticated user.
    """
    
    permission_classes = [IsAuthenticated]
    serializer_class = PasswordChangeSerializer

    def __init__(self, **kwargs: Any) -> None:
        """Initialize view with required services."""
        super().__init__(**kwargs)
        self.auth_service = AuthService()

    @extend_schema(
        responses={
            200: OpenApiResponse(description="Password changed successfully"),
            400: OpenApiResponse(description="Invalid password")
        }
    )
    def post(self, request, *args: Any, **kwargs: Any) -> Response:
        """Handle password change."""
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            # Change password
            if self.auth_service.change_password(
                user=request.user,
                current_password=serializer.validated_data['current_password'],
                new_password=serializer.validated_data['new_password'],
                ip_address=request.META.get('REMOTE_ADDR')
            ):
                return Response({'detail': _("Password changed successfully.")})

            return Response(
                {'detail': _("Current password is incorrect.")},
                status=status.HTTP_400_BAD_REQUEST
            )

        except ValidationError as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(
                "Password change failed",
                extra={'user_id': str(request.user.id)},
                exc_info=True
            )
            return Response(
                {'detail': _("Password change failed. Please try again.")},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class LogoutView(APIView):
    """
    Log out user.
    
    Invalidates the current auth token.
    """
    
    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs: Any) -> None:
        """Initialize view with required services."""
        super().__init__(**kwargs)
        self.auth_service = AuthService()

    @extend_schema(
        responses={
            200: OpenApiResponse(description="Logged out successfully")
        }
    )
    def post(self, request, *args: Any, **kwargs: Any) -> Response:
        """Handle user logout."""
        try:
            # Log out user
            self.auth_service.logout_user(
                user=request.user,
                all_sessions=request.data.get('all_sessions', False),
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
            return Response({'detail': _("Logged out successfully.")})

        except Exception as e:
            logger.error(
                "Logout failed",
                extra={'user_id': str(request.user.id)},
                exc_info=True
            )
            return Response(
                {'detail': _("Logout failed. Please try again.")},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
from django.views.decorators.csrf import csrf_exempt

import requests

@method_decorator(csrf_exempt, name='dispatch')
class GoogleAuthView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        try:
            access_token = request.data.get('access_token')
            if not access_token:
                return Response(
                    {'error': 'Access token is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Verify token with Google
            google_response = requests.get(
                'https://www.googleapis.com/oauth2/v3/userinfo',
                headers={'Authorization': f'Bearer {access_token}'}
            )
            google_response.raise_for_status()
            user_data = google_response.json()

            # Get or create user
            from django.contrib.auth import get_user_model
            User = get_user_model()
            
            try:
                user = User.objects.get(email=user_data['email'])
            except User.DoesNotExist:
                # Create new user
                user = User.objects.create_user(
                    email=user_data['email'],
                    first_name=user_data.get('given_name', ''),
                    last_name=user_data.get('family_name', ''),
                    password=None  # Password not needed for OAuth
                )
                user.email_verified = True  # Google has verified the email
                user.save()
            
            # Create auth token
            from knox.models import AuthToken
            _, token = AuthToken.objects.create(user)
            
            return Response({
                'user': {
                    'id': str(user.id),
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'email_verified': user.email_verified,
                },
                'token': token
            })

        except requests.exceptions.RequestException as e:
            logger.error(f"Google API error: {str(e)}")
            return Response(
                {'error': 'Failed to verify Google token'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        except Exception as e:
            logger.error(f"Google auth error: {str(e)}")
            return Response(
                {'error': 'Authentication failed'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    Get or update user profile.
    
    Allows authenticated users to view and update their profile information.
    """
    
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def get_object(self) -> AppUser:
        """Get the user profile."""
        return self.request.user

    @extend_schema(
        responses={
            200: UserSerializer,
            400: OpenApiResponse(description="Invalid data")
        }
    )
    def patch(self, request, *args: Any, **kwargs: Any) -> Response:
        """Handle partial profile update."""
        try:
            return super().patch(request, *args, **kwargs)
        except Exception as e:
            logger.error(
                "Profile update failed",
                extra={
                    'user_id': str(request.user.id),
                    'error': str(e)
                },
                exc_info=True
            )
            return Response(
                {'detail': _("Profile update failed. Please try again.")},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )