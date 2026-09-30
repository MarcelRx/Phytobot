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

Phytobot uses Docker for production deployment with automated CI/CD via GitHub Actions.

#### GitHub Actions CI/CD

The `.github/workflows/deploy.yml` workflow:

1. **Test Gate**: Runs `pytest -q` on every push and pull request
2. **Build & Push**: On successful tests to `main` branch, builds and pushes Docker image to Docker Hub
3. **Deployment is blocked** if tests fail

#### Required GitHub Secrets/Variables

Configure these in your GitHub repository settings (Settings → Secrets and variables → Actions):

**Docker Hub:**

- `DOCKER_USERNAME`: Your Docker Hub username
- `DOCKER_PASSWORD`: Your Docker Hub password or access token

**Application Secrets** (set as environment variables in your deployment platform):

- `GROQ_API_KEY`: Groq API key for Llama 3.1
- `PLANTID_API_KEY`: Plant.id API key for plant identification
- `TAVILY_API_KEY`: Tavily API key for web search
- `VECTOR_DB_PATH`: Path to vector database (default: `./vector_db`)

#### Vector Database Strategy

The production Docker image includes a **pre-built vector database**:

- Built during `docker build` using `python src/processor.py`
- Includes all PDF knowledge from `data/` (WHO monographs, herbal encyclopedia)
- Includes negative knowledge from `data/negative/` (toxic plants, safety data)
- Embedded in the image for fast, reliable startup
- No persistent storage dependency required

#### Docker Deployment

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

**Or pull from Docker Hub (after CI/CD push):**

```bash
docker run -d \
  -p 8501:8501 \
  -e GROQ_API_KEY=your_key \
  -e PLANTID_API_KEY=your_key \
  -e TAVILY_API_KEY=your_key \
  yourusername/phytobot:latest
```

#### Cloud Deployment Options

The Docker image can be deployed to:

- **Render**: Create a new Web Service, connect Docker Hub repository
- **Railway**: New Project → Deploy from Docker Registry
- **AWS ECS/Fargate**: Use Docker Hub image
- **Google Cloud Run**: Deploy container from Docker Hub
- **Azure Container Instances**: Deploy Docker Hub image

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
