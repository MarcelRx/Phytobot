"""
Safety decision layer for Phytobot.
Provides deterministic logic for safety decisions before final response generation.
"""

import logging
from typing import List, Optional, Tuple

from src.config import SafetyConfig

logger = logging.getLogger(__name__)


class SafetyDecision:
    """Safety decision result."""

    def __init__(
        self,
        is_safe: bool,
        requires_warning: bool,
        warning_message: str = "",
        risk_level: str = "unknown",
        confidence: str = "low",
    ):
        self.is_safe = is_safe
        self.requires_warning = requires_warning
        self.warning_message = warning_message
        self.risk_level = risk_level
        self.confidence = confidence


def make_safety_decision(
    safety_docs: List,
    medicinal_docs: List,
    identification_confidence: Optional[float] = None,
    plant_name: Optional[str] = None,
) -> SafetyDecision:
    """
    Make a deterministic safety decision based on retrieved evidence.

    Args:
        safety_docs: Safety documents from vector DB
        medicinal_docs: Medicinal documents from vector DB
        identification_confidence: Plant identification confidence (0-1)
        plant_name: Name of identified plant

    Returns:
        SafetyDecision object with decision and warning message
    """
    # Default to unsafe if no evidence
    if not safety_docs and not medicinal_docs:
        return SafetyDecision(
            is_safe=False,
            requires_warning=True,
            warning_message="No reliable evidence found for this plant. Cannot verify safety.",
            risk_level="unknown",
            confidence="low",
        )

    # Check identification confidence
    if (
        identification_confidence is not None
        and identification_confidence < SafetyConfig.IDENTIFICATION_CONFIDENCE_THRESHOLD
    ):
        return SafetyDecision(
            is_safe=False,
            requires_warning=True,
            warning_message=f"Plant identification confidence is low ({identification_confidence:.1%}). Do not rely on this identification for medicinal use.",
            risk_level="unknown",
            confidence="low",
        )

    # Analyze safety documents
    has_toxic_evidence = False
    has_look_alike_risk = False
    max_risk = "low"
    safety_status = "unknown"

    for doc in safety_docs:
        metadata = doc.metadata
        category = metadata.get("category", "")
        risk_level = metadata.get("risk_level", "low")
        safety_stat = metadata.get("safety_status", "unknown")

        # Check for specific categories separately
        if category == "toxic_plant":
            has_toxic_evidence = True
        elif category == "dangerous_look_alike":
            has_look_alike_risk = True

        # Track highest risk level
        risk_priority = {
            "critical": 4,
            "high": 3,
            "moderate": 2,
            "low": 1,
            "unknown": 0,
        }
        if risk_priority.get(risk_level, 0) > risk_priority.get(max_risk, 0):
            max_risk = risk_level

        # Update safety status
        if safety_stat == "unsafe":
            safety_status = "unsafe"
        elif safety_stat == "caution_required" and safety_status != "unsafe":
            safety_status = "caution_required"

    # Apply deterministic safety rules in priority order

    # 1. Check for dangerous look-alikes first (highest priority)
    if has_look_alike_risk:
        return SafetyDecision(
            is_safe=False,
            requires_warning=True,
            warning_message=f"DANGEROUS LOOK-ALIKE WARNING: {plant_name or 'This plant'} has dangerous look-alikes that can be confused with toxic plants. Expert verification is required before any use.",
            risk_level="high",
            confidence="moderate",
        )

    # 2. Check for critical/high toxicity
    if has_toxic_evidence:
        if max_risk == "critical":
            return SafetyDecision(
                is_safe=False,
                requires_warning=True,
                warning_message=f"CRITICAL TOXICITY WARNING: {plant_name or 'This plant'} has documented critical toxicity. NEVER use for medicinal purposes. Risk level: CRITICAL.",
                risk_level="critical",
                confidence="high",
            )
        elif max_risk == "high":
            return SafetyDecision(
                is_safe=False,
                requires_warning=True,
                warning_message=f"TOXICITY WARNING: {plant_name or 'This plant'} has documented high toxicity. Do not use for medicinal purposes without expert medical supervision. Risk level: HIGH.",
                risk_level="high",
                confidence="high",
            )
        else:
            return SafetyDecision(
                is_safe=False,
                requires_warning=True,
                warning_message=f"SAFETY WARNING: {plant_name or 'This plant'} has documented toxicity or safety concerns. Risk level: {max_risk.upper()}.",
                risk_level=max_risk,
                confidence="moderate",
            )

    # 3. Check for caution_required status (toxic_parts, etc.)
    if safety_status == "caution_required":
        return SafetyDecision(
            is_safe=False,
            requires_warning=True,
            warning_message=f"CAUTION REQUIRED: {plant_name or 'This plant'} requires caution. Certain parts or conditions may be dangerous. Risk level: {max_risk.upper()}.",
            risk_level=max_risk,
            confidence="moderate",
        )

    # If no safety evidence but medicinal evidence exists
    if not safety_docs and medicinal_docs:
        return SafetyDecision(
            is_safe=False,  # Default to unsafe without explicit safety evidence
            requires_warning=True,
            warning_message="LIMITED SAFETY INFORMATION: Medicinal evidence found but no explicit safety verification. Exercise caution and consult a healthcare provider.",
            risk_level="unknown",
            confidence="low",
        )

    # If medicinal evidence and safety evidence both exist and safety is okay
    if (
        medicinal_docs
        and safety_docs
        and not has_toxic_evidence
        and safety_status != "unsafe"
    ):
        return SafetyDecision(
            is_safe=True,
            requires_warning=False,
            warning_message="",
            risk_level="low",
            confidence="moderate",
        )

    # Default: insufficient evidence
    return SafetyDecision(
        is_safe=False,
        requires_warning=True,
        warning_message="INSUFFICIENT EVIDENCE: Unable to verify safety with available evidence. Consult a healthcare provider.",
        risk_level="unknown",
        confidence="low",
    )


