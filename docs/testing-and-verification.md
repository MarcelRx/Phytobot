# Testing and Verification

## Test Framework and Organization

### Test Framework

**Framework**: pytest

**Configuration**: `pytest.ini`

**Python Version**: 3.12

**Test Organization**:

- Test files located in `tests/` directory
- Test files follow naming convention: `test_*.py`
- Test classes follow naming convention: `Test*`
- Test functions follow naming convention: `test_*`

### Test Files

1. **test_app_session_state.py** - Streamlit session state caching logic
2. **test_bot_logic.py** - Core orchestration and response generation
3. **test_config.py** - Configuration validation
4. **test_evidence_logic.py** - Evidence state and trust label logic
5. **test_negative_knowledge.py** - Negative knowledge loading and conversion
6. **test_prompt_injection.py** - AI safety and prompt injection regression tests
7. **test_rate_limiter.py** - Session-based rate limiting
8. **test_safety.py** - Safety disclaimer verification
9. **test_safety_decision.py** - Deterministic safety decision logic
10. **test_validation.py** - Input validation (text and image)
11. **test_vision_module.py** - Plant identification and blur detection

## Test Scope

### Unit Tests

**Configuration Tests** (`test_config.py`):

- API configuration existence and timeout values
- Vector DB configuration (path, retrieval k, embedding model)
- LLM configuration (model name, temperature, model selection)
- Vision configuration (blur threshold, image size, allowed types)
- Search configuration (max web results)
- Text processing configuration (chunk size, overlap, max query length)
- Safety configuration (disclaimer phrases, standard disclaimer)

**Evidence Logic Tests** (`test_evidence_logic.py`):

- Evidence state determination (specific, partial, none, unknown plant)
- Trust label generation
- Input mode enumeration
- Evidence state enumeration

**Safety Tests** (`test_safety.py`):

- Disclaimer verification (present, missing, with required phrases)
- Case-insensitive disclaimer matching

**Validation Tests** (`test_validation.py`):

- Text input validation (empty, whitespace, valid, too long, at max length, normalization)
- Image validation (none, valid JPEG/PNG, too large, unsupported extension, corrupted)

**Negative Knowledge Tests** (`test_negative_knowledge.py`):

- Negative knowledge loading (directory not found, success, multiple files, non-JSON ignored)
- Entry conversion (toxic plant, toxic parts, look-alike, minimal entry)
- Metadata filters (safety and medicinal)

### Integration Tests

**Bot Logic Tests** (`test_bot_logic.py`):

- Successful response generation
- Vector DB failure handling
- Web search failure handling
- LLM failure handling
- Empty vector DB handling
- Missing disclaimer handling
- Model not found error
- Auth error
- Rate limit error
- Input mode variations (text-only, image-only with/without plant)
- Named plant in text without plant ID call
- Evidence state variations
- Trust label not hardcoded

**Safety Decision Tests** (`test_safety_decision.py`):

- Safety decision logic (no evidence, low confidence, critical/high toxicity, dangerous look-alike, caution required, medicinal-only, medicinal and safe)
- Conflict detection (toxicity with medicinal, safe with medicinal)
- Safety response formatting (with/without plant name, with conflict)
- Negative test cases (8 comprehensive scenarios based on real plants)

**Vision Module Tests** (`test_vision_module.py`):

- Blur detection (sharp image, nonexistent file, custom threshold)
- Plant identification (no API key, blurry image, API timeout, success, not a plant, malformed JSON, rate limit 429, rate limit with Retry-After, retry-after capped, auth 401/403, bad request 400, server error 500, network error, timeout error, no suggestions)

**App Session State Tests** (`test_app_session_state.py`):

- Session state initialization
- Image change clears cached identification
- Text-only query does not reuse image plant
- Failed identification not treated as success
- Rate limit not treated as identification

### End-to-End Tests

**Status**: ❌ No end-to-end tests

The test suite does not include end-to-end tests that simulate full user workflows from UI to response. All tests are unit or integration tests mocking external APIs.

### AI Evaluation Tests

**Status**: ❌ No AI evaluation tests

The test suite does not include:

- Retrieval quality evaluation
- LLM response accuracy evaluation
- Ground truth benchmarking
- Hallucination detection
- Safety warning effectiveness evaluation

### Security Tests

**Status**: ✅ Partially Implemented

**Security Test Coverage**:

- **Prompt Injection Tests** (`test_prompt_injection.py`):
  - Safety policy override attempts (26 tests)
  - Malicious retrieved documents handling
  - Mandatory warning enforcement
  - Low-confidence identification handling
  - Input validation safety
  - Unsupported medical claims detection
  - Evidence attribution distinction
  - Malformed or missing model output handling
  - LLM-generated text not trusted (metadata-based decisions)

- **Rate Limiter Tests** (`test_rate_limiter.py`):
  - Session-based rate limiting (14 tests)
  - Request limits and window reset
  - Operation-specific limits
  - Total request tracking

**Limitations**:

