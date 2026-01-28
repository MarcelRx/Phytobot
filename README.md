# 🌿 Phytobot
An intelligent educational chatbot for identifying medicinal plants and providing scientific information based on WHO monographs and the Encyclopedia of Herbal Medicine.

## Features
- **Plant Identification**: High-accuracy plant identification through image uploads using computer vision.
- **RAG System**: Information extraction from an internal database (WHO & Encyclopedia) using Vector Search to prevent AI hallucinations.
- **Medical Safety**: Strict adherence to safety protocols with mandatory medical disclaimers in every response.
- **Source Citations**: Direct transparency by providing PDF source names and page numbers for scientific validation.
- **Auto-Screenshot**: Automatically saves identification results for documentation and project tracking.

## Project Structure
- `data/`: Directory for PDF reference files (WHO/Encyclopedia).
- `src/`: Core logic containing:
    - `processor.py`: PDF parsing and vector database creation.
    - `vision_module.py`: Plant.id API integration.
    - `bot_logic.py`: LangChain RAG logic and Llama 3 integration.
- `app.py`: Streamlit interactive user interface.
- `screenshots/`: Automated storage for identification history.

## Installation and Usage
1. **Activate virtual environment**:
   ```bash
   source venv/bin/activate
