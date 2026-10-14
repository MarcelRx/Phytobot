"""
Session-based rate limiting for Phytobot.

Given Streamlit's architecture (stateless, session-scoped, no reliable IP access),
this module implements per-session rate limiting as a defensible abuse prevention control.

Limitations:
- Does not provide global or IP-based rate limiting
- Each Streamlit session has its own independent counter
- Multiple replicas or process restarts reset counters
- Cannot prevent coordinated attacks across multiple sessions
- User can bypass by opening new browser sessions

This is a best-effort control suitable for a portfolio deployment. For production
deployment with higher exposure, consider adding Redis or a dedicated rate-limiting service.
"""

import logging
import time
from dataclasses import dataclass
from typing import Dict, Optional

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """Rate limit configuration."""

    max_requests_per_window: int
    window_seconds: int
    operation_name: str


class RateLimiter:
    """
    Session-based rate limiter using in-memory tracking.

    Tracks request counts per operation type within time windows.
    Counters are stored in st.session_state and persist within a user session.
    """

    # Default rate limit configurations
    DEFAULT_CONFIGS = {
        "text_query": RateLimitConfig(
            max_requests_per_window=10, window_seconds=60, operation_name="text_query"
        ),
        "plant_identification": RateLimitConfig(
            max_requests_per_window=5,
            window_seconds=60,
            operation_name="plant_identification",
        ),
        "total_requests": RateLimitConfig(
            max_requests_per_window=15,
            window_seconds=60,
            operation_name="total_requests",
        ),
    }

    def __init__(
        self, session_state: Dict, configs: Optional[Dict[str, RateLimitConfig]] = None
    ):
        """
        Initialize rate limiter with session state.

        Args:
            session_state: Streamlit session_state dictionary
            configs: Optional custom rate limit configurations
        """
        self.session_state = session_state
        self.configs = configs or self.DEFAULT_CONFIGS

        # Initialize rate limit tracking structures in session state
        if "rate_limit_tracking" not in self.session_state:
            self.session_state["rate_limit_tracking"] = {
                "text_query": {"count": 0, "window_start": time.time()},
                "plant_identification": {"count": 0, "window_start": time.time()},
                "total_requests": {"count": 0, "window_start": time.time()},
            }

    def _is_window_expired(self, tracking: Dict, window_seconds: int) -> bool:
        """
        Check if the current time window has expired.

        Args:
            tracking: Tracking dictionary with count and window_start
            window_seconds: Window duration in seconds

        Returns:
            True if window has expired, False otherwise
        """
        return time.time() - tracking["window_start"] > window_seconds

    def _reset_window(self, tracking: Dict) -> None:
        """
        Reset the tracking window.

        Args:
            tracking: Tracking dictionary to reset
        """
        tracking["count"] = 0
        tracking["window_start"] = time.time()

    def check_rate_limit(self, operation: str) -> tuple[bool, Optional[str]]:
        """
        Check if a request is allowed under rate limits.

        Args:
            operation: Operation type (text_query, plant_identification, or total_requests)

        Returns:
            Tuple of (is_allowed, error_message)
        """
        if operation not in self.configs:
            logger.warning(f"Unknown operation type for rate limiting: {operation}")
            return True, None

        config = self.configs[operation]
        tracking = self.session_state["rate_limit_tracking"][operation]

        # Check if window has expired
        if self._is_window_expired(tracking, config.window_seconds):
            self._reset_window(tracking)
            logger.info(f"Rate limit window reset for {operation}")

        # Check if limit exceeded
        if tracking["count"] >= config.max_requests_per_window:
            logger.warning(
                f"Rate limit exceeded for {operation}: "
                f"{tracking['count']}/{config.max_requests_per_window} "
                f"in {config.window_seconds}s window"
            )
            return False, (
                f"Rate limit exceeded for {config.operation_name}. "
                f"Please wait {config.window_seconds} seconds before trying again. "
                f"Limit: {config.max_requests_per_window} requests per {config.window_seconds} seconds."
            )

        return True, None

    def record_request(self, operation: str) -> None:
        """
        Record a request for rate limiting purposes.

        Args:
            operation: Operation type to record
        """
        if operation not in self.session_state["rate_limit_tracking"]:
            logger.warning(f"Unknown operation type for recording: {operation}")
            return

        self.session_state["rate_limit_tracking"][operation]["count"] += 1
        logger.debug(
            f"Recorded request for {operation}: "
            f"count={self.session_state['rate_limit_tracking'][operation]['count']}"
        )

    def check_and_record(self, operation: str) -> tuple[bool, Optional[str]]:
        """
        Check rate limit and record request if allowed.

        Args:
            operation: Operation type

        Returns:
            Tuple of (is_allowed, error_message)
        """
        is_allowed, error_msg = self.check_rate_limit(operation)

        if is_allowed:
            self.record_request(operation)
            # Also count against total requests
            if operation != "total_requests":
                self.record_request("total_requests")

        return is_allowed, error_msg

    def get_remaining_requests(self, operation: str) -> int:
        """
        Get remaining requests for an operation in current window.

        Args:
            operation: Operation type

        Returns:
            Number of remaining requests
        """
        if operation not in self.session_state["rate_limit_tracking"]:
            return 0

        config = self.configs[operation]
        tracking = self.session_state["rate_limit_tracking"][operation]

        # Reset if window expired
        if self._is_window_expired(tracking, config.window_seconds):
            self._reset_window(tracking)

        return max(0, config.max_requests_per_window - tracking["count"])

    def get_window_reset_time(self, operation: str) -> float:
        """
        Get the time when the current window resets.

        Args:
            operation: Operation type

        Returns:
            Unix timestamp of window reset time
        """
        if operation not in self.session_state["rate_limit_tracking"]:
            return time.time()

        config = self.configs[operation]
        tracking = self.session_state["rate_limit_tracking"][operation]

        return tracking["window_start"] + config.window_seconds
