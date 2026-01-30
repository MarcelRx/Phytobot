import streamlit as st
from src.vision_module import identify_plant
from src.bot_logic import get_phytobot_response

# Page Config
st.set_page_config(page_title="Phytobot 🌿", layout="wide", page_icon="🌿")
st.title("Phytobot: Your AI Herbalist 🌿")

# Initialize session state for the chat input
if 'query_value' not in st.session_state:
    st.session_state.query_value = ""

tab1, tab2 = st.tabs(["Identify Plant", "Symptom & Recipe Expert"])

with tab1:
    uploaded_file = st.file_uploader("Upload a plant photo", type=['jpg','png','jpeg'])
    if uploaded_file:
        st.image(uploaded_file, width=300)
        if st.button("Identify & Analyze"):
            with open("temp.jpg", "wb") as f: f.write(uploaded_file.getbuffer())
            name, score = identify_plant("temp.jpg")
            
            if name == "BLURRY_IMAGE":
                st.error(f"PHOTO ALERT: Too blurry (Score: {score:.1f}). Please steady your hand and try again.")
            elif name:
                st.success(f"Identified: {name} ({score:.1%})")
                with st.spinner("Retrieving medicinal profile..."):
                    ans, _ = get_phytobot_response(f"Scientific profile and safety of {name}")
                    st.markdown(ans)
            else:
                st.warning("Could not identify. Try a closer shot of the leaves.")

with tab2:
    st.markdown("### 🍵 How can I help you today?")
    
    # Suggestion Buttons
    cols = st.columns(3)
    if cols[0].button("Recipe for Sleep"): st.session_state.query_value = "How do I make a tea for better sleep?"
    if cols[1].button("Help with Cough"): st.session_state.query_value = "What herbs help with a dry cough?"
    if cols[2].button("Learn about Ginger"): st.session_state.query_value = "Tell me the benefits and side effects of Ginger."

    user_msg = st.text_input("Describe symptoms, ask for a recipe, or learn about a plant:", value=st.session_state.query_value)

    if user_msg:
        with st.spinner("Consulting WHO Database & Internet..."):
            ans, docs = get_phytobot_response(user_msg)
            st.markdown(ans)
            with st.expander("View PDF Sources"):
                for d in docs:
                    st.caption(f"Source: {d.metadata.get('source')} | Page: {d.metadata.get('page','N/A')}")

st.sidebar.warning("Disclaimer: This is an educational tool. Herbal remedies can interact with medications. Always consult a doctor.")