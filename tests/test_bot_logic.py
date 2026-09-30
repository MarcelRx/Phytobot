"""
Tests for bot logic module.
Note: These tests are skipped if heavy dependencies (torch, langchain) are not available.
"""

from unittest.mock import MagicMock, patch

import pytest

# Try to import, but skip tests if dependencies are missing
try:
    from src.bot_logic import get_phytobot_response

    BOT_LOGIC_AVAILABLE = True
except ImportError:
    BOT_LOGIC_AVAILABLE = False
    pytest.skip("Heavy dependencies not available", allow_module_level=True)


@pytest.mark.skipif(not BOT_LOGIC_AVAILABLE, reason="Heavy dependencies not available")
class TestPhytobotResponse:
    """Test Phytobot response generation."""

    @patch("src.bot_logic.load_phytobot_resources")
    def test_get_response_success(self, mock_load_resources):
        """Test successful response generation."""
        # Mock resources
        mock_llm = MagicMock()
        # Create a proper response object with string content
        mock_response = MagicMock()
        mock_response.content = "Test response with medical advice"
        mock_llm.invoke.return_value = mock_response

        mock_vector_db = MagicMock()
        # Mock separate retrievers for medicinal and safety
        mock_retriever = MagicMock()
        mock_retriever.invoke.return_value = [
            MagicMock(page_content="Test document 1"),
            MagicMock(page_content="Test document 2"),
        ]
        mock_vector_db.as_retriever.return_value = mock_retriever

        mock_search = MagicMock()
        mock_search.invoke.return_value = ["Web result 1"]

        mock_load_resources.return_value = (None, mock_vector_db, mock_llm, mock_search)

        response, docs = get_phytobot_response("test query")

        assert response is not None
        # New implementation retrieves both medicinal and safety docs (2 + 2 = 4)
        assert len(docs) == 4
        assert isinstance(response, str)

    @patch("src.bot_logic.load_phytobot_resources")
    def test_get_response_vector_db_failure(self, mock_load_resources):
        """Test response generation when vector DB fails."""
        # Mock resources with failing vector DB
        mock_llm = MagicMock()
        # Create a proper response object with string content
        mock_response = MagicMock()
        mock_response.content = "Test response with medical advice"
        mock_llm.invoke.return_value = mock_response

        mock_vector_db = MagicMock()
        mock_retriever = MagicMock()
        mock_retriever.invoke.side_effect = Exception("DB error")
        mock_vector_db.as_retriever.return_value = mock_retriever

        mock_search = MagicMock()
        mock_search.invoke.return_value = ["Web result 1"]

        mock_load_resources.return_value = (None, mock_vector_db, mock_llm, mock_search)

        response, docs = get_phytobot_response("test query")

        # Should still return a response, not crash
        assert response is not None
        assert isinstance(response, str)
        assert len(docs) == 0

    @patch("src.bot_logic.load_phytobot_resources")
    def test_get_response_web_search_failure(self, mock_load_resources):
        """Test response generation when web search fails."""
        # Mock resources with failing web search
        mock_llm = MagicMock()
        # Create a proper response object with string content
        mock_response = MagicMock()
        mock_response.content = "Test response with medical advice"
        mock_llm.invoke.return_value = mock_response

        mock_vector_db = MagicMock()
        mock_retriever = MagicMock()
        mock_retriever.invoke.return_value = [MagicMock(page_content="Test document 1")]
        mock_vector_db.as_retriever.return_value = mock_retriever

        mock_search = MagicMock()
        mock_search.invoke.side_effect = Exception("Search error")

        mock_load_resources.return_value = (None, mock_vector_db, mock_llm, mock_search)

        response, docs = get_phytobot_response("test query")

        # Should still return a response, not crash
        assert response is not None
        assert isinstance(response, str)
        # New implementation retrieves both medicinal and safety docs (1 + 1 = 2)
        assert len(docs) == 2

    @patch("src.bot_logic.load_phytobot_resources")
    def test_get_response_llm_failure(self, mock_load_resources):
        """Test response generation when LLM fails."""
        # Mock resources with failing LLM
        mock_llm = MagicMock()
        mock_llm.invoke.side_effect = Exception("LLM error")

        mock_vector_db = MagicMock()
        mock_retriever = MagicMock()
        mock_retriever.invoke.return_value = []
        mock_vector_db.as_retriever.return_value = mock_retriever

        mock_search = MagicMock()
        mock_search.invoke.return_value = []

        mock_load_resources.return_value = (None, mock_vector_db, mock_llm, mock_search)

        response, docs = get_phytobot_response("test query")

        # Should return error message, not crash
        assert response is not None
        # Response is a string, not a MagicMock object
        assert isinstance(response, str)
        # Error handling in bot_logic returns a string error message
        assert "error" in response.lower() or "encountered an error" in response.lower()
        assert len(docs) == 0

    @patch("src.bot_logic.load_phytobot_resources")
    def test_get_response_empty_vector_db(self, mock_load_resources):
        """Test response generation with empty vector database."""
        # Mock resources with empty vector DB
        mock_llm = MagicMock()
        # Create a proper response object with string content
        mock_response = MagicMock()
        mock_response.content = "Test response with medical advice"
        mock_llm.invoke.return_value = mock_response

        mock_vector_db = MagicMock()
        mock_retriever = MagicMock()
        mock_retriever.invoke.return_value = []
        mock_vector_db.as_retriever.return_value = mock_retriever

        mock_search = MagicMock()
        mock_search.invoke.return_value = ["Web result 1"]

        mock_load_resources.return_value = (None, mock_vector_db, mock_llm, mock_search)

        response, docs = get_phytobot_response("test query")

        assert response is not None
        assert isinstance(response, str)
        assert len(docs) == 0

    @patch("src.bot_logic.load_phytobot_resources")
    def test_get_response_missing_disclaimer(self, mock_load_resources):
        """Test that disclaimer is appended when LLM response lacks it."""
        # Mock resources with LLM response without disclaimer
        mock_llm = MagicMock()
        # Create a proper response object with string content
        mock_response = MagicMock()
        mock_response.content = "Test response without any disclaimer"
        mock_llm.invoke.return_value = mock_response

        mock_vector_db = MagicMock()
        mock_retriever = MagicMock()
        mock_retriever.invoke.return_value = []
        mock_vector_db.as_retriever.return_value = mock_retriever

        mock_search = MagicMock()
        mock_search.invoke.return_value = []

        mock_load_resources.return_value = (None, mock_vector_db, mock_llm, mock_search)

        response, docs = get_phytobot_response("test query")

        assert response is not None
        # Response is a string, not a MagicMock object
        assert isinstance(response, str)
        # The safety module should append the disclaimer
        from src.config import SafetyConfig

        assert SafetyConfig.STANDARD_DISCLAIMER in response
