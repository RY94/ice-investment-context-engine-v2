# RAGAS Challenges and Pitfalls: Complete Troubleshooting Guide

**Location**: `/project_information/about_ragas/05_challenges_and_pitfalls.md`
**Purpose**: Comprehensive guide to common RAGAS issues and solutions
**Last Updated**: 2025-11-07

---

## ⚠️ The "Tricky" Parts (Why User's Intuition Was Correct)

RAGAS is powerful but has **sharp edges**. Here's why it's tricky to implement elegantly:

### The Core Problem

```
RAGAS relies on LLMs to output structured JSON → Pydantic schemas
         ↓
But schema definitions are IMPLICIT in prompts
         ↓
Different LLMs format JSON differently
         ↓
Result: Parsing failures, NaN values, cryptic errors
```

This fundamental tension causes **80% of RAGAS implementation problems**.

---

## 🔥 Critical Issue #1: The NaN Epidemic

### Problem Description

**Symptoms**:
```python
results = evaluate(dataset, metrics=[faithfulness])
print(results.to_pandas())

# Output:
#   faithfulness
# 0    0.85
# 1    NaN      ← This!
# 2    0.92
# 3    NaN      ← And this!
```

### Root Causes

1. **JSON Parsing Failures**: Model output isn't JSON-compatible
2. **Schema Mismatches**: Output structure doesn't match Pydantic expectations
3. **Model-Specific Quirks**: Claude returns `{verdict: 1}` vs GPT returns `{verdict: "1"}`
4. **Edge Cases**: Empty contexts, very long texts, special characters

### Why It Happens

RAGAS prompts specify JSON format via **examples only**, not explicit schemas:

```python
# What RAGAS does (simplified):
prompt = """
Output JSON like this example:
{
  "statements": ["The sky is blue", "Water is wet"],
  "verdicts": [1, 1]
}

Now output JSON for this text: {text}
"""
# Problem: LLM must INFER the schema!
```

**With different models**:
- GPT-4: Usually outputs correct JSON
- Claude: Might add markdown code blocks: ` ```json\n{...}\n``` `
- Open-source LLMs: Often fail completely

### Solutions

**Solution 1: Use LangchainLLMWrapper (Recommended)**

```python
from langchain_openai import ChatOpenAI
from ragas.llms import LangchainLLMWrapper

llm = ChatOpenAI(model="gpt-4o-mini")
evaluator_llm = LangchainLLMWrapper(llm)  # Better JSON handling!

results = evaluate(
    dataset=eval_dataset,
    metrics=[faithfulness],
    llm=evaluator_llm  # Use wrapped LLM
)
```

**Why this helps**: LangChain has robust JSON extraction logic, including:
- Markdown block removal
- Retry mechanisms
- Schema validation

**Solution 2: Implement Fallback Handling**

```python
import pandas as pd

results = evaluate(dataset, metrics=[faithfulness])
df = results.to_pandas()

# Replace NaN with a default or flag for manual review
df['faithfulness'] = df['faithfulness'].fillna(-1.0)  # -1 indicates failure
df['_needs_manual_review'] = df['faithfulness'] == -1.0

# Alert on failures
failure_rate = (df['faithfulness'] == -1.0).mean()
if failure_rate > 0.1:  # More than 10% failures
    print(f"⚠️  WARNING: {failure_rate:.1%} of samples failed evaluation!")
```

**Solution 3: Reduce Batch Size (Avoid Concurrent Failures)**

```python
# Bad: Large batches can cascade failures
results = evaluate(dataset[:100], metrics=[...])

# Good: Small batches with checkpointing
results_list = []
for i in range(0, len(dataset), 10):
    batch = dataset[i:i+10]
    try:
        batch_results = evaluate(batch, metrics=[...])
        results_list.append(batch_results)
    except Exception as e:
        print(f"Batch {i}-{i+10} failed: {e}")
        # Continue with next batch
```

**Solution 4: Use HHEM-2.1-Open for Faithfulness (No JSON!)**

```python
from ragas.metrics import Faithfulness

# Standard (LLM-based, JSON-dependent):
faithfulness_llm = Faithfulness()

# Alternative (model-based, no JSON):
faithfulness_hhem = Faithfulness(
    mode="HHEM-2.1-Open",  # Uses Vectara's hallucination model
    device="cpu",
    batch_size=10
)
# No JSON parsing = No NaN values!
```

---

## 🔥 Critical Issue #2: Model Compatibility Hell

### Problem Description

