# Phytobot
An intelligent educational chatbot for identifying medicinal plants and providing scientific information based on WHO monographs.

## Features
- Plant identification through images.
- Information extraction from internal database (WHO & Encyclopedia).
- Adherence to safety protocols and medical disclaimer.
- the project has the ability to extract information from the Encyclopedia of has herbal medicine.

## Project Structure
- `data/`: Directory for PDF reference files.
- `src/`: Core project logic code.
- `app.py`: Streamlit user interface.

## Installation and Usage
1. Activate virtual environment: `source venv/bin/activate`
2. Install dependencies: `pip install -r requirements.txt`
3. Run the application: `streamlit run app.py`

## License
This project is released under the MIT License.

## Technical Challenges & Solutions

- Challenge: Low-quality images leading to false identifications.
  - Solution: Implemented an accuracy threshold (40%) that warns users if the identification confidence is low.
  
- Challenge: Handling large PDF files for real-time chat.
  - Solution: Used LangChain's `RecursiveCharacterTextSplitter` to create optimal chunks and ChromaDB for high-speed vector search.
  
- Challenge: Ensuring medical safety.
  - Solution: Engineered specific prompts to force the LLM to include medical disclaimers and cite specific sources from the internal database.

 
## Screenshots

### Plant Identification
- Phytobot accurately identifies plants (even with lower confidence) and provides an immediate summary.
- [Plant Identification Example](./screenshots/detection_example.png)!

### Expert Chat & RAG System
- The chatbot retrieves specific medicinal advice from the WHO and Encyclopedia database, including source citations and page numbers.
- [Chatbot RAG Example](./screenshots/chat_example.png)!
