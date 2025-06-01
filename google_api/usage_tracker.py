import shelve
import time
from datetime import datetime, timedelta
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class UsageTracker:
    def __init__(self, storage_path: str = ".usage_data"):
        self.storage_path = storage_path
        self.daily_limit_bytes = 1 * 1024 * 1024 * 1024  # 1GB per day
        self.rate_limit_ops = 300  # 300 operations per minute
        self._init_storage()

    def _init_storage(self):
        """Initialize storage if it doesn't exist."""
        with shelve.open(self.storage_path) as db:
            if 'daily_usage' not in db:
                db['daily_usage'] = {}
            if 'minute_operations' not in db:
                db['minute_operations'] = {}

    def _cleanup_old_data(self):
        """Remove data older than 24 hours."""
        now = datetime.now()
        with shelve.open(self.storage_path) as db:
            # Clean up daily usage
            daily_usage = db['daily_usage']
            daily_usage = {k: v for k, v in daily_usage.items() 
                         if now - datetime.fromisoformat(k) < timedelta(days=1)}
            db['daily_usage'] = daily_usage

            # Clean up minute operations
            minute_ops = db['minute_operations']
            minute_ops = {k: v for k, v in minute_ops.items() 
                        if now - datetime.fromisoformat(k) < timedelta(minutes=1)}
            db['minute_operations'] = minute_ops

    def check_and_update_usage(self, bytes_size: int = 0) -> bool:
        """
        Check if operation is allowed and update usage.
        Returns True if operation is allowed, False if limit reached.
        """
        now = datetime.now()
        today = now.date().isoformat()
        minute = now.replace(second=0, microsecond=0).isoformat()

        self._cleanup_old_data()

        with shelve.open(self.storage_path) as db:
            # Check daily data limit
            daily_usage = db['daily_usage']
            today_usage = daily_usage.get(today, 0)
            if today_usage + bytes_size > self.daily_limit_bytes:
                wait_hours = 24 - now.hour
                logger.warning(f"Daily limit reached. Wait {wait_hours} hours before trying again.")
                return False

            # Check rate limit
            minute_ops = db['minute_operations']
            minute_count = minute_ops.get(minute, 0)
            if minute_count >= self.rate_limit_ops:
                logger.warning("Rate limit reached. Wait 1 minute before trying again.")
                return False

            # Update usage
            daily_usage[today] = today_usage + bytes_size
            minute_ops[minute] = minute_count + 1
            db['daily_usage'] = daily_usage
            db['minute_operations'] = minute_ops

        return True

    def get_remaining_daily_quota(self) -> int:
        """Get remaining daily quota in bytes."""
        today = datetime.now().date().isoformat()
        with shelve.open(self.storage_path) as db:
            daily_usage = db['daily_usage']
            today_usage = daily_usage.get(today, 0)
            return max(0, self.daily_limit_bytes - today_usage)

    def wait_if_needed(self, bytes_size: int = 0):
        """Wait if necessary to stay within limits."""
        while not self.check_and_update_usage(bytes_size):
            time.sleep(60)  # Wait a minute and try again 