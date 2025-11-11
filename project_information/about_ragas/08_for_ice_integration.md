# RAGAS Integration Guide for ICE Project

**Location**: `/project_information/about_ragas/08_for_ice_integration.md`
**Purpose**: Specific recommendations for integrating RAGAS into ICE evaluation framework
**Last Updated**: 2025-11-07
**Target Audience**: ICE Development Team

---

## 🎯 ICE-Specific Context

### ICE Architecture Characteristics

**What makes ICE unique**:
1. **LightRAG-based**: Uses knowledge graph + vector search (not standard vector DB)
2. **Multi-hop reasoning**: Supports 1-3 hop graph traversal
3. **Source attribution**: Every fact must trace to email source
4. **Investment focus**: Needs business metrics (risk awareness, actionability)
5. **Budget constraint**: <$200/month cost target
6. **Email-centric**: Data from research analyst emails, earnings reports, morning briefs

**Implications for RAGAS Integration**:
- ✅ Can use standard RAGAS metrics (Faithfulness, Answer Relevancy)
- ⚠️ Need custom metrics for multi-hop reasoning depth
- ⚠️ Need custom metrics for source attribution quality
- ⚠️ Cannot rely solely on automated metrics for business decisions
- ✅ Budget-conscious evaluation (small test sets, cheap evaluator LLMs)

---

## 🏗️ Recommended Architecture: Hybrid Approach

### Two-Layer Evaluation Framework

```
┌─────────────────────────────────────────────────────────────────┐
│                 ICE Evaluation Framework                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────────┐         ┌──────────────────────┐     │
│  │  AUTOMATED LAYER     │         │   MANUAL LAYER       │     │
│  │  (RAGAS)             │         │   (PIVF)             │     │
│  ├──────────────────────┤         ├──────────────────────┤     │
│  │                      │         │                      │     │
│  │ • Faithfulness       │         │ • Decision Clarity   │     │
│  │ • Answer Relevancy   │         │ • Risk Awareness     │     │
│  │ • Context Precision  │         │ • Opportunity Recog  │     │
│  │ • Entity F1          │         │ • Time Horizon       │     │
│  │ • Source Quality     │         │ • Multi-hop Depth    │     │
│  │                      │         │                      │     │
│  │ Run: Weekly (auto)   │         │ Run: Milestone (man) │     │
│  │ Cost: $0.60/month    │         │ Cost: 2hrs labor     │     │
│  │ Coverage: 30 queries │         │ Coverage: 20 queries │     │
│  │                      │         │                      │     │
│  └──────────────────────┘         └──────────────────────┘     │
│            │                                  │                  │
│            └──────────────┬───────────────────┘                 │
│                           ▼                                      │
│              ┌──────────────────────┐                           │
│              │  Combined Dashboard  │                           │
│              │  Quality Score Card  │                           │
│              └──────────────────────┘                           │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### Layer Responsibilities

**Automated Layer (RAGAS)** → Technical Quality
- Fast feedback loop (run on every commit or weekly)
- Detect regressions automatically
- Catch hallucinations, relevance issues
- Optimize retrieval and generation components

**Manual Layer (PIVF)** → Business Quality
- Deep qualitative assessment
- Investment decision quality
- Domain expertise validation
- Quarterly or major milestone reviews

---

## 📊 Recommended Metrics for ICE

### RAGAS Metrics Selection

Based on ICE's 30-query test set categories:

| **ICE Category** | **RAGAS Metric** | **Why** | **Data Needs** |
|------------------|------------------|---------|----------------|
| **Portfolio Inventory** (3 queries) | Answer Correctness | Exact ticker/count accuracy | reference |
| **Portfolio Risk** (5 queries) | Faithfulness + Context Precision | Hallucinated risks are dangerous | contexts |
| **Portfolio Opportunity** (5 queries) | Answer Relevancy + Faithfulness | Must address query + be grounded | contexts |
| **Entity Extraction** (5 queries) | Custom Aspect Critic (F1) | Ticker/analyst/rating extraction | reference |
| **Multi-Hop Reasoning** (5 queries) | Answer Correctness + Custom | Full reasoning chain validation | reference |
| **Comparative Analysis** (3 queries) | Answer Relevancy | Cross-holding comparison quality | - |
| **Email-Specific** (4 queries) | Faithfulness + Context Recall | Table/signal accuracy | reference |

### Custom Metrics for ICE

**Metric 1: Entity Extraction F1 Score**

```python
from ragas.metrics import AspectCritic

