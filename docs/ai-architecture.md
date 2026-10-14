# AI Architecture

## AI-Related Components and Responsibilities

Phytobot uses AI in three distinct areas:

1. **Computer Vision**: Plant identification via Plant.id API
2. **Semantic Retrieval**: Vector embeddings and similarity search
3. **Language Generation**: LLM-powered response generation via Groq

### Vision AI Component

**Location**: `src/vision_module.py`

**Responsibilities**:
- Image quality assessment (blur detection)
- Plant identification from images
- "Not a plant" detection
- Error handling for API failures

**AI Technology**: External API (Plant.id v3)

### Retrieval AI Component

**Location**: `src/processor.py` (ingestion), `src/bot_logic.py` (retrieval)

**Responsibilities**:
- Text embedding generation
- Semantic similarity search
- Document chunking and metadata attachment

**AI Technology**: HuggingFace sentence-transformers (all-MiniLM-L6-v2)

### Language Generation AI Component

**Location**: `src/bot_logic.py`

**Responsibilities**:
- Response generation from retrieved context
- Safety rule enforcement in prompts
- Structured response formatting
- Web search context integration

**AI Technology**: Llama 3.1-8b-instant via Groq API

## Model Providers and Identifiers

### Vision Model

**Provider**: Plant.id

**Model**: Proprietary (not specified in documentation, accessed via API)

**Interface**: REST API v3

**Configuration**:
- Endpoint: `https://api.plant.id/v3/identification`
- Authentication: API key header
- Parameters: Base64-encoded image, optional coordinates, similar_images flag
- Timeout: 30 seconds

**Access**: `src/vision_module.py::identify_plant()`

### Embedding Model

**Provider**: HuggingFace

**Model**: `all-MiniLM-L6-v2`

**Interface**: LangChain `HuggingFaceEmbeddings`

**Configuration**:
- Vector dimensions: 384
- Model repository: sentence-transformers
- Timeout: Not explicitly configured (uses model defaults)

**Access**: `src/processor.py::process_documents()`, `src/bot_logic.py::load_phytobot_resources()`

### Language Model

**Provider**: Groq

**Model**: Configurable via `GROQ_MODEL` environment variable

**Default Model**: `openai/gpt-oss-20b` (as per `src/config.py`)

**Alternative Models**: Can be changed via environment variable

**Interface**: LangChain `ChatGroq`

**Configuration**:
- Temperature: 0.1 (low temperature for consistent responses)
- Max retries: 2
- Timeout: 30 seconds
- Model selection: Via `GROQ_MODEL` environment variable

**Access**: `src/bot_logic.py::load_phytobot_resources()`

## Prompt Construction and Inference Flow

### Prompt Template

The system uses a structured prompt template via LangChain's `ChatPromptTemplate`. The prompt is constructed in `src/bot_logic.py::get_phytobot_response()`.

**Prompt Structure**:

```python
prompt = ChatPromptTemplate.from_template("""
You are Phytobot, a scientific herbalism assistant with a strong focus on plant safety.
User Question: {question}

{plant_info}

CRITICAL SAFETY RULES (Follow strictly):
- NEVER infer medicinal safety from plant identification alone
- NEVER ignore retrieved toxicity information
- Do not convert "traditional use" into evidence of safety
- Clearly distinguish established evidence from traditional use
- When evidence conflicts, explicitly report the conflict
- When identification is uncertain, say so
- Do not invent toxicity information
- Do not invent preparation instructions when source evidence is absent
- If toxic evidence is found, prioritize safety warnings over any medicinal information

Structure your answer in these EXACT blocks:

{plant_identification_section}

### Safety Status
(Based on retrieved safety evidence, indicate: documented safe/medicinal use, toxicity concern, dangerous plant parts, insufficient evidence, or identification uncertainty.)

### Verified WHO/Encyclopedia Data ({trust_label})
(Use INTERNAL MEDICINAL DATA. If not found, say 'No specific match in our medical library for this query.')

### Safety Evidence ({trust_label})
(Use INTERNAL SAFETY DATA. Report any toxicity, dangerous parts, contraindications, or warnings found. If no safety evidence found, state this explicitly.)

### Internet Research & Traditional Use (Web research only - verify with medical sources)
(Summarize INTERNET DATA. Clearly distinguish traditional use from authoritative evidence. Provide recipe steps or traditional uses found online only if safety evidence permits.)

### Safety & Disclaimer
(List side effects or drug interactions. End with: 'Not a substitute for medical advice.')

MEDICINAL DATA: {medicinal_context}
SAFETY DATA: {safety_context}
INTERNET DATA: {web_context}
SYSTEM SAFETY WARNING: {safety_warning}
SYSTEM IDENTIFICATION WARNING: {identification_warning}
""")
```

