"""
Tests for safety module.
"""
import pytest
from src.safety import verify_safety_disclaimer
from src.config import SafetyConfig


class TestSafetyDisclaimer:
    """Test safety disclaimer verification."""
    
    def test_verify_disclaimer_present(self):
        """Test that response with disclaimer is unchanged."""
        response = "This is a response. Not a substitute for medical advice."
        result = verify_safety_disclaimer(response)
        assert result == response
    
    def test_verify_disclaimer_missing(self):
        """Test that response without disclaimer gets standard disclaimer appended."""
        response = "This is a response without disclaimer."
        result = verify_safety_disclaimer(response)
        assert SafetyConfig.STANDARD_DISCLAIMER in result
        assert result.endswith(SafetyConfig.STANDARD_DISCLAIMER)
    
    def test_verify_disclaimer_with_medical_advice(self):
        """Test that response containing 'medical advice' is unchanged."""
        response = "This is medical advice content."
        result = verify_safety_disclaimer(response)
        assert result == response
    
    def test_verify_disclaimer_with_consult_doctor(self):
        """Test that response containing 'consult a doctor' is unchanged."""
        response = "Please consult a doctor before use."
        result = verify_safety_disclaimer(response)
        assert result == response
    
    def test_verify_disclaimer_case_insensitive(self):
        """Test that disclaimer check is case-insensitive."""
        response = "This is MEDICAL ADVICE content."
        result = verify_safety_disclaimer(response)
        assert result == response
