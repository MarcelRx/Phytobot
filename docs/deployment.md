# Deployment

## Prerequisites and Supported Runtime Versions

### System Requirements

**Operating System**:

- Linux (Ubuntu 24.04 for CI/CD)
- macOS (tested on macOS with Python 3.12)
- Windows (not explicitly tested, but should work with Python 3.12)

**Python Version**:

- **Required**: Python 3.12
- **Reason**: Compatibility with `torch==2.2.2` and `numpy==1.26.4`
- **Configuration**: Python version specified in GitHub Actions workflow (`.github/workflows/deploy.yml`)

**Note**: For Streamlit Community Cloud deployment, Python version must be set in the Streamlit app settings (Advanced settings) as `config.toml` cannot control the runtime Python version.

### Hardware Requirements

**Minimum**:

- CPU: Any modern CPU
- RAM: 4GB (8GB recommended for smooth operation)
- Disk: 2GB free space (for dependencies and vector database)

**Recommended**:

- CPU: Multi-core CPU for faster embedding generation
- RAM: 8GB or more
- Disk: 5GB free space

### Network Requirements

- Internet connection required for:
  - Downloading Python dependencies
  - External API calls (Plant.id, Groq, Tavily)
  - Streamlit Community Cloud deployment

## Dependency Installation

### Local Development

**Step 1: Clone Repository**

```bash
git clone https://github.com/MarcelRx/Phytobot.git
cd Phytobot
```

**Step 2: Create Virtual Environment (Recommended)**

```bash
python3.12 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

**Step 3: Install Dependencies**

```bash
pip install -r requirements.txt
```

**Dependencies**:

- Core: `numpy==1.26.4`, `opencv-python-headless==4.11.0.86`
- UI: `streamlit`, `python-dotenv`, `pillow`, `watchdog`
- AI/RAG: `langchain`, `langchain-community`, `langchain-groq`, `langchain-chroma`, `langchain-text-splitters`, `sentence-transformers==2.7.0`, `transformers==4.40.0`, `accelerate==0.30.0`, `torch==2.2.2`, `pypdf`
- Search: `langchain-tavily`, `requests`
- Testing: `pytest`

**Step 4: Verify Installation**

```bash
python -c "import streamlit; import torch; import langchain; print('Dependencies installed successfully')"
```

## Environment Configuration

### Local Development

**Step 1: Create `.env` File**

```bash
cp .env.example .env
```

**Step 2: Configure API Keys**
Edit `.env` file with your API keys:

```bash
GROQ_API_KEY=your_groq_api_key_here
PLANTID_API_KEY=your_plantid_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here
```

**Optional Configuration**:

```bash
VECTOR_DB_PATH=./vector_db
GROQ_MODEL=openai/gpt-oss-20b
```

**Step 3: Verify Configuration**

```bash
python -c "from src.config import validate_required_config; validate_required_config(); print('Configuration valid')"
```

### Production (Streamlit Community Cloud)

**Step 1: Connect Repository**

- Go to Streamlit Community Cloud
- Click "New app"
- Connect your GitHub repository
- Select `main` branch
- Select `app.py` as main file

**Step 2: Configure Secrets**

- In Streamlit app settings, go to "Secrets"
- Add the following secrets:
  - `GROQ_API_KEY`: Your Groq API key
  - `PLANTID_API_KEY`: Your Plant.id API key
  - `TAVILY_API_KEY`: Your Tavily API key
  - `VECTOR_DB_PATH`: `./vector_db` (optional, defaults to this value)

**Step 3: Configure Python Version**

- In Streamlit app settings (Advanced), set Python version to 3.12
- This is required for compatibility with torch and numpy versions

**Note**: Streamlit Community Cloud does not use a `.env` file. All configuration is done via the Secrets management UI.

### Rate Limiting Behavior on Streamlit Community Cloud

**Implementation**: Session-based rate limiting is implemented in `src/rate_limiter.py`

**Rate Limits**:

- Text queries: 10 requests per 60 seconds per session
- Plant identification: 5 requests per 60 seconds per session
- Total requests: 15 requests per 60 seconds per session

**Behavior on Streamlit Community Cloud**:

- Rate limiting is per-session (browser session)
- Counters reset when time window expires (60 seconds)
- Counters reset on Streamlit process restart
- Counters reset on new browser session
- Multiple replicas have independent counters
- Users can bypass by opening new browser sessions

**Limitations**:

- No global or IP-based rate limiting
- No distributed tracking across replicas
- No protection against coordinated multi-session abuse

**Note**: This is a best-effort control suitable for portfolio deployment. For production with higher exposure, consider adding Redis or a dedicated rate-limiting service.

## Local Development Startup

### Build Vector Database (First Time Only)

**Required**: If `vector_db/` directory does not exist

**Command**:

```bash
python src/processor.py
```

**Process**:

- Loads PDF files from `data/` directory
- Loads negative knowledge from `data/negative/`
- Splits text into chunks
- Generates embeddings
- Stores in ChromaDB at `./vector_db`

**Time**: Several minutes (depends on PDF size and CPU speed)

**Output**:

- Vector database created at `./vector_db`
- Log messages showing progress

**Verification**:

```bash
ls vector_db/
# Should see ChromaDB files (chroma.sqlite3, index files, etc.)
```

### Start Application

**Command**:

```bash
streamlit run app.py
```

**Default URL**: `http://localhost:8501`

