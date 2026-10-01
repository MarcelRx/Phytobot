"""
Tests for bot logic module.
Note: These tests are skipped if heavy dependencies (torch, langchain) are not available.
"""

from unittest.mock import MagicMock, patch

import pytest

# Try to import, but skip tests if dependencies are missing
try:
    from src.bot_logic import get_phytobot_response
    from src.config import EvidenceState, InputMode

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
        # Just check it's a string - exact content may vary with mock behavior
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

    @patch("src.bot_logic.load_phytobot_resources")
    def test_get_response_model_not_found_error(self, mock_load_resources):
        """Test response generation when Groq model is not found."""
        # Mock resources with model not found error
        mock_llm = MagicMock()
        mock_llm.invoke.side_effect = Exception(
            "Error code: 404 - {'error': {'message': 'The model `invalid-model` does not exist or you do not have access to it.', 'type': 'invalid_request_error', 'code': 'model_not_found'}}"
        )

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
        assert isinstance(response, str)
        assert len(docs) == 0

    @patch("src.bot_logic.load_phytobot_resources")
    def test_get_response_auth_error(self, mock_load_resources):
        """Test response generation when Groq authentication fails."""
        # Mock resources with auth error
        mock_llm = MagicMock()
        mock_llm.invoke.side_effect = Exception(
            "Error code: 401 - Authentication failed"
        )

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
        assert isinstance(response, str)
        assert len(docs) == 0

    @patch("src.bot_logic.load_phytobot_resources")
    def test_get_response_rate_limit_error(self, mock_load_resources):
        """Test response generation when Groq rate limit is exceeded."""
        # Mock resources with rate limit error
        mock_llm = MagicMock()
        mock_llm.invoke.side_effect = Exception("Error code: 429 - Rate limit exceeded")

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
        assert isinstance(response, str)
        assert len(docs) == 0

    @patch("src.bot_logic.load_phytobot_resources")
    def test_text_only_mode_no_plant_id(self, mock_load_resources):
        """Test that TEXT_ONLY mode does not include plant identification."""
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "Test response"
        mock_llm.invoke.return_value = mock_response

        mock_vector_db = MagicMock()
        mock_retriever = MagicMock()
        mock_retriever.invoke.return_value = []
        mock_vector_db.as_retriever.return_value = mock_retriever

        mock_search = MagicMock()
        mock_search.invoke.return_value = []

        mock_load_resources.return_value = (None, mock_vector_db, mock_llm, mock_search)

        response, docs = get_phytobot_response(
            "Give me a recipe for sleep tea", input_mode=InputMode.TEXT_ONLY
        )

        assert response is not None
        assert isinstance(response, str)
        # Should indicate no plant identification was performed
        assert "No plant identification was performed" in response

    @patch("src.bot_logic.load_phytobot_resources")
    def test_image_only_mode_with_plant(self, mock_load_resources):
        """Test that IMAGE_ONLY mode includes plant identification when plant is found."""
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "Test response"
        mock_llm.invoke.return_value = mock_response

        mock_vector_db = MagicMock()
        mock_retriever = MagicMock()
        mock_retriever.invoke.return_value = [MagicMock(page_content="Test doc")]
        mock_vector_db.as_retriever.return_value = mock_retriever

        mock_search = MagicMock()
        mock_search.invoke.return_value = []

        mock_load_resources.return_value = (None, mock_vector_db, mock_llm, mock_search)

        response, docs = get_phytobot_response(
            "Profile of chamomile",
            plant_name="Chamomile",
            identification_confidence=0.85,
            input_mode=InputMode.IMAGE_ONLY,
        )

        assert response is not None
        assert isinstance(response, str)
        # Should include plant identification
        assert "Identified: Chamomile" in response

    @patch("src.bot_logic.load_phytobot_resources")
    def test_image_only_mode_no_plant(self, mock_load_resources):
        """Test that IMAGE_ONLY mode reports when no plant is identified."""
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "Test response"
        mock_llm.invoke.return_value = mock_response

        mock_vector_db = MagicMock()
        mock_retriever = MagicMock()
        mock_retriever.invoke.return_value = []
        mock_vector_db.as_retriever.return_value = mock_retriever

        mock_search = MagicMock()
        mock_search.invoke.return_value = []

        mock_load_resources.return_value = (None, mock_vector_db, mock_llm, mock_search)

        response, docs = get_phytobot_response(
            "Profile of unknown plant",
            plant_name=None,
            input_mode=InputMode.IMAGE_ONLY,
        )

        assert response is not None
        assert isinstance(response, str)
        # Should indicate no plant was identified
        assert "No specific plant was identified" in response

    @patch("src.bot_logic.load_phytobot_resources")
    def test_named_plant_in_text_no_plant_id_call(self, mock_load_resources):
        """Test that naming a plant in text does not trigger plant identification."""
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "Test response"
        mock_llm.invoke.return_value = mock_response

        mock_vector_db = MagicMock()
        mock_retriever = MagicMock()
        mock_retriever.invoke.return_value = [MagicMock(page_content="Chamomile doc")]
        mock_vector_db.as_retriever.return_value = mock_retriever

        mock_search = MagicMock()
        mock_search.invoke.return_value = []

        mock_load_resources.return_value = (None, mock_vector_db, mock_llm, mock_search)

        response, docs = get_phytobot_response(
            "Give me a recipe using chamomile",
            plant_name="Chamomile",  # Plant name from user text, not from identification
            input_mode=InputMode.TEXT_ONLY,
        )

        assert response is not None
        assert isinstance(response, str)
        # Should be TEXT_ONLY mode, no identification performed
        assert "No plant identification was performed" in response

    @patch("src.bot_logic.load_phytobot_resources")
    def test_evidence_state_specific_internal(self, mock_load_resources):
        """Test SPECIFIC_INTERNAL_EVIDENCE state when both medicinal and safety docs exist."""
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "Test response"
        mock_llm.invoke.return_value = mock_response

        mock_vector_db = MagicMock()
        mock_retriever = MagicMock()
        # Return both medicinal and safety docs
        mock_retriever.invoke.return_value = [
            MagicMock(page_content="Medicinal doc"),
            MagicMock(page_content="Safety doc"),
        ]
        mock_vector_db.as_retriever.return_value = mock_retriever

        mock_search = MagicMock()
        mock_search.invoke.return_value = []

        mock_load_resources.return_value = (None, mock_vector_db, mock_llm, mock_search)

        response, docs = get_phytobot_response(
            "Query with evidence", input_mode=InputMode.TEXT_ONLY
        )

        assert response is not None
        # Should show high confidence trust label
        assert "Verified internal evidence" in response or "High confidence" in response

    @patch("src.bot_logic.load_phytobot_resources")
    def test_evidence_state_no_internal_evidence(self, mock_load_resources):
        """Test NO_RELEVANT_EVIDENCE state when no internal docs exist."""
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "Test response"
        mock_llm.invoke.return_value = mock_response

        mock_vector_db = MagicMock()
        mock_retriever = MagicMock()
        mock_retriever.invoke.return_value = []
        mock_vector_db.as_retriever.return_value = mock_retriever

        mock_search = MagicMock()
        mock_search.invoke.return_value = ["Web result"]

        mock_load_resources.return_value = (None, mock_vector_db, mock_llm, mock_search)

        response, docs = get_phytobot_response(
            "Query with no internal evidence", input_mode=InputMode.TEXT_ONLY
        )

        assert response is not None
        # Should NOT show Trust: 100%
        assert "Trust: 100%" not in response
        # Should indicate no verified internal evidence
        assert (
            "No verified internal evidence" in response
            or "Web research only" in response
        )

    @patch("src.bot_logic.load_phytobot_resources")
    def test_evidence_state_unknown_plant(self, mock_load_resources):
        """Test UNKNOWN_PLANT state for image mode with no plant identified."""
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "Test response"
        mock_llm.invoke.return_value = mock_response

        mock_vector_db = MagicMock()
        mock_retriever = MagicMock()
        mock_retriever.invoke.return_value = []
        mock_vector_db.as_retriever.return_value = mock_retriever

        mock_search = MagicMock()
        mock_search.invoke.return_value = []

        mock_load_resources.return_value = (None, mock_vector_db, mock_llm, mock_search)

        response, docs = get_phytobot_response(
            "Query with unknown plant",
            plant_name=None,
            input_mode=InputMode.IMAGE_ONLY,
        )

        assert response is not None
        # Should indicate plant identity not established
        assert (
            "Plant identity not established" in response
            or "No specific plant was identified" in response
        )

    @patch("src.bot_logic.load_phytobot_resources")
    def test_trust_label_not_hardcoded(self, mock_load_resources):
        """Test that trust label is dynamically calculated, not hardcoded to 100%."""
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "Test response"
        mock_llm.invoke.return_value = mock_response

        mock_vector_db = MagicMock()
        mock_retriever = MagicMock()
        mock_retriever.invoke.return_value = []
        mock_vector_db.as_retriever.return_value = mock_retriever

        mock_search = MagicMock()
        mock_search.invoke.return_value = []

        mock_load_resources.return_value = (None, mock_vector_db, mock_llm, mock_search)

        response, docs = get_phytobot_response(
            "Query with no evidence", input_mode=InputMode.TEXT_ONLY
        )

        assert response is not None
        # Should NOT show hardcoded Trust: 100%
        assert "Trust: 100%" not in response
