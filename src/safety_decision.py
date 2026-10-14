"""Deterministic safety decisions for Phytobot plant information."""

from dataclasses import dataclass
from typing import Any, Iterable


@dataclass(frozen=True)
class SafetyDecision:
    """Result of a deterministic plant-safety assessment."""

    is_safe: bool
    requires_warning: bool
    warning_message: str
    risk_level: str
    confidence: str


_RISK_PRIORITY = {
    "unknown": 0,
    "low": 1,
    "moderate": 2,
    "medium": 2,
    "high": 3,
    "critical": 4,
}

_TOXIC_CATEGORIES = {
    "toxic_plant",
    "toxic_parts",
    "dangerous_look_alike",
}

_LOOKALIKE_CATEGORIES = {
    "dangerous_look_alike",
    "look_alike",
    "lookalike",
}


def _metadata_for(document: Any) -> dict:
    """Safely retrieve metadata from a document or dictionary."""
    if isinstance(document, dict):
        metadata = document.get("metadata", {})
    else:
        metadata = getattr(document, "metadata", {})

    return metadata if isinstance(metadata, dict) else {}


def _normalized_metadata(document: Any) -> dict:
    """Normalize metadata keys for consistent lookups."""
    return {
        str(key).strip().lower(): value
        for key, value in _metadata_for(document).items()
    }


def _document_category(document: Any) -> str:
    metadata = _normalized_metadata(document)

    for key in ("category", "evidence_type", "type"):
        value = metadata.get(key)
        if value is not None:
            normalized = str(value).strip().lower()
            if normalized:
                return normalized

    return ""


def _document_risk(document: Any) -> str:
    metadata = _normalized_metadata(document)

    for key in ("risk_level", "risk", "toxicity_level"):
        value = metadata.get(key)
        if value is not None:
            normalized = str(value).strip().lower()
            if normalized in _RISK_PRIORITY:
                return normalized

    return "unknown"


def _document_status(document: Any) -> str:
    metadata = _normalized_metadata(document)

    for key in ("safety_status", "status"):
        value = metadata.get(key)
        if value is not None:
            normalized = str(value).strip().lower()
            if normalized:
                return normalized

    return ""


def _document_confidence(document: Any) -> float | None:
    metadata = _normalized_metadata(document)
    value = metadata.get(
        "identification_confidence",
        metadata.get("confidence"),
    )

    if value is None:
        return None

    try:
        confidence = float(value)
    except (TypeError, ValueError):
        return None

    if 0.0 <= confidence <= 1.0:
        return confidence

    return None


def _highest_risk(documents: Iterable[Any]) -> str:
    risks = [_document_risk(document) for document in documents]

    if not risks:
        return "unknown"

    return max(
        risks,
        key=lambda risk: _RISK_PRIORITY.get(risk, 0),
    )


def _has_category(
    documents: Iterable[Any],
    categories: set[str],
) -> bool:
    return any(_document_category(document) in categories for document in documents)


def _plant_label(plant_name: str | None) -> str:
    if plant_name is not None and str(plant_name).strip():
        return str(plant_name).strip()

    return "This plant"