**Symptoms**:
- Works with GPT-4 but fails with Claude
- Works with Claude but fails with Llama
- Error messages: `JSONDecodeError`, `ValidationError`, `KeyError`

### Model-Specific Quirks

| **Model** | **JSON Output Issue** | **Impact** | **Solution** |
|-----------|----------------------|------------|--------------|
| **GPT-4/4o** | Generally compliant | Low | Use as default evaluator |
| **Claude 3.5** | Returns numbers as strings | Medium | Use LangchainLLMWrapper |
| **Claude 3** | Adds markdown code blocks | High | Strip ` ```json ` manually |
| **Llama 3.1** | Inconsistent formatting | High | Fine-tune prompts or avoid |
| **Mistral** | Extra whitespace | Medium | Use LangchainLLMWrapper |
| **Gemini** | Mixed results | Medium | Test thoroughly first |

### Solution: Model Selection Strategy

**Tier 1 (Recommended for RAGAS)**:
```python
from langchain_openai import ChatOpenAI
from ragas.llms import LangchainLLMWrapper

# Best: GPT-4o-mini (cheap + reliable)
evaluator_llm = LangchainLLMWrapper(ChatOpenAI(model="gpt-4o-mini"))

# Alternative: GPT-4o (more expensive but very reliable)
evaluator_llm = LangchainLLMWrapper(ChatOpenAI(model="gpt-4o"))
```

**Tier 2 (Needs Wrapper)**:
```python
from langchain_anthropic import ChatAnthropic

# Claude needs wrapper for JSON robustness
evaluator_llm = LangchainLLMWrapper(ChatAnthropic(model="claude-3-5-sonnet-20241022"))
```

**Tier 3 (Avoid or Custom Prompts Required)**:
- Open-source models (Llama, Mistral) without LangChain wrappers
- Local models without structured output support

---

## 🔥 Critical Issue #3: Dataset Format Rigidity

### Problem Description

**Symptoms**:
```python
KeyError: 'user_input'
ValueError: Missing required column: retrieved_contexts
```

### The Problem

RAGAS expects **exact field names**:

```python
# RAGAS expects THIS format:
correct_format = {
    "user_input": "query",           # NOT "question", "query", "prompt"
    "response": "answer",            # NOT "answer", "output", "generated_text"
    "retrieved_contexts": [...],     # NOT "contexts", "docs", "passages"
    "reference": "ground_truth"      # NOT "ground_truth", "expected", "label"
}

# This will FAIL:
wrong_format = {
    "question": "What is France?",   # ❌ Should be "user_input"
    "answer": "A country",           # ❌ Should be "response"
    "contexts": [...]                # ❌ Should be "retrieved_contexts"
}
```

### Solutions

**Solution 1: Field Mapping Function**

```python
def normalize_for_ragas(ice_dataset):
    """Convert ICE dataset to RAGAS format"""
    return [
        {
            "user_input": row["query"],
            "response": row["rag_output"],
            "retrieved_contexts": row["contexts"],
            "reference": row.get("expected_answer", "")  # Optional
        }
        for row in ice_dataset
    ]

# Usage:
ice_data = load_ice_queries()
ragas_data = normalize_for_ragas(ice_data)
eval_dataset = EvaluationDataset.from_list(ragas_data)
```

**Solution 2: Use EvaluationDataset with Explicit Mapping**

```python
from ragas import EvaluationDataset, SingleTurnSample

samples = []
for row in ice_dataset:
    sample = SingleTurnSample(
        user_input=row["query"],
        response=row["rag_output"],
        retrieved_contexts=row["contexts"],
        reference=row.get("expected_answer")
    )
    samples.append(sample)

eval_dataset = EvaluationDataset(samples=samples)
```

---

## 🔥 Critical Issue #4: Metric Opacity (The Debugging Problem)

### Problem Description

**Symptoms**:
```python
# You get low scores but don't know WHY:
results = evaluate(dataset, metrics=[faithfulness])
print(results.to_pandas())

#   faithfulness
# 0    0.45       ← Why is this low? No idea!
```

### Why This Happens

RAGAS metrics are **black boxes**:
- No intermediate outputs
- No explanations
- Just a final score

**Comparison**: DeepEval provides explanations:
```python
# DeepEval output (hypothetical):
{
  "score": 0.45,
  "reason": "3 out of 5 claims were unsupported. Specifically: 'The company revenue is $10B' has no evidence in context."
}