entity_f1_metric = AspectCritic(
    name="entity_extraction_f1",
    definition="""
    Extract all entities from the response: tickers, company names, analyst names, ratings (BUY/SELL/HOLD).
    Compare with ground truth entities.
    Calculate F1 = 2 × (precision × recall) / (precision + recall)
    where:
      precision = (extracted entities in ground truth) / (total extracted)
      recall = (ground truth entities extracted) / (total in ground truth)
    Return score between 0 and 1.
    """,
    llm=evaluator_llm
)
```

**Metric 2: Multi-Hop Reasoning Depth**

```python
multi_hop_metric = AspectCritic(
    name="multi_hop_reasoning_depth",
    definition="""
    Analyze if the response demonstrates multi-hop reasoning through the knowledge graph.
    Score based on reasoning depth:
    - 0.33: Single-hop (direct facts only)
    - 0.67: Two-hop (connects 2 entities/relationships)
    - 1.00: Three-hop (connects 3+ entities/relationships)

    Example 3-hop: "TSMC supplies chips to NVDA, which competes with AMD in AI market"
    """,
    llm=evaluator_llm
)
```

**Metric 3: Source Attribution Quality**

```python
source_quality_metric = AspectCritic(
    name="source_attribution_quality",
    definition="""
    Evaluate source citations in the response. Score based on:
    - Are sources cited? (0.33)
    - Are sources specific (email names, dates)? (0.67)
    - Are sources authoritative (DBS, UOB, earnings reports)? (1.00)

    Example high-quality: "According to DBS Sales Scoop (Aug 21, 2025), SATS received BUY rating"
    """,
    llm=evaluator_llm
)
```

---

## 💻 Implementation Code for ICE

### Step 1: Install RAGAS

```bash
# In ICE environment
pip install ragas
pip install langchain-openai  # For LLM wrapper
```

### Step 2: Create ICE-RAGAS Adapter

```python
# File: src/ice_evaluation/ragas_adapter.py
# Location: /src/ice_evaluation/ragas_adapter.py
# Purpose: Adapt ICE outputs to RAGAS format
# Why: ICE uses LightRAG, RAGAS expects standard RAG format
# Relevant Files: ice_query_processor.py, ice_system_manager.py

from typing import List, Dict
from ragas import EvaluationDataset, SingleTurnSample

class ICEtoRAGASAdapter:
    """Convert ICE query results to RAGAS evaluation format"""

    def __init__(self, ice_system):
        self.ice_system = ice_system

    def query_and_prepare(self, queries: List[str], references: List[str] = None) -> EvaluationDataset:
        """
        Run queries through ICE and format for RAGAS evaluation

        Args:
            queries: List of queries to evaluate
            references: Optional ground truth answers

        Returns:
            EvaluationDataset ready for RAGAS evaluation
        """
        samples = []

        for idx, query in enumerate(queries):
            # Query ICE system
            ice_result = self.ice_system.query(query)

            # Extract contexts from LightRAG
            contexts = self._extract_contexts(ice_result)

            # Create RAGAS sample
            sample = SingleTurnSample(
                user_input=query,
                response=ice_result['answer'],
                retrieved_contexts=contexts,
                reference=references[idx] if references else None
            )
            samples.append(sample)

        return EvaluationDataset(samples=samples)

    def _extract_contexts(self, ice_result: Dict) -> List[str]:
        """
        Extract retrieved contexts from ICE result

        ICE returns source attribution, convert to list of context strings
        """
        contexts = []

        # From source_emails field
        if 'source_emails' in ice_result:
            for email in ice_result['source_emails']:
                contexts.append(f"Email: {email['filename']}\n{email['relevant_excerpt']}")

        # From graph_paths (for multi-hop queries)
        if 'graph_paths' in ice_result:
            for path in ice_result['graph_paths']:
                contexts.append(f"Graph Path: {path['relationship_chain']}\n{path['evidence']}")

        return contexts if contexts else ["No contexts retrieved"]
```

### Step 3: Create ICE Evaluation Script

```python
# File: scripts/evaluate_ice_with_ragas.py
# Location: /scripts/evaluate_ice_with_ragas.py
# Purpose: Run RAGAS evaluation on ICE system
# Why: Automated quality assessment for CI/CD
# Relevant Files: test_queries_v2.csv, ice_query_processor.py

import pandas as pd
from langchain_openai import ChatOpenAI
from ragas.llms import LangchainLLMWrapper
from ragas.metrics import Faithfulness, AnswerRelevancy, ContextPrecision
from ragas import evaluate
from src.ice_evaluation.ragas_adapter import ICEtoRAGASAdapter
from src.ice_core.ice_system_manager import ICESystemManager