def make_safety_decision(
    safety_docs: Iterable[Any] | None = None,
    medicinal_docs: Iterable[Any] | None = None,
    identification_confidence: float | None = None,
    plant_name: str | None = None,
) -> SafetyDecision:
    """Make a conservative safety decision from retrieved evidence.

    Argument order is safety_docs, medicinal_docs, identification_confidence,
    plant_name, matching the project's existing test and call conventions.
    Missing safety evidence is never treated as proof of safety.
    """
    safety_docs = list(safety_docs or [])
    medicinal_docs = list(medicinal_docs or [])
    all_docs = safety_docs + medicinal_docs
    plant_label = _plant_label(plant_name)

    if identification_confidence is None:
        confidence_values = [
            confidence
            for confidence in (_document_confidence(document) for document in all_docs)
            if confidence is not None
        ]

        if confidence_values:
            identification_confidence = min(confidence_values)

    if identification_confidence is not None and identification_confidence < 0.7:
        return SafetyDecision(
            is_safe=False,
            requires_warning=True,
            warning_message=(
                "WARNING: Plant identification confidence is low. "
                "The plant may have been misidentified. Do not consume "
                "or use it until its identity has been confirmed by "
                "a qualified expert."
            ),
            risk_level="unknown",
            confidence="low",
        )

    if not all_docs:
        return SafetyDecision(
            is_safe=False,
            requires_warning=True,
            warning_message=(
                "No reliable evidence was found for this plant. "
                "Its safety cannot be verified. Do not rely on this result "
                "to decide whether to use the plant medicinally; "
                "consult a qualified healthcare provider."
            ),
            risk_level="unknown",
            confidence="low",
        )

    categories = {_document_category(document) for document in all_docs}
    statuses = {_document_status(document) for document in all_docs}
    statuses.discard("")

    risk_level = _highest_risk(all_docs)
    has_toxic_evidence = bool(categories & _TOXIC_CATEGORIES)
    has_lookalike_evidence = bool(categories & _LOOKALIKE_CATEGORIES)

    # Toxicity evidence takes precedence over any positive medicinal claims.
    if has_lookalike_evidence:
        return SafetyDecision(
            is_safe=False,
            requires_warning=True,
            warning_message=(
                f"DANGEROUS LOOK-ALIKE WARNING: {plant_label} may be "
                "confused with a dangerous plant. Confirm the species "
                "with a qualified expert before consuming or using it."
            ),
            risk_level=risk_level,
            confidence="moderate",
        )
    if has_toxic_evidence:
        if risk_level == "critical":
            return SafetyDecision(
                is_safe=False,
                requires_warning=True,
                warning_message=(
                    f"CRITICAL TOXICITY WARNING: {plant_label} has "
                    "documented evidence of critical toxicity. "
                    "Do not consume or use this plant. Seek guidance "
                    "from a qualified professional."
                ),
                risk_level="critical",
                confidence="high",
            )

        if risk_level == "high":
            return SafetyDecision(
                is_safe=False,
                requires_warning=True,
                warning_message=(
                    f"TOXICITY WARNING: {plant_label} has documented "
                    "evidence of high toxicity or danger. Do not consume "
                    "or use it without authoritative professional guidance."
                ),
                risk_level="high",
                confidence="high",
            )

        if "caution_required" in statuses:
            return SafetyDecision(
                is_safe=False,
                requires_warning=True,
                warning_message=(
                    f"CAUTION REQUIRED: {plant_label} requires caution. "
                    "Certain plant parts or conditions may be dangerous. "
                    f"Risk level: {risk_level.upper()}."
                ),
                risk_level=risk_level,
                confidence="moderate",
            )

        return SafetyDecision(
            is_safe=False,
            requires_warning=True,
            warning_message=(
                f"SAFETY WARNING: Toxicity or a toxic plant part is "
                f"documented for {plant_label}. Do not assume that it is "
                "safe to consume or use medicinally. Consult a qualified "
                "healthcare provider."
            ),
            risk_level=risk_level,
            confidence="moderate",
        )

    if "unsafe" in statuses:
        return SafetyDecision(
            is_safe=False,
            requires_warning=True,
            warning_message=(
                f"SAFETY WARNING: Available evidence identifies "
                f"{plant_label} as unsafe. Do not consume or use it."
            ),
            risk_level=risk_level,
            confidence="high",
        )

    if "caution_required" in statuses:
        return SafetyDecision(
            is_safe=False,
            requires_warning=True,
            warning_message=(
                f"CAUTION REQUIRED: Available evidence indicates that "
                f"{plant_label} requires caution. Its safety is not fully "
                "established. Consult a qualified professional before "
                "medicinal use."
            ),
            risk_level=risk_level,
            confidence="moderate",
        )

    has_explicit_safe_status = "safe" in statuses
    has_low_risk_evidence = risk_level == "low"

    if (
        safety_docs
        and medicinal_docs
        and has_explicit_safe_status
        and has_low_risk_evidence
    ):
        return SafetyDecision(
            is_safe=True,
            requires_warning=False,
            warning_message="",
            risk_level="low",
            confidence="moderate",
        )

    if medicinal_docs:
        return SafetyDecision(
            is_safe=False,
            requires_warning=True,
            warning_message=(
                "LIMITED SAFETY INFORMATION: Medicinal information is "
                "available, but the retrieved evidence does not establish "
                "that this plant is safe to use. Reported medicinal use is "
                "not proof of safety. Consult a qualified healthcare "
                "provider before use."
            ),
            risk_level=risk_level,
            confidence="low",
        )

    return SafetyDecision(
        is_safe=False,
        requires_warning=True,
        warning_message=(
            "INSUFFICIENT SAFETY EVIDENCE: The available information does "
            "not establish that this plant is safe. Do not consume or use "
            "it medicinally based on this result. Consult a qualified "
            "healthcare provider."
        ),
        risk_level=risk_level,
        confidence="low",
    )


def check_for_conflicts(
    safety_docs: Iterable[Any] | None,
    medicinal_docs: Iterable[Any] | None,
) -> tuple[bool, str]:
    """Detect toxicity evidence that conflicts with medicinal evidence."""
    safety_docs = list(safety_docs or [])
    medicinal_docs = list(medicinal_docs or [])

    has_medicinal_evidence = bool(medicinal_docs) or _has_category(
        safety_docs,
        {"medicinal", "medicinal_use", "traditional_use"},
    )

    has_toxicity_evidence = _has_category(
        safety_docs,
        _TOXIC_CATEGORIES,
    ) or _has_category(
        medicinal_docs,
        _TOXIC_CATEGORIES,
    )

    if has_medicinal_evidence and has_toxicity_evidence:
        return (
            True,
            "Conflict detected: Medicinal evidence exists but toxicity "
            "concerns are also documented. Do not use without expert "
            "medical supervision.",
        )

    return False, ""


def format_safety_response(
    decision: SafetyDecision,
    safety_docs: Iterable[Any] | None = None,
    medicinal_docs: Iterable[Any] | None = None,
    plant_name: str | None = None,
) -> str:
    """Format the decision, evidence counts, and any conflict warning."""
    safety_docs = list(safety_docs or [])
    medicinal_docs = list(medicinal_docs or [])

    parts = []

    if plant_name and str(plant_name).strip():
        parts.append(f"Plant: {str(plant_name).strip()}")

    if decision.warning_message:
        parts.append(decision.warning_message)

    parts.append(
        f"Risk Level: {decision.risk_level.upper()}. "
        f"Medicinal evidence sources: {len(medicinal_docs)}. "
        f"Safety evidence sources: {len(safety_docs)}."
    )

    has_conflict, _ = check_for_conflicts(
        safety_docs,
        medicinal_docs,
    )

    if has_conflict:
        parts.append(
            "CONFLICT WARNING: Medicinal evidence exists, but toxicity "
            "concerns are also documented. Do not use without expert "
            "medical supervision."
        )

    return "\n\n".join(parts)