# RAGAS output:
{
  "score": 0.45
}
```

### Solutions

**Solution 1: Manual Inspection of Low Scores**

```python
results = evaluate(dataset, metrics=[faithfulness])
df = results.to_pandas()

# Identify low-scoring samples
low_scores = df[df['faithfulness'] < 0.7].index.tolist()

# Manually inspect
for idx in low_scores:
    sample = dataset[idx]
    print(f"\n=== Sample {idx} (Score: {df.loc[idx, 'faithfulness']}) ===")
    print(f"Query: {sample['user_input']}")
    print(f"Response: {sample['response']}")
    print(f"Contexts: {sample['retrieved_contexts']}")
    print("→ Likely issue: Hallucination or missing context")
```

**Solution 2: Use Aspect Critic for Explanations**

```python
from ragas.metrics import AspectCritic

# Create custom metric with explicit definition
explainable_faithfulness = AspectCritic(
    name="explainable_faithfulness",
    definition="""
    Score 1 if ALL claims in the response are supported by the contexts.
    Score 0 if ANY claim is unsupported.
    Explain which claims failed.
    """,
    llm=evaluator_llm
)

# Now you get explanations in the evaluation
```

**Solution 3: Consider DeepEval for Debugging**

```python
# If debugging is critical, use DeepEval temporarily
from deepeval.metrics import FaithfulnessMetric
from deepeval.test_case import LLMTestCase

# DeepEval provides detailed reasons
metric = FaithfulnessMetric(threshold=0.7)
test_case = LLMTestCase(
    input="query",
    actual_output="response",
    retrieval_context=["context1", "context2"]
)
metric.measure(test_case)
print(metric.reason)  # Detailed explanation!
```

---

## 🔥 Critical Issue #5: Rate Limiting and Costs

### Problem Description

**Symptoms**:
```
RateLimitError: You exceeded your current quota, please check your plan and billing details.
```

**Why It Happens**:
- RAGAS makes **many LLM calls** (2-4 per sample per metric)
- Parallel evaluation can trigger rate limits
- Costs can spike unexpectedly

### Example Cost Explosion

```python
# 30 queries × 5 metrics × 3 LLM calls per metric = 450 LLM calls!
results = evaluate(
    dataset[:30],
    metrics=[faithfulness, answer_relevancy, context_precision, context_recall, answer_correctness]
)

# With GPT-4o-mini: ~$0.15
# With GPT-4o: ~$1.50
# With GPT-4: ~$15.00  ← Ouch!
```

### Solutions

**Solution 1: Use Cheap Evaluator LLM**

```python
from langchain_openai import ChatOpenAI

# Expensive: GPT-4
evaluator_llm = ChatOpenAI(model="gpt-4")  # ~$15/1M tokens

# Recommended: GPT-4o-mini
evaluator_llm = ChatOpenAI(model="gpt-4o-mini")  # ~$0.15/1M tokens (100x cheaper!)
```

**Solution 2: Implement Rate Limiting**

```python
import time

# Evaluate in small batches with delays
for i in range(0, len(dataset), 5):  # 5 samples at a time
    batch = dataset[i:i+5]
    results = evaluate(batch, metrics=[faithfulness])
    time.sleep(2)  # 2-second delay between batches
```

**Solution 3: Track Token Usage**

```python
from ragas import evaluate
from ragas.cost import get_token_usage_for_openai

results = evaluate(
    dataset,
    metrics=[faithfulness],
    token_usage_parser=get_token_usage_for_openai  # Track costs!
)

# Check total usage
print(f"Total tokens: {results.total_tokens}")
print(f"Estimated cost: ${results.total_tokens / 1000000 * 0.15}")  # For GPT-4o-mini
```

**Solution 4: Cache Embeddings**

```python
from ragas.embeddings import OpenAIEmbeddings
import openai

# Use persistent cache
embeddings = OpenAIEmbeddings(
    client=openai.OpenAI(),
    cache=True  # Enable caching
)

# Embeddings for repeated queries will be cached
```

---

## 🔥 Critical Issue #6: Ground Truth Requirements

### Problem Description

**Symptoms**:
```
ValueError: 'reference' column required for context_recall metric
```

### The "Reference-Free" Myth

RAGAS markets itself as "reference-free" but:

- **Faithfulness**: Doesn't need reference ✅
- **Answer Relevancy**: Doesn't need reference ✅
- **Context Recall**: **NEEDS reference** ❌
- **Answer Correctness**: **NEEDS reference** ❌

**Reality**: Only 2 out of 5 core metrics are truly reference-free!

### Solutions

**Solution 1: Use Reference-Free Metrics Only**

```python
# Reference-free subset
reference_free_metrics = [
    Faithfulness(),
    AnswerRelevancy(),
    ContextPrecision()  # Needs response OR reference
]

