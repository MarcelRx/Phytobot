"""
Safety utilities for Phytobot.
"""
import logging
from src.config import SafetyConfig

logger = logging.getLogger(__name__)


def verify_safety_disclaimer(response: str) -> str:
    """
    Verify that the response contains required safety disclaimer phrases.
    If not, append a standardized disclaimer.
    
    Args:
        response: The generated response text
    
    Returns:
        Response with guaranteed safety disclaimer
    """
    response_lower = response.lower()
    has_disclaimer = any(phrase in response_lower for phrase in SafetyConfig.REQUIRED_DISCLAIMER_PHRASES)
    
    if not has_disclaimer:
        logger.warning("Response missing safety disclaimer, appending standard disclaimer")
        return response + SafetyConfig.STANDARD_DISCLAIMER
    
    return response
