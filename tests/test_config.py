"""
Tests for configuration module.
"""

import os
from unittest.mock import patch

from src.config import (
    APIConfig,
    LLMConfig,
    SafetyConfig,
    SearchConfig,
    TextConfig,
    VectorDBConfig,
    VisionConfig,
)


class TestAPIConfig:
    """Test API configuration."""

    def test_api_config_exists(self):
        """Test that APIConfig class exists and has expected attributes."""
        assert hasattr(APIConfig, "GROQ_API_KEY")
        assert hasattr(APIConfig, "PLANTID_API_KEY")
        assert hasattr(APIConfig, "TAVILY_API_KEY")
        assert hasattr(APIConfig, "REQUEST_TIMEOUT")
        assert hasattr(APIConfig, "PLANTID_TIMEOUT")
        assert hasattr(APIConfig, "TAVILY_TIMEOUT")

    def test_timeout_values(self):
        """Test that timeout values are reasonable."""
        assert APIConfig.REQUEST_TIMEOUT > 0
        assert APIConfig.PLANTID_TIMEOUT > 0
        assert APIConfig.TAVILY_TIMEOUT > 0


class TestVectorDBConfig:
    """Test vector database configuration."""

    def test_vector_db_config_exists(self):
        """Test that VectorDBConfig class exists and has expected attributes."""
        assert hasattr(VectorDBConfig, "VECTOR_DB_PATH")
        assert hasattr(VectorDBConfig, "EMBEDDING_MODEL")
        assert hasattr(VectorDBConfig, "RETRIEVAL_K")

    def test_retrieval_k_positive(self):
        """Test that retrieval k is positive."""
        assert VectorDBConfig.RETRIEVAL_K > 0

    def test_embedding_model_name(self):
        """Test that embedding model name is set."""
        assert isinstance(VectorDBConfig.EMBEDDING_MODEL, str)
        assert len(VectorDBConfig.EMBEDDING_MODEL) > 0


class TestLLMConfig:
    """Test LLM configuration."""

    def test_llm_config_exists(self):
        """Test that LLMConfig class exists and has expected attributes."""
        assert hasattr(LLMConfig, "MODEL_NAME")
        assert hasattr(LLMConfig, "TEMPERATURE")
        assert hasattr(LLMConfig, "MAX_RETRIES")

    def test_temperature_in_range(self):
        """Test that temperature is in valid range [0, 1]."""
        assert 0 <= LLMConfig.TEMPERATURE <= 1

    def test_model_name_is_not_obsolete(self):
        """Test that the default model is not a deprecated model."""
        assert LLMConfig.MODEL_NAME != "llama-3.1-8b-instant"
        assert LLMConfig.MODEL_NAME != "llama-3.3-70b-versatile"

    def test_model_name_is_production_model(self):
        """Test that the default model is a currently supported production model."""
        # openai/gpt-oss-20b is the recommended production model as of 2026
        assert LLMConfig.MODEL_NAME == "openai/gpt-oss-20b"

    @patch.dict(os.environ, {"GROQ_MODEL": "custom-model-name"}, clear=False)
    def test_model_name_from_env_var(self):
        """Test that model name can be configured via environment variable."""
        # Reload config to pick up the environment variable
        import importlib

        import src.config

        importlib.reload(src.config)
        from src.config import LLMConfig as ReloadedLLMConfig

        assert ReloadedLLMConfig.MODEL_NAME == "custom-model-name"

        # Clean up
        del os.environ["GROQ_MODEL"]
        importlib.reload(src.config)


class TestVisionConfig:
    """Test vision module configuration."""

    def test_vision_config_exists(self):
        """Test that VisionConfig class exists and has expected attributes."""
        assert hasattr(VisionConfig, "BLUR_THRESHOLD")
        assert hasattr(VisionConfig, "MAX_IMAGE_SIZE_MB")
        assert hasattr(VisionConfig, "ALLOWED_IMAGE_TYPES")

    def test_blur_threshold_positive(self):
        """Test that blur threshold is positive."""
        assert VisionConfig.BLUR_THRESHOLD > 0

    def test_max_image_size_positive(self):
        """Test that max image size is positive."""
        assert VisionConfig.MAX_IMAGE_SIZE_MB > 0

    def test_allowed_image_types(self):
        """Test that allowed image types is a list."""
        assert isinstance(VisionConfig.ALLOWED_IMAGE_TYPES, list)
        assert len(VisionConfig.ALLOWED_IMAGE_TYPES) > 0


class TestSearchConfig:
    """Test search configuration."""

    def test_search_config_exists(self):
        """Test that SearchConfig class exists and has expected attributes."""
        assert hasattr(SearchConfig, "MAX_WEB_RESULTS")

    def test_max_web_results_positive(self):
        """Test that max web results is positive."""
        assert SearchConfig.MAX_WEB_RESULTS > 0


class TestTextConfig:
    """Test text processing configuration."""

    def test_text_config_exists(self):
        """Test that TextConfig class exists and has expected attributes."""
        assert hasattr(TextConfig, "CHUNK_SIZE")
        assert hasattr(TextConfig, "CHUNK_OVERLAP")
        assert hasattr(TextConfig, "MAX_QUERY_LENGTH")

    def test_chunk_size_positive(self):
        """Test that chunk size is positive."""
        assert TextConfig.CHUNK_SIZE > 0

    def test_chunk_overlap_less_than_chunk_size(self):
        """Test that chunk overlap is less than chunk size."""
        assert TextConfig.CHUNK_OVERLAP < TextConfig.CHUNK_SIZE

    def test_max_query_length_positive(self):
        """Test that max query length is positive."""
        assert TextConfig.MAX_QUERY_LENGTH > 0


class TestSafetyConfig:
    """Test safety configuration."""

    def test_safety_config_exists(self):
        """Test that SafetyConfig class exists and has expected attributes."""
        assert hasattr(SafetyConfig, "REQUIRED_DISCLAIMER_PHRASES")
        assert hasattr(SafetyConfig, "STANDARD_DISCLAIMER")

    def test_required_disclaimer_phrases(self):
        """Test that required disclaimer phrases is a list."""
        assert isinstance(SafetyConfig.REQUIRED_DISCLAIMER_PHRASES, list)
        assert len(SafetyConfig.REQUIRED_DISCLAIMER_PHRASES) > 0

    def test_standard_disclaimer(self):
        """Test that standard disclaimer is a string."""
        assert isinstance(SafetyConfig.STANDARD_DISCLAIMER, str)
        assert len(SafetyConfig.STANDARD_DISCLAIMER) > 0
