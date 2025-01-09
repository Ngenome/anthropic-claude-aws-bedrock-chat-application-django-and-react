import time
import logging
from typing import Optional, Dict, Any, List
from django.utils.translation import gettext as _
from django.core.cache import cache
from django.conf import settings
from dataclasses import dataclass
from collections import defaultdict
import threading

logger = logging.getLogger(__name__)


class RateLimitError(Exception):
    """Exception raised when rate limit is exceeded."""
    def __init__(self, message: str, retry_after: Optional[int] = None):
        self.message = message
        self.retry_after = retry_after
        super().__init__(message)

    
@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""
    max_attempts: int
    period: int  # in seconds
    block_duration: Optional[int] = None  # in seconds

class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded."""
    pass

class RateLimitService:
    """Service for handling rate limiting."""

    # Default configurations for different actions
    DEFAULT_CONFIGS = {
        'login': RateLimitConfig(
            max_attempts=5,
            period=300,  # 5 minutes
            block_duration=1800  # 30 minutes
        ),
        'registration': RateLimitConfig(
            max_attempts=5,
            period=3600,  # 1 hour
            block_duration=86400  # 24 hours
        ),
        'password_reset': RateLimitConfig(
            max_attempts=3,
            period=3600,  # 1 hour
            block_duration=7200  # 2 hours
        ),
        'verification_email': RateLimitConfig(
            max_attempts=3,
            period=3600,  # 1 hour
            block_duration=7200  # 2 hours
        ),
        'api': RateLimitConfig(
            max_attempts=100,
            period=60,  # 1 minute
            block_duration=300  # 5 minutes
        ),
        'social_auth': RateLimitConfig(
        max_attempts=10,
        period=300,  # 5 minutes
        block_duration=300  # 30 minutes
    ),
    }

    def __init__(self):
        """Initialize the rate limit service."""
        self._local = threading.local()
        self._local.memory_store = defaultdict(list)
        self.use_cache = hasattr(settings, 'CACHES') and settings.CACHES.get('default')

    def _get_cache_key(self, identifier: str, action: str) -> str:
        """
        Generate a cache key for rate limiting.
        
        Args:
            identifier: Usually an IP address or user ID
            action: Type of action being rate limited
            
        Returns:
            str: Cache key
        """
        return f"ratelimit:{action}:{identifier}"

    def _get_block_key(self, identifier: str, action: str) -> str:
        """
        Generate a cache key for blocking.
        
        Args:
            identifier: Usually an IP address or user ID
            action: Type of action being rate limited
            
        Returns:
            str: Block key
        """
        return f"ratelimit:block:{action}:{identifier}"

    def _clean_old_attempts(
        self,
        attempts: list,
        period: int,
        current_time: Optional[float] = None
    ) -> list:
        """
        Remove attempts older than the period.
        
        Args:
            attempts: List of timestamp attempts
            period: Time period in seconds
            current_time: Optional current time for testing
            
        Returns:
            list: Cleaned list of attempts
        """
        if not current_time:
            current_time = time.time()
            
        cutoff = current_time - period
        return [ts for ts in attempts if ts > cutoff]

    def record_attempt(
        self,
        identifier: str,
        action: str,
        timestamp: Optional[float] = None
    ) -> None:
        """
        Record a rate limit attempt.
        
        Args:
            identifier: Usually an IP address or user ID
            action: Type of action being rate limited
            timestamp: Optional timestamp for testing
            
        Raises:
            ValueError: If action is not recognized
        """
        if action not in self.DEFAULT_CONFIGS:
            raise ValueError(f"Unknown rate limit action: {action}")

        if not timestamp:
            timestamp = time.time()

        cache_key = self._get_cache_key(identifier, action)

        if self.use_cache:
            # Using Redis/Memcached
            attempts = cache.get(cache_key, [])
            attempts.append(timestamp)
            
            # Get config
            config = self.DEFAULT_CONFIGS[action]
            
            # Clean old attempts
            attempts = self._clean_old_attempts(attempts, config.period, timestamp)
            
            # Store updated attempts
            cache.set(
                cache_key,
                attempts,
                timeout=config.period
            )
        else:
            # Using memory store
            self._local.memory_store[cache_key].append(timestamp)

    def is_rate_limited(
    self,
    identifier: str,
    action: str,
    max_attempts: Optional[int] = None,
    period: Optional[int] = None
) -> bool:
        """Check if an action is rate limited."""
        if action not in self.DEFAULT_CONFIGS:
            raise ValueError(f"Unknown rate limit action: {action}")

        # Check if explicitly blocked
        block_key = self._get_block_key(identifier, action)
        if self.use_cache and cache.get(block_key):
            raise RateLimitError(
                _("Account temporarily blocked. Please try again later."),
                retry_after=self.DEFAULT_CONFIGS[action].block_duration
            )

        # Get configuration
        config = self.DEFAULT_CONFIGS[action]
        max_attempts = max_attempts or config.max_attempts
        period = period or config.period

        cache_key = self._get_cache_key(identifier, action)
        current_time = time.time()

        if self.use_cache:
            attempts = cache.get(cache_key, [])
        else:
            attempts = self._local.memory_store[cache_key]

        # Clean old attempts
        attempts = self._clean_old_attempts(attempts, period, current_time)

        # Check if rate limited
        if len(attempts) >= max_attempts:
            # Set blocking key if configured
            if config.block_duration and self.use_cache:
                cache.set(
                    block_key,
                    True,
                    timeout=config.block_duration
                )
                
            retry_after = int(min(
                config.block_duration or period,
                attempts[0] + period - current_time
            ))
            
            raise RateLimitError(
                _("Too many attempts. Please try again later."),
                retry_after=retry_after
            )

        return False

    def get_remaining_attempts(
        self,
        identifier: str,
        action: str
    ) -> Dict[str, Any]:
        """
        Get remaining attempts information.
        
        Args:
            identifier: Usually an IP address or user ID
            action: Type of action being checked
            
        Returns:
            Dict containing:
                remaining_attempts: Number of attempts remaining
                reset_time: Time until rate limit resets
                is_blocked: Whether explicitly blocked
        """
        if action not in self.DEFAULT_CONFIGS:
            raise ValueError(f"Unknown rate limit action: {action}")

        config = self.DEFAULT_CONFIGS[action]
        cache_key = self._get_cache_key(identifier, action)
        block_key = self._get_block_key(identifier, action)
        current_time = time.time()

        # Check if blocked
        is_blocked = False
        if self.use_cache:
            is_blocked = bool(cache.get(block_key))

        # Get attempts
        if self.use_cache:
            attempts = cache.get(cache_key, [])
        else:
            attempts = self._local.memory_store[cache_key]

        # Clean old attempts
        attempts = self._clean_old_attempts(attempts, config.period, current_time)

        # Calculate remaining attempts
        remaining = max(0, config.max_attempts - len(attempts))

        # Calculate reset time
        reset_time = 0
        if attempts:
            oldest_attempt = min(attempts)
            reset_time = max(0, oldest_attempt + config.period - current_time)

        return {
            'remaining_attempts': remaining,
            'reset_time': int(reset_time),
            'is_blocked': is_blocked
        }

    def reset_rate_limit(self, identifier: str, action: str) -> None:
        """
        Reset rate limit for an identifier.
        
        Args:
            identifier: Usually an IP address or user ID
            action: Type of action to reset
            
        Raises:
            ValueError: If action is not recognized
        """
        if action not in self.DEFAULT_CONFIGS:
            raise ValueError(f"Unknown rate limit action: {action}")

        cache_key = self._get_cache_key(identifier, action)
        block_key = self._get_block_key(identifier, action)

        if self.use_cache:
            cache.delete(cache_key)
            cache.delete(block_key)
        else:
            self._local.memory_store[cache_key] = []

        logger.info(
            f"Rate limit reset for {identifier} ({action})",
            extra={
                'identifier': identifier,
                'action': action
            }
        )

    def block_identifier(
        self,
        identifier: str,
        action: str,
        duration: Optional[int] = None
    ) -> None:
        """
        Explicitly block an identifier.
        
        Args:
            identifier: Usually an IP address or user ID
            action: Type of action to block
            duration: Optional block duration in seconds
            
        Raises:
            ValueError: If action is not recognized
        """
        if action not in self.DEFAULT_CONFIGS:
            raise ValueError(f"Unknown rate limit action: {action}")

        if not duration:
            duration = self.DEFAULT_CONFIGS[action].block_duration or 3600

        block_key = self._get_block_key(identifier, action)
        
        if self.use_cache:
            cache.set(block_key, True, timeout=duration)

        logger.info(
            f"Identifier blocked: {identifier} ({action})",
            extra={
                'identifier': identifier,
                'action': action,
                'duration': duration
            }
        )

    def unblock_identifier(self, identifier: str, action: str) -> None:
        """
        Remove explicit block from an identifier.
        
        Args:
            identifier: Usually an IP address or user ID
            action: Type of action to unblock
            
        Raises:
            ValueError: If action is not recognized
        """
        if action not in self.DEFAULT_CONFIGS:
            raise ValueError(f"Unknown rate limit action: {action}")

        block_key = self._get_block_key(identifier, action)
        
        if self.use_cache:
            cache.delete(block_key)

        logger.info(
            f"Identifier unblocked: {identifier} ({action})",
            extra={
                'identifier': identifier,
                'action': action
            }
        )