### Inference Flow

1. **User Input**: User provides text query or uploads image
2. **Evidence Retrieval**:
   - Medicinal evidence retrieved from vector DB (k=3)
   - Safety evidence retrieved from vector DB (k=3)
   - Web search performed via Tavily (max 2 results)
3. **Safety Analysis**: Application logic analyzes safety docs for toxicity and risk level
4. **Evidence State**: Evidence state determined (specific, partial, web-only, none)
5. **Trust Label**: Human-readable trust label generated
6. **Warning Construction**: System-generated safety and identification warnings built
7. **Prompt Construction**: All context injected into prompt template
8. **LLM Invocation**: LangChain chain invokes Groq LLM
9. **Response Generation**: LLM generates structured response
10. **Disclaimer Verification**: Response checked for required disclaimer phrases; appended if missing

**Implementation**: `src/bot_logic.py::get_phytobot_response()`

## Model Orchestration

Phytobot does **not** implement multi-model orchestration, agents, or function calling. The system uses a single LLM for response generation. There is no:

- Multiple model coordination
- Model routing based on query type
- Agent-based decision making
- Function calling or tool use
- Model ensemble or voting

The architecture is a single-model RAG system with deterministic safety logic running before LLM invocation.

## Structured Output, Validation, and Parsing

### Structured Output

The LLM is instructed to generate responses in a specific block structure via prompt engineering. There is **no** structured output validation, schema enforcement, or parsing in the codebase.

**Blocks Required**:
- Plant Identification
- Safety Status
- Verified WHO/Encyclopedia Data
- Safety Evidence
- Internet Research & Traditional Use
- Safety & Disclaimer

**Validation**:
- No schema validation on LLM output
- No parsing or extraction of structured fields
- Response treated as raw Markdown
- Only disclaimer phrase validation (see below)

### Disclaimer Validation

**Location**: `src/safety.py::verify_safety_disclaimer()`

**Validation Logic**:
- Checks if response contains required phrases: "medical advice", "not a substitute", "consult a doctor"
- Case-insensitive matching
- If missing, appends standard disclaimer

**Standard Disclaimer**:
```
**Medical Disclaimer:** This information is for educational purposes only and is not a substitute for professional medical advice. Always consult a qualified healthcare provider before using herbal remedies.
```

## Context Handling and Conversation State

### Context Sources

The LLM receives context from three sources:

1. **Medicinal Context**: Retrieved from vector DB with `knowledge_type=medicinal` metadata filter
2. **Safety Context**: Retrieved from vector DB with `knowledge_type=safety_negative` metadata filter
3. **Web Context**: Retrieved from Tavily search API

### Context Limits

- Medicinal retrieval: k=3 documents
- Safety retrieval: k=3 documents
- Web search: max 2 results
- Total context length: Not explicitly limited; depends on retrieved document sizes

### Conversation State

Phytobot does **not** maintain conversation history or multi-turn context. Each query is processed independently with no memory of previous interactions.

**Reasoning**:
- Streamlit session state is used only for caching plant identification results
- No conversation history persistence
- No context carryover between queries
- Each response is self-contained

**Implementation**: No conversation history code exists in the codebase.

## Error Handling, Retries, Timeouts, and Fallbacks

### Vision Module (Plant.id API)

**Timeout**: 30 seconds (configurable via `APIConfig.PLANTID_TIMEOUT`)

