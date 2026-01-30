# Phytobot 🌿 
**AI-Powered Botanical Pharmacist & Plant Identifier**

Phytobot uses Llama 3.1 and RAG (Retrieval-Augmented Generation) to identify medicinal plants and provide verified recipes from the WHO and botanical encyclopedias.

### Features
* **Vision ID:** Automatic identification with a "Blur Alarm" to ensure quality.
* **Smart Fallback:** Searches the internet via Tavily if local PDFs don't have the answer.
* **Chat Logs:** Automatically records interactions for performance analysis.
* **Safety First:** Clear trust scores and medical disclaimers.

### Setup
1. **Clone the repo:** `git clone <your-link>`
2. **Install dependencies:** `pip install -r requirements.txt`
3. **Set up .env:** Add your `GROQ_API_KEY`, `TAVILY_API_KEY`, and `PLANTID_API_KEY`.
4. **Run the app:** `streamlit run app.py`

### Medical Disclaimer
This software is for educational purposes only. It is NOT a substitute for professional medical advice. Always consult a doctor before using herbal remedies.