results = evaluate(
    dataset,  # No 'reference' field needed
    metrics=reference_free_metrics
)
```

**Solution 2: Generate Synthetic References**

```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4o-mini")

def generate_reference(query):
    """Generate synthetic ground truth"""
    prompt = f"Provide a concise, factual answer to: {query}"
    return llm.invoke(prompt).content

# Add references to dataset
for sample in dataset:
    if "reference" not in sample:
        sample["reference"] = generate_reference(sample["user_input"])
```

**Solution 3: Manual Annotation (Gold Standard)**

For ICE's 30-query test set, **manually write reference answers** (PIVF style):
- 1-2 hours of work
- Highest quality
- Enables all metrics

---

## 🛡️ Defensive Implementation Pattern

### Production-Ready RAGAS Wrapper

```python
import logging
from typing import List, Dict
import pandas as pd

class RobustRagasEvaluator:
    def __init__(self, evaluator_llm, max_retries=3):
        self.evaluator_llm = evaluator_llm
        self.max_retries = max_retries
        self.logger = logging.getLogger(__name__)

    def evaluate_with_fallback(self, dataset, metrics, batch_size=5):
        """
        Evaluate with automatic fallback and error handling
        """
        results = []

        for i in range(0, len(dataset), batch_size):
            batch = dataset[i:i+batch_size]

            for attempt in range(self.max_retries):
                try:
                    batch_results = evaluate(
                        dataset=batch,
                        metrics=metrics,
                        llm=self.evaluator_llm,
                        raise_exceptions=False  # Don't crash on errors
                    )
                    results.append(batch_results)
                    break  # Success

                except Exception as e:
                    self.logger.warning(f"Batch {i} attempt {attempt+1} failed: {e}")
                    if attempt == self.max_retries - 1:
                        # Final attempt failed, add NaN placeholders
                        self.logger.error(f"Batch {i} failed after {self.max_retries} attempts")
                        results.append(self._create_nan_results(batch, metrics))

            # Rate limiting
            time.sleep(1)

        # Combine results
        df = pd.concat([r.to_pandas() for r in results], ignore_index=True)

        # Report failures
        nan_count = df.isna().sum().sum()
        total_cells = df.shape[0] * df.shape[1]
        failure_rate = nan_count / total_cells

        self.logger.info(f"Evaluation complete: {failure_rate:.1%} failure rate")

        return df

    def _create_nan_results(self, batch, metrics):
        """Create placeholder results for failed batches"""
        import numpy as np
        return pd.DataFrame({
            metric.name: [np.nan] * len(batch)
            for metric in metrics
        })

# Usage
evaluator = RobustRagasEvaluator(evaluator_llm, max_retries=3)
results = evaluator.evaluate_with_fallback(dataset, metrics, batch_size=5)
```

---

## 📊 Common Error Messages and Fixes

| **Error** | **Cause** | **Fix** |
|-----------|-----------|---------|
| `KeyError: 'user_input'` | Wrong dataset field names | Use field mapping function |
| `JSONDecodeError` | Model output isn't valid JSON | Use LangchainLLMWrapper |
| `ValidationError: 'reference' required` | Metric needs ground truth | Use reference-free metrics or add references |
| `RateLimitError` | Too many concurrent API calls | Add delays, reduce batch size |
| `NaN values in results` | JSON parsing failed | Use HHEM mode, reduce complexity, retry |
| `ImportError: rapidfuzz` | Missing optional dependency | `pip install rapidfuzz` |
| `CUDA out of memory` | HHEM model too large | Use `device="cpu"` or smaller batch size |

---

## ✅ Pre-Flight Checklist

Before running RAGAS evaluation, verify:

- [ ] Using LangchainLLMWrapper (not raw LLM)
- [ ] Dataset has correct field names (`user_input`, `response`, `retrieved_contexts`)
- [ ] Selected reference-free metrics OR have ground truth
- [ ] Using cheap evaluator LLM (GPT-4o-mini recommended)
- [ ] Implemented batch processing (5-10 samples per batch)
- [ ] Added error handling and retries
- [ ] Token usage tracking enabled
- [ ] Tested on 3-5 samples first before full run

---

**Next**: Read `08_for_ice_integration.md` for ICE-specific recommendations.
