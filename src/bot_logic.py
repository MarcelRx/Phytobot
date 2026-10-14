# Intelligent Fix: Inject 'nn' and 'torch' into builtins to prevent library-level NameErrors in Python 3.12
import builtins
import logging
from typing import Any, Dict, List, Tuple

import torch
import torch.nn as nn

builtins.nn = nn
builtins.torch = torch

import streamlit as st
from langchain_chroma import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_groq import ChatGroq

# Resilient Import: Try dedicated package first, fallback to community if version mismatch occurs
try:
    from langchain_tavily import TavilySearchResults
except (ImportError, ModuleNotFoundError):
    from langchain_community.tools.tavily_search import TavilySearchResults

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate

from src.config import (
    APIConfig,
    EvidenceState,
    InputMode,
    LLMConfig,
    NegativeKnowledgeConfig,
    SafetyConfig,
    SearchConfig,
    VectorDBConfig,
)
from src.evidence_logic import determine_evidence_state, get_trust_label
from src.negative_knowledge import (
    get_medicinal_metadata_filter,
    get_safety_metadata_filter,
)
from src.safety import verify_safety_disclaimer
from src.safety_decision import make_safety_decision

load_dotenv()

logger = logging.getLogger(__name__)


@st.cache_resource
def load_phytobot_resources():
    """Load and cache the resources used by Phytobot."""
    try:
        embeddings = HuggingFaceEmbeddings(model_name=VectorDBConfig.EMBEDDING_MODEL)
        vector_db = Chroma(
            persist_directory=VectorDBConfig.VECTOR_DB_PATH,
            embedding_function=embeddings,
        )
        llm = ChatGroq(
            model_name=LLMConfig.MODEL_NAME,
            groq_api_key=APIConfig.GROQ_API_KEY,
            temperature=LLMConfig.TEMPERATURE,
            timeout=APIConfig.REQUEST_TIMEOUT,
        )
        search = TavilySearchResults(
            max_results=SearchConfig.MAX_WEB_RESULTS,
            tavily_api_key=APIConfig.TAVILY_API_KEY,
        )
        return embeddings, vector_db, llm, search
    except Exception as e:
        logger.error(f"Failed to load Phytobot resources: {e}")
        raise


def retrieve_safety_evidence(vector_db, user_query: str) -> Tuple[List, str]:
    """Retrieve safety and negative evidence from the vector database."""
    try:
        safety_filter = get_safety_metadata_filter()
        retriever = vector_db.as_retriever(
            search_kwargs={
                "k": NegativeKnowledgeConfig.SAFETY_RETRIEVAL_K,
                "filter": safety_filter,
            }
        )
        safety_docs = retriever.invoke(user_query)
        safety_context = "\n".join(doc.page_content for doc in safety_docs)
        logger.info("Retrieved %s safety documents", len(safety_docs))
        return safety_docs, safety_context
    except Exception as e:
        logger.error("Safety evidence retrieval failed: %s", e)
        return [], ("Safety evidence retrieval failed. Safety could not be verified.")


def retrieve_medicinal_evidence(vector_db, user_query: str) -> Tuple[List, str]:
    """Retrieve medicinal evidence from the vector database."""
    try:
        medicinal_filter = get_medicinal_metadata_filter()
        retriever = vector_db.as_retriever(
            search_kwargs={
                "k": VectorDBConfig.RETRIEVAL_K,
                "filter": medicinal_filter,
            }
        )
        medicinal_docs = retriever.invoke(user_query)
        medicinal_context = "\n".join(doc.page_content for doc in medicinal_docs)
        logger.info("Retrieved %s medicinal documents", len(medicinal_docs))
        return medicinal_docs, medicinal_context
    except Exception as e:
        logger.error("Medicinal evidence retrieval failed: %s", e)
        return [], (
            "Medicinal evidence retrieval failed. Medicinal evidence "
            "could not be verified."
        )