**Custom Port**:

```bash
streamlit run app.py --server.port 8502
```

**Custom Address**:

```bash
streamlit run app.py --server.address 0.0.0.0 --server.port 8501
```

### Startup Verification

The application performs startup verification:

- Checks if `vector_db/` directory exists
- If missing, exits with error message
- Skips verification if `BUILDING_VECTOR_DB=1` is set (for Docker build)

**Error Message**:

```
Startup Error: Vector database not found at ./vector_db. Please run 'python src/processor.py' to build it.
```

## Build Commands

### No Build Step Required

**Local Development**: No build step required. Run `streamlit run app.py` directly.

**Streamlit Community Cloud**: No build step required. Streamlit runs `app.py` directly.

**Docker**: Build step required (see Docker section below).

### Vector Database Rebuild

**When to Rebuild**:

- After adding new PDF files to `data/`
- After updating negative knowledge JSON files in `data/negative/`
- After changing chunking configuration

**Command**:

```bash
python src/processor.py
```

**Commit to Git** (if using pre-built strategy):

```bash
git add vector_db/
git commit -m "Update vector database"
git push
```

## Database Initialization or Migrations

### Vector Database

**Initialization**: Vector database is built via `src/processor.py` (see above).

**Migrations**: No migration system. To update knowledge base:

1. Add/update PDF or JSON files
2. Rebuild vector database
3. Commit to Git (if using pre-built strategy)

**No Schema**: ChromaDB does not use a traditional schema. Metadata is attached during ingestion.

### No Other Databases

The application does not use:

- SQL databases
- NoSQL databases
- User databases
- Session databases

All persistence is:

- Vector database (ChromaDB)
- Streamlit session state (ephemeral)
- File system (PDFs, JSON files)

## Docker Setup

### Dockerfile Overview

**File**: `Dockerfile`

**Base Image**: `python:3.12-bookworm`

**System Dependencies**:

- OpenCV dependencies (libgl1, libglib2.0-0, libsm6, libxext6, libxrender-dev, libgomp1)

**Build Process**:

1. Install system dependencies
2. Copy and install Python dependencies
3. Copy application code
4. Copy data files (PDFs and negative knowledge)
5. Build vector database during image build (with `BUILDING_VECTOR_DB=1`)
6. Set environment variables
7. Expose port 8501
8. Configure health check
9. Run Streamlit

### Build Docker Image

**Command**:

```bash
docker build -t phytobot .
```

**Build Time**: Several minutes (includes vector database build)

**Build Context**: Includes `data/` directory which contains large PDF files. This may slow down the build.

