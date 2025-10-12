# ICE Portfolio Intelligence Validation Framework (PIVF)

> **Location**: `/ICE_VALIDATION_FRAMEWORK.md`
> **Purpose**: Comprehensive validation framework for ICE RAG solution quality assessment
> **Business Value**: Evidence-driven development, demo-ready reporting, continuous improvement engine
> **Relevant Files**: `MODIFIED_OPTION_4_ANALYSIS.md`, `ice_simplified.py`, `CLAUDE.md`, `ICE_DEVELOPMENT_TODO.md`

---

## 📋 Table of Contents

1. [Executive Summary](#executive-summary)
2. [Framework Philosophy](#framework-philosophy)
3. [The Golden Test Set](#the-golden-test-set)
4. [Multi-Dimensional Scoring System](#multi-dimensional-scoring-system)
5. [Source Quality Framework](#source-quality-framework)
6. [Progressive Validation Workflow](#progressive-validation-workflow)
7. [Snapshot-Based Regression Testing](#snapshot-based-regression-testing)
8. [Failure Mode Taxonomy](#failure-mode-taxonomy)
9. [Query Mode Optimization](#query-mode-optimization)
10. [Integration with Modified Option 4](#integration-with-modified-option-4)
11. [Cost-Aware Metrics](#cost-aware-metrics)
12. [Framework Architecture](#framework-architecture)
13. [Usage Guide](#usage-guide)
14. [Demo-Ready Reporting](#demo-ready-reporting)
15. [Continuous Improvement Loop](#continuous-improvement-loop)
16. [Edge Case Handling](#edge-case-handling)
17. [Extensibility](#extensibility)
18. [Golden Test Set Templates](#golden-test-set-templates)
19. [Reference Answer Templates](#reference-answer-templates)
20. [Appendices](#appendices)

---

## 1. Executive Summary

### 1.1 What is PIVF?

The **ICE Portfolio Intelligence Validation Framework (PIVF)** is a comprehensive, business-outcome focused testing methodology designed specifically for the Investment Context Engine (ICE) RAG solution. Unlike traditional technical validation frameworks that focus purely on metrics like precision/recall, PIVF evaluates the **investment decision quality** that ICE produces.

**Key Design Principles:**
- ✅ **Business-Outcome Focused**: Measures investment decision quality, not just technical correctness
- ✅ **Evidence-Driven**: All improvement decisions backed by quantitative validation data
- ✅ **User-Centric**: Manual scoring by domain expert (you), not automated LLM-as-judge
- ✅ **Capstone-Optimized**: Simple enough for solo developer, robust enough for demo credibility

### 1.2 Framework Components

**Core Elements:**
1. **20 Golden Queries**: Carefully curated test cases representing real portfolio intelligence needs
2. **9-Dimensional Scoring**: Technical quality (5) + Business quality (4) assessment per query
3. **Progressive Validation**: 3-stage workflow (Smoke 5min → Core 30min → Deep 2hr)
4. **Failure Mode Taxonomy**: Diagnostic framework for understanding WHY failures occur
5. **Integration with Modified Option 4**: F1 score decision gates for development prioritization

**What PIVF Enables:**
- ✅ **Evidence-based development**: Know what to build next based on validation data
- ✅ **Demo-ready reporting**: Generate stakeholder-facing quality summaries
- ✅ **Regression prevention**: Snapshot-based version comparison (detect degradation early)
- ✅ **Cost optimization**: Quality-to-cost ratio measurement across LightRAG modes

### 1.3 Integration with ICE Development

**Modified Option 4 Decision Framework:**

```
Phase 0: Baseline Validation (3 days)
├── Run PIVF Core Validation (20 queries)
├── Calculate Entity Extraction F1 Score (Q011-Q015)
└── Decision Gate:
    ├── F1 ≥ 0.85 → Baseline sufficient, skip enhanced docs
    ├── F1 < 0.85 → Try targeted fix (Phase 2)
    └── F1 < 0.70 → Consider full enhanced docs (Phase 3)

Phase 1-3: Feature Development
├── Implement changes (query intelligence, enhanced docs, etc.)
├── Run PIVF A/B Validation (baseline vs new version)
└── Decide: Keep, refine, or revert based on overall score change
```

**PIVF answers critical development questions:**
- "Is the baseline good enough or do we need enhanced documents?"
- "Which query mode (hybrid, global, local) performs best for portfolio risk queries?"
- "Did the last feature improve or degrade overall quality?"
- "Which dimension (relevance, actionability, traceability) needs most improvement?"

### 1.4 Quick Start Overview

**30-Minute Setup:**
```bash
# 1. Create validation directory structure
mkdir -p validation/{golden_test_set,reference_answers,snapshots,scoring_worksheets,reports,scripts}

# 2. Copy golden test set template
cp validation_templates/golden_test_set.json validation/golden_test_set/

# 3. Run first smoke test (5 minutes)
cd validation/scripts
python run_validation.py --mode smoke --output ../snapshots/v1.0_baseline_smoke.json

# 4. Review outputs, write reference answers for 5 smoke queries
# 5. Score manually in CSV (5 × 9 dimensions)
# 6. Generate report
python generate_report.py --snapshot v1.0_baseline_smoke --output ../reports/v1.0_report.md
```

**Weekly Validation Cadence:**
- **Monday**: Run Core Validation (30 min), identify weakest dimension
- **Tuesday-Thursday**: Targeted improvement work
- **Friday**: Re-run validation, compare snapshots, generate report

---

## 2. Framework Philosophy

### 2.1 Why Business-Outcome Focused?

**Traditional RAG Validation Approach:**
```
Metric: Precision = 0.87, Recall = 0.82
Interpretation: "Good enough?"
Problem: Doesn't tell you if users make better investment decisions
```

**PIVF Approach:**
```
Query: "What are risks for my NVDA position?"
ICE Response: "NVDA faces supply chain risks (TSMC Taiwan dependency),
              competition from AMD/Intel custom AI chips, and regulatory
              scrutiny (export controls). Sources: [SEC 10-K 2024, Reuters
              2024-03-15, Goldman Sachs analyst report]"

Scoring:
├── Relevance: 5/5 (perfectly addresses query)
├── Accuracy: 4/5 (all facts verifiable, minor timing detail off)
├── Completeness: 4/5 (covers 3/4 major risk categories)
├── Actionability: 5/5 (investor can decide on position adjustment)
├── Traceability: 5/5 (3 credible sources cited)
├── Decision Clarity: 5/5 (clear risk assessment for portfolio decision)
├── Risk Awareness: 5/5 (comprehensive risk coverage)
├── Opportunity Recognition: 3/5 (didn't mention offsetting opportunities)
├── Time Horizon: 4/5 (mix of near-term and structural risks)

Overall: 4.4/5.0 = Excellent investment intelligence
```

**Key Insight**: Technical metrics (precision/recall) are necessary but not sufficient. What matters is whether the output helps an investor make better portfolio decisions.

### 2.2 Human-Centric Scoring (Not Automated)

**Why Manual Scoring:**
1. **Domain Expertise Required**: Only a domain expert can judge "Decision Clarity" or "Risk Awareness"
2. **LLM-as-Judge Unreliable**: Studies show GPT-4 scoring has 0.3-0.5 correlation with human judgment on subjective dimensions
3. **Capstone Scale**: 20 queries × 9 dimensions = 180 scores × ~10 seconds = 30 minutes (manageable for solo developer)
4. **Learning Value**: Manual scoring forces deep engagement with ICE output quality

**When to Automate:**
- **Entity extraction F1**: Automated (ground truth labels → precision/recall calculation)
- **Source freshness**: Automated (date parsing)
- **Source authority**: Automated (tier lookup table: SEC=5, Bloomberg=5, Reuters=4, etc.)
- **Cost tracking**: Automated (API call logs)

**When to Keep Manual:**
- All 9 quality dimensions (requires investment expertise)
- Failure mode classification (requires understanding of WHY)
- Reference answer authoring (requires domain knowledge)

### 2.3 Progressive Complexity

**Stage 1: Smoke Test (5 minutes)**
- **Purpose**: Quick sanity check that ICE is functional
- **Scope**: 5 queries (1 from each category)
- **Scoring**: Pass/Fail only (does it return reasonable output?)
- **Use Case**: After code changes, before commit

**Stage 2: Core Validation (30 minutes)**
- **Purpose**: Comprehensive quality assessment
- **Scope**: All 20 golden queries
- **Scoring**: Full 9-dimensional scoring
- **Use Case**: Weekly quality check, version comparison, Modified Option 4 Phase 0 decision gate

**Stage 3: Deep Validation (2 hours)**
- **Purpose**: Detailed failure analysis and improvement planning
- **Scope**: 20 queries + failure mode classification + query mode experiments
- **Scoring**: 9 dimensions + manual failure notes + mode performance matrix
- **Use Case**: Major feature integration (enhanced documents, email pipeline, etc.)

**Principle**: Start simple (smoke), scale to rigor (core), deep-dive when needed (deep).

### 2.4 Alignment with ICE Design Principles

**ICE Core Principles** (from PROJECT_STRUCTURE.md):
1. **Simplicity**: Lightweight, maintainable components
2. **Traceability**: Every fact must have source attribution
3. **Security**: Never expose API keys or proprietary data
4. **Performance**: Optimize for single developer maintainability

**PIVF Alignment:**
1. **Simplicity**: 500 lines of validation code, 20 queries, CSV scoring (no database)
2. **Traceability**: Dedicated scoring dimension + source quality framework
3. **Security**: No API keys in validation data, use test portfolio (not real holdings)
4. **Performance**: Terminal-based workflow, no web UI overhead

---

## 3. The Golden Test Set

### 3.1 Design Philosophy

**What Makes a Good Test Query:**
1. **Representative**: Covers real portfolio intelligence use cases
2. **Specific**: Clear expected output (not vague exploration)
3. **Measurable**: Can be scored across all 9 dimensions
4. **Diverse**: Spans multiple categories (risk, opportunities, entities, relationships)
5. **Stable**: Query meaning doesn't change over time (though answers might due to market changes)

**Anti-Patterns to Avoid:**
- ❌ **Too vague**: "Tell me about tech stocks" (what specifically?)
- ❌ **Too narrow**: "What was NVDA's Q3 2023 revenue?" (single fact lookup, not intelligence)
- ❌ **Time-sensitive**: "Should I buy NVDA today?" (answer changes daily, hard to benchmark)
- ❌ **Opinion-seeking**: "Is NVDA overvalued?" (subjective, no ground truth)

### 3.2 Test Set Structure (20 Queries)

**Category Breakdown:**
- **Portfolio Risk Queries** (5): Q001-Q005 - Risk analysis for specific holdings
- **Portfolio Opportunity Queries** (5): Q006-Q010 - Growth opportunities and catalysts
- **Entity Extraction Queries** (5): Q011-Q015 - Ticker, analyst, company extraction accuracy
- **Multi-Hop Reasoning Queries** (3): Q016-Q018 - Complex relationship traversal
- **Comparative Analysis Queries** (2): Q019-Q020 - Cross-holding comparisons

**Category 1: Portfolio Risk Queries (Q001-Q005)**

**Purpose**: Validate ICE's ability to identify and articulate investment risks for a specific holding.

**Recommended LightRAG Mode**: `hybrid` (combines local entity focus + global context)

**Example**:

```json
{
  "id": "Q001",
  "category": "portfolio_risk",
  "query": "What are the main business and market risks facing NVDA?",
  "portfolio_context": ["NVDA", "AAPL", "TSLA", "GOOGL", "MSFT"],
  "expected_topics": [
    "supply_chain_risk",
    "competition",
    "regulatory_export_controls",
    "customer_concentration",
    "valuation_risk"
  ],
  "expected_sources": ["SEC 10-K", "analyst_reports", "news"],
  "minimum_sources": 3,
  "recommended_mode": "hybrid",
  "expected_response_time": "< 5 seconds"
}
```

**Reference Answer Template** (manually authored):

```markdown
**NVDA Key Risks:**

1. **Supply Chain Dependency** (HIGH):
   - 100% reliance on TSMC Taiwan for advanced chip manufacturing
   - Geopolitical risk (China-Taiwan tensions)
   - Source: NVDA 10-K 2024, Risk Factors section

2. **Competitive Threats** (MEDIUM):
   - AMD gaining data center share with MI300 series
   - Custom chips from hyperscalers (Google TPU, Amazon Trainium)
   - Intel re-entering GPU market
   - Source: Goldman Sachs Semiconductors Report Q1 2024

3. **Regulatory/Export Controls** (HIGH):
   - U.S. restrictions on AI chip sales to China (40% of revenue exposure)
   - Potential EU AI regulations
   - Source: Reuters 2024-03-15, Bloomberg Gov

4. **Customer Concentration** (MEDIUM):
   - Top 5 customers = 60% of data center revenue
   - Microsoft, Meta, Google, Amazon dependency
   - Source: NVDA 10-K 2024

5. **Valuation Risk** (MEDIUM):
   - Trading at 40x forward P/E (vs 5-year avg 25x)
   - High expectations priced in
   - Source: Bloomberg Terminal data

**Overall Risk Assessment**: Moderate-High. Strong fundamentals but elevated macro risks.
```

**Scoring Expectations:**
- **Relevance**: 5/5 (directly answers "what are the risks")
- **Accuracy**: 5/5 (all facts verifiable from sources)
- **Completeness**: 4/5 (covers 4/5 major risk categories, might miss minor ones)
- **Actionability**: 5/5 (investor can assess position size based on this)
- **Traceability**: 5/5 (every claim has source)
- **Decision Clarity**: 5/5 (clear risk-reward trade-off articulated)
- **Risk Awareness**: 5/5 (comprehensive coverage of risk types)
- **Opportunity Recognition**: 3/5 (focus is risks, not offsetting opportunities)
- **Time Horizon**: 4/5 (mix of near-term and structural risks)

**Overall Target**: 4.5/5.0

**Complete Category 1 Queries:**

```json
{
  "portfolio_risk_queries": [
    {
      "id": "Q001",
      "query": "What are the main business and market risks facing NVDA?",
      "holdings": ["NVDA"]
    },
    {
      "id": "Q002",
      "query": "What regulatory and legal risks does AAPL face?",
      "holdings": ["AAPL"]
    },
    {
      "id": "Q003",
      "query": "What are the key operational risks for TSLA's manufacturing?",
      "holdings": ["TSLA"]
    },
    {
      "id": "Q004",
      "query": "What competitive threats is GOOGL facing in search and cloud?",
      "holdings": ["GOOGL"]
    },
    {
      "id": "Q005",
      "query": "What are the main risks to MSFT's cloud growth trajectory?",
      "holdings": ["MSFT"]
    }
  ]
}
```

---

**Category 2: Portfolio Opportunity Queries (Q006-Q010)**

**Purpose**: Validate ICE's ability to identify growth catalysts, market opportunities, and positive developments.

**Recommended LightRAG Mode**: `global` (broader market context + trend analysis)

**Example**:

```json
{
  "id": "Q006",
  "category": "portfolio_opportunity",
  "query": "What are the key growth drivers and opportunities for NVDA?",
  "portfolio_context": ["NVDA", "AAPL", "TSLA", "GOOGL", "MSFT"],
  "expected_topics": [
    "AI_data_center_demand",
    "automotive_AI",
    "enterprise_AI_adoption",
    "software_revenue_expansion",
    "new_product_launches"
  ],
  "expected_sources": ["earnings_calls", "analyst_reports", "news"],
  "minimum_sources": 3,
  "recommended_mode": "global",
  "expected_response_time": "< 5 seconds"
}
```

**Reference Answer Template**:

```markdown
**NVDA Key Growth Opportunities:**

1. **AI Data Center Expansion** (VERY HIGH):
   - H100/H200 GPU demand exceeding supply by 3-4x
   - Hyperscaler capex increasing 40% YoY for AI infrastructure
   - Source: NVDA Q4 2024 Earnings Call, Morgan Stanley Research

2. **Enterprise AI Adoption** (HIGH):
   - 50,000+ companies deploying NVIDIA AI Enterprise software
   - Recurring software revenue growing 150% YoY
   - Source: NVDA Investor Presentation Q1 2024

3. **Automotive AI** (MEDIUM):
   - DRIVE platform design wins with Mercedes, BYD, Lucid
   - $14B automotive pipeline over 6 years
   - Source: NVDA GTC 2024 Keynote

4. **Sovereign AI** (EMERGING):
   - Governments building national AI infrastructure
   - Japan, Singapore, UAE AI supercomputer projects
   - Source: Reuters 2024-02-20

5. **New Product Cycle** (HIGH):
   - Blackwell architecture launching H2 2024
   - 2.5x performance improvement over Hopper
   - Source: NVDA GTC 2024

**Overall Opportunity Assessment**: Very Strong. Multiple high-growth vectors with limited cannibalization.
```

**Complete Category 2 Queries:**

```json
{
  "portfolio_opportunity_queries": [
    {
      "id": "Q006",
      "query": "What are the key growth drivers and opportunities for NVDA?",
      "holdings": ["NVDA"]
    },
    {
      "id": "Q007",
      "query": "What new product opportunities does AAPL have in AI and services?",
      "holdings": ["AAPL"]
    },
    {
      "id": "Q008",
      "query": "What are the main growth catalysts for TSLA in 2024-2025?",
      "holdings": ["TSLA"]
    },
    {
      "id": "Q009",
      "query": "What opportunities does GOOGL have in AI and cloud expansion?",
      "holdings": ["GOOGL"]
    },
    {
      "id": "Q010",
      "query": "What are the key growth areas for MSFT beyond Azure?",
      "holdings": ["MSFT"]
    }
  ]
}
```

---

**Category 3: Entity Extraction Queries (Q011-Q015)**

**Purpose**: Validate ICE's precision in extracting structured entities (tickers, analysts, firms, ratings, price targets).

**Recommended LightRAG Mode**: `local` (focused entity extraction)

**⚠️ Critical for Modified Option 4**: These queries produce the **Entity Extraction F1 Score** that determines Phase 0 decision gate (F1 ≥ 0.85 → baseline sufficient).

**Example**:

```json
{
  "id": "Q011",
  "category": "entity_extraction",
  "query": "Extract all ticker symbols mentioned in this analyst report: 'Goldman Sachs upgrades NVDA to BUY with $500 PT, downgrades INTC to SELL. Maintains HOLD on AMD and QCOM.'",
  "ground_truth": {
    "tickers": ["NVDA", "INTC", "AMD", "QCOM"],
    "ratings": [
      {"ticker": "NVDA", "rating": "BUY"},
      {"ticker": "INTC", "rating": "SELL"},
      {"ticker": "AMD", "rating": "HOLD"},
      {"ticker": "QCOM", "rating": "HOLD"}
    ],
    "price_targets": [
      {"ticker": "NVDA", "value": 500, "currency": "USD"}
    ],
    "analysts": [{"firm": "Goldman Sachs"}]
  },
  "recommended_mode": "local",
  "automated_scoring": true
}
```

**Automated F1 Calculation**:

```python
# Ground truth
gt_tickers = {"NVDA", "INTC", "AMD", "QCOM"}

# ICE extraction
ice_tickers = {"NVDA", "INTC", "AMD"}  # Missed QCOM

# Metrics
true_positives = len(gt_tickers & ice_tickers)  # 3
false_positives = len(ice_tickers - gt_tickers)  # 0
false_negatives = len(gt_tickers - ice_tickers)  # 1 (QCOM)

precision = 3 / (3 + 0) = 1.00
recall = 3 / (3 + 1) = 0.75
f1 = 2 * (1.00 * 0.75) / (1.00 + 0.75) = 0.857

# Decision: F1 = 0.857 > 0.85 → Baseline sufficient!
```

**Complete Category 3 Queries:**

```json
{
  "entity_extraction_queries": [
    {
      "id": "Q011",
      "query": "Extract tickers from: 'Goldman Sachs upgrades NVDA to BUY with $500 PT, downgrades INTC to SELL.'",
      "ground_truth": {
        "tickers": ["NVDA", "INTC"],
        "ratings": [{"ticker": "NVDA", "rating": "BUY"}, {"ticker": "INTC", "rating": "SELL"}],
        "price_targets": [{"ticker": "NVDA", "value": 500}],
        "analysts": [{"firm": "Goldman Sachs"}]
      }
    },
    {
      "id": "Q012",
      "query": "Extract analyst and firm from: 'John Doe at Morgan Stanley maintains OVERWEIGHT on AAPL.'",
      "ground_truth": {
        "analysts": [{"name": "John Doe", "firm": "Morgan Stanley"}],
        "tickers": ["AAPL"],
        "ratings": [{"ticker": "AAPL", "rating": "OVERWEIGHT"}]
      }
    },
    {
      "id": "Q013",
      "query": "Extract price targets from: 'Barclays raises TSLA PT to $275 from $225.'",
      "ground_truth": {
        "tickers": ["TSLA"],
        "price_targets": [{"ticker": "TSLA", "old_value": 225, "new_value": 275}],
        "analysts": [{"firm": "Barclays"}]
      }
    },
    {
      "id": "Q014",
      "query": "Extract all entities from: 'JPMorgan analyst Sarah Smith upgrades GOOGL to BUY, PT $150.'",
      "ground_truth": {
        "analysts": [{"name": "Sarah Smith", "firm": "JPMorgan"}],
        "tickers": ["GOOGL"],
        "ratings": [{"ticker": "GOOGL", "rating": "BUY"}],
        "price_targets": [{"ticker": "GOOGL", "value": 150}]
      }
    },
    {
      "id": "Q015",
      "query": "Extract entities from: 'Citi maintains NEUTRAL on MSFT, sees upside to $400 from Azure growth.'",
      "ground_truth": {
        "analysts": [{"firm": "Citi"}],
        "tickers": ["MSFT"],
        "ratings": [{"ticker": "MSFT", "rating": "NEUTRAL"}],
        "price_targets": [{"ticker": "MSFT", "value": 400}],
        "catalysts": ["Azure growth"]
      }
    }
  ]
}
```

**Category 3 Scoring Notes:**
- **Automated**: Precision, Recall, F1 calculated programmatically
- **Manual dimensions still apply**: Relevance, Actionability, Traceability, etc.
- **Aggregate F1**: Average of Q011-Q015 F1 scores → Modified Option 4 Phase 0 decision

---

**Category 4: Multi-Hop Reasoning Queries (Q016-Q018)**

**Purpose**: Validate ICE's ability to traverse relationships across 2-3 hops in the knowledge graph.

**Recommended LightRAG Mode**: `kg` or `mixed` (explicit graph traversal)

**Example**:

```json
{
  "id": "Q016",
  "category": "multi_hop_reasoning",
  "query": "NVDA supplies GPUs to Microsoft Azure. How do Microsoft's cloud business risks indirectly affect my NVDA position?",
  "portfolio_context": ["NVDA"],
  "expected_hops": [
    "NVDA → SUPPLIES_TO → MSFT (Azure)",
    "MSFT (Azure) → HAS_RISK → AWS/GCP competition",
    "AWS/GCP competition → IMPACTS → NVDA GPU demand"
  ],
  "expected_topics": [
    "customer_concentration_risk",
    "cloud_competition",
    "hyperscaler_capex_sensitivity"
  ],
  "minimum_sources": 2,
  "recommended_mode": "kg"
}
```

**Reference Answer Template**:

```markdown
**NVDA's Indirect Exposure to Microsoft Azure Risks:**

**Relationship Chain**:
1. NVDA → Supplies H100/H200 GPUs → Microsoft Azure (data center AI workloads)
2. Microsoft Azure → Competes with → AWS, Google Cloud
3. Cloud competition → Affects → Azure revenue growth → Azure capex → NVDA GPU orders

**Risk Transmission Mechanism**:
- If Azure loses cloud market share to AWS/GCP → Lower Azure growth rate
- Lower Azure growth → Reduced Microsoft capex on AI infrastructure
- Reduced capex → Fewer NVDA GPU orders → Revenue impact

**Quantitative Context**:
- Microsoft = ~15% of NVDA data center revenue (Source: NVDA 10-K 2024)
- Azure growing 30% YoY vs AWS 12%, GCP 28% (Source: Q4 2024 earnings)
- Current risk: LOW (Azure still growing strongly)

**Portfolio Implication**:
- NVDA diversified across 5+ hyperscalers (risk mitigation)
- Monitor Azure market share trends quarterly
- Hedge: Consider cloud-agnostic AI beneficiaries

**Overall Assessment**: Low immediate risk, but monitor Azure competitive position.
```

**Complete Category 4 Queries:**

```json
{
  "multi_hop_reasoning_queries": [
    {
      "id": "Q016",
      "query": "NVDA supplies GPUs to Microsoft Azure. How do Microsoft's cloud business risks indirectly affect my NVDA position?",
      "expected_hops": 3,
      "holdings": ["NVDA"]
    },
    {
      "id": "Q017",
      "query": "AAPL uses TSMC for chip manufacturing. How do TSMC's geopolitical risks affect AAPL's supply chain?",
      "expected_hops": 2,
      "holdings": ["AAPL"]
    },
    {
      "id": "Q018",
      "query": "GOOGL competes with MSFT in cloud and enterprise AI. How does this competitive dynamic affect both my GOOGL and MSFT holdings?",
      "expected_hops": 2,
      "holdings": ["GOOGL", "MSFT"]
    }
  ]
}
```

---

**Category 5: Comparative Analysis Queries (Q019-Q020)**

**Purpose**: Validate ICE's ability to compare holdings, identify correlations, and provide portfolio-level insights.

**Recommended LightRAG Mode**: `global` (cross-entity synthesis)

**Example**:

```json
{
  "id": "Q019",
  "category": "comparative_analysis",
  "query": "Compare the AI positioning of NVDA vs AMD. Which has stronger competitive moat?",
  "portfolio_context": ["NVDA", "AMD"],
  "expected_topics": [
    "CUDA_ecosystem_lock-in",
    "software_platform_advantages",
    "market_share_comparison",
    "pricing_power"
  ],
  "minimum_sources": 4,
  "recommended_mode": "global"
}
```

**Complete Category 5 Queries:**

```json
{
  "comparative_analysis_queries": [
    {
      "id": "Q019",
      "query": "Compare the AI positioning of NVDA vs AMD. Which has stronger competitive moat?",
      "holdings": ["NVDA", "AMD"]
    },
    {
      "id": "Q020",
      "query": "How correlated are AAPL, MSFT, and GOOGL in terms of regulatory risks?",
      "holdings": ["AAPL", "MSFT", "GOOGL"]
    }
  ]
}
```

---

### 3.3 Golden Test Set Summary

**Total**: 20 queries across 5 categories
- Portfolio Risk: 5 queries (Q001-Q005)
- Portfolio Opportunity: 5 queries (Q006-Q010)
- Entity Extraction: 5 queries (Q011-Q015) → **Modified Option 4 F1 score**
- Multi-Hop Reasoning: 3 queries (Q016-Q018)
- Comparative Analysis: 2 queries (Q019-Q020)

**Distribution by LightRAG Mode:**
- `hybrid`: 10 queries (50%) - Default mode for portfolio queries
- `global`: 7 queries (35%) - Broader context queries
- `local`: 2 queries (10%) - Entity extraction
- `kg`/`mixed`: 1 query (5%) - Explicit graph traversal

**Automation Level:**
- **Fully automated**: Entity extraction F1 (Q011-Q015)
- **Partially automated**: Source quality, cost tracking
- **Manual**: 9-dimensional quality scoring (all 20 queries)

---

## 4. Multi-Dimensional Scoring System

### 4.1 Scoring Philosophy

**Why 9 Dimensions?**
- **5 Technical Dimensions**: Focus on RAG system quality (information retrieval + synthesis)
- **4 Business Dimensions**: Focus on investment decision quality (portfolio management value)

**Why 1-5 Scale?**
- **Granular enough**: Differentiate between poor (1), weak (2), acceptable (3), good (4), excellent (5)
- **Not too granular**: 1-10 scale creates false precision (is there really a difference between 7 and 8?)
- **Intuitive**: Maps to academic grading (F, D, C, B, A)

**Scoring Calibration:**
- **1 = Unusable**: Output is misleading, incorrect, or irrelevant (would harm investment decision)
- **2 = Poor**: Major gaps, but some salvageable information
- **3 = Acceptable**: Meets minimum bar for use, but missing depth or has minor inaccuracies
- **4 = Good**: High quality, actionable, would use in real portfolio decision
- **5 = Excellent**: Exceeds expectations, comprehensive, accurate, highly actionable

### 4.2 Technical Quality Dimensions (5)

#### **Dimension 1: Relevance**

**Definition**: Does the response directly address the query?

**Scoring Rubric:**
- **5/5**: Perfect match. Answers exactly what was asked, no tangents.
- **4/5**: Mostly relevant. Minor tangents or missing one sub-aspect.
- **3/5**: Partially relevant. Covers main topic but misses key sub-questions.
- **2/5**: Loosely related. Talks about the general area but not the specific query.
- **1/5**: Irrelevant. Answer is about a different topic entirely.

**Example** (Q001: "What are the main business and market risks facing NVDA?"):

**5/5 Response**:
> "NVDA faces 5 main risks: (1) Supply chain dependency on TSMC Taiwan, (2) Competition from AMD/Intel custom chips, (3) Export controls limiting China sales, (4) Customer concentration in 5 hyperscalers, (5) Valuation risk at 40x P/E."

**3/5 Response**:
> "NVDA is a leading GPU manufacturer with strong AI data center growth. The company reported 265% revenue growth in Q4 2024..."
> *Analysis: Talks about NVDA but doesn't address "risks" specifically.*

**1/5 Response**:
> "The semiconductor industry is undergoing significant changes due to AI adoption..."
> *Analysis: Generic industry commentary, not NVDA-specific risks.*

---

#### **Dimension 2: Accuracy**

**Definition**: Are the facts, figures, and claims in the response correct and verifiable?

**Scoring Rubric:**
- **5/5**: All facts verifiable, no errors detected.
- **4/5**: 1 minor inaccuracy (e.g., slightly outdated figure, minor timing error).
- **3/5**: 2-3 minor inaccuracies OR 1 moderate error.
- **2/5**: Multiple inaccuracies or 1 major error that affects conclusions.
- **1/5**: Fundamentally incorrect information (e.g., wrong company, fabricated data).

**Common Error Types:**
- **Factual Error**: "NVDA manufactures chips in Taiwan" (NVDA is fabless, TSMC manufactures)
- **Timing Error**: "NVDA Q4 2024 revenue was $18B" (actually $22.1B)
- **Attribution Error**: "CEO Jensen Huang announced layoffs" (Huang has not announced layoffs)
- **Magnitude Error**: "NVDA has 95% data center GPU market share" (actually ~85%)

**Verification Process:**
- Cross-check key claims against sources (SEC filings, earnings calls, reputable news)
- Flag any claim that cannot be verified
- Deduct 1 point per minor error, 2 points per major error

---

#### **Dimension 3: Completeness**

**Definition**: Does the response cover all major aspects of the topic?

**Scoring Rubric:**
- **5/5**: Comprehensive. Covers all expected topics (from query template "expected_topics").
- **4/5**: Mostly complete. Covers 4/5 expected topics.
- **3/5**: Partial coverage. Covers 3/5 expected topics OR misses critical sub-category.
- **2/5**: Superficial. Only 1-2 major points covered.
- **1/5**: Minimal. Single sentence or very limited scope.

**Example** (Q001: NVDA risks - expected 5 risk categories):

**5/5 Coverage**:
- ✅ Supply chain risk
- ✅ Competition risk
- ✅ Regulatory/export risk
- ✅ Customer concentration risk
- ✅ Valuation risk

**3/5 Coverage**:
- ✅ Supply chain risk
- ✅ Competition risk
- ❌ Regulatory/export risk (missing)
- ✅ Customer concentration risk
- ❌ Valuation risk (missing)

**Trade-off with Brevity**: Sometimes a concise, focused answer (4 points, but very actionable) is better than a comprehensive but sprawling answer (5 points, but hard to act on). Use "Actionability" dimension to capture this.

---

#### **Dimension 4: Actionability**

**Definition**: Can an investor use this response to make a concrete portfolio decision?

**Scoring Rubric:**
- **5/5**: Highly actionable. Clear implications for position sizing, hedging, or monitoring.
- **4/5**: Actionable. Provides decision direction but lacks specifics.
- **3/5**: Moderately actionable. Useful context but no clear decision path.
- **2/5**: Weakly actionable. Interesting information but no portfolio implications.
- **1/5**: Not actionable. Pure description with no decision support.

**Key Actionability Elements:**
1. **Directional Guidance**: Should investor increase/decrease/hold position?
2. **Risk Magnitude**: HIGH/MEDIUM/LOW labeling helps prioritize
3. **Monitoring Triggers**: What to watch for (e.g., "monitor Azure market share trends quarterly")
4. **Hedging Suggestions**: Alternative exposures or offsetting positions
5. **Time Horizon**: Near-term vs long-term implications

**Example**:

**5/5 Actionable**:
> "NVDA's Taiwan supply chain risk is HIGH. Recommend: (1) Limit NVDA to <10% portfolio weight, (2) Monitor TSMC Arizona fab progress quarterly, (3) Consider hedging with INTC (onshore manufacturing exposure)."

**3/5 Actionable**:
> "NVDA relies on TSMC Taiwan for manufacturing, which creates geopolitical risk."
> *Analysis: Identifies risk but doesn't suggest what to do about it.*

**1/5 Actionable**:
> "NVDA is a technology company."
> *Analysis: True but utterly useless for investment decisions.*

---

#### **Dimension 5: Traceability**

**Definition**: Are sources cited, and are they credible?

**Scoring Rubric:**
- **5/5**: Every claim has a source. Sources are Tier 1 (SEC, Bloomberg, analyst reports).
- **4/5**: Most claims sourced. 1-2 minor claims unsourced. All sources credible.
- **3/5**: Some sources provided, but key claims lack attribution OR sources are Tier 2-3.
- **2/5**: Minimal sourcing. Most claims lack attribution.
- **1/5**: No sources cited at all.

**Source Authority Tiers** (see Section 5 for full framework):
- **Tier 1** (Authority = 5): SEC filings, earnings calls, Tier 1 analyst reports (GS, MS, JPM)
- **Tier 2** (Authority = 4): Bloomberg Terminal, Reuters, WSJ, FT
- **Tier 3** (Authority = 3): CNBC, MarketWatch, reputable industry blogs
- **Tier 4** (Authority = 2): Aggregators (Yahoo Finance, Seeking Alpha)
- **Tier 5** (Authority = 1): Unknown/unverified sources

**Example**:

**5/5 Traceability**:
> "NVDA's Q4 2024 data center revenue was $18.4B (Source: NVDA Q4 2024 Earnings Release). Taiwan supply chain dependency creates geopolitical risk (Source: NVDA 10-K 2024, Risk Factors p.23)."

**3/5 Traceability**:
> "NVDA's data center revenue was strong. Geopolitical risks exist around Taiwan manufacturing."
> *Analysis: Claims are vague and unsourced.*

**1/5 Traceability**:
> "NVDA makes lots of money from AI."
> *Analysis: No sources, vague claims.*

---

### 4.3 Business Quality Dimensions (4)

#### **Dimension 6: Decision Clarity**

**Definition**: Does the response provide clear guidance for investment decisions?

**Scoring Rubric:**
- **5/5**: Crystal clear decision implications. Investor knows exactly what action to take.
- **4/5**: Clear guidance with minor ambiguity.
- **3/5**: Some decision direction but requires investor interpretation.
- **2/5**: Vague or conflicting signals.
- **1/5**: No decision guidance at all.

**Key Elements:**
1. **Risk-Reward Balance**: Explicitly states trade-offs
2. **Position Sizing Guidance**: Should position be large/medium/small?
3. **Action Triggers**: When to buy more, sell, or hold
4. **Confidence Level**: HIGH/MEDIUM/LOW conviction in the assessment

**Example**:

**5/5 Decision Clarity**:
> "NVDA Overall Assessment: HOLD with bullish bias. Risks are elevated but manageable. Recommend maintaining current 8% portfolio weight. If Taiwan geopolitical tensions escalate (trigger: military exercises), reduce to 5%. If H200 supply constraints ease (trigger: lead times <8 weeks), increase to 10%."

**3/5 Decision Clarity**:
> "NVDA has both risks and opportunities. Investors should consider their risk tolerance."
> *Analysis: Generic advice, no specific guidance.*

---

#### **Dimension 7: Risk Awareness**

**Definition**: Does the response adequately identify and articulate downside risks?

**Scoring Rubric:**
- **5/5**: Comprehensive risk coverage across multiple categories (operational, market, regulatory, etc.)
- **4/5**: Good risk coverage, might miss 1 minor risk category.
- **3/5**: Identifies major risks but superficial treatment.
- **2/5**: Mentions risks but lacks depth or misses major categories.
- **1/5**: No risk discussion or overly optimistic.

**Risk Categories** (for comprehensive coverage):
1. **Operational**: Supply chain, manufacturing, execution
2. **Market**: Competition, market share erosion, pricing pressure
3. **Regulatory**: Legal, compliance, export controls
4. **Financial**: Valuation, leverage, cash flow
5. **Macro**: Economic cycle, interest rates, geopolitical

**Example**:

**5/5 Risk Awareness**:
> "NVDA faces 5 major risk categories: (1) Operational - TSMC dependency, (2) Market - AMD/Intel competition, (3) Regulatory - export controls, (4) Financial - 40x P/E valuation, (5) Macro - China-Taiwan geopolitical tensions. All risks rated MEDIUM-HIGH with mitigation strategies outlined."

**3/5 Risk Awareness**:
> "NVDA has competition from AMD and some regulatory risks in China."
> *Analysis: Touches on 2/5 risk categories, lacks depth.*

---

#### **Dimension 8: Opportunity Recognition**

**Definition**: Does the response identify growth catalysts and upside opportunities?

**Scoring Rubric:**
- **5/5**: Identifies multiple specific, actionable opportunities with catalysts.
- **4/5**: Good opportunity identification, minor gaps in specificity.
- **3/5**: General opportunities mentioned but lacks specifics or catalysts.
- **2/5**: Vague or generic opportunity discussion.
- **1/5**: No opportunities mentioned or overly pessimistic.

**Opportunity Types:**
1. **Product Cycles**: New product launches, technology shifts
2. **Market Expansion**: TAM growth, new customer segments
3. **Strategic Initiatives**: M&A, partnerships, platform plays
4. **Competitive Advantages**: Moat expansion, pricing power
5. **Macro Tailwinds**: Industry trends, regulatory support

**Example**:

**5/5 Opportunity Recognition**:
> "NVDA has 4 major growth vectors: (1) Blackwell architecture launch (2.5x performance), (2) Enterprise AI software revenue expanding 150% YoY, (3) Sovereign AI government contracts ($5B+ pipeline), (4) Automotive DRIVE platform ($14B 6-year pipeline). Catalysts: Blackwell production ramp Q3 2024, NVIDIA AI Enterprise attachment rate increasing."

**3/5 Opportunity Recognition**:
> "NVDA should benefit from AI growth trends."
> *Analysis: Generic, no specific catalysts or quantification.*

---

#### **Dimension 9: Time Horizon**

**Definition**: Does the response distinguish between near-term and long-term factors?

**Scoring Rubric:**
- **5/5**: Clear delineation of near-term (<1yr), medium-term (1-3yr), long-term (3yr+) factors.
- **4/5**: Good time horizon awareness, minor gaps.
- **3/5**: Some time horizon distinction but mostly generic.
- **2/5**: Conflates short-term and long-term factors.
- **1/5**: No time horizon awareness.

**Time Horizon Labels:**
- **Immediate** (<3 months): Earnings, product launches, regulatory events
- **Near-term** (3-12 months): Next 1-4 quarters, visible pipeline
- **Medium-term** (1-3 years): Product cycles, market share shifts
- **Long-term** (3+ years): Structural trends, industry evolution

**Example**:

**5/5 Time Horizon**:
> "NVDA Outlook: (1) Near-term (Q1-Q2 2024): H200 ramp, potential supply constraints, (2) Medium-term (2024-2025): Blackwell adoption cycle, enterprise AI software growth, (3) Long-term (2025+): Automotive AI, Sovereign AI, potential CUDA moat erosion risk."

**3/5 Time Horizon**:
> "NVDA has good growth prospects and some risks."
> *Analysis: No time dimension specified.*

---

### 4.4 Overall Score Calculation

**Formula**:
```
Overall Score = (Relevance + Accuracy + Completeness + Actionability + Traceability +
                 Decision Clarity + Risk Awareness + Opportunity Recognition + Time Horizon) / 9
```

**Interpretation**:
- **4.5-5.0**: Excellent - Production-ready, exceeds Bloomberg quality
- **4.0-4.4**: Good - High quality, would use in real portfolio decisions
- **3.5-3.9**: Acceptable - Meets minimum bar, but needs improvement
- **3.0-3.4**: Below Bar - Significant gaps, not reliable for decisions
- **<3.0**: Poor - Fundamental issues, major rework needed

**Benchmark Targets**:
- **Phase 0 Baseline**: ≥3.5 overall → Baseline usable
- **Production Release**: ≥4.0 overall → Competitive with manual research
- **Capstone Demo**: ≥4.2 overall → Impressive, publication-worthy

**Per-Dimension Targets**:
- All dimensions ≥3.0 (no catastrophic failures)
- Critical dimensions (Relevance, Accuracy, Actionability) ≥4.0
- At least 5/9 dimensions ≥4.0

---

### 4.5 Scoring Worksheet Template

**CSV Format** (for easy manual scoring):

```csv
Query_ID,Relevance,Accuracy,Completeness,Actionability,Traceability,Decision_Clarity,Risk_Awareness,Opportunity_Recognition,Time_Horizon,Overall,Notes
Q001,5,5,4,5,5,5,5,3,4,4.56,"Excellent risk analysis. Minor: Could improve opportunity balance."
Q002,4,5,4,4,5,4,4,4,3,4.11,"Good regulatory analysis. Timing could be more specific."
...
```

**Scoring Tips**:
1. **Score immediately after reading response** (don't batch all 20 at once, fatigue bias)
2. **Use reference answers** for calibration (first time through)
3. **Write brief notes** for borderline scores (3-4 boundary)
4. **Track time**: Should take ~90 seconds per query (9 dimensions × 10 sec each)

---

## 5. Source Quality Framework

### 5.1 Source Quality Dimensions

**Three Pillars**:
1. **Freshness**: How recent is the information?
2. **Authority**: How credible is the source?
3. **Relevance**: How directly does it address the query?

**Combined Source Quality Score**:
```
Source Quality = Avg(Freshness, Authority, Relevance)
```

**Why Source Quality Matters**:
- Investment decisions are time-sensitive (stale data = bad decisions)
- Source credibility affects confidence (SEC filing > Reddit post)
- Relevance filtering prevents "kitchen sink" citation spam

---

### 5.2 Freshness Scoring

**Definition**: How recent is the information relative to the query context?

**Automated Scoring** (parseable from source metadata):

| **Freshness Tier** | **Age** | **Score** | **Use Cases** |
|--------------------|---------|-----------|---------------|
| Real-time | Same day | 5 | Breaking news, earnings releases |
| Very Fresh | 1-7 days | 4 | Weekly analysis, recent developments |
| Fresh | 1-4 weeks | 3 | Monthly trends, quarterly updates |
| Stale | 1-6 months | 2 | Historical context, older earnings |
| Outdated | >6 months | 1 | Archival, outdated analysis |

**Context-Dependent Adjustments**:
- **Structural information**: "NVDA is fabless" → Freshness less critical (3-year-old source OK)
- **Financial metrics**: "NVDA Q4 revenue" → Freshness critical (must be <1 month)
- **Regulatory filings**: 10-K annual reports → 1-year freshness acceptable

**Example**:
```python
def calculate_freshness(source_date, query_date):
    age_days = (query_date - source_date).days

    if age_days == 0: return 5  # Same day
    elif age_days <= 7: return 4  # Within week
    elif age_days <= 30: return 3  # Within month
    elif age_days <= 180: return 2  # Within 6 months
    else: return 1  # Outdated
```

---

### 5.3 Authority Scoring

**Definition**: How credible and trustworthy is the source?

**Tier System** (manually curated lookup table):

| **Tier** | **Authority** | **Score** | **Examples** |
|----------|---------------|-----------|--------------|
| Tier 1: Primary | Official, audited, regulatory | 5 | SEC filings (10-K, 10-Q, 8-K), earnings calls, company press releases |
| Tier 2: Premium | Professional, paywalled, institutional | 5 | Bloomberg Terminal, FactSet, Tier 1 analyst reports (GS, MS, JPM) |
| Tier 3: Reputable | Established media, fact-checked | 4 | Reuters, WSJ, Financial Times, Bloomberg News |
| Tier 4: Mainstream | General financial media | 3 | CNBC, MarketWatch, Yahoo Finance, Seeking Alpha |
| Tier 5: Aggregators | User-generated, unverified | 2 | Reddit r/investing, Twitter, blogs |
| Tier 6: Unknown | No verification possible | 1 | Anonymous sources, unattributed claims |

**Authority Lookup Table** (automated):

```python
AUTHORITY_TIERS = {
    # Tier 1: Primary sources
    'sec.gov': 5,
    'investor_relations': 5,  # Company IR pages
    'earnings_call': 5,

    # Tier 2: Premium professional
    'bloomberg_terminal': 5,
    'factset.com': 5,
    'goldmansachs_research': 5,
    'morganstanley_research': 5,
    'jpmorgan_research': 5,

    # Tier 3: Reputable news
    'reuters.com': 4,
    'wsj.com': 4,
    'ft.com': 4,
    'bloomberg.com': 4,  # Bloomberg News (not Terminal)

    # Tier 4: Mainstream
    'cnbc.com': 3,
    'marketwatch.com': 3,
    'finance.yahoo.com': 3,
    'seekingalpha.com': 3,

    # Tier 5: Aggregators
    'reddit.com': 2,
    'twitter.com': 2,

    # Default
    'unknown': 1
}
```

**Edge Cases**:
- **Analyst reports from Tier 2 firms on Tier 4 aggregators**: Use original source authority (e.g., Goldman Sachs report on Yahoo Finance = Authority 5)
- **Company social media**: Twitter/LinkedIn from official verified accounts = Authority 4 (semi-official)

---

### 5.4 Relevance Scoring

**Definition**: How directly does the source address the specific query?

**Manual Scoring** (query-specific, cannot be automated):

| **Relevance Level** | **Score** | **Description** | **Example** |
|---------------------|-----------|-----------------|-------------|
| Exact Match | 5 | Source directly answers the query | Query: "NVDA risks" → Source: "NVDA 10-K Risk Factors section" |
| Closely Related | 4 | Source covers the topic with 1 level of inference | Query: "NVDA risks" → Source: "NVDA Q4 earnings call (discusses risks during Q&A)" |
| Broadly Relevant | 3 | Source is about the right entity/topic but tangential | Query: "NVDA risks" → Source: "Semiconductor industry risks" (not NVDA-specific) |
| Tangentially Related | 2 | Source requires 2+ levels of inference | Query: "NVDA risks" → Source: "Taiwan geopolitical analysis" (NVDA not mentioned) |
| Weak Connection | 1 | Source is only indirectly related | Query: "NVDA risks" → Source: "General AI trends" (very indirect) |

**Relevance Penalties**:
- **Source mentions entity but focuses on different aspect**: Relevance = 3
  - Query: "NVDA risks" → Source: "NVDA product roadmap" (positive focus)
- **Source is about related entity but not the query entity**: Relevance = 2
  - Query: "NVDA risks" → Source: "AMD competitive analysis"

---

### 5.5 Combined Source Quality Example

**Query**: "What are the main business and market risks facing NVDA?"

**Source 1: NVDA 10-K 2024 (Risk Factors section)**
- Freshness: 2 months old → Score = 3 (Fresh)
- Authority: SEC filing → Score = 5 (Tier 1)
- Relevance: Exact match (Risk Factors section) → Score = 5
- **Source Quality = (3 + 5 + 5) / 3 = 4.33**

**Source 2: Goldman Sachs Semiconductors Report (Q1 2024)**
- Freshness: 1 week old → Score = 4 (Very Fresh)
- Authority: Tier 1 analyst → Score = 5 (Tier 2)
- Relevance: Covers NVDA competitive risks → Score = 4 (Closely Related)
- **Source Quality = (4 + 5 + 4) / 3 = 4.33**

**Source 3: Reuters article "Taiwan tensions escalate" (2024-03-15)**
- Freshness: Same day → Score = 5 (Real-time)
- Authority: Reuters → Score = 4 (Tier 3)
- Relevance: Geopolitical context (not NVDA-specific) → Score = 2 (Tangential)
- **Source Quality = (5 + 4 + 2) / 3 = 3.67**

**Source 4: Reddit r/stocks discussion about NVDA**
- Freshness: Same day → Score = 5 (Real-time)
- Authority: Reddit → Score = 2 (Tier 5)
- Relevance: NVDA discussion → Score = 3 (Broadly Relevant)
- **Source Quality = (5 + 2 + 3) / 3 = 3.33**

**Average Source Quality across all sources = (4.33 + 4.33 + 3.67 + 3.33) / 4 = 3.92**

**Interpretation**: Strong source quality (Tier 1 + Tier 2 sources dominate), acceptable mix of freshness and authority. Reddit source pulls down average slightly.

**Target**: Average Source Quality ≥ 3.5 for production-ready responses

---

## 6. Progressive Validation Workflow

### 6.1 Stage 1: Smoke Test (5 Minutes)

**Purpose**: Quick sanity check that ICE is functional after code changes.

**Scope**: 5 queries (1 from each category)

**Selected Queries**:
1. Q001 (Portfolio Risk)
2. Q006 (Portfolio Opportunity)
3. Q011 (Entity Extraction)
4. Q016 (Multi-Hop Reasoning)
5. Q019 (Comparative Analysis)

**Scoring**: Pass/Fail only (no detailed 9-dimensional scoring)

**Pass Criteria**:
- ✅ ICE returns a response (not error/timeout)
- ✅ Response is >50 words (not empty stub)
- ✅ At least 1 source cited
- ✅ Response is relevant to the query (manual spot-check)

**Workflow**:
```bash
# Run smoke test
cd validation/scripts
python run_validation.py --mode smoke --output ../snapshots/smoke_$(date +%Y%m%d_%H%M%S).json

# Quick review (30 seconds per query)
cat ../snapshots/smoke_*.json | grep "response" | head -5

# Decision
# ✅ All pass → Proceed with commit
# ❌ Any fail → Debug before commit
```

**When to Run**:
- After every significant code change (before git commit)
- After merging feature branches
- Before running Core Validation (Stage 2)

---

### 6.2 Stage 2: Core Validation (30 Minutes)

**Purpose**: Comprehensive quality assessment for version comparison and Modified Option 4 decision gates.

**Scope**: All 20 golden queries

**Scoring**: Full 9-dimensional manual scoring

**Workflow**:

**Step 1: Run validation script (5 minutes)**
```bash
cd validation/scripts
python run_validation.py --mode core --output ../snapshots/v1.0_baseline_core.json
```

**Step 2: Manual scoring (20 minutes - 1 min per query)**
```bash
# Open scoring worksheet
open ../scoring_worksheets/v1.0_baseline_scoring.csv

# For each of 20 queries:
#  1. Read ICE response (in JSON snapshot)
#  2. Read reference answer (if first time)
#  3. Score 9 dimensions (1-5 scale)
#  4. Write brief note for borderline scores

# Scoring pace: ~90 seconds per query × 20 = 30 minutes
```

**Step 3: Generate report (5 minutes)**
```bash
python generate_report.py \
    --snapshot v1.0_baseline_core \
    --scoring v1.0_baseline_scoring.csv \
    --output ../reports/v1.0_baseline_report.md

# Review report
cat ../reports/v1.0_baseline_report.md
```

**When to Run**:
- **Weekly**: Regular quality monitoring
- **Before major integrations**: Modified Option 4 Phase 0 (baseline validation)
- **After feature deployment**: A/B comparison (v1.0 vs v1.1)

**Output**:
- Overall score (e.g., 4.1/5.0)
- Per-dimension breakdown (which dimensions are weakest?)
- Entity extraction F1 score (Q011-Q015 average)
- Recommended next actions

---

### 6.3 Stage 3: Deep Validation (2 Hours)

**Purpose**: Detailed failure analysis and query mode optimization for major features.

**Scope**: 20 queries + failure mode classification + mode experimentation

**Workflow**:

**Step 1: Core validation (30 minutes)**
- Run all 20 queries through standard core validation

**Step 2: Failure mode analysis (30 minutes)**
```bash
# For each query with score <4.0:
#  1. Classify failure mode (Data Gaps, Entity Errors, Relationship Issues, etc.)
#  2. Write detailed failure note
#  3. Propose specific fix

python analyze_failures.py \
    --scoring v1.1_enhanced_scoring.csv \
    --threshold 4.0 \
    --output ../reports/v1.1_failure_analysis.md
```

**Step 3: Query mode optimization (45 minutes)**
```bash
# Run each query across all 6 LightRAG modes
python run_validation.py \
    --mode deep \
    --query-modes naive,local,global,hybrid,kg,mixed \
    --output ../snapshots/v1.1_mode_matrix.json

# Compare mode performance
python generate_mode_report.py \
    --snapshot v1.1_mode_matrix.json \
    --output ../reports/v1.1_mode_optimization.md
```

**Step 4: Cost analysis (15 minutes)**
```bash
# Calculate quality-to-cost ratio across modes
python cost_analysis.py \
    --snapshot v1.1_mode_matrix.json \
    --api-logs ../logs/api_calls.json \
    --output ../reports/v1.1_cost_report.md
```

**When to Run**:
- **Before major releases**: Enhanced documents integration, email pipeline, etc.
- **Quarterly deep-dives**: Comprehensive system health check
- **After performance issues**: Diagnose root causes

**Output**:
- Failure taxonomy breakdown (% of failures in each category)
- Mode performance matrix (which mode works best for each query type?)
- Cost-quality trade-off analysis
- Detailed improvement roadmap

---

### 6.4 Validation Cadence Summary

| **Stage** | **Frequency** | **Duration** | **Purpose** |
|-----------|---------------|--------------|-------------|
| Smoke Test | After every code change | 5 min | Prevent regressions |
| Core Validation | Weekly + before integrations | 30 min | Monitor quality, decision gates |
| Deep Validation | Before major releases + quarterly | 2 hr | Root cause analysis, optimization |

**Recommended Workflow**:
- **Daily development**: Smoke tests only
- **Weekly rhythm**: Core validation every Monday morning
- **Before capstone demo/defense**: Deep validation (comprehensive quality check)

---

## 7. Snapshot-Based Regression Testing

### 7.1 Snapshot Format

**Purpose**: Preserve exact ICE outputs for version comparison.

**JSON Structure**:
```json
{
  "metadata": {
    "version": "v1.0_baseline",
    "timestamp": "2024-03-15T14:30:00Z",
    "ice_git_commit": "a1b2c3d",
    "validation_stage": "core",
    "total_queries": 20
  },
  "queries": [
    {
      "id": "Q001",
      "query": "What are the main business and market risks facing NVDA?",
      "portfolio_context": ["NVDA", "AAPL", "TSLA", "GOOGL", "MSFT"],
      "ice_response": {
        "text": "NVDA faces 5 main risks: (1) Supply chain dependency...",
        "sources": [
          {
            "title": "NVDA 10-K 2024",
            "url": "https://sec.gov/...",
            "date": "2024-02-01",
            "freshness": 3,
            "authority": 5,
            "relevance": 5,
            "source_quality": 4.33
          }
        ],
        "mode_used": "hybrid",
        "response_time_sec": 3.2,
        "api_cost_usd": 0.02
      }
    }
  ]
}
```

**Snapshot Naming Convention**:
```
v{major}.{minor}_{feature}_{stage}.json

Examples:
- v1.0_baseline_core.json (Phase 0 baseline)
- v1.1_enhanced_docs_core.json (Phase 3 enhanced documents)
- v1.2_email_pipeline_deep.json (Email integration deep validation)
```

---

### 7.2 Version Comparison Workflow

**Scenario**: You integrated enhanced documents (Phase 3). Did it improve quality?

**Step 1: Run baseline validation**
```bash
# Save baseline snapshot (before integration)
git checkout v1.0_baseline
python run_validation.py --mode core --output ../snapshots/v1.0_baseline_core.json
```

**Step 2: Integrate feature and run new validation**
```bash
# Integrate enhanced documents
# ... code changes ...

# Save new snapshot
git checkout v1.1_enhanced_docs
python run_validation.py --mode core --output ../snapshots/v1.1_enhanced_core.json
```

**Step 3: Compare snapshots**
```bash
python generate_report.py \
    --compare v1.0_baseline_core v1.1_enhanced_core \
    --output ../reports/v1.0_vs_v1.1_comparison.md
```

**Comparison Report Contents**:
```markdown
# ICE Validation Comparison: v1.0 Baseline vs v1.1 Enhanced Documents

## Overall Score Change:
- v1.0 Baseline: 3.8/5.0
- v1.1 Enhanced: 4.1/5.0
- **Δ +0.3** ✅ IMPROVEMENT

## Per-Dimension Changes:
| Dimension | v1.0 | v1.1 | Δ | Verdict |
|-----------|------|------|---|---------|
| Relevance | 4.2 | 4.3 | +0.1 | Slight improvement |
| Accuracy | 3.5 | 4.0 | **+0.5** | ✅ Major improvement |
| Completeness | 3.8 | 4.1 | +0.3 | Improvement |
| ... | | | | |

## Entity Extraction F1 Score:
- v1.0: 0.78 (below threshold)
- v1.1: 0.92 (**above 0.85 threshold** ✅)
- **Δ +0.14** → Enhanced documents solved the problem!

## Query-Level Changes:
| Query | v1.0 Score | v1.1 Score | Δ | Analysis |
|-------|------------|------------|---|----------|
| Q001 | 4.0 | 4.2 | +0.2 | Better risk articulation |
| Q011 | 3.2 | 4.5 | **+1.3** | ✅ Entity extraction vastly improved |
| Q007 | 4.5 | 4.2 | **-0.3** | ⚠️ Slight regression (investigate) |

## Regression Alerts:
- Q007, Q008: Slight score decreases (Δ -0.2 to -0.3)
- **Root cause**: Enhanced documents added entity markup that diluted opportunity focus
- **Recommendation**: Adjust markup density or use conditional formatting

## Decision:
- **KEEP enhanced documents** ✅
- **Address regression** in Q007/Q008 with targeted fix
- **Overall improvement**: +7.9% quality gain
```

---

### 7.3 Regression Detection Rules

**Automatic Alerts**:
1. **Overall score decrease >0.2**: Major regression, investigate immediately
2. **Any dimension decrease >0.5**: Critical regression in specific area
3. **>3 queries with score decrease**: Systemic issue, not isolated failures
4. **Entity F1 decrease >0.05**: Entity extraction regression

**Statistical Significance** (for formal A/B testing):
```python
from scipy import stats

# Paired t-test (same queries, before/after)
t_statistic, p_value = stats.ttest_rel(v1_scores, v2_scores)

if p_value < 0.05:
    print("Statistically significant change")
else:
    print("Change within noise, inconclusive")
```

**Decision Framework**:
- **p < 0.05 AND overall +0.3**: Keep feature ✅
- **p < 0.05 AND overall -0.2**: Revert feature ❌
- **p ≥ 0.05**: Change within noise, need more data or deeper analysis

---

## 8. Failure Mode Taxonomy

### 8.1 The 5 Failure Categories

**Purpose**: Understand WHY queries fail, not just THAT they fail.

| **Category** | **Description** | **Symptoms** | **Fixes** |
|--------------|-----------------|--------------|-----------|
| 1. Data Gaps | Missing data sources or stale data | Low Completeness, outdated sources | Add data sources, increase refresh rate |
| 2. Entity Errors | Incorrect ticker/analyst extraction | Low Accuracy (Q011-Q015), wrong entities | Enhanced documents, better NER |
| 3. Relationship Misconnection | Wrong graph edges or missing hops | Low multi-hop scores (Q016-Q018) | Improve graph building logic |
| 4. Query Understanding | Misinterprets user intent | Low Relevance, off-topic responses | Optimize query mode, better prompts |
| 5. Synthesis Weakness | Poor synthesis/summarization | Low Actionability, Decision Clarity | Enhance QueryEngine prompts |

---

### 8.2 Failure Mode Analysis Workflow

**For each query scoring <4.0**:

**Step 1: Read the response and identify symptom**
- What dimension(s) scored lowest?
- What specific aspect is missing or wrong?

**Step 2: Classify failure mode (pick 1 primary + optional secondary)**
- Review symptom patterns in taxonomy table
- Assign Category 1-5

**Step 3: Write failure note**
```csv
Query_ID,Score,Failure_Mode,Symptom,Proposed_Fix
Q003,3.2,Data_Gaps + Entity_Errors,"Missing TSLA manufacturing risks, wrong supplier extraction","Add TSLA 10-K data + improve supply chain entity extraction"
```

**Step 4: Aggregate across all failures**
```bash
python analyze_failures.py \
    --scoring v1.0_baseline_scoring.csv \
    --output ../reports/v1.0_failure_breakdown.md
```

**Example Output**:
```markdown
# Failure Mode Breakdown (v1.0 Baseline)

**Total Queries Scoring <4.0**: 8/20 (40%)

## Failure Distribution:
| Category | Count | % of Failures | Priority |
|----------|-------|---------------|----------|
| Synthesis Weakness | 4 | 50% | 🔥 HIGH |
| Data Gaps | 2 | 25% | MEDIUM |
| Entity Errors | 1 | 12.5% | LOW |
| Query Understanding | 1 | 12.5% | LOW |
| Relationship Misconnection | 0 | 0% | N/A |

## Key Insights:
- **Primary bottleneck**: QueryEngine synthesis (50% of failures)
- **Recommendation**: Focus development effort on improving QueryEngine prompts and query modes
- **Entity extraction**: Only 1/8 failures (12.5%) → Enhanced documents NOT urgent priority
- **Data coverage**: 2/8 failures → Consider adding SEC EDGAR or email pipeline data

## Detailed Failures:
### Q003 (Synthesis Weakness):
**Score**: 3.2/5.0
**Problem**: TSLA manufacturing risks identified but poorly synthesized (listy, no prioritization)
**Fix**: Enhance QueryEngine to add risk severity labels (HIGH/MEDIUM/LOW)

### Q007 (Data Gaps):
**Score**: 3.5/5.0
**Problem**: Missing AAPL AI product opportunities (no Vision Pro mentioned)
**Fix**: Add Apple Newsroom or product launch data source
```

---

### 8.3 Using Failure Analysis for Development Priorities

**Modified Option 4 Integration**:

```python
# Modified Option 4 Phase 0 Decision Gate
entity_failures = count_failures(category="Entity_Errors")
total_failures = count_failures(all_categories)

if (entity_failures / total_failures) > 0.40:
    decision = "Entity extraction is bottleneck → Proceed with enhanced docs (Phase 3)"
elif (entity_failures / total_failures) < 0.20:
    decision = "Entity extraction NOT bottleneck → Skip enhanced docs, focus on other areas"
else:
    decision = "Mixed signal → Try targeted entity fix (Phase 2)"
```

**Example Decision Logic** (based on failure breakdown above):
- **Entity Errors**: 1/8 failures (12.5%) → **BELOW 20% threshold**
- **Decision**: **Skip enhanced documents Phase 3** ✅
- **Redirect effort**: Focus on Synthesis Weakness (4/8 = 50%) → Improve QueryEngine prompts

**This is the power of PIVF**: Data-driven prioritization, not gut feel.

---

## 9. Query Mode Optimization

### 9.1 LightRAG's 6 Query Modes

**Overview**:
| **Mode** | **Description** | **Use Cases** | **Cost** | **Speed** |
|----------|-----------------|---------------|----------|-----------|
| `naive` | Simple vector search | Basic fact lookup | Low | Fast |
| `local` | Entity-focused retrieval | Ticker extraction, entity-specific queries | Low | Fast |
| `global` | Broader context synthesis | Market trends, comparative analysis | Medium | Medium |
| `hybrid` | Combines local + global | Portfolio risks/opportunities | Medium-High | Medium |
| `kg` | Explicit graph traversal | Multi-hop reasoning | High | Slow |
| `mixed` | Dynamic mode selection | Adaptive to query type | Variable | Variable |

**Current ICE Default**: `hybrid` (hardcoded in ice_simplified.py QueryEngine)

---

### 9.2 Mode Performance Matrix

**Goal**: Identify which mode works best for each query category.

**Experiment**:
```bash
# Run all 20 queries across all 6 modes
python run_validation.py \
    --mode deep \
    --query-modes naive,local,global,hybrid,kg,mixed \
    --output ../snapshots/mode_matrix.json
```

**Example Results**:

| **Query Category** | **naive** | **local** | **global** | **hybrid** | **kg** | **mixed** | **Winner** |
|--------------------|-----------|-----------|------------|------------|---------|-----------|------------|
| Portfolio Risk (Q001-Q005) | 3.2 | 3.8 | 4.0 | **4.4** | 4.1 | 4.3 | `hybrid` |
| Portfolio Opportunity (Q006-Q010) | 3.5 | 3.6 | **4.2** | 4.0 | 3.9 | 4.1 | `global` |
| Entity Extraction (Q011-Q015) | 3.0 | **4.5** | 3.2 | 3.8 | 3.5 | 4.2 | `local` |
| Multi-Hop (Q016-Q018) | 2.8 | 3.2 | 3.5 | 3.9 | **4.3** | 4.0 | `kg` |
| Comparative (Q019-Q020) | 3.1 | 3.4 | **4.0** | 3.8 | 3.7 | 3.9 | `global` |

**Insights**:
- **Portfolio Risk**: `hybrid` wins (local entity focus + global risk context)
- **Portfolio Opportunity**: `global` wins (broader market/trend synthesis)
- **Entity Extraction**: `local` dominates (focused retrieval)
- **Multi-Hop**: `kg` wins (explicit graph traversal needed)
- **Comparative**: `global` wins (cross-entity synthesis)

**Recommendation**: Implement smart mode routing in QueryEngine:

```python
def select_query_mode(query_type):
    mode_map = {
        'portfolio_risk': 'hybrid',
        'portfolio_opportunity': 'global',
        'entity_extraction': 'local',
        'multi_hop': 'kg',
        'comparative': 'global'
    }
    return mode_map.get(query_type, 'hybrid')  # Default hybrid
```

---

### 9.3 Cost-Quality Trade-offs

**Scenario**: `kg` mode gives best multi-hop scores but is 3x more expensive than `hybrid`. Worth it?

**Analysis**:

| **Mode** | **Avg Score** | **Avg Cost** | **Quality-to-Cost Ratio** |
|----------|---------------|--------------|---------------------------|
| `naive` | 3.1 | $0.01 | 310 |
| `local` | 3.8 | $0.015 | 253 |
| `global` | 4.0 | $0.03 | 133 |
| `hybrid` | 4.2 | $0.04 | **105** |
| `kg` | 4.3 | $0.12 | 36 |
| `mixed` | 4.1 | $0.06 | 68 |

**Interpretation**:
- **Best value**: `hybrid` (105 quality-per-dollar) → Current default is optimal ✅
- **kg expensive**: Only 2% better quality than `hybrid` but 3x cost → Use sparingly
- **Recommendation**: Use `kg` only for explicit multi-hop queries (Q016-Q018), stick to `hybrid` for most queries

---

## 10. Integration with Modified Option 4

### 10.1 Phase 0 Decision Gate (Baseline Validation)

**Timeline**: 3 days
**Goal**: Determine if baseline ICE is sufficient or if enhanced documents are needed.

**Validation Steps**:

**Day 1: Setup & Smoke Test**
```bash
# 1. Create validation environment
mkdir -p validation/{golden_test_set,snapshots,scoring_worksheets,reports,scripts}

# 2. Run smoke test
cd validation/scripts
python run_validation.py --mode smoke --output ../snapshots/v1.0_baseline_smoke.json

# 3. Verify ICE is functional (all 5 smoke queries return reasonable output)
```

**Day 2: Core Validation & Scoring**
```bash
# 1. Run full 20-query validation
python run_validation.py --mode core --output ../snapshots/v1.0_baseline_core.json

# 2. Manual scoring (30 minutes)
# Open scoring_worksheets/v1.0_baseline_scoring.csv
# Score all 20 queries across 9 dimensions

# 3. Calculate Entity Extraction F1 (automated)
python calculate_f1.py \
    --queries Q011,Q012,Q013,Q014,Q015 \
    --snapshot v1.0_baseline_core.json \
    --output entity_f1.json
```

**Day 3: Analysis & Decision**
```bash
# 1. Generate validation report
python generate_report.py \
    --snapshot v1.0_baseline_core \
    --scoring v1.0_baseline_scoring.csv \
    --output ../reports/v1.0_baseline_report.md

# 2. Run failure analysis
python analyze_failures.py \
    --scoring v1.0_baseline_scoring.csv \
    --threshold 4.0 \
    --output ../reports/v1.0_failure_breakdown.md

# 3. Make Modified Option 4 decision
python modified_option_4_decision.py \
    --report v1.0_baseline_report.md \
    --failures v1.0_failure_breakdown.md
```

**Decision Logic**:

```python
# modified_option_4_decision.py

entity_f1 = load_f1_score("entity_f1.json")
overall_score = load_overall_score("v1.0_baseline_report.md")
entity_failure_pct = load_entity_failure_percentage("v1.0_failure_breakdown.md")

# Decision gates
if entity_f1 >= 0.85:
    decision = "✅ BASELINE SUFFICIENT - Entity extraction meets threshold"
    next_phase = "Skip Phase 3 (enhanced docs), focus on query intelligence"

elif entity_f1 >= 0.70:
    decision = "⚠️ BORDERLINE - Try targeted fix first"
    next_phase = "Phase 2: Targeted entity extraction improvements (<100 lines)"

else:  # entity_f1 < 0.70
    decision = "❌ BASELINE INSUFFICIENT - Enhanced documents needed"
    next_phase = "Phase 3: Full enhanced documents integration (1,001 lines)"

# Additional check: Are entity errors actually the bottleneck?
if entity_failure_pct < 20 and overall_score < 3.5:
    decision += " BUT entity errors are NOT primary bottleneck"
    next_phase = "Focus on Synthesis Weakness / Data Gaps instead"

print(f"""
Modified Option 4 Phase 0 Results:
==================================
Entity Extraction F1: {entity_f1:.3f}
Overall Validation Score: {overall_score:.2f}/5.0
Entity Failures: {entity_failure_pct:.1f}% of all failures

DECISION: {decision}
NEXT PHASE: {next_phase}
""")
```

**Example Output**:

```
Modified Option 4 Phase 0 Results:
==================================
Entity Extraction F1: 0.822
Overall Validation Score: 3.85/5.0
Entity Failures: 12.5% of all failures

DECISION: ⚠️ BORDERLINE - Try targeted fix first BUT entity errors are NOT primary bottleneck
NEXT PHASE: Focus on Synthesis Weakness (50% of failures) via QueryEngine improvements
```

---

### 10.2 A/B Validation (Before/After Feature Integration)

**Scenario**: You implemented QueryEngine improvements. Did it work?

**Workflow**:

**Step 1: Run baseline (before)**
```bash
git checkout v1.0_baseline
python run_validation.py --mode core --output ../snapshots/v1.0_baseline_AB.json
# Score manually → v1.0_baseline_scoring.csv
```

**Step 2: Implement feature**
```bash
git checkout -b query_engine_improvements
# ... make changes to QueryEngine prompts ...
git add . && git commit -m "Enhance QueryEngine synthesis prompts"
```

**Step 3: Run new version (after)**
```bash
python run_validation.py --mode core --output ../snapshots/v1.1_improvements_AB.json
# Score manually → v1.1_improvements_scoring.csv
```

**Step 4: Statistical comparison**
```bash
python ab_comparison.py \
    --baseline v1.0_baseline_AB \
    --variant v1.1_improvements_AB \
    --output ../reports/ab_test_results.md
```

**Example Report**:

```markdown
# A/B Test Results: v1.0 Baseline vs v1.1 QueryEngine Improvements

## Statistical Significance:
- **Paired t-test p-value**: 0.023 (< 0.05) → **Statistically significant** ✅
- **Effect size (Cohen's d)**: 0.52 (medium effect)

## Overall Score Change:
- v1.0: 3.85/5.0
- v1.1: 4.15/5.0
- **Δ +0.30** (7.8% improvement) ✅

## Dimension-Level Changes:
| Dimension | v1.0 | v1.1 | Δ | Significance |
|-----------|------|------|---|--------------|
| Actionability | 3.6 | 4.2 | **+0.6** | p=0.01 ✅ |
| Decision Clarity | 3.5 | 4.0 | **+0.5** | p=0.03 ✅ |
| Synthesis Quality | 3.7 | 4.1 | +0.4 | p=0.05 ✅ |
| Relevance | 4.0 | 4.1 | +0.1 | p=0.22 (NS) |

## Failure Reduction:
- v1.0: 8/20 queries <4.0 (40% failure rate)
- v1.1: 4/20 queries <4.0 (20% failure rate)
- **Δ -50% failures** ✅

## Recommendation:
**DEPLOY v1.1** - Statistically significant improvement across synthesis dimensions, no regressions detected.
```

---

## 11. Cost-Aware Metrics

### 11.1 Quality-to-Cost Ratio

**Definition**:
```
Quality-to-Cost Ratio = Overall Score / API Cost (per query)
```

**Why It Matters**:
- LightRAG API costs can vary 10x depending on query mode and document count
- Optimizing for score alone can lead to unsustainable costs
- Need to balance quality with efficiency

**Example Calculation**:

| **Version** | **Avg Score** | **Avg API Cost** | **Ratio** | **Interpretation** |
|-------------|---------------|------------------|-----------|---------------------|
| v1.0 Baseline (`hybrid`) | 3.85 | $0.04 | 96.25 | Baseline |
| v1.1 Enhanced Docs (`hybrid`) | 4.15 | $0.05 | 83.00 | Better quality, worse efficiency |
| v1.2 Mode-Optimized (`smart routing`) | 4.10 | $0.035 | **117.14** | Best efficiency ✅ |

**Interpretation**:
- **v1.1**: +7.8% quality but -13.8% efficiency → Acceptable trade-off for capstone
- **v1.2**: +6.5% quality AND +21.8% efficiency → Optimal production config

---

### 11.2 Cost Breakdown by Query Mode

**Measured across Deep Validation (Stage 3)**:

| **Mode** | **Avg Tokens** | **Avg Cost** | **Avg Score** | **Efficiency Rank** |
|----------|----------------|--------------|---------------|---------------------|
| `naive` | 500 | $0.01 | 3.1 | 1 (most efficient) |
| `local` | 750 | $0.015 | 3.8 | 2 |
| `global` | 1500 | $0.03 | 4.0 | 4 |
| `hybrid` | 2000 | $0.04 | 4.2 | 3 |
| `kg` | 6000 | $0.12 | 4.3 | 6 (least efficient) |
| `mixed` | 3000 | $0.06 | 4.1 | 5 |

**Smart Routing Cost Savings**:
```python
# Baseline: All queries use hybrid
baseline_cost = 20 queries × $0.04 = $0.80

# Smart routing: Use optimal mode per category
smart_cost = (
    5 × $0.04 +  # Portfolio Risk → hybrid
    5 × $0.03 +  # Portfolio Opportunity → global
    5 × $0.015 + # Entity Extraction → local
    3 × $0.12 +  # Multi-Hop → kg
    2 × $0.03    # Comparative → global
) = $0.695

savings = ($0.80 - $0.695) / $0.80 = 13.1% cost reduction
```

**Recommendation**: Implement smart mode routing for 13% cost savings with minimal quality impact.

---

##