**Error Handling**:
- **Timeout**: Returns `PlantIdentificationResult.TIMEOUT`
- **Network Error**: Returns `PlantIdentificationResult.NETWORK_ERROR`
- **Auth Error (401/403)**: Returns `PlantIdentificationResult.AUTH_ERROR`
- **Rate Limit (429)**: Implements retry logic with Retry-After header parsing (max 1 retry)
- **Server Error (500+)**: Returns `PlantIdentificationResult.API_ERROR`
- **Malformed Response**: Returns `PlantIdentificationResult.API_ERROR`
- **Blurry Image**: Returns `PlantIdentificationResult.BLURRY_IMAGE` (pre-API)

**Retries**:
- Rate limit (429): 1 retry with Retry-After header parsing (capped at 60 seconds)
- Other errors: No retries

**Fallbacks**:
- No fallback model or API
- If Plant.id fails, user sees error message and no identification occurs

### LLM (Groq API)

**Timeout**: 30 seconds (configurable via `APIConfig.REQUEST_TIMEOUT`)

**Error Handling**:
- **Timeout**: Not explicitly handled in code; would raise LangChain exception
- **Auth Error**: Not explicitly handled; would raise LangChain exception
- **Rate Limit**: Not explicitly handled; would raise LangChain exception
- **Model Not Found**: Tested in test suite with mock
- **Max Retries**: Configured to 2 in `LLMConfig.MAX_RETRIES` (LangChain-level retry)

**Retries**:
- LangChain-level retries: 2 (configured in `ChatGroq`)
- Application-level retries: None

**Fallbacks**:
- No fallback model or API
- If LLM fails, exception propagates to user

### Web Search (Tavily API)

**Timeout**: 15 seconds (configurable via `APIConfig.TAVILY_TIMEOUT`)

**Error Handling**:
- **Failure**: Caught with try/except; sets `web_context = "Web search currently unavailable."`
- **Evidence State Update**: If web search succeeds but no internal evidence found, updates state to `WEB_ONLY_EVIDENCE`

**Retries**:
- No retries implemented

**Fallbacks**:
- If Tavily fails, system continues with internal evidence only
- Web search is treated as supplementary, not required

### Vector Database

**Error Handling**:
- **Load Failure**: Caught in `load_phytobot_resources()`; raises exception
- **Retrieval Failure**: Caught in retrieval functions; returns empty list and error message

**Retries**:
- No retries implemented

**Fallbacks**:
- If vector DB fails, system cannot function (required component)
- Startup verification checks for vector DB existence

## AI-Specific Testing and Evaluation

### Test Coverage

**Vision Module Tests** (`tests/test_vision_module.py`):
- Blur detection with sharp/nonexistent images
- Custom threshold testing
- API key missing
- Blurry image handling
- API timeout
- Successful identification
- Not a plant detection
- Malformed JSON
- Rate limit (429) handling
- Rate limit with Retry-After header
- Retry-After header capping
- Auth errors (401/403)
- Bad request (400)
- Server error (500)
- Network error
- Timeout error
- No suggestions in response

**Bot Logic Tests** (`tests/test_bot_logic.py`):
- Successful response generation
- Vector DB failure handling
- Web search failure handling
- LLM failure handling
- Empty vector DB handling
- Missing disclaimer handling
- Model not found error
- Auth error
- Rate limit error
- Text-only mode without plant ID
- Image-only mode with/without plant
- Named plant in text without plant ID call
- Evidence state variations
- Trust label not hardcoded

**Safety Decision Tests** (`tests/test_safety_decision.py`):
- No evidence scenarios
- Low identification confidence
- Critical/high toxicity
- Dangerous look-alikes
- Caution required
- Medicinal-only evidence
- Medicinal and safe evidence
- Conflict detection
- Negative test cases (8 comprehensive scenarios)

**External API Mocking**:
- Plant.id API is mocked in tests
- Groq LLM is mocked in tests
- Tavily search is mocked in tests
- Tests do not require real API keys (use test keys for CI)

### Evaluation Methods

**No Systematic Evaluation**:
- No automated retrieval quality evaluation
- No LLM response accuracy evaluation
- No ground truth dataset for benchmarking
- No human evaluation framework
- No A/B testing capability

**Manual Evaluation**:
- Manual testing by developer during development
- User feedback not systematically collected

