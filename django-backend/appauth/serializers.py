from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
from .models import AppUser
import re

class UserSerializer(serializers.ModelSerializer):
    """Serializer for user profile data."""
    
    class Meta:
        model = AppUser
        fields = [
            'id', 'email', 'first_name', 'last_name',
            'avatar', 'email_verified', 'date_joined',
            'last_login'
        ]
        read_only_fields = [
            'id', 'email', 'email_verified',
            'date_joined', 'last_login'
        ]

class RegisterSerializer(serializers.Serializer):
    """Serializer for user registration."""
    
    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    first_name = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=30
    )
    last_name = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=150
    )

    def validate_email(self, value):
        """Validate email address."""
        normalized_email = value.lower()
        
        # Check if email already exists
        if AppUser.objects.filter(email=normalized_email).exists():
            raise serializers.ValidationError(
                _("A user with this email already exists.")
            )
            
        # Additional email validation (e.g., domain blacklist)
        domain = normalized_email.split('@')[1]
        if domain in ['tempmail.com', 'throwaway.com']:  # Example domains
            raise serializers.ValidationError(
                _("This email domain is not allowed.")
            )
            
        return normalized_email

    def validate_password(self, value):
        """Validate password strength."""
        try:
            # Use Django's password validation
            validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError(list(e.messages))

        # Additional custom password validation
        if len(value) < 8:
            raise serializers.ValidationError(
                _("Password must be at least 8 characters long.")
            )
            
        if not re.search(r'[A-Z]', value):
            raise serializers.ValidationError(
                _("Password must contain at least one uppercase letter.")
            )
            
        if not re.search(r'[a-z]', value):
            raise serializers.ValidationError(
                _("Password must contain at least one lowercase letter.")
            )
            
        if not re.search(r'\d', value):
            raise serializers.ValidationError(
                _("Password must contain at least one number.")
            )
            
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', value):
            raise serializers.ValidationError(
                _("Password must contain at least one special character.")
            )

        return value

    def validate(self, attrs):
        """Validate the entire registration data."""
        if attrs['password'] != attrs.pop('password_confirm'):
            raise serializers.ValidationError({
                'password_confirm': _("Passwords do not match.")
            })
            
        return attrs

    def create(self, validated_data):
        """Create a new user."""
        return AppUser.objects.create_user(**validated_data)

class LoginSerializer(serializers.Serializer):
    """Serializer for user login."""
    
    email = serializers.EmailField(
        required=True,
        error_messages={
            'required': _('Email is required'),
            'invalid': _('Enter a valid email address')
        }
    )
    password = serializers.CharField(
        write_only=True,
        required=True,
        error_messages={
            'required': _('Password is required')
        },
        style={'input_type': 'password'}
    )
    device_info = serializers.JSONField(required=False)

    def validate_email(self, value):
        """Normalize email address."""
        return value.lower().strip()

    def validate(self, attrs):
        """Validate the entire login data."""
        # Add any additional validation here
        return attrs

class PasswordResetRequestSerializer(serializers.Serializer):
    """Serializer for password reset request."""
    
    email = serializers.EmailField(required=True)

    def validate_email(self, value):
        """Normalize email address."""
        return value.lower()

class PasswordResetConfirmSerializer(serializers.Serializer):
    """Serializer for password reset confirmation."""
    
    token = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)
    new_password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    new_password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )

    def validate_email(self, value):
        """Normalize email address."""
        return value.lower()

    def validate_new_password(self, value):
        """Validate new password strength."""
        try:
            validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return value

    def validate(self, attrs):
        """Validate password confirmation."""
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({
                'new_password_confirm': _("Passwords do not match.")
            })
        return attrs

class PasswordChangeSerializer(serializers.Serializer):
    """Serializer for password change."""
    
    current_password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    new_password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    new_password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )

    def validate_new_password(self, value):
        """Validate new password strength."""
        user = self.context['request'].user
        
        try:
            validate_password(value, user)
        except ValidationError as e:
            raise serializers.ValidationError(list(e.messages))

        if value == self.initial_data.get('current_password'):
            raise serializers.ValidationError(
                _("New password must be different from current password.")
            )
            
        return value

    def validate(self, attrs):
        """Validate password confirmation."""
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({
                'new_password_confirm': _("Passwords do not match.")
            })
        return attrs

class EmailVerificationSerializer(serializers.Serializer):
    """Serializer for email verification."""
    
    token = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)

    def validate_email(self, value):
        """Normalize email address."""
        return value.lower()

class ResendVerificationSerializer(serializers.Serializer):
    """Serializer for resending verification email."""
    
    email = serializers.EmailField(required=True)

    def validate_email(self, value):
        """Normalize email and check if user exists."""
        email = value.lower()
        
        try:
            user = AppUser.objects.get(email=email)
            if user.email_verified:
                raise serializers.ValidationError(
                    _("This email is already verified.")
                )
        except AppUser.DoesNotExist:
            raise serializers.ValidationError(
                _("No user found with this email address.")
            )
            
        return email

class GoogleAuthSerializer(serializers.Serializer):
    """Serializer for Google OAuth authentication."""
    access_token = serializers.CharField(required=True)
    id_token = serializers.CharField(required=False, allow_blank=True)

    def validate_access_token(self, value):
        if not value:
            raise serializers.ValidationError("Access token is required")
        return value