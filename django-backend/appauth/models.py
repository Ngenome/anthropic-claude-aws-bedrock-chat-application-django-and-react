import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
import secrets


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular user."""
        if not email:
            raise ValueError(_('Users must have an email address'))
        
        # Normalize email
        email = self.normalize_email(email)
        
        # Generate username only if not provided in extra_fields
        if 'username' not in extra_fields:
            username = self.generate_unique_username(email)
            extra_fields['username'] = username
        
        # Set defaults for regular users
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        
        # Create user instance
        user = self.model(email=email, **extra_fields)
        
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
            
        try:
            user.full_clean()
        except ValidationError as e:
            raise ValueError(str(e))
            
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Create and save a superuser."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('email_verified', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))

        return self.create_user(email, password, **extra_fields)

    def generate_unique_username(self, email):
        """Generate a unique username from email."""
        # Get the part before @ and remove special characters
        base = email.split('@')[0].lower()
        base = ''.join(e for e in base if e.isalnum())
        
        # If base is too short, pad it
        if len(base) < 3:
            base = base + 'user'
            
        username = base
        counter = 1
        
        # Keep trying until we find a unique username
        while self.filter(username=username).exists():
            username = f"{base}{counter}"
            counter += 1
            
        return username


class AppUser(AbstractUser):
    """
    Custom user model that uses email for authentication.
    
    Attributes:
        id (UUIDField): Primary key
        email (EmailField): User's email address (unique)
        username (CharField): Auto-generated username
        email_verified (BooleanField): Whether email has been verified
        email_verification_token (CharField): Token for email verification
        email_verification_sent_at (DateTimeField): When verification email was sent
        password_reset_token (CharField): Token for password reset
        password_reset_sent_at (DateTimeField): When password reset email was sent
        last_login_ip (GenericIPAddressField): IP address of last login
        login_attempts (IntegerField): Number of failed login attempts
        locked_until (DateTimeField): Account locked until this time
        avatar (ImageField): User's profile picture
        is_active (BooleanField): Whether this user account is active
    """
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text=_("Unique identifier for the user")
    )
    
    email = models.EmailField(
        _('email address'),
        unique=True,
        error_messages={
            'unique': _("A user with that email already exists."),
        }
    )
    
    username = models.CharField(
        _('username'),
        max_length=150,
        unique=True,
        help_text=_('Auto-generated username for the user.'),
        error_messages={
            'unique': _("A user with that username already exists."),
        }
    )
    
    # Email verification fields
    email_verified = models.BooleanField(
        _('email verified'),
        default=False,
        help_text=_('Designates whether this user has verified their email address.')
    )
    
    email_verification_token = models.CharField(
        max_length=200,
        blank=True,
        help_text=_('Token for verifying email address')
    )
    
    email_verification_sent_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('When the verification email was last sent')
    )
    
    # Password reset fields
    password_reset_token = models.CharField(
        max_length=200,
        blank=True,
        help_text=_('Token for password reset')
    )
    
    password_reset_sent_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('When the password reset email was sent')
    )
    
    # Security fields
    last_login_ip = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text=_('IP address of last login')
    )
    
    login_attempts = models.PositiveIntegerField(
        default=0,
        help_text=_('Number of failed login attempts')
    )
    
    locked_until = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('Account locked until this time')
    )
    
    # Profile fields
    avatar = models.ImageField(
        upload_to='avatars/',
        null=True,
        blank=True,
        help_text=_('User profile picture')
    )

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['username']),
            models.Index(fields=['email_verified']),
        ]

    def __str__(self):
        return self.email

    def clean(self):
        super().clean()
        self.email = self.__class__.objects.normalize_email(self.email)

    def email_user(self, subject, message, from_email=None, **kwargs):
        """Send an email to this user."""
        from django.core.mail import send_mail
        send_mail(subject, message, from_email, [self.email], **kwargs)

    def generate_token(self, purpose: str) -> str:
        """Generate a secure token for email verification or password reset."""
        token = secrets.token_urlsafe(32)
        
        if purpose == 'email_verification':
            self.email_verification_token = token
            self.email_verification_sent_at = timezone.now()
        elif purpose == 'password_reset':
            self.password_reset_token = token
            self.password_reset_sent_at = timezone.now()
        
        self.save(update_fields=[
            f'{purpose}_token',
            f'{purpose}_sent_at'
        ])
        return token

    def verify_token(self, token: str, purpose: str, max_age_hours: int = 24) -> bool:
        """Verify a token for email verification or password reset."""
        if purpose == 'email_verification':
            stored_token = self.email_verification_token
            sent_at = self.email_verification_sent_at
        elif purpose == 'password_reset':
            stored_token = self.password_reset_token
            sent_at = self.password_reset_sent_at
        else:
            return False

        if not stored_token or not sent_at:
            return False

        # Check token age
        age = timezone.now() - sent_at
        if age.total_seconds() > max_age_hours * 3600:
            return False

        # Use constant-time comparison
        return secrets.compare_digest(stored_token, token)

    def clear_token(self, purpose: str) -> None:
        """Clear a verification or reset token."""
        if purpose == 'email_verification':
            self.email_verification_token = ''
            self.email_verification_sent_at = None
        elif purpose == 'password_reset':
            self.password_reset_token = ''
            self.password_reset_sent_at = None
        
        self.save(update_fields=[
            f'{purpose}_token',
            f'{purpose}_sent_at'
        ])

    def record_login_attempt(self, successful: bool, ip_address: str = None):
        """Record a login attempt and handle account locking."""
        if successful:
            self.login_attempts = 0
            self.locked_until = None
            if ip_address:
                self.last_login_ip = ip_address
        else:
            self.login_attempts += 1
            
            # Lock account after 5 failed attempts
            if self.login_attempts >= 5:
                self.locked_until = timezone.now() + timezone.timedelta(minutes=30)
        
        self.save(update_fields=['login_attempts', 'locked_until', 'last_login_ip'])

    def is_locked(self) -> bool:
        """Check if the account is currently locked."""
        if self.locked_until and self.locked_until > timezone.now():
            return True
        
        # Reset if lock has expired
        if self.locked_until:
            self.locked_until = None
            self.login_attempts = 0
            self.save(update_fields=['locked_until', 'login_attempts'])
        
        return False