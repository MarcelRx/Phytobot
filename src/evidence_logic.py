"""
Evidence state and trust label logic for Phytobot.
This module is lightweight and does not depend on heavy libraries like langchain.
"""

from typing import List
from src.config import EvidenceState, InputMode


def determine_evidence_state(
    medicinal_docs: List,
    safety_docs: List,
    input_mode: InputMode,
    plant_name: str = None,
) -> EvidenceState:
    """
    Determine the evidence state based on retrieved documents and input mode.

    Args:
        medicinal_docs: Medicinal documents from vector DB
        safety_docs: Safety documents from vector DB
        input_mode: The input mode (TEXT_ONLY, IMAGE_ONLY, IMAGE_AND_TEXT)
        plant_name: Optional plant name from vision module or user text

    Returns:
        EvidenceState enum value
    """
    # If no plant is identified and this is an image request, it's unknown
    if input_mode in (InputMode.IMAGE_ONLY, InputMode.IMAGE_AND_TEXT) and not plant_name:
        return EvidenceState.UNKNOWN_PLANT

    # Check for specific internal evidence
    has_medicinal_evidence = len(medicinal_docs) > 0
    has_safety_evidence = len(safety_docs) > 0

    if has_medicinal_evidence and has_safety_evidence:
        return EvidenceState.SPECIFIC_INTERNAL_EVIDENCE
    elif has_medicinal_evidence or has_safety_evidence:
        return EvidenceState.PARTIAL_INTERNAL_EVIDENCE
    else:
        return EvidenceState.NO_RELEVANT_EVIDENCE


def get_trust_label(evidence_state: EvidenceState) -> str:
    """
    Get a human-readable trust label based on evidence state.

    Args:
        evidence_state: The determined evidence state

    Returns:
        Trust label string
    """
    trust_labels = {
        EvidenceState.SPECIFIC_INTERNAL_EVIDENCE: "Verified internal evidence (High confidence)",
        EvidenceState.PARTIAL_INTERNAL_EVIDENCE: "Partial internal evidence (Moderate confidence)",
        EvidenceState.WEB_ONLY_EVIDENCE: "Web research only (Low confidence)",
        EvidenceState.NO_RELEVANT_EVIDENCE: "No verified internal evidence found",
        EvidenceState.UNKNOWN_PLANT: "Plant identity not established",
    }
    return trust_labels.get(evidence_state, "Unknown evidence state")