def evaluate_ice_with_ragas(test_csv_path: str, output_csv_path: str):
    """
    Evaluate ICE using RAGAS metrics

    Args:
        test_csv_path: Path to test_queries_v2.csv
        output_csv_path: Path to save results
    """

    # 1. Load test queries
    test_df = pd.read_csv(test_csv_path)
    queries = test_df['query'].tolist()
    references = test_df['reference_answer'].tolist() if 'reference_answer' in test_df else None

    # 2. Initialize ICE system
    ice_system = ICESystemManager()

    # 3. Convert ICE results to RAGAS format
    adapter = ICEtoRAGASAdapter(ice_system)
    eval_dataset = adapter.query_and_prepare(queries, references)

    # 4. Setup RAGAS evaluation
    evaluator_llm = LangchainLLMWrapper(ChatOpenAI(model="gpt-4o-mini"))

    # ICE-recommended metrics
    metrics = [
        Faithfulness(llm=evaluator_llm),
        AnswerRelevancy(llm=evaluator_llm),
        ContextPrecision(llm=evaluator_llm),
    ]

    # 5. Run evaluation
    print(f"Evaluating {len(queries)} queries with RAGAS...")
    results = evaluate(
        dataset=eval_dataset,
        metrics=metrics,
        llm=evaluator_llm,
        raise_exceptions=False  # Continue on errors
    )

    # 6. Save results
    results_df = results.to_pandas()
    results_df['query'] = queries
    results_df['category'] = test_df['category']
    results_df.to_csv(output_csv_path, index=False)

    # 7. Print summary
    print("\n=== RAGAS Evaluation Results ===")
    print(results_df[['faithfulness', 'answer_relevancy', 'context_precision']].describe())

    # Alert on low scores
    low_scores = results_df[results_df['faithfulness'] < 0.7]
    if not low_scores.empty:
        print(f"\n⚠️  {len(low_scores)} queries scored below 0.7 on faithfulness!")
        print(low_scores[['query', 'faithfulness']])

    return results_df

# Usage
if __name__ == "__main__":
    results = evaluate_ice_with_ragas(
        test_csv_path="test_queries_v2.csv",
        output_csv_path="results/ragas_evaluation_results.csv"
    )
```

### Step 4: Run Evaluation

```bash
# Weekly automated evaluation
python scripts/evaluate_ice_with_ragas.py

# Output:
# Evaluating 30 queries with RAGAS...
# === RAGAS Evaluation Results ===
#       faithfulness  answer_relevancy  context_precision
# count   30.000000         30.000000          30.000000
# mean     0.847000          0.912000           0.785000
# std      0.123000          0.089000           0.156000
# min      0.450000          0.720000           0.450000
# ...
```

---

## 📈 Cost Estimation for ICE

### Monthly Evaluation Costs

**Scenario 1: Weekly Core Validation (30 queries)**

```
Metrics: 3 (Faithfulness, Answer Relevancy, Context Precision)
Queries: 30
Frequency: Weekly (4 times/month)
Evaluator LLM: GPT-4o-mini

Calculation:
- Tokens per query per metric: ~800
- Total tokens per run: 30 × 3 × 800 = 72,000 tokens
- Cost per run: 72,000 / 1,000,000 × $0.15 = $0.011
- Monthly cost: $0.011 × 4 = $0.044

Result: ~$0.05/month
```

**Scenario 2: Deep Validation (180 runs = 30 queries × 6 modes)**

```
Frequency: Quarterly (once every 3 months)

Calculation:
- Tokens per deep validation: 30 × 6 × 3 × 800 = 432,000 tokens
- Cost per deep validation: $0.065
- Monthly amortized cost: $0.065 / 3 = $0.022

Result: ~$0.02/month
```

**Scenario 3: With Custom Metrics (5 total)**

```
Metrics: 5 (add Entity F1, Multi-Hop Depth, Source Quality)
Monthly cost: $0.05 × (5/3) = $0.083

Result: ~$0.08/month
```

**Total RAGAS Cost for ICE: <$0.10/month**

✅ **Well within <$200/month budget!**

---

## 🔄 Integration Workflow

### Weekly Automated Evaluation

```yaml
# .github/workflows/ice_evaluation.yml
name: ICE Quality Check

on:
  schedule:
    - cron: '0 9 * * 1'  # Every Monday 9am
  workflow_dispatch:  # Manual trigger

jobs:
  ragas_evaluation:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install ragas langchain-openai

      - name: Run RAGAS evaluation
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: |
          python scripts/evaluate_ice_with_ragas.py

      - name: Upload results
        uses: actions/upload-artifact@v3
        with:
          name: ragas-results
          path: results/ragas_evaluation_results.csv

      - name: Check for regressions
        run: |
          python scripts/check_quality_regression.py
```

---

## ⚙️ Configuration Best Practices for ICE

### 1. Use Budget-Conscious Settings

```python
from langchain_openai import ChatOpenAI

