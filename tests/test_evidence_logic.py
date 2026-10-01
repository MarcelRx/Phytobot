"""
Tests for evidence state and trust label logic.
These tests test the new evidence state determination logic without requiring heavy dependencies.
"""

from unittest.mock import MagicMock

from src.config import EvidenceState, InputMode
from src.evidence_logic import determine_evidence_state, get_trust_label


def test_determine_evidence_state():

    # Test SPECIFIC_INTERNAL_EVIDENCE - both medicinal and safety docs
    medicinal_docs = [MagicMock()]
    safety_docs = [MagicMock()]
    state = determine_evidence_state(
        medicinal_docs, safety_docs, InputMode.TEXT_ONLY, "Chamomile"
    )
    assert state == EvidenceState.SPECIFIC_INTERNAL_EVIDENCE

    # Test PARTIAL_INTERNAL_EVIDENCE - only medicinal docs
    medicinal_docs = [MagicMock()]
    safety_docs = []
    state = determine_evidence_state(
        medicinal_docs, safety_docs, InputMode.TEXT_ONLY, "Chamomile"
    )
    assert state == EvidenceState.PARTIAL_INTERNAL_EVIDENCE

    # Test PARTIAL_INTERNAL_EVIDENCE - only safety docs
    medicinal_docs = []
    safety_docs = [MagicMock()]
    state = determine_evidence_state(
        medicinal_docs, safety_docs, InputMode.TEXT_ONLY, "Chamomile"
    )
    assert state == EvidenceState.PARTIAL_INTERNAL_EVIDENCE

    # Test NO_RELEVANT_EVIDENCE - no docs
    medicinal_docs = []
    safety_docs = []
    state = determine_evidence_state(
        medicinal_docs, safety_docs, InputMode.TEXT_ONLY, "Chamomile"
    )
    assert state == EvidenceState.NO_RELEVANT_EVIDENCE

    # Test UNKNOWN_PLANT - image mode with no plant name
    medicinal_docs = []
    safety_docs = []
    state = determine_evidence_state(
        medicinal_docs, safety_docs, InputMode.IMAGE_ONLY, None
    )
    assert state == EvidenceState.UNKNOWN_PLANT

    # Test UNKNOWN_PLANT - image_and_text mode with no plant name
    state = determine_evidence_state(
        medicinal_docs, safety_docs, InputMode.IMAGE_AND_TEXT, None
    )
    assert state == EvidenceState.UNKNOWN_PLANT


def test_get_trust_label():
    """Test trust label generation."""

    # Test each evidence state
    assert "High confidence" in get_trust_label(
        EvidenceState.SPECIFIC_INTERNAL_EVIDENCE
    )
    assert "Moderate confidence" in get_trust_label(
        EvidenceState.PARTIAL_INTERNAL_EVIDENCE
    )
    assert "Low confidence" in get_trust_label(EvidenceState.WEB_ONLY_EVIDENCE)
    assert "No verified internal evidence" in get_trust_label(
        EvidenceState.NO_RELEVANT_EVIDENCE
    )
    assert "Plant identity not established" in get_trust_label(
        EvidenceState.UNKNOWN_PLANT
    )


def test_input_mode_enum():
    """Test InputMode enum values."""
    assert InputMode.TEXT_ONLY.value == "text_only"
    assert InputMode.IMAGE_ONLY.value == "image_only"
    assert InputMode.IMAGE_AND_TEXT.value == "image_and_text"


def test_evidence_state_enum():
    """Test EvidenceState enum values."""
    assert (
        EvidenceState.SPECIFIC_INTERNAL_EVIDENCE.value == "specific_internal_evidence"
    )
    assert EvidenceState.PARTIAL_INTERNAL_EVIDENCE.value == "partial_internal_evidence"
    assert EvidenceState.WEB_ONLY_EVIDENCE.value == "web_only_evidence"
    assert EvidenceState.NO_RELEVANT_EVIDENCE.value == "no_relevant_evidence"
    assert EvidenceState.UNKNOWN_PLANT.value == "unknown_plant"