def check_for_conflicts(safety_docs: List, medicinal_docs: List) -> Tuple[bool, str]:
    """
    Check for conflicts between safety and medicinal evidence.

    Args:
        safety_docs: Safety documents from vector DB
        medicinal_docs: Medicinal documents from vector DB

    Returns:
        Tuple of (has_conflict, conflict_description)
    """
    if not safety_docs or not medicinal_docs:
        return False, ""

    # Check if safety docs indicate toxicity
    has_toxicity = any(
        doc.metadata.get("category") in ["toxic_plant", "toxic_parts"]
        for doc in safety_docs
    )

    if has_toxicity:
        return (
            True,
            "Conflict detected: Medicinal evidence exists but toxicity concerns are also documented. Do not use without expert medical supervision.",
        )

    return False, ""


def format_safety_response(
    safety_decision: SafetyDecision,
    safety_docs: List,
    medicinal_docs: List,
    plant_name: Optional[str] = None,
) -> str:
    """
    Format safety information for response.

    Args:
        safety_decision: SafetyDecision object
        safety_docs: Safety documents
        medicinal_docs: Medicinal documents
        plant_name: Plant name

    Returns:
        Formatted safety information string
    """
    parts = []

    # Add plant identification
    if plant_name:
        parts.append(f"**Plant Identified:** {plant_name}")

    # Add safety status
    if safety_decision.is_safe:
        parts.append("**Safety Status:** Documented medicinal use with safety evidence")
    else:
        parts.append(f"**Safety Status:** {safety_decision.warning_message}")

    # Add risk level
    parts.append(f"**Risk Level:** {safety_decision.risk_level.upper()}")

    # Check for conflicts
    has_conflict, conflict_desc = check_for_conflicts(safety_docs, medicinal_docs)
    if has_conflict:
        parts.append(f"**⚠️ CONFLICT WARNING:** {conflict_desc}")

    # Add evidence summary
    if safety_docs:
        parts.append(
            f"**Safety Evidence:** {len(safety_docs)} safety documents retrieved"
        )
    else:
        parts.append("**Safety Evidence:** No safety documents found")

    if medicinal_docs:
        parts.append(
            f"**Medicinal Evidence:** {len(medicinal_docs)} medicinal documents retrieved"
        )
    else:
        parts.append("**Medicinal Evidence:** No medicinal documents found")

    return "\n\n".join(parts)