# Recommended for ICE: GPT-4o-mini
evaluator_llm = ChatOpenAI(
    model="gpt-4o-mini",  # $0.15/1M tokens vs $15/1M for GPT-4
    temperature=0.0,       # Deterministic for consistency
    max_retries=3         # Retry on transient failures
)
```

### 2. Implement Caching

```python
from ragas.embeddings import OpenAIEmbeddings
import openai

# Cache embeddings for repeated queries
embeddings = OpenAIEmbeddings(
    client=openai.OpenAI(),
    cache=True
)
```

### 3. Batch Processing

```python
# Evaluate in small batches to avoid rate limits
for i in range(0, len(queries), 5):
    batch = queries[i:i+5]
    results = evaluate_batch(batch)
    time.sleep(1)  # Throttle
```

---

## 🎯 Success Metrics

### Track These KPIs

**Technical Metrics (RAGAS)**:
- Average Faithfulness Score: Target >0.85
- Average Answer Relevancy: Target >0.90
- Average Context Precision: Target >0.80
- NaN Rate: Target <5%

**Business Metrics (Manual PIVF)**:
- Decision Clarity: Target >4.0/5
- Risk Awareness: Target >4.0/5
- Opportunity Recognition: Target >3.8/5
- Multi-Hop Reasoning: Target >3.5/5

**Operational Metrics**:
- Evaluation Time: <10 minutes for 30 queries
- Cost per Evaluation: <$0.05
- Failure Rate: <10% (NaN or errors)

---

## 🚀 Implementation Roadmap

### Phase 1: Foundation (Week 1)
- [ ] Install RAGAS and dependencies
- [ ] Create ICEtoRAGASAdapter
- [ ] Test on 5 sample queries
- [ ] Verify results make sense

### Phase 2: Integration (Week 2)
- [ ] Implement evaluation script
- [ ] Add custom ICE metrics (Entity F1, Multi-Hop)
- [ ] Run full 30-query evaluation
- [ ] Debug any NaN issues

### Phase 3: Automation (Week 3)
- [ ] Set up CI/CD workflow
- [ ] Create quality dashboard
- [ ] Implement alerting (Slack/email on failures)
- [ ] Document usage for team

### Phase 4: Refinement (Week 4)
- [ ] Compare RAGAS vs Manual PIVF scores
- [ ] Calibrate metric weights
- [ ] Add mode-specific evaluations
- [ ] Create quarterly deep validation process

---

## ⚠️ ICE-Specific Gotchas

### Issue 1: LightRAG Context Extraction

**Problem**: LightRAG returns graph paths, not flat contexts

**Solution**:
```python
def extract_contexts_from_lightrag(result):
    """LightRAG-specific context extraction"""
    contexts = []

    # From entities
    for entity in result.get('entities', []):
        contexts.append(f"Entity: {entity['name']}\n{entity['description']}")

    # From relationships
    for rel in result.get('relationships', []):
        contexts.append(f"Relationship: {rel['source']} → {rel['target']}\n{rel['description']}")

    return contexts
```

### Issue 2: Email Source Attribution

**Problem**: RAGAS doesn't validate source quality

**Solution**: Use custom Aspect Critic metric (see above)

### Issue 3: Multi-Hop Reasoning

**Problem**: Standard RAGAS metrics don't measure reasoning depth

**Solution**: Implement custom multi-hop metric (see above)

---

## 📚 Additional Resources

**ICE-Specific Documentation**:
- See `ICE_VALIDATION_FRAMEWORK.md` for PIVF golden queries
- See `CLAUDE_PATTERNS.md` for source attribution patterns
- See `test_queries_v2.csv` for complete test dataset

**RAGAS Documentation**:
- See `01_overview.md` for RAGAS fundamentals
- See `02_metrics_deep_dive.md` for metric details
- See `05_challenges_and_pitfalls.md` for troubleshooting

---

## ✅ Final Recommendations

**DO**:
✅ Use hybrid approach (RAGAS + manual PIVF)
✅ Start with 3 core metrics (Faithfulness, Answer Relevancy, Context Precision)
✅ Add custom ICE metrics (Entity F1, Multi-Hop, Source Quality)
✅ Use GPT-4o-mini for cost efficiency
✅ Implement robust error handling (NaN fallback)
✅ Track token costs

**DON'T**:
❌ Rely solely on RAGAS for business decisions
❌ Use expensive evaluator LLMs (GPT-4)
❌ Run large batches without rate limiting
❌ Skip custom metrics for ICE-specific needs
❌ Ignore NaN values (they indicate real issues)
❌ Forget to cache embeddings

**Expected Outcome**:
- **Technical Quality**: Automated, fast, consistent
- **Business Quality**: Manual PIVF validation
- **Cost**: <$0.10/month (well within budget)
- **Confidence**: Quantitative + qualitative evidence
- **Iteration Speed**: Weekly feedback loop

---

**This completes the RAGAS learning documentation for ICE integration.**
