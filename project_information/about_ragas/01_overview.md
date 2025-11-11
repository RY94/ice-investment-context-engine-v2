# RAGAS Overview: Architecture and Concepts

**Location**: `/project_information/about_ragas/01_overview.md`
**Purpose**: Foundational understanding of RAGAS framework
**Last Updated**: 2025-11-07

---

## 🎯 What is RAGAS?

**RAGAS** (Retrieval-Augmented Generation Assessment) is an **open-source Python framework** specifically designed to evaluate the quality of Retrieval-Augmented Generation (RAG) systems.

### Key Characteristics

- **License**: Apache-2.0
- **GitHub**: explodinggradients/ragas (11.4k+ stars, 260+ contributors)
- **Latest Release**: v0.3.8 (as of 2025-11-07)
- **Primary Focus**: RAG pipeline evaluation (not general LLM evaluation)
- **Core Innovation**: "Reference-free" evaluation (doesn't always need human-annotated ground truth)

---

## 🔍 Why RAGAS Exists

### The Problem RAGAS Solves

Traditional LLM evaluation methods fall short for RAG systems because:

1. **Retrieval Quality ≠ Generation Quality**: A system can retrieve perfect documents but generate poor answers
2. **Hallucination Risk**: LLMs can fabricate information even with good context
3. **Manual Evaluation Doesn't Scale**: Human review of every RAG output is expensive and slow
4. **Black-Box Problem**: Hard to diagnose WHY a RAG system fails (retrieval vs generation vs both?)

### RAGAS Solution

RAGAS addresses these challenges by:

✅ **Component-Level Evaluation**: Separately assesses retrieval and generation quality
✅ **Automated Metrics**: Uses LLMs as evaluators (LLM-as-Judge pattern)
✅ **Synthetic Test Generation**: Can create test datasets automatically
✅ **Framework Integration**: Works with LangChain, LlamaIndex, and custom RAG systems

---

## 🏗️ Architecture Overview

### High-Level Structure

```
┌─────────────────────────────────────────────────────────────┐
│                     RAGAS Framework                          │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Metrics    │  │   TestSet    │  │ Integrations │     │
│  │   Engine     │  │  Generator   │  │    Layer     │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│         ▲                 ▲                  ▲              │
│         │                 │                  │              │
│         └─────────────────┴──────────────────┘              │
│                          │                                   │
│                   ┌──────▼───────┐                         │
│                   │   Evaluation  │                         │
│                   │     Core      │                         │
│                   └──────────────┘                          │
│                          │                                   │
│         ┌────────────────┴────────────────┐                │
│         ▼                                  ▼                │
│  ┌─────────────┐                   ┌─────────────┐        │
│  │  LLM        │                   │  Embeddings │        │
│  │  Providers  │                   │  Providers  │        │
│  └─────────────┘                   └─────────────┘        │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Source Code Organization

Located in `/src/ragas/` with the following structure:

```
ragas/
├── metrics/              # Evaluation metrics implementations
│   ├── _answer_correctness.py
│   ├── _faithfulness.py
│   ├── _context_precision.py
│   └── ...
├── llms/                 # LLM provider wrappers
│   ├── langchain.py
│   ├── llama_index.py
│   └── ...
├── embeddings/           # Embedding model interfaces
├── testset/              # Synthetic test generation
├── integrations/         # Third-party integrations
├── evaluation.py         # Core evaluation orchestration
├── dataset.py            # Dataset handling and validation
├── executor.py           # Async execution engine
└── cost.py              # Token usage tracking
```

---

## 🎭 Core Components

### 1. Metrics Engine

**Purpose**: Calculates evaluation scores across multiple dimensions

**Key Metrics Categories**:
- **Retrieval**: Context Precision, Context Recall, Context Relevance
- **Generation**: Faithfulness, Answer Relevancy, Answer Correctness
- **RAG-Specific**: Noise Sensitivity, Response Groundedness
- **Traditional NLP**: BLEU, ROUGE, CHRF, Semantic Similarity
- **Agentic**: Tool Call Accuracy, Agent Goal Accuracy, Topic Adherence

**Implementation Pattern**:
```python
from ragas.metrics import Faithfulness, AnswerRelevancy

class Metric:
    name: str
    _required_columns: tuple  # Dataset fields needed

    async def _ascore(self, row, callbacks) -> float:
        # LLM-based scoring logic
        pass
```

### 2. TestSet Generator

**Purpose**: Automatically create evaluation datasets from source documents

**Capabilities**:
- Generates diverse question types (simple, reasoning, multi-hop)
- Creates reference answers
- Produces distractor documents
- Supports multiple languages

**Workflow**:
```
Documents → Chunk → Extract Entities → Generate Questions → Create Test Set
```

### 3. Evaluation Core

**Purpose**: Orchestrates metric calculation across datasets

**Key Classes**:
- `EvaluationDataset`: Structured container for evaluation data
- `evaluate()`: Main function to run metrics on datasets
- `SingleTurnSample`: Single query-response evaluation unit
- `MultiTurnSample`: Conversational evaluation unit

**Usage Pattern**:
```python
from ragas import evaluate, EvaluationDataset

results = evaluate(
    dataset=eval_dataset,
    metrics=[faithfulness, answer_relevancy],
    llm=evaluator_llm,
    callbacks=[tracer]  # Optional observability
)
```

### 4. LLM Provider Layer

**Purpose**: Abstract LLM provider differences (OpenAI, Anthropic, local models)

**Supported Wrappers**:
- `LangchainLLMWrapper`: For LangChain LLMs
- `LlamaIndexLLMWrapper`: For LlamaIndex LLMs
- Direct API wrappers: OpenAI, Azure, Anthropic

**Why This Matters**:
- JSON output formatting varies by provider
- Different models have different prompt requirements
- Wrapper handles schema validation and retry logic

### 5. Integrations Layer

**Purpose**: Connect RAGAS with observability and development platforms

**Supported Platforms**:
- **LangSmith**: LangChain's tracing platform
- **Opik**: Open-source experiment tracking
- **Helicone**: LLM observability and caching
- **Arize Phoenix**: ML observability
- **Athina**: LLM testing platform

---

## 🎯 When to Use RAGAS

### ✅ RAGAS is Great For:

1. **RAG Pipeline Evaluation**: If you built a RAG system and need systematic evaluation
2. **Component-Level Diagnosis**: When you need to isolate retrieval vs generation failures
3. **Automated Testing**: CI/CD integration for regression detection
4. **Benchmarking**: Comparing multiple RAG configurations or LLM models
5. **Research & Development**: Iterating on RAG architectures with quantitative feedback

### ❌ RAGAS is NOT Ideal For:

1. **Non-RAG LLM Apps**: General chatbots, text generation, summarization (use DeepEval instead)
2. **Real-Time Production Monitoring**: High-latency LLM-as-Judge pattern (use TruLens instead)
3. **Business Outcome Metrics**: Investment decision quality, user satisfaction (needs human evaluation)
4. **Zero-Ground-Truth Scenarios**: Most metrics still need reference answers
5. **Ultra-Low-Cost Requirements**: RAGAS makes many LLM calls (expensive)

---

## 🔄 RAGAS Workflow (End-to-End)

### Standard Evaluation Pipeline

```
┌──────────────────────────────────────────────────────────────────┐
│  Step 1: Prepare Your RAG System                                  │
│  - Build retriever (vector DB, BM25, hybrid)                      │
│  - Build generator (LLM with prompt template)                     │
│  - Test that it returns responses                                 │
└────────────────────────┬─────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────────┐
│  Step 2: Collect Evaluation Data                                  │
│  - Run queries through your RAG system                            │
│  - Capture: query, retrieved_contexts, response                   │
│  - Optionally: Add reference answers (ground truth)               │
└────────────────────────┬─────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────────┐
│  Step 3: Create EvaluationDataset                                 │
│  - Format data into RAGAS schema                                  │
│  - Fields: user_input, response, retrieved_contexts, reference    │
│  - Load from dict, CSV, JSON, or HuggingFace                      │
└────────────────────────┬─────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────────┐
│  Step 4: Select Metrics                                           │
│  - Choose based on what you want to measure                       │
│  - Retrieval: context_precision, context_recall                   │
│  - Generation: faithfulness, answer_relevancy                     │
│  - Hybrid: answer_correctness, factual_correctness                │
└────────────────────────┬─────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────────┐
│  Step 5: Run Evaluation                                           │
│  - Call evaluate() with dataset + metrics                         │
│  - RAGAS makes LLM calls to score each sample                     │
│  - Handles async execution, batching, retries                     │
└────────────────────────┬─────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────────┐
│  Step 6: Analyze Results                                          │
│  - Convert to pandas: results.to_pandas()                         │
│  - Identify low-scoring samples                                   │
│  - Debug failures (retrieval vs generation issues)                │
│  - Track token costs: results.total_tokens                        │
└────────────────────────┬─────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────────┐
│  Step 7: Iterate & Improve                                        │
│  - Improve retrieval (chunking, indexing, reranking)              │
│  - Improve generation (prompts, LLM selection, context filtering) │
│  - Re-evaluate and compare versions                               │
└──────────────────────────────────────────────────────────────────┘
```

---

## 📊 RAGAS vs Manual Evaluation

| **Aspect** | **Manual Evaluation** | **RAGAS Evaluation** |
|------------|-----------------------|----------------------|
| **Speed** | Slow (hours per 20 queries) | Fast (minutes per 100 queries) |
| **Cost** | High (human time) | Medium (LLM API calls) |
| **Consistency** | Variable (human bias) | Consistent (algorithmic) |
| **Scalability** | Poor | Excellent |
| **Business Metrics** | ✅ Can capture | ❌ Cannot capture |
| **Technical Metrics** | ❌ Hard to quantify | ✅ Precise scores |
| **Debugging** | ✅ Contextual insights | ❌ Opaque scores |
| **CI/CD Integration** | ❌ Not feasible | ✅ Automated |

**Conclusion**: Use BOTH - RAGAS for automated technical metrics, manual evaluation for business quality

---

## 🔮 Evolution and Roadmap

### RAGAS Timeline

- **2023 Q3**: Initial release (v0.1.0) - Basic RAG metrics
- **2024 Q1**: Agent evaluation metrics added
- **2024 Q3**: Multi-turn conversation support
- **2025 Q1**: v0.3.0 - Synthetic testset generation improvements
- **2025 Q4** (Planned): Real-time evaluation, advanced agentic metrics

### Current State (v0.3.8)

✅ **Mature**:
- Core RAG metrics (Faithfulness, Context Precision, Answer Relevancy)
- LangChain/LlamaIndex integration
- HuggingFace dataset support
- Basic observability integration

⚠️ **In Development**:
- Agent evaluation metrics (stable but evolving)
- Multi-language support (experimental)
- Custom metric creation (API stabilizing)

❌ **Not Yet Supported**:
- Streaming evaluation
- Multi-modal RAG (images, audio)
- Fine-grained source attribution

---

## 🎓 Learning Path

**Beginner** (1-2 hours):
1. Read this overview
2. Run official quickstart: `ragas quickstart rag_eval`
3. Evaluate a simple RAG with 5 queries

**Intermediate** (1 day):
1. Read `02_metrics_deep_dive.md`
2. Implement custom RAG evaluation with 20+ queries
3. Integrate with LangSmith for tracing

**Advanced** (1 week):
1. Read `04_implementation_guide.md` and `05_challenges_and_pitfalls.md`
2. Deploy RAGAS in production CI/CD pipeline
3. Create custom metrics for domain-specific needs

---

## 📚 Additional Resources

### Official Documentation
- **Main Docs**: https://docs.ragas.io/
- **API Reference**: https://docs.ragas.io/en/latest/references/
- **Examples**: https://github.com/explodinggradients/ragas/tree/main/docs/howtos/

### Community
- **Discord**: https://discord.gg/5djav8GGNZ (800+ members)
- **GitHub Discussions**: https://github.com/explodinggradients/ragas/discussions

### Related Papers
- **Original Paper**: [Ragas: Automated Evaluation of Retrieval Augmented Generation](https://arxiv.org/abs/2309.15217)
- **RAG Survey**: [Retrieval-Augmented Generation for Large Language Models: A Survey](https://arxiv.org/abs/2312.10997)

---

**Next**: Read `02_metrics_deep_dive.md` to understand each metric in detail.
