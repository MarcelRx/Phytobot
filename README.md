# Phytobot 🌿

**AI-Powered Botanical Pharmacist & Plant Identifier**

Phytobot uses Llama 3.1 and RAG (Retrieval-Augmented Generation) to identify medicinal plants and provide verified recipes from the WHO and botanical encyclopedias.

## Features

- **Vision ID:** Automatic identification with a "Blur Alarm" to ensure quality.
- **Smart Fallback:** Searches the internet via Tavily if local PDFs don't have the answer.
- **Safety Layer:** Dedicated negative knowledge base for toxic plants and safety warnings.
- **Dual Retrieval:** Separate retrieval of medicinal evidence and safety evidence.
- **Deterministic Safety Logic:** Mandatory warnings for toxic plants and dangerous look-alikes.
- **Trust Levels:** Clear distinction between authoritative evidence and traditional use.
- **Medical Disclaimers:** Automatic safety disclaimers on all responses.

## Safety Architecture

Phytobot implements a multi-layered safety system:

### Negative Knowledge Base

- **Location:** `data/negative/`
- **Contents:** Structured JSON files with authoritative toxic plant information
- **Sources:** USDA, WHO, National Poisons Information Service, European Medicines Agency, and other authoritative organizations
- **Categories:**
  - Toxic plants (e.g., Oleander, Foxglove, Poison Hemlock)
  - Plants with toxic parts (e.g., Rhubarb leaves, Potato sprouts)
  - Dangerous look-alikes (e.g., Wild Carrot vs Poison Hemlock)

### Safety Decision Layer

- **Identification ≠ Safety:** Plant identification confidence is not used as a safety score
- **Mandatory Warnings:** Critical and high-risk plants trigger mandatory safety warnings
- **Uncertainty Preference:** System prefers stating uncertainty over making unsafe assumptions
- **Conflict Detection:** Identifies conflicts between medicinal and toxicity evidence

### Response Structure

1. **Plant Identification:** Plant name and confidence level
2. **Safety Status:** Documented safe/medicinal use, toxicity concern, or insufficient evidence
3. **Verified WHO/Encyclopedia Data:** Authoritative medicinal information
4. **Safety Evidence:** Toxicity information, dangerous parts, contraindications
5. **Internet Research & Traditional Use:** Clearly distinguished from authoritative evidence
6. **Safety & Disclaimer:** Required medical disclaimer

## Setup

### Local Development

1. **Clone the repo:** `git clone https://github.com/MarcelRx/Phytobot.git`
2. **Install dependencies:** `pip install -r requirements.txt`
3. **Set up .env:** Copy `.env.example` to `.env` and add your API keys:
   - `GROQ_API_KEY`: Your Groq API key for Llama 3.1
   - `PLANTID_API_KEY`: Your Plant.id API key for plant identification
   - `TAVILY_API_KEY`: Your Tavily API key for web search
   - `VECTOR_DB_PATH`: Path to store vector database (default: `./vector_db`)
4. **Create vector database:** `python3 src/processor.py`
   - This processes PDF files from `data/` and negative knowledge from `data/negative/`
5. **Run the app:** `streamlit run app.py`

### Production Deployment

Phytobot is deployed to **Streamlit Community Cloud** directly from GitHub.

#### Deployment Architecture

```
GitHub Repository
        ↓
Streamlit Community Cloud
        ↓
Live Phytobot
```

#### GitHub Actions CI

The `.github/workflows/deploy.yml` workflow:

1. **Test Gate**: Runs `pytest -q` on every push and pull request
2. **Quality Gate**: Blocks if tests fail
3. **No deployment**: Deployment is handled by Streamlit Community Cloud, not GitHub Actions

#### Streamlit Community Cloud Deployment

1. **Prepare GitHub Repository**
   - Ensure your code is pushed to GitHub
   - The repository includes:
     - `app.py` (entrypoint)
     - `requirements.txt` (dependencies)
     - `data/` (knowledge base PDFs)
     - `data/negative/` (safety knowledge)
     - `vector_db/` (pre-built vector database)