### Run Docker Container

**Command**:

```bash
docker run -p 8501:8501 \
  -e GROQ_API_KEY=your_groq_api_key \
  -e PLANTID_API_KEY=your_plantid_api_key \
  -e TAVILY_API_KEY=your_tavily_api_key \
  phytobot
```

**With Environment File**:

```bash
docker run -p 8501:8501 --env-file .env phytobot
```

**Background Mode**:

```bash
docker run -d -p 8501:8501 --env-file .env --name phytobot phytobot
```

### Docker Compose (Optional)

Create `docker-compose.yml`:

```yaml
version: "3.8"
services:
  phytobot:
    build: .
    ports:
      - "8501:8501"
    env_file:
      - .env
    restart: unless-stopped
```

**Run**:

```bash
docker-compose up -d
```

### Health Check

**Configuration**: Health check in Dockerfile

- **Interval**: 30 seconds
- **Timeout**: 10 seconds
- **Start Period**: 60 seconds
- **Retries**: 3
- **Command**: HTTP request to `http://localhost:8501/_stcore/health`

**Manual Health Check**:

```bash
curl http://localhost:8501/_stcore/health
```

## CI/CD and Production Deployment Process

### GitHub Actions CI

**File**: `.github/workflows/deploy.yml`

**Triggers**:

- Push to `main` branch
- Pull request to `main` branch

**Workflow Steps**:

1. Checkout code
2. Set up Python 3.12
3. Install dependencies
4. Run tests with environment variables

**Purpose**: Quality gate for code changes. Does not handle deployment.

**Test Execution**:

```bash
pytest -q
```

**Environment Variables for CI**:

```bash
GROQ_API_KEY=test_key_for_ci
PLANTID_API_KEY=test_key_for_ci
TAVILY_API_KEY=test_key_for_ci
```

### Production Deployment (Streamlit Community Cloud)

**Deployment Method**: Manual deployment via Streamlit Community Cloud UI

**Process**:

1. Code pushed to GitHub
2. Streamlit Community Cloud connected to repository
3. Deployment triggered manually or on push (depending on configuration)
4. Streamlit runs `app.py`
5. Application accessible at Streamlit-provided URL

**Deployment Strategy**:

- Pre-built vector database committed to Git (71MB)
- No build step at deployment time
- Fast startup and reliable deployment
- Vector database loads from committed files

**Auto-Deploy**: Can be configured in Streamlit Community Cloud to auto-deploy on push to `main` branch.

**Current Status**: As of documentation creation, deployment to Streamlit Community Cloud is pending. Live demo is not yet available.

**Vector Database Loading**:

- Pre-built vector database is committed to Git (`vector_db/` directory)
- Application loads existing database on startup
- No rebuild required at deployment time
- Startup verification checks for `vector_db/` directory existence
- If missing, application exits with error

### Alternative Deployment Options

**Docker Deployment**:

- Build Docker image locally
- Push to container registry (Docker Hub, AWS ECR, etc.)
- Deploy to container hosting (AWS ECS, Google Cloud Run, Azure Container Instances, etc.)
- Configure environment variables via platform secrets management

**Self-Hosted**:

- Run on VPS or bare metal
- Use systemd or supervisor for process management
- Configure reverse proxy (nginx, Apache) with SSL
- Use environment variables or `.env` file for secrets

## Health Checks and Logs

### Health Check

**Streamlit Health Endpoint**: `/_stcore/health`

**Implementation**: Built-in Streamlit health check

**Docker Health Check**: Configured in Dockerfile (see above)

**Custom Health Checks**: No custom health checks implemented.

### Logs

**Local Development**:

- Logs printed to console
- Python `logging` module used throughout codebase
- Log level: INFO (configurable)

**Streamlit Community Cloud**:

- Logs available in Streamlit app UI
- Application logs accessible via Streamlit dashboard

**Docker**:

- Logs accessible via `docker logs` command
- Example: `docker logs phytobot`

**Log Levels**:

