import logging
from typing import Optional, Dict, Any, List
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.core.mail import get_connection
from django.core.mail.backends.smtp import EmailBackend
from django.utils.translation import gettext as _

logger = logging.getLogger(__name__)

class EmailError(Exception):
    """Base exception for email-related errors."""
    pass

class EmailService:
    """Service for handling all email operations."""

    def __init__(self):
        self.from_email = getattr(
            settings,
            'DEFAULT_FROM_EMAIL',
            'noreply@yourdomain.com'
        )
        
        # Get email backend settings
        self.host = settings.EMAIL_HOST
        self.port = settings.EMAIL_PORT
        self.username = settings.EMAIL_HOST_USER
        self.password = settings.EMAIL_HOST_PASSWORD
        self.use_tls = settings.EMAIL_USE_TLS
        self.use_ssl = getattr(settings, 'EMAIL_USE_SSL', False)
        self.timeout = getattr(settings, 'EMAIL_TIMEOUT', None)
        
    def get_connection(self) -> EmailBackend:
        """Get a connection to the email server."""
        try:
            return get_connection(
                host=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                use_tls=self.use_tls,
                use_ssl=self.use_ssl,
                timeout=self.timeout
            )
        except Exception as e:
            logger.error(f"Failed to get email connection: {str(e)}")
            raise EmailError(_("Could not connect to email server"))

    def send_email(
        self,
        to_email: str,
        subject: str,
        template_name: str,
        context: Dict[str, Any],
        from_email: Optional[str] = None,
        bcc: Optional[List[str]] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
        priority: Optional[int] = None
    ) -> bool:
        """
        Send an email using a template.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            template_name: Name of the template (without .html/.txt extension)
            context: Context data for the template
            from_email: Optional sender email (defaults to DEFAULT_FROM_EMAIL)
            bcc: Optional list of BCC recipients
            attachments: Optional list of attachment dicts with 'filename' and 'content'
            priority: Optional email priority (1-5, 1 being highest)
            
        Returns:
            bool: True if email was sent successfully
            
        Raises:
            EmailError: If email sending fails
        """
        try:
            # Render templates
            html_content = render_to_string(f"{template_name}.html", context)
            text_content = strip_tags(html_content)  # Fallback for non-HTML clients
            
            # Create email message
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=from_email or self.from_email,
                to=[to_email],
                bcc=bcc,
                connection=self.get_connection()
            )
            
            # Add HTML content
            email.attach_alternative(html_content, "text/html")
            
            # Add any attachments
            if attachments:
                for attachment in attachments:
                    email.attach(
                        attachment['filename'],
                        attachment['content'],
                        attachment.get('mimetype', 'application/octet-stream')
                    )
            
            # Set priority if specified
            if priority:
                if 1 <= priority <= 5:
                    email.extra_headers['Priority'] = str(priority)
                    
            # Send email
            email.send(fail_silently=False)
            
            logger.info(
                f"Email sent successfully to {to_email}",
                extra={
                    'template': template_name,
                    'to_email': to_email,
                    'subject': subject
                }
            )
            
            return True
            
        except Exception as e:
            logger.error(
                f"Failed to send email to {to_email}: {str(e)}",
                extra={
                    'template': template_name,
                    'to_email': to_email,
                    'subject': subject,
                    'error': str(e)
                },
                exc_info=True
            )
            raise EmailError(_("Failed to send email"))

    def send_verification_email(self, user) -> bool:
        """
        Send email verification email to user.
        
        Args:
            user: AppUser instance
            
        Returns:
            bool: True if email sent successfully
            
        Raises:
            EmailError: If email sending fails
        """
        # Generate verification token
        token = user.generate_token('email_verification')
        
        # Construct verification URL
        verification_url = f"{settings.FRONTEND_URL}/auth/verify-email?token={token}&email={user.email}"
        
        context = {
            'user': user,
            'verification_url': verification_url,
            'site_name': settings.SITE_NAME,
            'support_email': settings.SUPPORT_EMAIL,
            'token_expiry_hours': 24  # Token validity duration
        }
        
        return self.send_email(
            to_email=user.email,
            subject=_("Verify your email address"),
            template_name='auth/email/verification',
            context=context,
            priority=2  # High priority for verification emails
        )

    def send_password_reset_email(self, user) -> bool:
        """
        Send password reset email to user.
        
        Args:
            user: AppUser instance
            
        Returns:
            bool: True if email sent successfully
            
        Raises:
            EmailError: If email sending fails
        """
        # Generate password reset token
        token = user.generate_token('password_reset')
        
        # Construct reset URL
        reset_url = f"{settings.FRONTEND_URL}/auth/reset?token={token}&email={user.email}"
        
        context = {
            'user': user,
            'reset_url': reset_url,
            'site_name': settings.SITE_NAME,
            'support_email': settings.SUPPORT_EMAIL,
            'token_expiry_hours': 24,  # Token validity duration
            'ip_address': user.last_login_ip  # For security notification
        }
        
        return self.send_email(
            to_email=user.email,
            subject=_("Reset your password"),
            template_name='auth/email/password_reset',
            context=context,
            priority=2  # High priority for password reset
        )

    def send_password_change_notification(self, user) -> bool:
        """
        Send notification when password is changed.
        
        Args:
            user: AppUser instance
            
        Returns:
            bool: True if email sent successfully
            
        Raises:
            EmailError: If email sending fails
        """
        context = {
            'user': user,
            'site_name': settings.SITE_NAME,
            'support_email': settings.SUPPORT_EMAIL,
            'ip_address': user.last_login_ip,
            'timestamp': user.password_reset_sent_at
        }
        
        return self.send_email(
            to_email=user.email,
            subject=_("Your password has been changed"),
            template_name='auth/email/password_changed',
            context=context,
            priority=2
        )

    def send_suspicious_login_notification(
        self, 
        user,
        ip_address: str,
        location: Optional[str] = None,
        device_info: Optional[str] = None
    ) -> bool:
        """
        Send notification about suspicious login attempt.
        
        Args:
            user: AppUser instance
            ip_address: IP address of the login attempt
            location: Optional location info derived from IP
            device_info: Optional device/browser info
            
        Returns:
            bool: True if email sent successfully
            
        Raises:
            EmailError: If email sending fails
        """
        context = {
            'user': user,
            'ip_address': ip_address,
            'location': location,
            'device_info': device_info,
            'timestamp': user.last_login_ip,
            'site_name': settings.SITE_NAME,
            'support_email': settings.SUPPORT_EMAIL
        }
        
        return self.send_email(
            to_email=user.email,
            subject=_("Suspicious login attempt detected"),
            template_name='auth/email/suspicious_login',
            context=context,
            priority=1  # Highest priority for security notifications
        )