- No formal LLM prompt injection testing (tests cover deterministic safety layer only)
- No adversarial input testing beyond validation
- SQL injection testing (not applicable as no SQL database)
- XSS testing (not applicable as server-side rendering)
- Authentication testing (no authentication implemented)

## Test Execution

### Commands

**Run all tests**:

```bash
pytest
```

**Run with verbose output**:

```bash
pytest -v
```

**Run specific test file**:

```bash
pytest tests/test_bot_logic.py
```

**Run specific test class**:

```bash
pytest tests/test_vision_module.py::TestPlantIdentification
```

**Run specific test function**:

```bash
pytest tests/test_vision_module.py::TestPlantIdentification::test_identify_plant_success
```

### Environment Setup

**Required Environment Variables**:

```bash
GROQ_API_KEY=test_key_for_ci
PLANTID_API_KEY=test_key_for_ci
TAVILY_API_KEY=test_key_for_ci
```

**CI Configuration**: The GitHub Actions workflow (`.github/workflows/deploy.yml`) sets these environment variables for automated testing.

**Local Testing**: Tests can be run locally by setting environment variables or creating a `.env` file with the required keys. Actual API keys are not required for tests as external APIs are mocked.

### Mocked Dependencies

**External APIs**:

- Plant.id API: Mocked in `test_vision_module.py`
- Groq LLM API: Mocked in `test_bot_logic.py`
- Tavily Search API: Mocked in `test_bot_logic.py`

**Mocking Library**: Tests use `unittest.mock` for mocking external API calls.

**Vector Database**: ChromaDB is not mocked; tests use actual ChromaDB instances with test data or empty databases.

## CI Workflow

### GitHub Actions Configuration

**File**: `.github/workflows/deploy.yml`

**Triggers**:

- Push to `main` branch
- Pull request to `main` branch

**Runner**: `ubuntu-24.04`

**Python Version**: 3.12

**Steps**:

1. Checkout code
2. Set up Python 3.12
3. Install dependencies from `requirements.txt`
4. Run tests with environment variables set

**Purpose**: Quality gate for code changes. Does not handle deployment (deployment is managed by Streamlit Community Cloud).

## Test Coverage

### Coverage Status

**Status**: ❌ Not measured

The project does not currently measure code coverage. No coverage tool (e.g., `pytest-cov`) is configured in `requirements.txt` or `pytest.ini`.

### Estimated Coverage

Based on test file organization, the following areas have test coverage:

**High Coverage**:

- Configuration validation
- Input validation
- Safety disclaimer verification
- Evidence state logic
- Negative knowledge loading
- Safety decision logic
- Vision module error handling

**Moderate Coverage**:

- Bot logic orchestration
- API failure scenarios

**Low/No Coverage**:

- Streamlit UI components
- Knowledge ingestion (`src/processor.py`)
- Prompt construction details
- LLM response quality
- Retrieval accuracy
- End-to-end workflows

## Actual Test Execution Results

### Test Run Summary

**Date**: 2026-10-14 (Updated after security hardening)

**Command**:

```bash
GROQ_API_KEY=test_key_for_ci PLANTID_API_KEY=test_key_for_ci TAVILY_API_KEY=test_key_for_ci pytest -q
```

**Results**:

- **Collected**: 158 tests
- **Passed**: 158 tests
- **Failed**: 0 tests
- **Skipped**: 0 tests
- **Warnings**: 2 warnings (LangChain pydantic v1 compatibility only)

**New Tests Added**:

- 26 prompt injection and AI safety regression tests (`test_prompt_injection.py`)
- 14 rate limiter tests (`test_rate_limiter.py`)

### Warnings

1. **LangChain/Pydantic Warning**:

   ```
   LangChainDeprecationWarning: As of langchain-core 0.3.0, LangChain uses pydantic v2 internally.
   The langchain_core.pydantic_v1 module was a compatibility shim for pydantic v1.
   ```

   - **Impact**: Non-critical. Compatibility warning for LangChain and Pydantic v1/v2 transition.
   - **Fix**: Update code to import from Pydantic directly instead of `langchain_core.pydantic_v1`.
   - **Note**: Not blocking for release; requires LangChain ecosystem migration.
   - **Status**: pytest-asyncio warning fixed by adding `asyncio_default_fixture_loop_scope = function` to pytest.ini

### Test Breakdown by File

| Test File                  | Tests   | Status         |
| -------------------------- | ------- | -------------- |
| test_app_session_state.py  | 5       | All passed     |
| test_bot_logic.py          | 20      | All passed     |
| test_config.py             | 19      | All passed     |
| test_evidence_logic.py     | 4       | All passed     |
| test_negative_knowledge.py | 10      | All passed     |
| test_safety.py             | 5       | All passed     |
| test_safety_decision.py    | 27      | All passed     |
| test_validation.py         | 10      | All passed     |
| test_vision_module.py      | 18      | All passed     |
| **Total**                  | **158** | **All passed** |

### Test Execution Time

**Total Time**: 74.63 seconds (1 minute 14 seconds)

**Average per Test**: ~0.47 seconds

## Known Test Gaps

### Missing Test Coverage

