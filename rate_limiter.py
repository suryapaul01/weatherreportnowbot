import asyncio
from datetime import datetime, timedelta
from typing import Dict, List
from config import Config


class RateLimiter:
    def __init__(self):
        self.config = Config()
        self.user_requests: Dict[int, List[datetime]] = {}
        self.max_requests = self.config.RATE_LIMIT_REQUESTS
        self.window_hours = self.config.RATE_LIMIT_WINDOW_HOURS

    async def check_rate_limit(self, user_id: int) -> bool:
        """Check if user is within rate limit."""
        now = datetime.now()
        window_start = now - timedelta(hours=self.window_hours)
        
        # Get user's request history
        if user_id not in self.user_requests:
            self.user_requests[user_id] = []
        
        user_history = self.user_requests[user_id]
        
        # Remove old requests outside the window
        user_history[:] = [req_time for req_time in user_history if req_time > window_start]
        
        # Check if user has exceeded the limit
        if len(user_history) >= self.max_requests:
            return False
        
        # Add current request
        user_history.append(now)
        return True

    async def get_remaining_requests(self, user_id: int) -> int:
        """Get remaining requests for user."""
        now = datetime.now()
        window_start = now - timedelta(hours=self.window_hours)
        
        if user_id not in self.user_requests:
            return self.max_requests
        
        user_history = self.user_requests[user_id]
        recent_requests = [req_time for req_time in user_history if req_time > window_start]
        
        return max(0, self.max_requests - len(recent_requests))

    async def get_reset_time(self, user_id: int) -> datetime:
        """Get when the rate limit resets for user."""
        if user_id not in self.user_requests or not self.user_requests[user_id]:
            return datetime.now()
        
        oldest_request = min(self.user_requests[user_id])
        return oldest_request + timedelta(hours=self.window_hours)

    async def cleanup_old_requests(self):
        """Clean up old request records to prevent memory leaks."""
        now = datetime.now()
        window_start = now - timedelta(hours=self.window_hours)
        
        for user_id in list(self.user_requests.keys()):
            user_history = self.user_requests[user_id]
            user_history[:] = [req_time for req_time in user_history if req_time > window_start]
            
            # Remove empty histories
            if not user_history:
                del self.user_requests[user_id]