- INFO: Normal operation
- WARNING: Non-critical issues (e.g., web search failure)
- ERROR: Critical errors (e.g., API failures)

**Log Content**:

- Application state and flow
- Error messages
- API failures
- Retrieval results (counts, not content)
- Identification results (plant names, confidence scores)

**No Log Aggregation**: No centralized log aggregation or monitoring.

## External Service Requirements

### Required External Services

**Plant.id API**:

- **Purpose**: Plant identification
- **API Key**: Required
- **Rate Limits**: Enforced by API provider
- **Endpoint**: `https://api.plant.id/v3/identification`
- **Documentation**: https://plant.id/

**Groq API**:

- **Purpose**: LLM inference
- **API Key**: Required
- **Rate Limits**: Enforced by API provider
- **Models**: Llama 3.1-8b-instant (configurable)
- **Documentation**: https://console.groq.com/

**Tavily API**:

- **Purpose**: Web search
- **API Key**: Required
- **Rate Limits**: Enforced by API provider
- **Documentation**: https://tavily.com/

### Optional External Services

**HuggingFace**:

- **Purpose**: Download embedding model (all-MiniLM-L6-v2)
- **API Key**: Not required (public model)
- **Download**: Automatic on first run
- **Caching**: Model cached locally after first download

### Service Dependencies

**Critical Dependencies**:

- Plant.id API: Required for plant identification
- Groq API: Required for LLM response generation
- Tavily API: Required for web search (can fail gracefully)

**Graceful Degradation**:

- Plant.id failure: Plant identification unavailable, text queries still work
- Groq failure: Application unavailable (no LLM)
- Tavily failure: Web search unavailable, internal retrieval still works

## Troubleshooting

### Common Failure Modes

#### 1. Vector Database Not Found

**Error**:

```
Startup Error: Vector database not found at ./vector_db. Please run 'python src/processor.py' to build it.
```

**Solution**:

```bash
python src/processor.py
```

#### 2. Missing API Keys

**Error**:

```
Configuration Error: Missing required environment variables:
  - GROQ_API_KEY: GROQ_API_KEY is required for LLM functionality
  - PLANTID_API_KEY: PLANTID_API_KEY is required for plant identification
  - TAVILY_API_KEY: TAVILY_API_KEY is required for web search
```

**Solution**:

- Local: Add API keys to `.env` file
- Streamlit Community Cloud: Add secrets in app settings

#### 3. Python Version Mismatch

**Error**:

```
ImportError: Library requires Python 3.12
```

**Solution**:

- Ensure Python 3.12 is installed
- Use virtual environment with Python 3.12
- On Streamlit Community Cloud, set Python version to 3.12 in Advanced settings

#### 4. Dependency Installation Failures

**Error**:

```
ERROR: Could not find a version that satisfies the requirement torch==2.2.2
```

**Solution**:

- Ensure Python 3.12 is installed
- Upgrade pip: `pip install --upgrade pip`
- Try installing without version pin first: `pip install torch`

#### 5. OpenCV Import Errors

**Error**:

```
ImportError: libGL.so.1: cannot open shared object file
```

**Solution**:

- Docker: System dependencies already installed in Dockerfile
- Local: Install OpenCV system dependencies (see Dockerfile for list)
- Alternative: Use `opencv-python-headless` (already in requirements.txt)

#### 6. Streamlit Won't Start

**Error**:

```
StreamlitRuntimeException: 'app.py' not found
```

**Solution**:

- Ensure you're in the correct directory
- Run from repository root: `streamlit run app.py`

#### 7. Plant Identification Rate Limit

**Error**:

```
Plant identification is temporarily unavailable because the identification service is rate-limited.
```

**Solution**:

- Wait for rate limit to reset
- Upgrade Plant.id API plan for higher rate limits
- Retry after delay (application implements retry logic)

#### 8. LLM Model Not Found

**Error**:

```
Model not found: openai/gpt-oss-20b
```

**Solution**:

