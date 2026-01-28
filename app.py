import streamlit as st
import os
import datetime
from src.vision_module import identify_plant
from src.bot_logic import get_phytobot_response

# Set initial page settings
st.set_page_config(page_title="Phytobot", page_icon="🌿", layout="centered")

# Ensure screenshot folder exists
if not os.path.exists("./screenshots"):
    os.makedirs("./screenshots")

# Create main title and header
st.title("🌿 Phytobot")
st.subheader("Herbal Medicine Intelligent Assistant")
st.markdown("---")

# Create tab layout for different functionalities
tab1, tab2 = st.tabs(["Identification", "Expert Chat"])

with tab1:
    st.header("Plant Identification")
    # Create image upload interface
    uploaded_file = st.file_uploader("Upload a clear photo of the plant", type=['jpg', 'png', 'jpeg'])
    
    if uploaded_file:
        # Display uploaded image
        st.image(uploaded_file, caption="Uploaded Image", width=300)
        
        if st.button("Identify & Analyze"):
            # Save image with timestamp for archive and demo
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            temp_path = f"./screenshots/ident_{ts}.png"
            
            # Save static file for README display (optional)
            readme_demo_path = "./screenshots/detection_example.png"
            
            # Get file bytes and save to both paths
            file_bytes = uploaded_file.getbuffer()
            with open(temp_path, "wb") as f:
                f.write(file_bytes)
            with open(readme_demo_path, "wb") as f:
                f.write(file_bytes)
                
            # Analyze image with loading indicator
            with st.spinner("Analyzing image..."):
                name, prob = identify_plant(temp_path)
                
                # Check if plant was identified
                if name:
                    # Display warning if confidence is low
                    if prob < 0.40:
                        st.warning(f"Low confidence: {prob:.2%}. Please check if the plant matches: {name}")
                    else:
                        st.success(f"Identified as: {name} ({prob:.2%})")
                    
                    # Automatically call RAG for scientific information
                    query = f"Provide detailed medicinal info about {name} from the database."
                    response, _ = get_phytobot_response(query)
                    st.info("Scientific Information (from WHO/Encyclopedia):")
                    st.markdown(response)
                else:
                    st.error("Could not identify the plant. Try another photo.")

with tab2:
    st.header("Ask Phytobot")
    # Create chat interface with example
    user_msg = st.text_input("Example: What is ginger used for?")
    
    if user_msg:
        # Process user query with loading indicator
        with st.spinner("Searching trusted sources..."):
            ans, docs = get_phytobot_response(user_msg)
            st.markdown(ans)
            
            # Display extracted document sources
            with st.expander("View Document Sources"):
                for doc in docs:
                    filename = os.path.basename(doc.metadata.get('source', 'Unknown'))
                    page = doc.metadata.get('page', 'N/A')
                    st.caption(f"File: {filename} | Page: {page}")

# Display disclaimer in sidebar
st.sidebar.markdown("### Disclaimer")
st.sidebar.warning("This tool is for educational purposes only. Always consult a healthcare professional before using herbal remedies.")