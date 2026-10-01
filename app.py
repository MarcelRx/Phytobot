import logging
import os
import sys

import streamlit as st

from src.bot_logic import get_phytobot_response
from src.config import VectorDBConfig
from src.validation import validate_image_file, validate_text_input
from src.vision_module import identify_plant

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Startup verification: Check vector database exists
# Skip if BUILDING_VECTOR_DB is set (for Docker build context)
if not os.getenv("BUILDING_VECTOR_DB"):
    vector_db_path = VectorDBConfig.VECTOR_DB_PATH
    if not os.path.exists(vector_db_path):
        error_msg = f"Startup Error: Vector database not found at {vector_db_path}. Please run 'python src/processor.py' to build it."
        logger.error(error_msg)
        print(error_msg, file=sys.stderr)
        sys.exit(1)

    logger.info(f"Vector database found at {vector_db_path}")

# Page Config
st.set_page_config(page_title="Phytobot 🌿", layout="wide", page_icon="🌿")
st.title("Phytobot: Your AI Herbalist 🌿")

# Initialize session state for the chat input
if "query_value" not in st.session_state:
    st.session_state.query_value = ""

tab1, tab2 = st.tabs(["Identify Plant", "Symptom & Recipe Expert"])

with tab1:
    uploaded_file = st.file_uploader(
        "Upload a plant photo", type=["jpg", "png", "jpeg"]
    )
    if uploaded_file:
        st.image(uploaded_file, width=300)
        if st.button("Identify & Analyze"):
            # Validate image
            is_valid, error_msg = validate_image_file(uploaded_file)
            if not is_valid:
                st.error(error_msg)
                logger.warning(f"Image validation failed: {error_msg}")
            else:
                # Use session state to prevent duplicate API calls on reruns
                file_key = f"identified_{uploaded_file.name}_{uploaded_file.size}"
                if file_key not in st.session_state:
                    with open("temp.jpg", "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    name, score, result_type = identify_plant("temp.jpg")
                    st.session_state[file_key] = (name, score, result_type)
                else:
                    name, score, result_type = st.session_state[file_key]
                    logger.info(
                        f"Using cached identification result for {uploaded_file.name}"
                    )

                if result_type.value == "blurry_image":
                    st.error(
                        f"PHOTO ALERT: Too blurry (Score: {score:.1f}). Please steady your hand and try again."
                    )
                    logger.info(f"Blurry image detected (score: {score:.1f})")
                elif result_type.value == "success" and name:
                    st.success(f"Identified: {name} ({score:.1%})")
                    with st.spinner(
                        "Retrieving medicinal profile and safety information..."
                    ):
                        ans, _ = get_phytobot_response(
                            f"Scientific profile and safety of {name}",
                            plant_name=name,
                            identification_confidence=score,
                        )
                        st.markdown(ans)
                        logger.info(f"Successfully retrieved profile for {name}")
                elif result_type.value == "not_a_plant":
                    st.warning(
                        "This image does not appear to contain a plant. Please try a different photo."
                    )
                    logger.info("Image identified as not a plant")
                elif result_type.value == "rate_limit":
                    st.warning(
                        "Plant identification is temporarily unavailable because the identification service is rate-limited. Please try again later."
                    )
                    logger.warning("Plant identification failed due to rate limiting")
                elif result_type.value == "auth_error":
                    st.error(
                        "Plant identification service authentication failed. Please contact support."
                    )
                    logger.error(
                        "Plant identification failed due to authentication error"
                    )
                elif result_type.value in ("network_error", "timeout"):
                    st.warning(
                        "Plant identification service is temporarily unavailable due to network issues. Please try again later."
                    )
                    logger.warning(
                        f"Plant identification failed due to {result_type.value}"
                    )
                else:
                    st.warning("Could not identify. Try a closer shot of the leaves.")
                    logger.warning("Plant identification failed")

with tab2:
    st.markdown("### How can I help you today?")

    # Suggestion Buttons
    cols = st.columns(3)
    if cols[0].button("Recipe for Sleep"):
        st.session_state.query_value = "How do I make a tea for better sleep?"
    if cols[1].button("Help with Cough"):
        st.session_state.query_value = "What herbs help with a dry cough?"
    if cols[2].button("Learn about Ginger"):
        st.session_state.query_value = (
            "Tell me the benefits and side effects of Ginger."
        )

    user_msg = st.text_input(
        "Describe symptoms, ask for a recipe, or learn about a plant:",
        value=st.session_state.query_value,
    )

    if user_msg:
        # Validate text input
        is_valid, error_msg = validate_text_input(user_msg)
        if not is_valid:
            st.error(error_msg)
            logger.warning(f"Text validation failed: {error_msg}")
        else:
            with st.spinner("Consulting WHO Database & Internet..."):
                ans, docs = get_phytobot_response(user_msg)
                st.markdown(ans)
                with st.expander("View PDF Sources"):
                    for d in docs:
                        st.caption(
                            f"Source: {d.metadata.get('source')} | Page: {d.metadata.get('page', 'N/A')}"
                        )
                logger.info(
                    f"Processed query successfully, retrieved {len(docs)} sources"
                )

st.sidebar.warning(
    "Disclaimer: This is an educational tool. Herbal remedies can interact with medications. Always consult a doctor."
)