1. **Knowledge Ingestion**:
   - `src/processor.py` has no dedicated tests
   - PDF processing, chunking, and embedding generation are not tested
   - Vector database build process is not tested

2. **Streamlit UI**:
   - UI components and user interactions are not tested
   - No automated UI testing (e.g., with Streamlit testing tools)

3. **Retrieval Quality**:
   - No evaluation of retrieval accuracy
   - No ground truth queries for benchmarking
   - No precision/recall metrics

4. **LLM Response Quality**:
   - No evaluation of LLM response accuracy
   - No hallucination detection tests
   - No grounding verification tests

5. **End-to-End Workflows**:
   - No full workflow tests from UI to response
   - No integration tests with real external APIs (all mocked)

6. **Prompt Engineering**:
   - No tests for prompt effectiveness
   - No tests for safety rule adherence in LLM responses

7. **Concurrency**:
   - No tests for concurrent user scenarios
   - No tests for race conditions in session state

8. **Performance**:
   - No performance tests for large knowledge bases
   - No load testing for API rate limits

### Unverified Behaviors

1. **Vector Database Accuracy**:
   - Embedding quality not verified
   - Retrieval correctness not systematically verified
   - Metadata filtering correctness not tested at scale

2. **Safety Logic Edge Cases**:
   - Complex conflict scenarios not fully tested
   - Safety logic with incomplete metadata not tested

3. **API Error Recovery**:
   - Recovery from transient API failures not tested
   - Retry logic effectiveness not verified

4. **Large Input Handling**:
   - Very large text inputs (at/beyond limits) not thoroughly tested
   - Very large image files (at/beyond limits) not thoroughly tested

5. **Deployment Verification**:
   - No tests verify application runs correctly after deployment
   - No health check tests

## Recommendations

### High Priority

1. **Add Knowledge Ingestion Tests**:
   - Test PDF processing and chunking
   - Test embedding generation
   - Test vector database build process
   - Verify metadata attachment

2. **Add Retrieval Quality Evaluation**:
   - Create ground truth query dataset
   - Implement precision/recall metrics
   - Test retrieval for known toxic plants
   - Test retrieval for known medicinal plants

3. **Add End-to-End Tests**:
   - Test full workflow from image upload to response
   - Test full workflow from text query to response
   - Test error scenarios end-to-end

### Medium Priority

4. **Add LLM Response Evaluation**:
   - Test safety rule adherence in responses
   - Test disclaimer presence in responses
   - Test grounding in retrieved context

5. **Add Coverage Measurement**:
   - Install `pytest-cov`
   - Measure and report coverage
   - Set coverage targets (e.g., 80%)

6. **Add Performance Tests**:
   - Test retrieval speed with large knowledge bases
   - Test API timeout handling
   - Test memory usage during ingestion

### Low Priority

7. **Add UI Tests**:
   - Test Streamlit UI components
   - Test user interaction flows

8. **Add Security Tests**:
   - Test prompt injection resistance
   - Test adversarial input handling

9. **Fix Deprecation Warnings**:
   - Configure asyncio default fixture loop scope
   - Update LangChain imports for Pydantic v2

## Verification Summary

### What Was Verified

✅ **Test Execution**: All 158 tests pass successfully
✅ **Configuration Tests**: All configuration classes and values validated
✅ **Input Validation**: Text and image validation logic tested
✅ **Safety Logic**: Safety decision logic tested with 8 comprehensive scenarios
✅ **Vision Module**: Plant identification and blur detection tested with various error scenarios
✅ **Evidence Logic**: Evidence state and trust label logic tested
✅ **Negative Knowledge**: Loading and conversion of safety knowledge tested
✅ **Disclaimer Enforcement**: Safety disclaimer verification tested
✅ **API Error Handling**: Mocked API failures tested
✅ **CI Workflow**: GitHub Actions workflow configured and verified

### What Was Not Verified

❌ **Knowledge Ingestion**: PDF processing, chunking, and embedding generation not tested
❌ **Retrieval Quality**: No systematic evaluation of retrieval accuracy
❌ **LLM Response Quality**: No evaluation of LLM response accuracy or grounding
❌ **End-to-End Workflows**: No full workflow tests
❌ **Code Coverage**: Coverage not measured
❌ **Real API Integration**: All external APIs mocked in tests
❌ **Deployment**: No post-deployment verification tests
❌ **Performance**: No performance or load tests
❌ **Security**: No dedicated security tests

### Test Execution Limitations

1. **Environment Variables**: Tests require mock API keys to pass configuration validation
2. **Vector Database**: Tests use actual ChromaDB but with test data, not production knowledge base
3. **External APIs**: All external APIs are mocked; real API behavior not tested
4. **No Real Images**: Vision module tests use mocks, not actual image files
5. **No Real LLM**: LLM responses are mocked; actual LLM behavior not tested

### Conclusion

The test suite provides good coverage of core application logic, error handling, and safety decision-making. However, there are significant gaps in knowledge ingestion testing, retrieval quality evaluation, and end-to-end verification. The tests pass reliably and serve as an effective quality gate for code changes via CI, but additional testing is needed to fully verify the RAG pipeline and LLM integration quality.
