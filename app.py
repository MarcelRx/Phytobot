import streamlit as st
import datetime
from src.vision_module import identify_plant
from src.bot_logic import get_phytobot_response

# Set Streamlit page configuration
st.set_page_config(page_title="Phytobot", page_icon="")

# Create main title and header
st.title("Phytobot")
st.subheader("Herbal Medicine Intelligent Assistant (Based on WHO)")

# Create tab layout for different functionalities
tab1, tab2 = st.tabs(["Image Identification", "Chat & Questions"])

with tab1:
    # Create image upload interface
    uploaded_file = st.file_uploader("Upload plant image here", type=['jpg', 'png', 'jpeg'])
    if uploaded_file:
        # Display uploaded image
        st.image(uploaded_file, width=300)
        if st.button("Analyze Plant"):
            # Generate timestamp-based filename to prevent overwriting
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = f"./screenshots/ident_{timestamp}.jpg"
            
            # Save uploaded file with timestamp
            with open(screenshot_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # Save a static copy for README (optional)
            with open("./screenshots/detection_example.png", "wb") as f:
                f.write(uploaded_file.getbuffer())

            # Identify plant using saved image
            name, prob = identify_plant(screenshot_path)
            
            # Check if plant was identified
            if name:
                # Display warning if confidence is below 40%
                if prob < 0.40:
                    st.warning(f"Low confidence: {prob:.2%}. Please ensure the photo is clear and taken in good light.")
                else:
                    st.success(f"Plant identified: {name} (Accuracy: {prob:.2%})")
                
                # Generate query based on identified plant
                query = f"Provide detailed medicinal info about {name} from the database."
                response, _ = get_phytobot_response(query)
                # Display medicinal information
                st.markdown(response)
            else:
                st.error("Sorry, plant could not be identified. Please try a different angle.")

with tab2:
    # Create chat interface
    user_msg = st.text_input("Ask your question (e.g., What are the benefits of aloe vera?)")
    if user_msg:
        # Process user query with loading indicator
        with st.spinner("Searching trusted sources..."):
            ans, docs = get_phytobot_response(user_msg)
            st.write(ans)
            # Display source documents in expandable section
            with st.expander("View extracted sources"):
                for doc in docs:
                    st.caption(f"Source: {doc.metadata['source']} - Page: {doc.metadata.get('page', 'Unknown')}")

# Display disclaimer in sidebar
st.sidebar.warning("Disclaimer: This information is for educational purposes only.")