import streamlit as st
import os
from src.vision_module import identify_plant
from src.bot_logic import get_phytobot_response

# Page Config
st.set_page_config(
    page_title="Phytobot AI",
    page_icon="🌿",
    layout="centered"
)

# Custom CSS
st.markdown("""
<style>
.stMainBlockContainer {
    padding-bottom: 120px !important;
}
footer {visibility: hidden;}
header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# Session State
if "messages" not in st.session_state:
    st.session_state.messages = []
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0

# Header
st.title("🌿 Phytobot")
st.caption("Herbal Medicine Intelligent Assistant")
st.divider()

# Chat History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("trust_info"):
            st.info(msg["trust_info"])
        if msg.get("sources"):
            with st.expander("Sources (Internal Database)"):
                for doc in msg["sources"]:
                    src = os.path.basename(
                        doc.metadata.get("source", "Database")
                    )
                    page = doc.metadata.get("page", "N/A")
                    st.write(f"📖 {src} — Page {page}")

# Sidebar
with st.sidebar:
    st.header("Attachments")
    img_file = st.file_uploader(
        "Upload plant photo",
        type=["jpg", "png", "jpeg"],
        key=f"u_{st.session_state.uploader_key}"
    )

# Chat Input
user_text = st.chat_input("Ask about a medicinal plant...")

# Main Logic
if user_text or img_file:

    with st.chat_message("user"):
        if img_file:
            st.image(img_file, width=200)
        if user_text:
            st.markdown(user_text)

    st.session_state.messages.append({
        "role": "user",
        "content": user_text if user_text else "Image uploaded"
    })

    with st.chat_message("assistant"):
        with st.spinner("Analyzing..."):

            query = user_text if user_text else "Identify this plant."
            trust_info = ""

            if img_file:
                temp_path = f"./temp_{st.session_state.uploader_key}.png"
                with open(temp_path, "wb") as f:
                    f.write(img_file.getbuffer())

                plant_name, prob = identify_plant(temp_path)

                if plant_name:
                    query = f"Medicinal uses of {plant_name}. {user_text or ''}"
                    trust_info = (
                        f"{plant_name} identified with {prob:.1%} confidence"
                    )

            response_gen, docs, source_type = get_phytobot_response(query)

            st.markdown(f"**Source Type:** {source_type}")
            full_answer = st.write_stream(response_gen)

            if trust_info:
                st.success(f"🌿 {trust_info}")

    st.session_state.messages.append({
        "role": "assistant",
        "content": full_answer,
        "sources": docs,
        "trust_info": trust_info
    })

    if img_file:
        st.session_state.uploader_key += 1
        st.rerun()
