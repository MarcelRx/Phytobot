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
    LLMConfig,
    NegativeKnowledgeConfig,
    SafetyConfig,
    SearchConfig,
    VectorDBConfig,
)
from src.negative_knowledge import (
    get_medicinal_metadata_filter,
    get_safety_metadata_filter,
)
from src.safety import verify_safety_disclaimer

load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)


@st.cache_resource
def load_phytobot_resources():
    """
    Standardized resource loader.
    Using st.cache_resource ensures models are only loaded into memory once.
    """
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
    """
    Retrieve safety/negative evidence from vector database.

    Args:
        vector_db: Chroma vector database instance
        user_query: The user's query

    Returns:
        Tuple of (safety_documents, safety_context)
    """
    try:
        safety_filter = get_safety_metadata_filter()
        retriever = vector_db.as_retriever(
            search_kwargs={
                "k": NegativeKnowledgeConfig.SAFETY_RETRIEVAL_K,
                "filter": safety_filter,
            }
        )
        safety_docs = retriever.invoke(user_query)
        safety_context = "\n".join([d.page_content for d in safety_docs])
        logger.info(f"Retrieved {len(safety_docs)} safety documents")
        return safety_docs, safety_context
    except Exception as e:
        logger.error(f"Safety evidence retrieval failed: {e}")
        return [], "Safety evidence retrieval failed."


def retrieve_medicinal_evidence(vector_db, user_query: str) -> Tuple[List, str]:
    """
    Retrieve medicinal evidence from vector database.

    Args:
        vector_db: Chroma vector database instance
        user_query: The user's query

    Returns:
        Tuple of (medicinal_documents, medicinal_context)
    """
    try:
        medicinal_filter = get_medicinal_metadata_filter()
        retriever = vector_db.as_retriever(
            search_kwargs={"k": VectorDBConfig.RETRIEVAL_K, "filter": medicinal_filter}
        )
        medicinal_docs = retriever.invoke(user_query)
        medicinal_context = "\n".join([d.page_content for d in medicinal_docs])
        logger.info(f"Retrieved {len(medicinal_docs)} medicinal documents")
        return medicinal_docs, medicinal_context
    except Exception as e:
        logger.error(f"Medicinal evidence retrieval failed: {e}")
        return [], "Medicinal evidence retrieval failed."


def analyze_safety_risk(safety_docs: List) -> Dict[str, Any]:
    """
    Analyze safety documents to determine risk level and required warnings.

    Args:
        safety_docs: List of safety documents from vector DB

    Returns:
        Dictionary with safety analysis results
    """
    if not safety_docs:
        return {
            "has_toxic_evidence": False,
            "risk_level": "unknown",
            "requires_warning": False,
            "safety_status": "insufficient_evidence",
        }

    # Check for toxic evidence
    has_toxic_evidence = False
    max_risk = "low"
    safety_status = "potential_concern"

    for doc in safety_docs:
        metadata = doc.metadata
        category = metadata.get("category", "")
        risk_level = metadata.get("risk_level", "low")
        safety_stat = metadata.get("safety_status", "unknown")

        # Check for toxic categories
        if category in ["toxic_plant", "toxic_parts", "dangerous_look_alike"]:
            has_toxic_evidence = True

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

    # Determine if warning is required
    requires_warning = (
        has_toxic_evidence
        or max_risk in SafetyConfig.MANDATORY_WARNING_RISKS
        or safety_status in ["unsafe", "caution_required"]
    )

    return {
        "has_toxic_evidence": has_toxic_evidence,
        "risk_level": max_risk,
        "requires_warning": requires_warning,
        "safety_status": safety_status,
    }


