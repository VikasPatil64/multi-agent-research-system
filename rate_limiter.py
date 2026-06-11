import time
from functools import wraps
from datetime import datetime, timedelta
import json
import os

class RateLimiter:
    """Rate limiter for API calls with persistence across runs"""
    
    def __init__(self, max_calls_per_minute=5, daily_limit=18, quota_file="quota_tracker.json"):
        self.max_calls_per_minute = max_calls_per_minute
        self.daily_limit = daily_limit
        self.quota_file = quota_file
        self.calls = []
        self.load_daily_usage()
    
    def load_daily_usage(self):
        """Load daily usage from previous runs"""
        try:
            with open(self.quota_file, 'r') as f:
                data = json.load(f)
                today = datetime.now().strftime('%Y-%m-%d')
                if data.get('date') == today:
                    self.daily_used = data.get('count', 0)
                else:
                    self.daily_used = 0
        except FileNotFoundError:
            self.daily_used = 0
    
    def save_daily_usage(self):
        """Save daily usage to file"""
        with open(self.quota_file, 'w') as f:
            json.dump({
                'date': datetime.now().strftime('%Y-%m-%d'),
                'count': self.daily_used
            }, f)
    
    def can_make_request(self):
        """Check if we can make a request (rate limit + daily quota)"""
        # Check daily quota
        if self.daily_used >= self.daily_limit:
            print(f"❌ Daily quota exhausted: {self.daily_used}/{self.daily_limit}")
            return False
        
        # Check per-minute rate limit
        now = datetime.now()
        self.calls = [call for call in self.calls if now - call < timedelta(minutes=1)]
        
        if len(self.calls) >= self.max_calls_per_minute:
            oldest = self.calls[0]
            wait_time = 60 - (now - oldest).seconds
            if wait_time > 0:
                print(f"⏳ Rate limit: Waiting {wait_time} seconds...")
                time.sleep(wait_time + 1)
        
        return True
    
    def record_request(self):
        """Record a successful request"""
        self.calls.append(datetime.now())
        self.daily_used += 1
        self.save_daily_usage()
        remaining = self.daily_limit - self.daily_used
        print(f"📊 API calls today: {self.daily_used}/{self.daily_limit} ( {remaining} remaining )")
    
    def get_remaining(self):
        """Get remaining calls for today"""
        return max(0, self.daily_limit - self.daily_used)

# Global rate limiter instance
limiter = RateLimiter(max_calls_per_minute=5, daily_limit=18)  # Leave 2 as buffer

def rate_limited(func):
    """Decorator to rate limit LLM calls"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not limiter.can_make_request():
            raise Exception(f"Rate limit exceeded. {limiter.get_remaining()} calls remaining today. Please try tomorrow.")
        result = func(*args, **kwargs)
        limiter.record_request()
        return result
    return wrapper

def check_quota():
    """Check if quota is available without making a request"""
    return limiter.can_make_request()

def get_remaining_quota():
    """Get remaining quota for today"""
    return limiter.get_remaining()