- Check `GROQ_MODEL` environment variable
- Update to valid Groq model name
- Default model may have changed; check Groq documentation

#### 9. Vector Database Build Fails

**Error**:

```
Failed to create vector database: ...
```

**Solution**:

- Ensure `data/` directory exists and contains PDF files
- Ensure `data/negative/` directory exists and contains JSON files
- Check disk space
- Check memory availability
- Try building with smaller batch size (edit `src/processor.py`)

#### 10. Docker Build Fails

**Error**:

```
ERROR [build step] ...
```

**Solution**:

- Ensure Docker is running
- Check Dockerfile syntax
- Ensure sufficient disk space for build context
- Try building without cache: `docker build --no-cache -t phytobot .`

### Debug Mode

**Enable Debug Logging**:

```python
# In app.py or src/config.py
logging.basicConfig(level=logging.DEBUG)
```

**Verbose pytest**:

```bash
pytest -vv
```

**Streamlit Debug Mode**:

```bash
streamlit run app.py --logger.level=debug
```

### Getting Help

**Check Logs**:

- Local: Console output
- Streamlit Community Cloud: App logs in dashboard
- Docker: `docker logs phytobot`

**Run Tests**:

```bash
pytest -v
```

**Verify Configuration**:

```bash
python -c "from src.config import validate_required_config; validate_required_config()"
```

**Check Dependencies**:

```bash
pip list
```

## Production Limitations and Unverified Deployment Steps

### Production Limitations

1. **No Horizontal Scaling**: Monolithic architecture does not support horizontal scaling
2. **No Load Balancing**: No load balancer configuration
3. **No Caching Layer**: No Redis or similar caching
4. **No Monitoring**: No application monitoring or alerting
5. **No Backups**: Vector database is committed to Git but no automated backups
6. **No Rollback Strategy**: No automated rollback mechanism
7. **No Blue-Green Deployment**: No blue-green or canary deployment strategy
8. **No A/B Testing**: No A/B testing capability

### Unverified Deployment Steps

The following deployment methods have not been verified:

1. **Kubernetes Deployment**: No Kubernetes manifests or Helm charts
2. **AWS ECS Deployment**: No ECS task definitions
3. **Google Cloud Run Deployment**: No Cloud Run configuration
4. **Azure Container Instances**: No ACI configuration
5. **Heroku Deployment**: No Heroku configuration
6. **Self-Hosted with SSL**: No SSL certificate configuration documented
7. **Reverse Proxy Configuration**: No nginx or Apache configuration documented
8. **Process Manager Configuration**: No systemd or supervisor configuration documented

### Deployment Verification

**Streamlit Community Cloud**: Deployment method is documented but not yet verified (deployment pending as of documentation creation).

**Docker**: Docker build and run commands are documented but not tested in this documentation task.

**Local Development**: Local development setup is verified and tested.

## Summary

### Local Development

- ✅ Verified and tested
- Python 3.12 required
- Vector database build required (first time)
- `.env` file for API keys
- `streamlit run app.py` to start

### Streamlit Community Cloud

- ⚠️ Documented but not yet verified (deployment pending)
- Pre-built vector database committed to Git
- Secrets configured in Streamlit UI
- Python 3.12 configured in Advanced settings
- No build step required

### Docker

- ⚠️ Documented but not tested
- Dockerfile provided
- Vector database built during image build
- Environment variables via `--env-file` or `-e`
- Health check configured

### CI/CD

- ✅ GitHub Actions workflow verified
- Runs pytest on push/PR to main
- Does not handle deployment
- Quality gate only

### Recommendations

1. **Verify Streamlit Deployment**: Deploy to Streamlit Community Cloud and verify configuration
2. **Test Docker Build**: Test Docker build and run locally
3. **Add Monitoring**: Implement application monitoring for production
4. **Add Backups**: Implement automated backups for vector database
5. **Add Rollback Strategy**: Implement rollback mechanism for deployments
6. **Document Alternative Deployments**: Document Kubernetes, ECS, or other deployment methods if needed
