import streamlit as st
from src.vision_module import identify_plant
from src.bot_logic import get_phytobot_response

st.set_page_config(page_title="Phytobot", page_icon="")

st.title("Phytobot")
st.subheader("Herbal Medicine Intelligent Assistant (Based on WHO)")

tab1, tab2 = st.tabs(["Image Identification", "Chat & Questions"])

with tab1:
    uploaded_file = st.file_uploader("Upload plant image here", type=['jpg', 'png', 'jpeg'])
    if uploaded_file:
        st.image(uploaded_file, width=300)
        if st.button("Analyze Plant"):
            with open("temp.jpg", "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            name, prob = identify_plant("temp.jpg")
            if name:
                st.success(f"Plant identified: {name} (Accuracy: {prob:.2%})")
                query = f"Provide detailed medicinal info about {name} from the database."
                response, _ = get_phytobot_response(query)
                st.markdown(response)
            else:
                st.error("Sorry, plant could not be identified.")

with tab2:
    user_msg = st.text_input("Ask your question (e.g., What are the benefits of aloe vera?)")
    if user_msg:
        with st.spinner("Searching trusted sources..."):
            ans, docs = get_phytobot_response(user_msg)
            st.write(ans)
            with st.expander("View extracted sources"):
                for doc in docs:
                    st.caption(f"Source: {doc.metadata['source']} - Page: {doc.metadata.get('page', 'Unknown')}")

st.sidebar.warning("Disclaimer: This information is for educational purposes only.")