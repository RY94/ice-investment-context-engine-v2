# RAGAS Metrics: Complete Reference Guide

**Location**: `/project_information/about_ragas/02_metrics_deep_dive.md`
**Purpose**: Comprehensive understanding of all RAGAS evaluation metrics
**Last Updated**: 2025-11-07

---

## 📊 Metrics Taxonomy

RAGAS provides **20+ metrics** organized into 6 categories:

```
RAGAS Metrics
├── RAG-Specific (Core)
│   ├── Retrieval Quality
│   │   ├── Context Precision
│   │   ├── Context Recall
│   │   └── Context Relevance
│   └── Generation Quality
│       ├── Faithfulness
│       ├── Answer Relevancy
│       └── Answer Correctness
├── Component-Level
│   ├── Entity-Based
│   ├── Noise Sensitivity
│   └── Response Groundedness
├── Traditional NLP
│   ├── BLEU
│   ├── ROUGE-L
│   ├── CHRF
│   └── Semantic Similarity
├── Agentic (Advanced)
│   ├── Tool Call Accuracy
│   ├── Agent Goal Accuracy
│   └── Topic Adherence
├── General Purpose
│   ├── Aspect Critic
│   ├── Instance Rubrics
│   └── Rubrics-Based Scoring
└── SQL-Specific
    └── SQL Correctness
```

---

## 🎯 Core RAG Metrics (Most Important)

### 1. Faithfulness

**What it measures**: How factually grounded the response is in the retrieved context

**Formula**:
```
Faithfulness = (Claims supported by context) / (Total claims in response)
```

**Score Range**: 0.0 to 1.0 (higher is better)

**How it works**:
1. **Claim Extraction**: LLM extracts all factual statements from the response
2. **Claim Verification**: Each claim is checked against retrieved contexts
3. **Score Calculation**: Ratio of verified claims to total claims

**Data Requirements**:
```python
{
    "user_input": "When was the first super bowl?",
    "response": "The first superbowl was held on Jan 15, 1967",
    "retrieved_contexts": [
        "The first AFL-NFL World Championship Game in professional American football, known retroactively as Super Bowl I, was held on January 15, 1967."
    ]
}
```

**Example Scores**:
- Perfect grounding: 1.0
- Half the claims unsupported: 0.5
- Complete hallucination: 0.0

**When to use**:
- Detect hallucinations
- Ensure factual accuracy
- Validate that responses don't fabricate information

**Limitations**:
- Doesn't check if claims are actually correct, only if they're in context
- Subjective claim extraction (depends on LLM interpretation)
- Can miss subtle misrepresentations