def analyze_safety_risk(safety_docs: List) -> Dict[str, Any]:
    """
    Analyze retrieved safety metadata.

    This summary supports the response prompt. The deterministic decision
    itself is made by make_safety_decision().
    """
    if not safety_docs:
        return {
            "has_toxic_evidence": False,
            "risk_level": "unknown",
            "requires_warning": True,
            "safety_status": "insufficient_evidence",
        }

    has_toxic_evidence = False
    max_risk = "unknown"
    safety_status = "unknown"

    risk_priority = {
        "critical": 4,
        "high": 3,
        "moderate": 2,
        "low": 1,
        "unknown": 0,
    }

    for doc in safety_docs:
        metadata = getattr(doc, "metadata", None)
        if not isinstance(metadata, dict):
            metadata = {}

        category = metadata.get("category", "")
        risk_level = metadata.get("risk_level", "unknown")
        safety_stat = metadata.get("safety_status", "unknown")

        if not isinstance(category, str):
            category = ""
        if not isinstance(risk_level, str):
            risk_level = "unknown"
        if not isinstance(safety_stat, str):
            safety_stat = "unknown"

        category = category.strip().lower()
        risk_level = risk_level.strip().lower()
        safety_stat = safety_stat.strip().lower()

        if category in {
            "toxic_plant",
            "toxic_parts",
            "dangerous_look_alike",
        }:
            has_toxic_evidence = True

        if risk_level not in risk_priority:
            risk_level = "unknown"

        if risk_priority[risk_level] > risk_priority[max_risk]:
            max_risk = risk_level

        if safety_stat == "unsafe":
            safety_status = "unsafe"
        elif safety_stat == "caution_required" and safety_status != "unsafe":
            safety_status = "caution_required"
        elif safety_stat == "safe" and safety_status == "unknown":
            safety_status = "safe"

    requires_warning = (
        has_toxic_evidence
        or max_risk in SafetyConfig.MANDATORY_WARNING_RISKS
        or safety_status
        in {
            "unsafe",
            "caution_required",
            "unknown",
        }
    )

    return {
        "has_toxic_evidence": has_toxic_evidence,
        "risk_level": max_risk,
        "requires_warning": requires_warning,
        "safety_status": safety_status,
    }


def _enforce_deterministic_warnings(
    response_content: str,
    safety_warning: str,
    identification_warning: str,
) -> str:
    """
    Ensure required system warnings are present after LLM generation.

    Warnings are prepended only when their exact text is not already present.
    """
    if not isinstance(response_content, str):
        response_content = str(response_content)

    warnings_to_add = []

    for warning in (safety_warning, identification_warning):
        if warning and warning not in response_content:
            warnings_to_add.append(warning)

    if warnings_to_add:
        response_content = "\n\n".join(warnings_to_add) + "\n\n" + response_content

    return response_content


