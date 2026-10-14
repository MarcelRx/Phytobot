"""
Tests for session-based rate limiting.
"""

import time

from src.rate_limiter import RateLimitConfig, RateLimiter


class TestRateLimiter:
    """Test suite for RateLimiter class."""

    def test_initialization(self):
        """Test that rate limiter initializes tracking structures."""
        session_state = {}
        limiter = RateLimiter(session_state)

        assert "rate_limit_tracking" in session_state
        assert "text_query" in session_state["rate_limit_tracking"]
        assert "plant_identification" in session_state["rate_limit_tracking"]
        assert "total_requests" in session_state["rate_limit_tracking"]

    def test_first_request_allowed(self):
        """Test that first request is always allowed."""
        session_state = {}
        limiter = RateLimiter(session_state)

        is_allowed, error_msg = limiter.check_and_record("text_query")

        assert is_allowed is True
        assert error_msg is None
        assert session_state["rate_limit_tracking"]["text_query"]["count"] == 1

    def test_request_within_limit(self):
        """Test that requests within limit are allowed."""
        session_state = {}
        limiter = RateLimiter(session_state)

        # Make 5 requests (limit is 10)
        for _ in range(5):
            is_allowed, error_msg = limiter.check_and_record("text_query")
            assert is_allowed is True
            assert error_msg is None

        assert session_state["rate_limit_tracking"]["text_query"]["count"] == 5

    def test_request_exceeds_limit(self):
        """Test that requests exceeding limit are blocked."""
        session_state = {}
        # Use a stricter config for testing
        strict_config = {
            "text_query": RateLimitConfig(
                max_requests_per_window=3,
                window_seconds=60,
                operation_name="text_query",
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
        limiter = RateLimiter(session_state, strict_config)

        # Make 3 requests (at limit)
        for _ in range(3):
            is_allowed, error_msg = limiter.check_and_record("text_query")
            assert is_allowed is True

        # 4th request should be blocked
        is_allowed, error_msg = limiter.check_and_record("text_query")
        assert is_allowed is False
        assert error_msg is not None
        assert "Rate limit exceeded" in error_msg
        assert "text_query" in error_msg.lower()

    def test_window_reset(self):
        """Test that rate limit window resets after expiration."""
        session_state = {}
        # Use a short window for testing
        short_window_config = {
            "text_query": RateLimitConfig(
                max_requests_per_window=2,
                window_seconds=1,  # 1 second window
                operation_name="text_query",
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
        limiter = RateLimiter(session_state, short_window_config)

        # Exhaust limit
        for _ in range(2):
            limiter.check_and_record("text_query")

        # Next request should be blocked
        is_allowed, _ = limiter.check_rate_limit("text_query")
        assert is_allowed is False

        # Wait for window to expire
        time.sleep(1.1)

        # Request should now be allowed
        is_allowed, _ = limiter.check_and_record("text_query")
        assert is_allowed is True

    def test_total_requests_tracking(self):
        """Test that total_requests counter tracks all operations."""
        session_state = {}
        limiter = RateLimiter(session_state)

        # Make text queries
        limiter.check_and_record("text_query")
        limiter.check_and_record("text_query")

        # Make plant identification requests
        limiter.check_and_record("plant_identification")

        # Total should be 3
        assert session_state["rate_limit_tracking"]["total_requests"]["count"] == 3

    def test_plant_identification_limit(self):
        """Test plant identification rate limiting."""
        session_state = {}
        limiter = RateLimiter(session_state)

        # Plant identification limit is 5 per 60 seconds
        for _ in range(5):
            is_allowed, error_msg = limiter.check_and_record("plant_identification")
            assert is_allowed is True

        # 6th request should be blocked
        is_allowed, error_msg = limiter.check_and_record("plant_identification")
        assert is_allowed is False
        assert "Rate limit exceeded" in error_msg
        assert "plant_identification" in error_msg.lower()

    def test_unknown_operation(self):
        """Test handling of unknown operation types."""
        session_state = {}
        limiter = RateLimiter(session_state)

        # Unknown operation should be allowed (safe default)
        is_allowed, error_msg = limiter.check_and_record("unknown_operation")
        assert is_allowed is True

    def test_get_remaining_requests(self):
        """Test getting remaining request count."""
        session_state = {}
        limiter = RateLimiter(session_state)

        # Make 3 requests
        for _ in range(3):
            limiter.check_and_record("text_query")

        # Should have 7 remaining (limit is 10)
        remaining = limiter.get_remaining_requests("text_query")
        assert remaining == 7

    def test_get_remaining_requests_after_expiration(self):
        """Test that remaining requests reset after window expiration."""
        session_state = {}
        short_window_config = {
            "text_query": RateLimitConfig(
                max_requests_per_window=2, window_seconds=1, operation_name="text_query"
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
        limiter = RateLimiter(session_state, short_window_config)

        # Exhaust limit
        for _ in range(2):
            limiter.check_and_record("text_query")

        # Should have 0 remaining
        remaining = limiter.get_remaining_requests("text_query")
        assert remaining == 0

        # Wait for window to expire
        time.sleep(1.1)

        # Should have full limit available again
        remaining = limiter.get_remaining_requests("text_query")
        assert remaining == 2

    def test_get_window_reset_time(self):
        """Test getting window reset time."""
        session_state = {}
        limiter = RateLimiter(session_state)

        reset_time = limiter.get_window_reset_time("text_query")
        current_time = time.time()

        # Reset time should be approximately 60 seconds in the future
        assert reset_time > current_time
        assert reset_time <= current_time + 61  # Allow 1 second margin

    def test_check_without_record(self):
        """Test check_rate_limit without recording."""
        session_state = {}
        limiter = RateLimiter(session_state)

        # Check should be allowed
        is_allowed, _ = limiter.check_rate_limit("text_query")
        assert is_allowed is True

        # Count should still be 0
        assert session_state["rate_limit_tracking"]["text_query"]["count"] == 0

    def test_separate_operation_limits(self):
        """Test that different operations have separate limits."""
        session_state = {}
        limiter = RateLimiter(session_state)

        # Exhaust text query limit
        for _ in range(10):
            limiter.check_and_record("text_query")

        # Text queries should be blocked
        is_allowed, _ = limiter.check_rate_limit("text_query")
        assert is_allowed is False

        # Plant identification should still be allowed (different limit)
        is_allowed, _ = limiter.check_rate_limit("plant_identification")
        assert is_allowed is True

    def test_session_state_persistence(self):
        """Test that session state persists across rate limiter instances."""
        session_state = {}
        limiter1 = RateLimiter(session_state)

        # Make a request
        limiter1.check_and_record("text_query")

        # Create new limiter with same session state
        limiter2 = RateLimiter(session_state)

        # Count should persist
        assert session_state["rate_limit_tracking"]["text_query"]["count"] == 1

        # Second request should be counted correctly
        limiter2.check_and_record("text_query")
        assert session_state["rate_limit_tracking"]["text_query"]["count"] == 2