## Model Limitations, Failure Modes, and Known Risks

### Vision Model Limitations

**Limitations**:
- Accuracy depends on image quality (blur detection mitigates but does not eliminate)
- Cannot identify plants from partial or obscured images
- Geographic coordinates are hardcoded in code (49.1951, 16.6068) and not user-configurable
- Rate limits may prevent identification during high usage
- API downtime would prevent all plant identification

**Failure Modes**:
- Returns wrong plant identification
- Fails to identify plant (no suggestions)
- Incorrectly identifies non-plant as plant
- Rate limit errors prevent identification

**Known Risks**:
- Misidentification could lead to unsafe plant recommendations
- No cross-verification with other botanical databases
- Identification confidence is not a safety indicator

### Embedding Model Limitations

**Limitations**:
- all-MiniLM-L6-v2 is a general-purpose model, not domain-specific for botany
- May not capture nuanced botanical terminology
- Semantic similarity may not reflect botanical relationships
- 384-dimensional vectors may have limited discrimination capacity for large knowledge bases

**Failure Modes**:
- Retrieves irrelevant documents
- Fails to retrieve relevant documents (low recall)
- Retrieves documents with low precision for botanical queries

**Known Risks**:
- Poor retrieval quality could lead to missing safety information
- No reranking or hybrid search to improve precision

### Language Model Limitations

**Limitations**:
- LLM may hallucinate facts not present in retrieved context
- LLM may not follow safety rules strictly despite prompt instructions
- LLM may conflate traditional use with authoritative evidence
- LLM may invent toxicity information when none exists
- LLM may generate preparation instructions without source evidence
- No structured output validation
- Temperature 0.1 reduces but does not eliminate variability

**Failure Modes**:
- Generates unsafe recommendations despite safety rules
- Omits required response blocks
- Ignores retrieved toxicity information
- Misrepresents evidence quality
- Fails to append disclaimer (mitigated by verification function)

**Known Risks**:
- LLM behavior is not deterministic; safety-critical decisions rely on deterministic layer
- LLM may misinterpret or misrepresent retrieved context
- No adversarial testing against prompt injection

### System-Level Risks

**Safety Layer Dependency**:
- All safety-critical decisions rely on deterministic application logic (`src/safety_decision.py`)
- If safety logic has bugs, LLM could generate unsafe responses
- No independent safety validation of LLM outputs

**Knowledge Base Completeness**:
- Negative knowledge base is not exhaustive
- Unknown toxic plants may not trigger warnings
- New toxicity information requires manual updates

**Identification ≠ Safety**:
- Plant identification confidence is explicitly not used as a safety score
- However, users may misinterpret high identification confidence as safety assurance

**Web Search Reliability**:
- Tavily search results are not vetted for accuracy
- Web information may contradict authoritative sources
- System depends on LLM to distinguish traditional use from evidence

**No Conversation Memory**:
- Multi-turn context could improve safety and accuracy
- Current implementation processes each query independently

**No User Feedback Loop**:
- No mechanism for users to report incorrect or unsafe responses
- No learning from user corrections

## Security Considerations

### Prompt Injection

**Vulnerability**: User queries could attempt to manipulate the LLM via prompt injection.

**Mitigations**:
- System prompt includes safety rules
- Deterministic safety layer runs before LLM
- However, no formal prompt injection testing or mitigation

**Risk Level**: Moderate (not systematically addressed)

### Retrieved Content Trust

**Vulnerability**: Retrieved documents from vector DB or web search could contain malicious or misleading content.

**Mitigations**:
- Vector DB uses curated sources (WHO monographs, encyclopedia, authoritative safety data)
- Web search is treated as low-confidence source
- Trust labels explicitly indicate evidence quality

**Risk Level**: Low for vector DB, moderate for web search

### LLM Output Validation

**Vulnerability**: LLM could generate harmful content despite safety rules.

**Mitigations**:
- Disclaimer enforcement function appends medical disclaimer
- Deterministic safety warnings are added before LLM generation
- No content filtering or safety validation of LLM output

**Risk Level**: Moderate (relies on prompt engineering and deterministic layer)