def get_phytobot_response(
    user_query: str,
    plant_name: str = None,
    identification_confidence: float = None,
    input_mode: InputMode = InputMode.TEXT_ONLY,
) -> Tuple[str, List]:
    """
    Generate a response using retrieval, web search, and an LLM.

    Deterministic safety decisions are applied before generation, and required
    safety and identification warnings are enforced after generation.

    Returns:
        Tuple of (response_text, internal_documents)
    """
    try:
        _, vector_db, llm, search = load_phytobot_resources()

        medicinal_docs, medicinal_context = retrieve_medicinal_evidence(
            vector_db, user_query
        )
        safety_docs, safety_context = retrieve_safety_evidence(vector_db, user_query)

        safety_analysis = analyze_safety_risk(safety_docs)

        # Keep identification confidence separate so the safety decision
        # cannot suppress the independent identification warning.
        safety_decision = make_safety_decision(
            safety_docs=safety_docs,
            medicinal_docs=medicinal_docs,
            identification_confidence=None,
            plant_name=plant_name,
        )

        evidence_state = determine_evidence_state(
            medicinal_docs,
            safety_docs,
            input_mode,
            plant_name,
        )
        trust_label = get_trust_label(evidence_state)

        internal_docs = medicinal_docs + safety_docs

        logger.info(
            "Total internal documents retrieved: %s",
            len(internal_docs),
        )
        logger.info(
            "Evidence state: %s, Trust label: %s",
            evidence_state.value,
            trust_label,
        )
        logger.info(
            "Deterministic safety decision: is_safe=%s, "
            "requires_warning=%s, risk_level=%s",
            safety_decision.is_safe,
            safety_decision.requires_warning,
            safety_decision.risk_level,
        )

        # Web search is supplemental evidence, not a replacement for
        # explicit safety verification from the internal safety evidence.
        web_context = ""
        web_search_performed = False

        try:
            web_results = search.invoke(user_query)
            web_context = str(web_results)
            web_search_performed = True
            logger.info("Web search completed successfully")
        except Exception as e:
            logger.warning("Web search failed: %s", e)
            web_context = "Web search currently unavailable."

        if (
            evidence_state == EvidenceState.NO_RELEVANT_EVIDENCE
            and web_search_performed
        ):
            evidence_state = EvidenceState.WEB_ONLY_EVIDENCE
            trust_label = get_trust_label(evidence_state)

        # Use the deterministic decision as the authoritative warning.
        safety_warning = ""
        if safety_decision.requires_warning:
            safety_warning = safety_decision.warning_message

        # Keep identification uncertainty independent of safety retrieval.
        identification_warning = ""
        if (
            identification_confidence is not None
            and identification_confidence
            < SafetyConfig.IDENTIFICATION_CONFIDENCE_THRESHOLD
        ):
            identification_warning = (
                "IDENTIFICATION WARNING: Plant identification confidence "
                f"is low ({identification_confidence:.1%}). Do not rely on "
                "this identification for medicinal use."
            )

        plant_identification_section = ""

        if input_mode == InputMode.TEXT_ONLY:
            plant_identification_section = (
                "### Plant Identification\n"
                "No plant identification was performed (text-only query)."
            )
        elif input_mode in (
            InputMode.IMAGE_ONLY,
            InputMode.IMAGE_AND_TEXT,
        ):
            if plant_name:
                plant_identification_section = (
                    f"### Plant Identification\nIdentified: {plant_name}"
                )
                if identification_confidence is not None:
                    plant_identification_section += (
                        f" (confidence: {identification_confidence:.1%})"
                    )
            else:
                plant_identification_section = (
                    "### Plant Identification\n"
                    "No specific plant was identified from the image."
                )

        prompt = ChatPromptTemplate.from_template(
            """
You are Phytobot, a scientific herbalism assistant with a strong focus on
plant safety.

User Question: {question}

{plant_info}

CRITICAL SAFETY RULES:
- Never infer medicinal safety from plant identification alone.
- Never ignore retrieved toxicity information.
- Do not convert traditional use into evidence of safety.
- Clearly distinguish established evidence from traditional use.
- When evidence conflicts, explicitly report the conflict.
- When identification is uncertain, say so.
- Do not invent toxicity information.
- Do not invent preparation instructions when source evidence is absent.
- If toxic evidence is found, prioritize safety warnings over medicinal claims.
- Missing safety evidence does not mean that a plant is safe.
- Do not claim that a plant is verified safe unless the retrieved evidence
  explicitly supports that status.
- Treat system safety and identification warnings as mandatory.

Structure your answer in these blocks:

{plant_identification_section}

### Safety Status
Based on the retrieved evidence, indicate documented safety status,
toxicity concerns, dangerous plant parts, insufficient evidence, or
identification uncertainty. Do not overstate what the evidence establishes.

### Verified WHO/Encyclopedia Data ({trust_label})
Use internal medicinal data. If no relevant data is found, say:
'No specific match in our medical library for this query.'

### Safety Evidence ({trust_label})
Use internal safety data. Report toxicity, dangerous parts,
contraindications, and warnings found. If no safety evidence was found,
state that explicitly.

### Internet Research & Traditional Use
Summarize web research separately from authoritative medical evidence.
Clearly distinguish traditional use from verified safety evidence.
Do not provide preparation instructions when the evidence does not
support doing so safely.

### Safety & Disclaimer
List relevant documented side effects or interactions. End with:
'Not a substitute for medical advice.'

MEDICINAL DATA:
{medicinal_context}

SAFETY DATA:
{safety_context}

INTERNET DATA:
{web_context}

SYSTEM SAFETY WARNING:
{safety_warning}

SYSTEM IDENTIFICATION WARNING:
{identification_warning}
"""
        )

        chain = prompt | llm
        response = chain.invoke(
            {
                "question": user_query,
                "plant_info": (
                    f"Plant Name: {plant_name}"
                    if plant_name
                    else "Plant Name: Not provided"
                ),
                "plant_identification_section": (plant_identification_section),
                "trust_label": trust_label,
                "medicinal_context": medicinal_context,
                "safety_context": safety_context,
                "web_context": web_context,
                "safety_warning": safety_warning,
                "identification_warning": identification_warning,
            }
        )

        # First enforce the standard medical disclaimer.
        response_content = verify_safety_disclaimer(response.content)

        # Then enforce deterministic warnings independently of the LLM.
        response_content = _enforce_deterministic_warnings(
            response_content=response_content,
            safety_warning=safety_warning,
            identification_warning=identification_warning,
        )

        return response_content, internal_docs

    except Exception as e:
        error_str = str(e)

        if (
            "model_not_found" in error_str
            or "does not exist" in error_str
            or "404" in error_str
        ):
            logger.error(
                "Groq model not found or unavailable: %s",
                LLMConfig.MODEL_NAME,
            )
        elif "401" in error_str or "authentication" in error_str.lower():
            logger.error("Groq API authentication failed")
        elif "429" in error_str or "rate limit" in error_str.lower():
            logger.error("Groq API rate limit exceeded")
        else:
            logger.error(
                "Critical error in get_phytobot_response: %s",
                e,
            )

        error_message = (
            "I apologize, but I encountered an error processing your request. "
            "Please try again later."
        )
        return error_message, []