**Alternative Implementation**: HHEM-2.1-Open (Vectara's hallucination model)
```python
from ragas.metrics import Faithfulness

faithfulness = Faithfulness(mode="HHEM-2.1-Open", device="cpu", batch_size=10)
```

---

### 2. Answer Relevancy (aka Response Relevancy)

**What it measures**: How well the response addresses the user's query

**Formula**:
```
Answer Relevancy = (1/N) × Σ cosine_similarity(embedding(generated_question_i), embedding(user_input))

where N = number of generated questions (default 3)
```

**Score Range**: 0.0 to 1.0 (higher is better)

**How it works**:
1. **Reverse Question Generation**: LLM generates questions that the response would answer
2. **Embedding Comparison**: Compute cosine similarity between generated questions and original query
3. **Averaging**: Mean of all similarity scores

**Example**:
```
User Input: "Where is France and what is its capital?"

Response A (Low relevancy): "France is in western Europe"
→ Generated Q: "Where is France located?"
→ Similarity: 0.6

Response B (High relevancy): "France is in western Europe and Paris is its capital"
→ Generated Q1: "Where is France?"
→ Generated Q2: "What is the capital of France?"
→ Similarity: 0.95
```

**Data Requirements**:
```python
{
    "user_input": "What is the capital of France?",
    "response": "Paris is the capital of France, located in the north-central part of the country."
}
```

**When to use**:
- Detect off-topic responses
- Measure completeness (did it answer all parts of the question?)
- Penalize verbose or rambling answers

**Limitations**:
- Requires LLM + embeddings (expensive)
- Embedding similarity can miss semantic nuances
- Number of generated questions affects score (N parameter tuning needed)

---

### 3. Context Precision

**What it measures**: How well the retrieval system ranks relevant chunks over irrelevant ones

**Formula**:
```
Context Precision@K = Σ (Precision@k × v_k) / Total relevant items in top K

where:
  v_k = 1 if chunk k is relevant, 0 otherwise
  Precision@k = true_positives@k / (true_positives@k + false_positives@k)
```

**Score Range**: 0.0 to 1.0 (higher is better)

**How it works**:
1. **Relevance Assessment**: LLM judges if each retrieved chunk is relevant to the query
2. **Position-Weighted Scoring**: Earlier relevant chunks contribute more to the score
3. **Mean Average Precision**: Calculates precision at each relevant chunk position

**Example**:
```
Query: "How do I handle exceptions in Python?"
Retrieved Contexts: [Relevant, Irrelevant, Relevant, Relevant, Irrelevant]

Calculation:
- Position 1: Relevant → Precision@1 = 1/1 = 1.0
- Position 2: Irrelevant → Skip
- Position 3: Relevant → Precision@3 = 2/3 = 0.67
- Position 4: Relevant → Precision@4 = 3/4 = 0.75

Context Precision = (1.0 + 0.67 + 0.75) / 3 = 0.81
```

**Data Requirements** (4 variants available):

**LLM-Based (with reference)**:
```python
{
    "user_input": "query",
    "retrieved_contexts": [...],
    "reference": "expected answer"
}
```

**LLM-Based (without reference)**:
```python
{
    "user_input": "query",
    "retrieved_contexts": [...],
    "response": "generated answer"
}
```

**Non-LLM (requires rapidfuzz)**:
```python
{
    "retrieved_contexts": [...],
    "reference_contexts": [...]  # Ground truth contexts
}
```

**When to use**:
- Optimize retrieval ranking algorithms
- Detect if irrelevant chunks pollute the context window
- A/B test different retrieval strategies (vector search vs hybrid vs reranking)

**Limitations**:
- Relevance judgment is subjective (depends on evaluator LLM)
- Doesn't measure if the TOP-1 result is perfect, just overall ranking quality
- Expensive (requires LLM call per chunk)

---

### 4. Context Recall

**What it measures**: What fraction of the ground truth answer is retrievable from the contexts

**Formula**:
```
Context Recall = (Ground truth sentences supported by contexts) / (Total ground truth sentences)
```

**Score Range**: 0.0 to 1.0 (higher is better)

**How it works**:
1. **Ground Truth Decomposition**: Break reference answer into atomic facts
2. **Attribution Checking**: Verify if each fact can be found in retrieved contexts
3. **Coverage Calculation**: Ratio of attributed facts to total facts

**Example**:
```
Ground Truth: "France is in Europe. Paris is its capital. It has 67 million people."
Retrieved Contexts: ["France is a European country.", "Paris is the capital of France."]

Supported: 2/3 sentences
Context Recall = 0.67
```

**Data Requirements**:
```python
{
    "user_input": "Tell me about France",
    "retrieved_contexts": [...],
    "reference": "France is in Europe and its capital is Paris."  # Ground truth
}
```

**When to use**:
- Detect if retrieval is missing critical information
- Measure "coverage" of your knowledge base
- Identify gaps in document indexing

**Limitations**:
- **Requires ground truth answers** (not truly "reference-free")
- Doesn't care if irrelevant information is also retrieved
- Sentence-level granularity may miss nuanced incompleteness

---

### 5. Answer Correctness (Hybrid Metric)

**What it measures**: Combination of semantic similarity + factual overlap with ground truth

**Formula**:
```
Answer Correctness = w₁ × F1_score + w₂ × Semantic_Similarity

where:
  F1_score = harmonic mean of precision and recall (factual statements)
  Semantic_Similarity = cosine similarity of embeddings
  w₁, w₂ = weights (default: [0.75, 0.25])
```

**Score Range**: 0.0 to 1.0 (higher is better)

**How it works**:
1. **Factual Comparison**: Extract facts from answer and reference, compute F1
2. **Semantic Comparison**: Embed both texts, compute cosine similarity
3. **Weighted Combination**: Blend factual precision with semantic closeness

**Data Requirements**:
```python
{
    "user_input": "Who won the most super bowls?",
    "response": "The most super bowls have been won by The New England Patriots",
    "reference": "The New England Patriots have won the Super Bowl a record six times"
}
```

**When to use**:
- End-to-end quality assessment (considers both retrieval and generation)
- Balances strict factual accuracy with semantic meaning
- Good for general RAG benchmarking

**Limitations**:
- Requires ground truth reference
- Weights (w₁, w₂) are somewhat arbitrary
- Factual F1 calculation is LLM-dependent

---

## 🔬 Advanced Metrics

### 6. Context Relevance (Noise Sensitivity)

**What it measures**: Fraction of retrieved contexts that are actually relevant

**Formula**:
```
Context Relevance = (Relevant sentences in contexts) / (Total sentences in contexts)
```

**Use case**: Detect if retrieval is pulling in too much noise

---

### 7. Factual Correctness

**What it measures**: Like Answer Correctness but with stricter factual checking

**Mode**: Can use F1 or precision-only scoring

**Use case**: When factual accuracy is critical (medical, legal, financial)

---

### 8. Context Entities Recall

**What it measures**: What fraction of entities in ground truth are present in contexts

**Use case**: Entity-heavy domains (knowledge graphs, structured data)

---

## 🤖 Agentic Metrics (For Multi-Step RAG)

### 9. Tool Call Accuracy

**What it measures**: Whether the RAG agent called the right tools with correct parameters

**Use case**: Multi-tool RAG systems (web search + vector DB + SQL)

---

### 10. Agent Goal Accuracy

**What it measures**: Whether the agent achieved the user's intended goal

**Use case**: Task-oriented RAG (booking, analysis, report generation)

---

### 11. Topic Adherence

**What it measures**: Whether the conversation stays on topic across turns

**Use case**: Multi-turn RAG chatbots

---

## 📐 Traditional NLP Metrics

These are **reference-based** and don't use LLMs:

### 12. BLEU
- **What**: N-gram overlap with reference
- **Use**: Translation-style tasks
- **Range**: 0-1

### 13. ROUGE-L
- **What**: Longest common subsequence
- **Use**: Summarization tasks
- **Range**: 0-1

### 14. CHRF
- **What**: Character n-gram F-score
- **Use**: Morphology-rich languages
- **Range**: 0-100

### 15. Semantic Similarity
- **What**: Cosine similarity of embeddings
- **Use**: Meaning preservation
- **Range**: 0-1

---

## 🎨 Custom Metrics: Aspect Critic & Rubrics

### 16. Aspect Critic

**What it measures**: User-defined aspect of quality

**Example**:
```python
from ragas.metrics import AspectCritic

aspect_critic = AspectCritic(
    name="investment_actionability",
    definition="Is the response actionable for portfolio managers? Score 1 if it provides clear buy/sell/hold guidance with reasoning, 0 otherwise.",
    llm=evaluator_llm
)
```

**Use case**: Domain-specific evaluation (ICE could use this for investment decision quality!)

---

### 17. Instance Rubrics & Rubrics-Based Scoring

**What it measures**: Multi-level scoring with detailed rubrics

**Example**:
```python
rubrics = {
    "score0_description": "Off-topic or irrelevant",
    "score1_description": "Partially addresses the query",
    "score2_description": "Fully relevant and comprehensive"
}
```

**Use case**: Fine-grained quality assessment

---

## 🎯 Metric Selection Guide for ICE

### For ICE's 30-Query Test Set

| **ICE Category** | **Recommended RAGAS Metrics** | **Why** |
|------------------|-------------------------------|---------|
| **Portfolio Inventory** | Answer Correctness, Context Recall | Need exact ticker/count accuracy |
| **Portfolio Risk** | Faithfulness, Context Precision | Hallucinated risks are dangerous |
| **Portfolio Opportunity** | Answer Relevancy, Faithfulness | Must address query + be grounded |
| **Entity Extraction** | Custom Aspect Critic (F1) | RAGAS doesn't have entity F1 metric |
| **Multi-Hop Reasoning** | Answer Correctness, Context Precision | Need full reasoning chain |
| **Email-Specific** | Faithfulness, Context Recall | Table/analyst signal accuracy |

### Cost-Optimized Subset (Top 5)

If you need to minimize LLM calls, prioritize:

1. **Faithfulness** → Detect hallucinations
2. **Answer Relevancy** → Ensure query is addressed
3. **Context Precision** → Optimize retrieval ranking
4. **Semantic Similarity** → Cheap, no LLM needed
5. **Custom Aspect Critic** → Domain-specific quality

---

## 💰 Cost Analysis

**Typical Costs per Sample** (with GPT-4o-mini as evaluator):

| **Metric** | **LLM Calls** | **Tokens** | **Cost** |
|------------|---------------|------------|----------|
| Faithfulness | 2-3 | ~500-1000 | $0.001 |
| Answer Relevancy | 3-4 | ~600-1200 | $0.0015 |
| Context Precision | 1 per chunk | ~200 per chunk | $0.0004 per chunk |
| Context Recall | 1-2 | ~400-800 | $0.001 |
| Answer Correctness | 1-2 | ~500-1000 | $0.0012 |
| Semantic Similarity | 0 (embeddings only) | N/A | $0.0001 |

**For ICE's 30-query test set**:
- All 5 core metrics: ~30 × $0.005 = **$0.15 per run**
- Weekly validation (30 queries): ~$0.60/month
- With 180 runs (6 modes): ~$27 per deep validation

**Cost Optimization**:
- Use Haiku (Claude) or GPT-4o-mini for evaluation (10x cheaper than GPT-4)
- Cache embeddings for repeated queries
- Run expensive metrics only on failed samples

---

**Next**: Read `04_implementation_guide.md` for practical code examples.