def get_phytobot_response(
    user_query: str, plant_name: str = None, identification_confidence: float = None
) -> Tuple[str, List]:
    """
    Generate a response to the user's query using RAG and web search.
    Now includes separate retrieval of medicinal and safety evidence.

    Args:
        user_query: The user's question or request
        plant_name: Optional plant name from vision module
        identification_confidence: Optional confidence score from vision module

    Returns:
        Tuple of (response_text, internal_documents)
    """
    try:
        # Retrieve cached resources
        _, vector_db, llm, search = load_phytobot_resources()

        # Separate retrieval for medicinal and safety evidence
        medicinal_docs, medicinal_context = retrieve_medicinal_evidence(
            vector_db, user_query
        )
        safety_docs, safety_context = retrieve_safety_evidence(vector_db, user_query)

        # Analyze safety risk
        safety_analysis = analyze_safety_risk(safety_docs)

        # Combine all internal documents
        internal_docs = medicinal_docs + safety_docs
        logger.info(f"Total internal documents retrieved: {len(internal_docs)}")

        # Web search
        web_context = ""
        try:
            web_results = search.invoke(user_query)
            web_context = str(web_results)
            logger.info("Web search completed successfully")
        except Exception as e:
            logger.warning(f"Web search failed: {e}")
            web_context = "Web search currently unavailable."

        # Build safety warning based on analysis
        safety_warning = ""
        if safety_analysis["requires_warning"]:
            if safety_analysis["has_toxic_evidence"]:
                safety_warning = "⚠️ SAFETY WARNING: Toxicity evidence found for this plant. Do not use for medicinal purposes without expert verification."
            elif safety_analysis["risk_level"] in SafetyConfig.MANDATORY_WARNING_RISKS:
                safety_warning = f"⚠️ SAFETY WARNING: High risk plant ({safety_analysis['risk_level']} risk level). Exercise extreme caution."
            elif safety_analysis["safety_status"] == "caution_required":
                safety_warning = "⚠️ SAFETY WARNING: This plant requires caution. Certain parts or conditions may be dangerous."

        # Check identification confidence if provided
        identification_warning = ""
        if (
            identification_confidence is not None
            and identification_confidence
            < SafetyConfig.IDENTIFICATION_CONFIDENCE_THRESHOLD
        ):
            identification_warning = f"⚠️ IDENTIFICATION WARNING: Plant identification confidence is low ({identification_confidence:.1%}). Do not rely on this identification for medicinal use."

        # Enhanced prompt with safety prioritization
        prompt = ChatPromptTemplate.from_template("""
    You are Phytobot, a scientific herbalism assistant with a strong focus on plant safety.
    User Question: {question}

    {plant_info}

    CRITICAL SAFETY RULES (Follow strictly):
    - NEVER infer medicinal safety from plant identification alone
    - NEVER ignore retrieved toxicity information
    - Do not convert "traditional use" into evidence of safety
    - Clearly distinguish established evidence from traditional use
    - When evidence conflicts, explicitly report the conflict
    - When identification is uncertain, say so
    - Do not invent toxicity information
    - Do not invent preparation instructions when source evidence is absent
    - If toxic evidence is found, prioritize safety warnings over any medicinal information

    Structure your answer in these EXACT blocks:

    ### Plant Identification
    (What plant was identified and with what confidence. If identification is uncertain, state this clearly.)

    ### Safety Status
    (Based on retrieved safety evidence, indicate: documented safe/medicinal use, toxicity concern, dangerous plant parts, insufficient evidence, or identification uncertainty.)

    ### Verified WHO/Encyclopedia Data (Trust: 100%)
    (Use INTERNAL MEDICINAL DATA. If not found, say 'No specific match in our medical library.')

    ### Safety Evidence (Trust: 100%)
    (Use INTERNAL SAFETY DATA. Report any toxicity, dangerous parts, contraindications, or warnings found. If no safety evidence found, state this explicitly.)

    ### Internet Research & Traditional Use (Trust: 50%)
    (Summarize INTERNET DATA. Clearly distinguish traditional use from authoritative evidence. Provide recipe steps or traditional uses found online only if safety evidence permits.)

    ### Safety & Disclaimer
    (List side effects or drug interactions. End with: 'Not a substitute for medical advice.')

    MEDICINAL DATA: {medicinal_context}
    SAFETY DATA: {safety_context}
    INTERNET DATA: {web_context}
    SYSTEM SAFETY WARNING: {safety_warning}
    SYSTEM IDENTIFICATION WARNING: {identification_warning}
    """)

        chain = prompt | llm
        response = chain.invoke(
            {
                "question": user_query,
                "plant_info": f"Plant Name: {plant_name}"
                if plant_name
                else "Plant Name: Not provided",
                "medicinal_context": medicinal_context,
                "safety_context": safety_context,
                "web_context": web_context,
                "safety_warning": safety_warning,
                "identification_warning": identification_warning,
            }
        )

        # Verify and enforce safety disclaimer
        response_content = verify_safety_disclaimer(response.content)

        return response_content, internal_docs

    except Exception as e:
        logger.error(f"Critical error in get_phytobot_response: {e}")
        error_message = "I apologize, but I encountered an error processing your request. Please try again later."
        return error_message, []
