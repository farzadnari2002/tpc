import time
from django.core.cache import cache
from django.conf import settings
from rest_framework.throttling import BaseThrottle
from rest_framework.exceptions import Throttled


class CustomThrottled(Throttled):
    """Custom exception for throttling that displays wait time in HH:MM:SS format."""
    def __init__(self, wait=None):
        self.wait = wait or 0
        hours, remainder = divmod(int(self.wait), 3600)
        minutes, seconds = divmod(remainder, 60)
        self.detail = f"{hours:02}:{minutes:02}:{seconds:02}"

    def __str__(self):
        return self.detail


class IPThrottling(BaseThrottle):
    """
    Custom throttle class that enforces rate limiting based on configurable time windows.
    """
    def __init__(
        self, scope='ip_throttling',
        time_out=settings.OTP["LONG_TIME_SECONDS"],
        max_requests=settings.OTP["LONG_MAX_REQUESTS"]):
        """
        Initialize the throttle with specific parameters.
        :param scope: A unique identifier for the throttling logic (used in cache keys).
        :param time_out: Time duration for the throttle window (in seconds).
        :param max_requests: Maximum allowed requests within the time_out window.
        """
        self.scope = scope
        self.time_out = time_out
        self.max_requests = max_requests

    def get_cache_key(self, request, view):
        """
        Generates a unique cache key for the request based on the client's IP address.
        :param request: Incoming request object.
        :param view: View that is being throttled.
        :return: A string representing the cache key.
        """
        ip = self.get_ident(request)  # Identifies the client by their IP address
        return f"{self.scope}:{ip}"

    def allow_request(self, request, view):
        self.key = self.get_cache_key(request, view)
        if not self.key:
            return True

        throttle_data = cache.get(self.key)
        now = time.time()

        if throttle_data:
            request_count, first_request_time = throttle_data
            elapsed_time = now - float(first_request_time)

            if elapsed_time < self.time_out:
                if request_count < self.max_requests:
                    cache.set(self.key, (request_count + 1, first_request_time), timeout=self.time_out)
                    return True
                raise CustomThrottled(wait=self.wait())

            cache.set(self.key, (1, now), timeout=self.time_out)
            return True

        cache.set(self.key, (1, now), timeout=self.time_out)
        return True

    def wait(self):
        throttle_data = cache.get(self.key)
        if not throttle_data:
            return None
        request_count, first_request_time = throttle_data
        remaining_time = self.time_out - (time.time() - float(first_request_time))
        return max(0, remaining_time)


# region Phone Throttle

class PhoneThrottle(BaseThrottle):
    """
    Throttle class that allows configuration of scope, time_out, and max_requests.
    """
    def __init__(self, scope, time_out, max_requests):
        self.scope = scope
        self.time_out = time_out
        self.max_requests = max_requests

    def get_cache_key(self, request, view):
        phone = request.data.get("phone")
        if not phone:
            return None
        return f"{self.scope}:{phone}"

    def allow_request(self, request, view):
        self.key = self.get_cache_key(request, view)
        if not self.key:
            return True

        throttle_data = cache.get(self.key)
        now = time.time()

        if throttle_data:
            request_count, first_request_time = throttle_data
            elapsed_time = now - float(first_request_time)

            if elapsed_time < self.time_out:
                if request_count < self.max_requests:
                    cache.set(self.key, (request_count + 1, first_request_time), timeout=self.time_out)
                    return True
                raise CustomThrottled(wait=self.wait())

            cache.set(self.key, (1, now), timeout=self.time_out)
            return True

        cache.set(self.key, (1, now), timeout=self.time_out)
        return True

    def wait(self):
        throttle_data = cache.get(self.key)
        if not throttle_data:
            return None
        request_count, first_request_time = throttle_data
        remaining_time = self.time_out - (time.time() - float(first_request_time))
        return max(0, remaining_time)

# endregion


# region Dual Throttle

class DualThrottle(BaseThrottle):
    """
    A throttle class that supports dual time-based limits:
    1. Short-term limit (e.g., 1 request every 120 seconds).
    2. Long-term limit (e.g., 15 requests every 2 hours).
    """
    def __init__(
        self, scope='phone_dual_throttle',
        short_time_out=settings.OTP["EXPIRATION_TIME_SECONDS"],
        short_max_requests=1,
        long_time_out=settings.OTP["LONG_TIME_SECONDS"],
        long_max_requests=settings.OTP["LONG_MAX_REQUESTS"]):
        self.scope = scope
        self.short_time_out = short_time_out  # Short-term time window in seconds
        self.short_max_requests = short_max_requests  # Max requests in short-term window
        self.long_time_out = long_time_out  # Long-term time window in seconds
        self.long_max_requests = long_max_requests  # Max requests in long-term window

    def get_cache_key(self, request, view):
        """
        Generates a cache key for the user based on the throttle scope and phone number.
        """
        phone = request.data.get("phone")
        if not phone:
            return None
        return f"{self.scope}:{phone}"

    def get_throttle_data(self, key):
        """
        Retrieves throttle data from cache.
        :param key: Cache key.
        :return: List of timestamps of past requests.
        """
        return cache.get(key, [])

    def set_throttle_data(self, key, timestamps):
        """
        Stores updated request timestamps in cache.
        :param key: Cache key.
        :param timestamps: List of timestamps.
        """
        # Set expiration time to the maximum of both time windows
        cache.set(key, timestamps, timeout=max(self.short_time_out, self.long_time_out))

    def allow_request(self, request, view):
        """
        Checks if the request is allowed under both short-term and long-term limits.
        """
        self.key = self.get_cache_key(request, view)
        if not self.key:
            return True

        now = time.time()
        timestamps = self.get_throttle_data(self.key)

        # Remove timestamps outside of both time windows
        timestamps = [ts for ts in timestamps if now - ts <= self.long_time_out]

        # Check short-term limit
        short_term_timestamps = [ts for ts in timestamps if now - ts <= self.short_time_out]
        if len(short_term_timestamps) >= self.short_max_requests:
            wait_time = self.short_time_out - (now - short_term_timestamps[0])
            raise CustomThrottled(wait=wait_time)

        # Check long-term limit
        if len(timestamps) >= self.long_max_requests:
            wait_time = self.long_time_out - (now - timestamps[0])
            raise CustomThrottled(wait=wait_time)

        # Add current request timestamp and update cache
        timestamps.append(now)
        self.set_throttle_data(self.key, timestamps)
        return True

    def wait(self):
        """
        Returns the remaining time for the first valid time window.
        """
        if not self.key:
            return None

        now = time.time()
        timestamps = self.get_throttle_data(self.key)

        # Check remaining time for short-term limit
        short_term_timestamps = [ts for ts in timestamps if now - ts <= self.short_time_out]
        if len(short_term_timestamps) >= self.short_max_requests:
            return self.short_time_out - (now - short_term_timestamps[0])

        # Check remaining time for long-term limit
        if len(timestamps) >= self.long_max_requests:
            return self.long_time_out - (now - timestamps[0])

        return None

# endregion