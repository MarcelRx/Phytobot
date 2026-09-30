"""
Centralized configuration for Phytobot.
"""

import logging
import os
import sys

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


def validate_required_config():
    """
    Validate that all required environment variables are set.
    Fails clearly with descriptive error messages if configuration is missing.
    Skip validation if BUILDING_VECTOR_DB is set (for Docker build context).
    """
    # Skip validation during vector DB build (Docker build phase)
    if os.getenv("BUILDING_VECTOR_DB"):
        logger.info("Skipping config validation during vector DB build")
        return

    required_vars = {
        "GROQ_API_KEY": "GROQ_API_KEY is required for LLM functionality",
        "PLANTID_API_KEY": "PLANTID_API_KEY is required for plant identification",
        "TAVILY_API_KEY": "TAVILY_API_KEY is required for web search",
    }

    missing_vars = []
    for var_name, description in required_vars.items():
        if not os.getenv(var_name):
            missing_vars.append(f"  - {var_name}: {description}")

    if missing_vars:
        error_msg = (
            "Configuration Error: Missing required environment variables:\n"
            + "\n".join(missing_vars)
        )
        logger.error(error_msg)
        print(error_msg, file=sys.stderr)
        sys.exit(1)

    logger.info("All required configuration variables are present")


# Validate configuration on import
validate_required_config()


# API Configuration
class APIConfig:
    """API-related configuration."""

    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    PLANTID_API_KEY = os.getenv("PLANTID_API_KEY")
    TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

    # API timeouts (seconds)
    REQUEST_TIMEOUT = 30
    PLANTID_TIMEOUT = 30
    TAVILY_TIMEOUT = 15


# Vector Database Configuration
class VectorDBConfig:
    """Vector database configuration."""

    VECTOR_DB_PATH = os.getenv("VECTOR_DB_PATH", "./vector_db")
    EMBEDDING_MODEL = "all-MiniLM-L6-v2"
    RETRIEVAL_K = 3  # Number of documents to retrieve


# LLM Configuration
class LLMConfig:
    """LLM configuration."""

    MODEL_NAME = "llama-3.1-8b-instant"
    TEMPERATURE = 0.1
    MAX_RETRIES = 2


# Vision Configuration
class VisionConfig:
    """Vision module configuration."""

    BLUR_THRESHOLD = 70
    MAX_IMAGE_SIZE_MB = 10
    ALLOWED_IMAGE_TYPES = ["jpg", "jpeg", "png"]


# Search Configuration
class SearchConfig:
    """Search configuration."""

    MAX_WEB_RESULTS = 2


# Text Processing Configuration
class TextConfig:
    """Text processing configuration."""

    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 200
    MAX_QUERY_LENGTH = 1000


# Safety Configuration
class SafetyConfig:
    """Safety-related configuration."""

    REQUIRED_DISCLAIMER_PHRASES = [
        "medical advice",
        "not a substitute",
        "consult a doctor",
    ]
    STANDARD_DISCLAIMER = "\n\n**Medical Disclaimer:** This information is for educational purposes only and is not a substitute for professional medical advice. Always consult a qualified healthcare provider before using herbal remedies."

    # Safety thresholds
    IDENTIFICATION_CONFIDENCE_THRESHOLD = (
        0.70  # Below this, identification is uncertain
    )
    TOXICITY_RISK_LEVELS = ["critical", "high", "moderate", "low"]
    MANDATORY_WARNING_RISKS = ["critical", "high"]


# Negative Knowledge Configuration
class NegativeKnowledgeConfig:
    """Negative knowledge base configuration."""

    NEGATIVE_DATA_PATH = "./data/negative"
    NEGATIVE_METADATA_KEY = (
        "knowledge_type"  # Metadata key to distinguish negative knowledge
    )
    KNOWLEDGE_TYPES = [
        "medicinal",
        "safety_negative",
    ]  # Types of knowledge in vector DB
    SAFETY_RETRIEVAL_K = 3  # Number of safety documents to retrieve
