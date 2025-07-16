import re
import logging
from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta
from config import Config


class SecurityManager:
    def __init__(self):
        self.config = Config()
        self.logger = logging.getLogger(__name__)
        
        # Blocked users and spam detection
        self.blocked_users: Set[int] = set()
        self.spam_tracker: Dict[int, List[datetime]] = {}
        self.flood_tracker: Dict[int, List[datetime]] = {}
        
        # Security settings
        self.max_messages_per_minute = 10
        self.max_identical_messages = 3
        self.spam_window_minutes = 5
        
        # Malicious patterns
        self.malicious_patterns = [
            r'<script.*?>.*?</script>',
            r'javascript:',
            r'vbscript:',
            r'onload\s*=',
            r'onerror\s*=',
            r'onclick\s*=',
            r'<iframe.*?>',
            r'<object.*?>',
            r'<embed.*?>',
        ]
        
        # Compiled regex patterns
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.malicious_patterns]

    async def is_user_blocked(self, user_id: int) -> bool:
        """Check if user is blocked."""
        return user_id in self.blocked_users

    async def block_user(self, user_id: int, reason: str = "Security violation") -> None:
        """Block a user."""
        self.blocked_users.add(user_id)
        self.logger.warning(f"User {user_id} blocked: {reason}")

    async def unblock_user(self, user_id: int) -> None:
        """Unblock a user."""
        self.blocked_users.discard(user_id)
        self.logger.info(f"User {user_id} unblocked")

    async def check_flood_protection(self, user_id: int) -> bool:
        """Check if user is flooding (too many messages)."""
        now = datetime.now()
        window_start = now - timedelta(minutes=1)
        
        # Initialize user tracking if not exists
        if user_id not in self.flood_tracker:
            self.flood_tracker[user_id] = []
        
        user_messages = self.flood_tracker[user_id]
        
        # Remove old messages outside the window
        user_messages[:] = [msg_time for msg_time in user_messages if msg_time > window_start]
        
        # Check if user exceeded the limit
        if len(user_messages) >= self.max_messages_per_minute:
            self.logger.warning(f"User {user_id} exceeded flood limit: {len(user_messages)} messages/minute")
            return False
        
        # Add current message
        user_messages.append(now)
        return True

    async def check_spam_detection(self, user_id: int, message_text: str) -> bool:
        """Check for spam patterns."""
        now = datetime.now()
        window_start = now - timedelta(minutes=self.spam_window_minutes)
        
        # Initialize user tracking if not exists
        if user_id not in self.spam_tracker:
            self.spam_tracker[user_id] = []
        
        user_messages = self.spam_tracker[user_id]
        
        # Remove old messages outside the window
        user_messages[:] = [msg_time for msg_time in user_messages if msg_time > window_start]
        
        # Count identical messages
        identical_count = sum(1 for _ in user_messages)
        
        if identical_count >= self.max_identical_messages:
            self.logger.warning(f"User {user_id} detected as spam: {identical_count} identical messages")
            return False
        
        # Add current message
        user_messages.append(now)
        return True

    async def sanitize_input(self, text: str) -> str:
        """Sanitize user input to prevent injection attacks."""
        if not text:
            return ""
        
        # Remove malicious patterns
        sanitized = text
        for pattern in self.compiled_patterns:
            sanitized = pattern.sub('', sanitized)
        
        # Remove excessive whitespace
        sanitized = re.sub(r'\s+', ' ', sanitized).strip()
        
        # Limit length
        max_length = 1000
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length] + "..."
        
        return sanitized

    async def validate_location_input(self, location: str) -> bool:
        """Validate location input."""
        if not location or len(location.strip()) == 0:
            return False
        
        # Check length
        if len(location) > 100:
            return False
        
        # Check for malicious patterns
        for pattern in self.compiled_patterns:
            if pattern.search(location):
                return False
        
        # Check for valid location characters
        valid_pattern = re.compile(r'^[a-zA-Z0-9\s\-\.,\(\)]+$')
        if not valid_pattern.match(location):
            return False
        
        return True

    async def validate_coordinates(self, latitude: float, longitude: float) -> bool:
        """Validate GPS coordinates."""
        # Check latitude range
        if not (-90 <= latitude <= 90):
            return False
        
        # Check longitude range
        if not (-180 <= longitude <= 180):
            return False
        
        return True

    async def is_admin_user(self, user_id: int) -> bool:
        """Check if user is admin."""
        return user_id == self.config.ADMIN_ID

    async def log_security_event(self, user_id: int, event_type: str, details: str) -> None:
        """Log security events."""
        self.logger.warning(f"Security event - User: {user_id}, Type: {event_type}, Details: {details}")

    async def check_user_permissions(self, user_id: int, action: str) -> bool:
        """Check if user has permission for specific action."""
        # Check if user is blocked
        if await self.is_user_blocked(user_id):
            await self.log_security_event(user_id, "BLOCKED_USER_ACCESS", f"Attempted action: {action}")
            return False
        
        # Check flood protection
        if not await self.check_flood_protection(user_id):
            await self.log_security_event(user_id, "FLOOD_DETECTED", f"Action: {action}")
            return False
        
        # Admin-only actions
        admin_actions = ["stats", "users", "admin_callback"]
        if action in admin_actions and not await self.is_admin_user(user_id):
            await self.log_security_event(user_id, "UNAUTHORIZED_ADMIN_ACCESS", f"Action: {action}")
            return False
        
        return True

    async def cleanup_old_tracking_data(self) -> None:
        """Clean up old tracking data to prevent memory leaks."""
        now = datetime.now()
        cutoff_time = now - timedelta(hours=1)
        
        # Clean spam tracker
        for user_id in list(self.spam_tracker.keys()):
            user_messages = self.spam_tracker[user_id]
            user_messages[:] = [msg_time for msg_time in user_messages if msg_time > cutoff_time]
            
            if not user_messages:
                del self.spam_tracker[user_id]
        
        # Clean flood tracker
        for user_id in list(self.flood_tracker.keys()):
            user_messages = self.flood_tracker[user_id]
            user_messages[:] = [msg_time for msg_time in user_messages if msg_time > cutoff_time]
            
            if not user_messages:
                del self.flood_tracker[user_id]

    async def get_security_stats(self) -> Dict:
        """Get security statistics."""
        return {
            "blocked_users_count": len(self.blocked_users),
            "tracked_users_spam": len(self.spam_tracker),
            "tracked_users_flood": len(self.flood_tracker),
            "blocked_users": list(self.blocked_users)
        }