2. **Connect to Streamlit Community Cloud**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Click "New app"
   - Sign in with your GitHub account
   - Authorize Streamlit to access your repositories

3. **Select Repository**
   - Choose the Phytobot repository
   - Select the `main` branch
   - Select `app.py` as the main file

4. **Configure Secrets**
   In the Streamlit Community Cloud app settings, add these secrets:
   - `GROQ_API_KEY`: Your Groq API key for Llama 3.1
   - `PLANTID_API_KEY`: Your Plant.id API key for plant identification
   - `TAVILY_API_KEY`: Your Tavily API key for web search
   - `VECTOR_DB_PATH`: `./vector_db` (default, can be omitted)

5. **Deploy**
   - Click "Deploy"
   - Streamlit will install dependencies from `requirements.txt`
   - The vector database is already included in the repository
   - The app will start automatically

#### Vector Database Strategy

The repository includes a **pre-built vector database** (`vector_db/`):

- Committed to the repository for reliable Streamlit Community Cloud deployment
- Includes all PDF knowledge from `data/` (WHO monographs, herbal encyclopedia)
- Includes negative knowledge from `data/negative/` (toxic plants, safety data)
- No build step required at deployment time
- Fast, reliable startup

**To rebuild the vector database** (after updating knowledge base):

```bash
python src/processor.py
git add vector_db/
git commit -m "Update vector database"
git push
```

#### Optional: Docker Deployment (Local/Alternative)

Docker can be used for local development or alternative deployment platforms.

**Build locally:**

```bash
docker build -t phytobot .
```

**Run with environment variables:**

```bash
docker run -d \
  -p 8501:8501 \
  -e GROQ_API_KEY=your_key \
  -e PLANTID_API_KEY=your_key \
  -e TAVILY_API_KEY=your_key \
  phytobot
```

Docker is not required for the primary Streamlit Community Cloud deployment.

#### Application Startup

The application performs startup verification:

- Checks for required API keys (GROQ_API_KEY, PLANTID_API_KEY, TAVILY_API_KEY)
- Verifies vector database exists at `VECTOR_DB_PATH`
- Fails clearly with descriptive error messages if configuration is missing
- Exposes health check endpoint at `/_stcore/health`

## Testing

Run the test suite:

```bash
pytest -q
```

The test suite includes:

- Phase 1 regression tests (existing functionality)
- Phase 2 safety decision tests (8 comprehensive safety scenarios)
- Negative knowledge loading tests
- Conflict detection tests

## Limitations

### Safety Limitations

- **Not Exhaustive:** The negative knowledge base is not exhaustive. Always err on the side of caution.
- **Identification Errors:** Plant identification can be incorrect, especially with low confidence scores.
- **Look-alike Risks:** Many plants have dangerous look-alikes that require expert verification.
- **Preparation Methods:** The system does not provide preparation instructions unless explicitly documented in authoritative sources.
- **Individual Variability:** Individual reactions to plants can vary widely.

### Technical Limitations

- **API Dependencies:** Requires internet access for Plant.id and Tavily APIs.
- **Image Quality:** Blurry or poor-quality images will be rejected.
- **Vector Database:** Must be rebuilt when knowledge base is updated.

### Evidence Quality

- **Authoritative vs Traditional:** System clearly distinguishes between WHO/encyclopedia data (100% trust) and internet/traditional use (50% trust).
- **Traditional Use ≠ Safety:** Historical or traditional use does not imply safety.
- **Insufficient Evidence:** When evidence is insufficient, the system explicitly states this rather than making assumptions.

## Medical Disclaimer

This software is for educational purposes only. It is NOT a substitute for professional medical advice. Always consult a doctor before using herbal remedies.

**Critical Safety Notes:**

- Never use plants identified as toxic or with high toxicity warnings
- Do not rely on plant identification with low confidence (<70%)
- Expert verification is required for plants with dangerous look-alikes
- This system cannot guarantee plant safety or accurate identification
