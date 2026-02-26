import time
from typing import List


class RateLimiter:
    """
    Manages rate limits for the Gemini API.
    Free tier allows 3 requests per minute.
    
    This class is designed for single-threaded use (Streamlit apps).
    For multi-threaded environments, consider using threading.Lock.
    """
    
    def __init__(self, max_requests: int = 3, time_window_seconds: int = 60):
        """
        Initialize rate limiter.
        
        Args:
            max_requests: Maximum number of requests allowed in the time window
            time_window_seconds: Time window in seconds
        """
        if max_requests <= 0:
            raise ValueError("max_requests must be positive")
        if time_window_seconds <= 0:
            raise ValueError("time_window_seconds must be positive")
            
        self.max_requests = max_requests
        self.time_window_seconds = time_window_seconds
        
    def add_request(self, request_times: List[float]) -> List[float]:
        """
        Records a new request time.
        
        Args:
            request_times: List of previous request timestamps
            
        Returns:
            Updated list with new request timestamp appended
        """
        request_times.append(time.time())
        return request_times
        
    def clean_old_requests(self, request_times: List[float]) -> List[float]:
        """
        Removes requests that are older than the time window.
        
        Args:
            request_times: List of request timestamps
            
        Returns:
            Filtered list containing only requests within the time window
        """
        current_time = time.time()
        cutoff_time = current_time - self.time_window_seconds
        return [t for t in request_times if t > cutoff_time]
        
    def can_make_request(self, request_times: List[float]) -> bool:
        """
        Checks if a new request can be made.
        
        Args:
            request_times: List of request timestamps
            
        Returns:
            True if a new request can be made, False otherwise
        """
        valid_requests = self.clean_old_requests(request_times)
        return len(valid_requests) < self.max_requests
        
    def get_wait_time(self, request_times: List[float]) -> int:
        """
        Calculates how many seconds to wait until the next request is allowed.
        
        Args:
            request_times: List of request timestamps
            
        Returns:
            Number of seconds to wait (0 if no wait needed)
        """
        valid_requests = self.clean_old_requests(request_times)
        if len(valid_requests) < self.max_requests:
            return 0
            
        # Sort to get the oldest request
        sorted_requests = sorted(valid_requests)
        oldest_request_time = sorted_requests[0]
        time_passed = time.time() - oldest_request_time
        wait_time = self.time_window_seconds - time_passed
        
        return max(0, int(wait_time))
