"""
Input validation utilities for Phytobot.
"""
import logging
import os
from typing import Tuple, Optional
from PIL import Image
import io

from src.config import VisionConfig, TextConfig

logger = logging.getLogger(__name__)


def validate_text_input(text: str) -> Tuple[bool, Optional[str]]:
    """
    Validate text input from user.
    
    Args:
        text: The user's text input
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not text or not text.strip():
        return False, "Please enter a question or request."
    
    if len(text) > TextConfig.MAX_QUERY_LENGTH:
        return False, f"Your input is too long. Please keep it under {TextConfig.MAX_QUERY_LENGTH} characters."
    
    # Normalize whitespace
    text = " ".join(text.split())
    
    return True, None


def validate_image_file(uploaded_file) -> Tuple[bool, Optional[str]]:
    """
    Validate uploaded image file.
    
    Args:
        uploaded_file: Streamlit uploaded file object
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if uploaded_file is None:
        return False, "No file uploaded."
    
    # Check file size
    file_size_mb = uploaded_file.size / (1024 * 1024)
    if file_size_mb > VisionConfig.MAX_IMAGE_SIZE_MB:
        return False, f"File too large. Maximum size is {VisionConfig.MAX_IMAGE_SIZE_MB}MB."
    
    # Check file extension
    file_ext = uploaded_file.name.lower().split('.')[-1]
    if file_ext not in VisionConfig.ALLOWED_IMAGE_TYPES:
        return False, f"Unsupported file type. Please upload: {', '.join(VisionConfig.ALLOWED_IMAGE_TYPES)}"
    
    # Validate actual image content
    try:
        image_bytes = uploaded_file.getvalue()
        img = Image.open(io.BytesIO(image_bytes))
        img.verify()  # Verify it's a valid image
        
        # Reopen after verify (verify closes the file)
        img = Image.open(io.BytesIO(image_bytes))
        
        # Check actual format matches extension
        actual_format = img.format.lower()
        if actual_format == 'jpeg':
            actual_format = 'jpg'
        
        if actual_format not in VisionConfig.ALLOWED_IMAGE_TYPES:
            return False, f"Image format mismatch. File appears to be {actual_format}, not {file_ext}."
        
        logger.info(f"Image validation passed: {uploaded_file.name} ({file_size_mb:.2f}MB, {actual_format})")
        return True, None
        
    except Exception as e:
        logger.error(f"Image validation failed: {e}")
        return False, "Invalid or corrupted image file. Please upload a valid image."
