import streamlit as st
from src.bot_logic import get_phytobot_response

st.title("🌿 Phytobot")
query = st.text_input("Ask about medicinal plants:")

if query:
    response, sources = get_phytobot_response(query)
    st.write(response)
    st.caption(f"Sources: {len(sources)}")