# Financial Calculator Strategic Plan
## Hybrid Solution: Transparent Retrieval + Tool-Augmented Fallback

**Created**: 2025-10-26
**Status**: Planning Phase (Not Yet Implemented)
**Priority**: Medium (Post-MVP, Week 8-9)
**Complexity**: Medium (est. 3-4 days implementation)

---

## Executive Summary

**Problem**: LightRAG's LLM performs non-deterministic on-the-fly financial calculations instead of retrieving pre-extracted MARGIN tags, violating ICE's fact-grounded principle.

**Solution**: Hybrid approach combining:
- **Solution 2**: Transparent method attribution (user knows if retrieved vs calculated)
- **Solution 3**: Deterministic Python tools (accurate, auditable calculations)

**Core Principle**: Retrieval-first with deterministic fallback, full transparency, consistent output format.

---

## 1. Strategic Context

### ICE Architecture Alignment

**UDMA (User-Directed Modular Architecture)**:
- ✅ Simple orchestration layer (hybrid query processor ~300 lines)
- ✅ Production calculation module (FinancialCalculator ~400 lines)
- ✅ Delegates to battle-tested tools (Python Decimal for precision)
- ✅ Total budget: ~700 lines (within <10,000 line constraint)

**Fact-Grounded Principle**:
- ✅ 100% source attribution (both retrieved and calculated values)
- ✅ Confidence scoring reflects method (retrieved: 0.95, calculated: 0.90)
- ✅ Complete audit trail (formula + inputs + sources)
- ✅ No LLM hallucinations (deterministic Python calculations)

**Cost-Consciousness**:
- ✅ Retrieval-first minimizes API calls (cached MARGIN tags)
- ✅ Calculation fallback avoids unnecessary graph rebuilds
- ✅ Deterministic tools reduce retry costs (no LLM calculation errors)

### Business Value Proposition

**For Boutique Hedge Funds**:
1. **Regulatory Compliance**: Full audit trail for calculated metrics
2. **Professional Accuracy**: Deterministic calculations (no rounding errors)
3. **Cost Efficiency**: Fallback avoids expensive graph rebuilds
4. **Transparency**: Clear distinction between retrieved vs derived data

**Investment Intelligence Use Cases**:
1. **Margin Analysis**: "What's NVDA's operating margin trend?"
2. **Profitability Screening**: "Which holdings have margins >30%?"
3. **Competitive Benchmarking**: "Compare margins: NVDA vs AMD"
4. **Multi-Hop Reasoning**: "Which AI chip suppliers have improving margins?"

---

## 2. Technical Architecture

### 2.1 System Components

```
┌─────────────────────────────────────────────────────────────────┐
│                     USER QUERY INTERFACE                        │
│  "What was Tencent's operating margin in Q2 2024?"             │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│              HYBRID QUERY PROCESSOR (Orchestrator)              │
│  • Parse query (ticker, period, metric)                        │
│  • Route to retrieval or calculation                           │
│  • Format unified response                                     │
└─────────────────────────────────────────────────────────────────┘
          ↓ (Attempt 1)              ↓ (Attempt 2)
┌──────────────────────┐    ┌──────────────────────────────────┐
│  RETRIEVAL STRATEGY  │    │  CALCULATION STRATEGY            │
│  ──────────────────  │    │  ────────────────────            │
│  1. Search for       │    │  1. Extract components           │
│     MARGIN tags      │    │     from graph                   │
│  2. Return if found  │    │  2. Call FinancialCalculator     │
│  3. High confidence  │    │  3. Return with formula          │
│     (0.95)           │    │  4. Medium confidence (0.90)     │
└──────────────────────┘    └──────────────────────────────────┘
          ↓                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    LIGHTRAG KNOWLEDGE GRAPH                     │
│  • MARGIN tags (pre-extracted, preferred)                      │
│  • TABLE_METRIC tags (components for calculation)              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                   FINANCIAL CALCULATOR TOOL                     │
│  • Deterministic Python calculations                           │
│  • Decimal precision (no floating point errors)                │
│  • Formula library (margins, ratios, returns)                  │
│  • Complete audit trail                                        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                     UNIFIED RESPONSE FORMAT                     │
│  {                                                              │
│    "answer": "36.3%",                                          │
│    "method": "retrieved|calculated",                           │
│    "confidence": 0.95,                                         │
│    "sources": [...],                                           │
│    "metadata": {formula, inputs, ...}                          │
│  }                                                              │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Decision Flow

```python
def query_margin(ticker, period, margin_type):
    """Hybrid query with retrieval-first + calculation fallback"""

    # STEP 1: Attempt Retrieval (Preferred)
    margin_tag = search_graph(f"[MARGIN:{margin_type}|ticker:{ticker}|period:{period}]")

    if margin_tag:
        return {
            'answer': margin_tag.value,           # e.g., "36.3%"
            'method': 'retrieved',                # Transparent method
            'confidence': margin_tag.confidence,  # High (0.95)
            'sources': [margin_tag],              # Direct citation
            'metadata': {
                'extraction_date': margin_tag.extraction_date,
                'table_source': margin_tag.document_id
            }
        }

    # STEP 2: Retrieval Failed → Attempt Calculation (Fallback)
    components = extract_components(ticker, period, margin_type)

    if not components:
        return error_response("Insufficient data")

    # Use deterministic Python tool (NOT LLM math)
    calc_result = FinancialCalculator.calculate_operating_margin(
        operating_profit=components['numerator'],
        revenue=components['denominator']
    )

    return {
        'answer': f"{calc_result['value']}%",    # e.g., "37.50%"
        'method': 'calculated',                  # Transparent method
        'confidence': 0.90,                      # Lower (derived)
        'sources': components['sources'],        # Component citations
        'metadata': {
            'formula': calc_result['formula'],   # Audit trail
            'inputs': calc_result['inputs'],     # Traceability
            'precision': calc_result['precision'] # Deterministic
        }
    }
```

### 2.3 Component Design

#### Component A: FinancialCalculator (Core Tool)

**File**: `src/ice_core/financial_calculator.py`
**Lines**: ~400 (production module)

**Features**:
- Deterministic calculations using Python `Decimal` (no float errors)
- Formula library: margins, ratios, returns, leverage metrics
- Complete audit trail: formula + inputs + sources + precision
- Error handling: division by zero, unit mismatches, invalid inputs
- Extensible: Easy to add new financial formulas

**Example Formulas**:
```python
# Profitability Margins
operating_margin = (operating_profit / revenue) × 100
gross_margin = (gross_profit / revenue) × 100
net_margin = (net_income / revenue) × 100
ebitda_margin = (ebitda / revenue) × 100

# Returns
return_on_equity = (net_income / shareholders_equity) × 100
return_on_assets = (net_income / total_assets) × 100
return_on_invested_capital = (nopat / invested_capital) × 100

# Leverage Ratios
debt_to_equity = total_debt / shareholders_equity
interest_coverage = ebit / interest_expense

# Liquidity Ratios
current_ratio = current_assets / current_liabilities
quick_ratio = (current_assets - inventory) / current_liabilities
```

#### Component B: HybridQueryProcessor (Orchestrator)

**File**: `src/ice_core/hybrid_query_processor.py`
**Lines**: ~300 (simple orchestration)

**Responsibilities**:
1. Parse user query → Extract (ticker, period, metric)
2. Attempt retrieval → Search MARGIN tags in graph
3. Fallback to calculation → Extract components + call FinancialCalculator
4. Format response → Unified output with method transparency
5. Log method used → Analytics for retrieval vs calculation rates

**Key Methods**:
```python
class HybridQueryProcessor:
    def query_margin(ticker, period, margin_type) → QueryResult
    def _attempt_retrieval(ticker, period, margin_type) → Optional[QueryResult]
    def _attempt_calculation(ticker, period, margin_type) → Optional[QueryResult]
    def _extract_components(ticker, period, margin_type) → Dict
    def _parse_metric_value(result, metric_name) → float
```

#### Component C: QueryResult (Data Structure)

**File**: `src/ice_core/hybrid_query_processor.py`
**Lines**: ~20 (dataclass)

**Schema**:
```python
@dataclass
class QueryResult:
    answer: str              # "36.3%" or "37.50%"
    method: str              # "retrieved" | "calculated" | "failed"
    confidence: float        # 0.95 (retrieved) | 0.90 (calculated)
    sources: List[str]       # MARGIN tags or TABLE_METRIC tags
    metadata: Dict[str, Any] # Formula, inputs, extraction_date, etc.
```

---

## 3. Implementation Phases

### Phase 1: Core Infrastructure (Week 8, Days 1-2)

**Deliverables**:
1. ✅ `FinancialCalculator` class with margin calculations
2. ✅ Unit tests for deterministic calculations
3. ✅ Formula validation (compare with Excel/financial calculators)

**Acceptance Criteria**:
- All margin formulas match industry standards
- Decimal precision to 2 decimal places (e.g., 37.50%)
- Division by zero handled gracefully
- 100% test coverage for calculation logic

### Phase 2: Hybrid Processor (Week 8, Days 3-4)

**Deliverables**:
1. ✅ `HybridQueryProcessor` with retrieval-first logic
2. ✅ Component extraction from LightRAG graph
3. ✅ Integration with FinancialCalculator
4. ✅ Unified response formatting

**Acceptance Criteria**:
- Retrieval works when MARGIN tags exist
- Calculation works when only components exist
- Error handling when neither exists
- Method attribution always present

### Phase 3: Integration & Testing (Week 9, Days 1-2)

**Deliverables**:
1. ✅ Integrate with `ice_query_workflow.ipynb`
2. ✅ End-to-end testing with 11 portfolio test datasets
3. ✅ Validation against PIVF golden queries
4. ✅ Performance benchmarking (retrieval vs calculation speed)

**Acceptance Criteria**:
- All 20 PIVF queries work (retrieved or calculated)
- Retrieval rate ≥70% (prefer pre-extracted data)
- Calculation accuracy 100% (deterministic Python)
- Response time <2s for both methods

### Phase 4: Documentation & Analytics (Week 9, Day 3)

**Deliverables**:
1. ✅ User guide: "Understanding Retrieved vs Calculated Answers"
2. ✅ Developer docs: "Adding New Financial Formulas"
3. ✅ Analytics dashboard: Method usage statistics
4. ✅ Serena memory: Implementation patterns and learnings

**Acceptance Criteria**:
- User guide explains transparency clearly
- Developer docs enable easy formula addition
- Analytics track retrieval/calculation rates
- Patterns documented for future reference

---

## 4. Design Decisions & Rationale

### 4.1 Why Retrieval-First?

**Decision**: Always attempt retrieval before calculation

**Rationale**:
1. **Speed**: Direct tag lookup faster than component extraction + calculation
2. **Confidence**: Pre-extracted data has higher confidence (0.95 vs 0.90)
3. **Source Attribution**: MARGIN tags cite exact table row/column
4. **Cost**: Cached retrieval cheaper than LLM-based component extraction

**Tradeoff**: Requires graph rebuild when extraction code changes (stale graph issue)

**Mitigation**: Stale-graph detection warns user to rebuild

### 4.2 Why Deterministic Tools?

**Decision**: Use Python Decimal for calculations, not LLM math

**Rationale**:
1. **Accuracy**: Decimal avoids floating-point errors (0.1 + 0.2 ≠ 0.3)
2. **Determinism**: Same inputs always produce same output
3. **Auditability**: Formula + inputs preserved for compliance
4. **Performance**: Local Python faster than LLM API calls

**Tradeoff**: Limited to formulas we explicitly implement

**Mitigation**: Formula library covers 90% of common metrics, extensible design

### 4.3 Why Unified Response Format?

**Decision**: Same structure for both retrieved and calculated results

**Rationale**:
1. **User Experience**: Consistent interface regardless of method
2. **Analytics**: Easy to track method usage rates
3. **Testing**: Same validation logic for both paths
4. **Future-Proof**: Can add new methods (e.g., ML-predicted) seamlessly

**Tradeoff**: Retrieved data includes unused fields (formula, inputs)

**Mitigation**: Metadata clearly indicates method, unused fields null/empty

### 4.4 Why Confidence Scoring?

**Decision**: Retrieved (0.95) > Calculated (0.90)

**Rationale**:
1. **Risk Awareness**: User knows derived values less certain
2. **Retrieval Preference**: Encourages graph rebuild for better data
3. **Investment Decisions**: Higher confidence for direct facts
4. **Regulatory Compliance**: Distinguish primary vs derived data

**Tradeoff**: Calculated values (Python Decimal) actually 100% accurate

**Mitigation**: Confidence reflects "source quality" not "calculation accuracy"

---

## 5. Integration Points

### 5.1 LightRAG Knowledge Graph

**Current Storage**:
```
ice_lightrag/storage/
├── vdb_entities.json           # Entity embeddings
├── vdb_relationships.json      # Relationship embeddings
├── graph_chunk_entity_relation.graphml  # Graph structure
└── kv_store_full_docs.json     # Full documents with inline tags
```

**Tags Used**:
- **Retrieval**: `[MARGIN:Operating Margin|value:36.3%|period:2Q2024|ticker:TCEHY|confidence:0.95]`
- **Calculation**: `[TABLE_METRIC:Operating Profit|value:69.2B|...]` + `[TABLE_METRIC:Total Revenue|value:184.5B|...]`

**Query Interface**:
```python
# Current LightRAG query
result = rag.query("What is Tencent's operating margin?", param={'mode': 'hybrid'})

# Enhanced hybrid query
hybrid_processor = HybridQueryProcessor(rag)
result = hybrid_processor.query_margin('TCEHY', '2Q2024', 'operating')
```

### 5.2 Email Ingestion Pipeline

**Current Flow**:
```
Email (Tencent Q2 2025 Earnings.eml)
  → Docling AI (extract table)
  → TableEntityExtractor (create margin entities)
  → enhanced_doc_creator (inject MARGIN tags)
  → LightRAG (store in graph)
```

**Enhancement Opportunity** (Future):
```
enhanced_doc_creator (inject MARGIN tags)
  → FinancialCalculator.validate_margin() ← NEW
  → Verify calculated margin matches extracted margin
  → Flag discrepancies for review
```

**Benefit**: Data quality assurance (catch extraction errors)

### 5.3 Query Workflow Notebook

**Current** (`ice_query_workflow.ipynb`):
```python
# Cell 15: Simple query
query = "What was Tencent's operating margin in Q2 2024?"
result = rag.query(query, param=QueryParam(mode="hybrid"))
print(result)
```

**Enhanced** (with hybrid processor):
```python
# Cell 15a: Hybrid query with transparency
from src.ice_core.hybrid_query_processor import HybridQueryProcessor

processor = HybridQueryProcessor(rag)
result = processor.query_margin('TCEHY', '2Q2024', 'operating')

print(f"Answer: {result.answer}")
print(f"Method: {result.method.upper()}")  # RETRIEVED or CALCULATED
print(f"Confidence: {result.confidence}")

if result.method == 'calculated':
    print(f"Formula: {result.metadata['formula']}")
    print(f"Inputs: {result.metadata['inputs']}")
```

**Benefit**: User sees method used, builds trust in derived values

### 5.4 PIVF Validation Framework

**Current**: 20 golden queries for benchmarking

**Enhancement**: Track method usage per query type
```python
# PIVF validation with method tracking
pivf_results = []

for query in golden_queries:
    result = hybrid_processor.query_margin(query.ticker, query.period, query.metric)
    pivf_results.append({
        'query': query,
        'method': result.method,
        'confidence': result.confidence,
        'accuracy': compare_to_ground_truth(result.answer, query.expected)
    })

# Analytics
retrieval_rate = sum(r['method'] == 'retrieved' for r in pivf_results) / len(pivf_results)
print(f"Retrieval rate: {retrieval_rate:.1%}")  # Target: ≥70%
```

**Benefit**: Quantify retrieval vs calculation reliance, guide graph improvements

---

## 6. Success Metrics

### 6.1 Technical Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Retrieval Rate** | ≥70% | % of queries answered via MARGIN tags |
| **Calculation Accuracy** | 100% | Deterministic Python calculations |
| **Response Time (Retrieval)** | <1s | Direct tag lookup |
| **Response Time (Calculation)** | <2s | Component extraction + calculation |
| **Confidence Differentiation** | 0.95 vs 0.90 | Retrieved vs calculated |
| **Formula Coverage** | ≥90% | % of common metrics supported |

### 6.2 Business Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Query Success Rate** | ≥95% | % of queries answered (retrieved or calculated) |
| **User Trust** | High | User feedback on method transparency |
| **Cost Efficiency** | <$200/month | API costs with hybrid approach |
| **Audit Trail Completeness** | 100% | All answers have sources + formula |

### 6.3 Analytics Dashboard

**Tracked Metrics**:
```python
{
    'total_queries': 1000,
    'retrieval_queries': 720,      # 72% (above target)
    'calculation_queries': 250,    # 25%
    'failed_queries': 30,          # 3%
    'avg_retrieval_time': 0.8,     # seconds
    'avg_calculation_time': 1.5,   # seconds
    'confidence_distribution': {
        '0.95': 720,  # Retrieved
        '0.90': 250,  # Calculated
        '0.00': 30    # Failed
    }
}
```

---

## 7. Risk Assessment & Mitigation

### Risk 1: Low Retrieval Rate (<70%)

**Scenario**: Most queries use calculation instead of retrieval

**Impact**: Slower responses, lower confidence scores, increased API costs

**Mitigation**:
1. Rebuild graph regularly (weekly/monthly schedule)
2. Stale-graph detection warns proactively
3. Expand MARGIN tag coverage (more margin types)
4. Analytics identify which margins missing from graph

### Risk 2: Component Extraction Failure

**Scenario**: Cannot extract Operating Profit or Revenue for calculation

**Impact**: Query fails even with fallback

**Mitigation**:
1. Robust TABLE_METRIC extraction (already implemented)
2. Multiple extraction patterns (tag + natural language)
3. Clear error messages guide user to rebuild graph
4. Log failures for analysis (improve extraction)

### Risk 3: Formula Errors

**Scenario**: Wrong formula used or incorrect calculation

**Impact**: Wrong answers damage user trust, investment decisions

**Mitigation**:
1. Unit tests against industry-standard calculators
2. Validation against Excel financial formulas
3. Peer review of formula implementations
4. User-reported discrepancies tracked and fixed

### Risk 4: Complexity Creep

**Scenario**: Users request exotic financial metrics

**Impact**: Formula library grows, maintenance burden increases

**Mitigation**:
1. Start with core metrics (margins, returns, ratios)
2. Prioritize by user demand (track requests)
3. Extensible design (easy to add formulas)
4. Document formula sources (GAAP, IFRS, industry standards)

---

## 8. Future Enhancements

### Phase 5: Machine Learning Predictions (Post-MVP)

**Concept**: Train ML model to predict margins when data sparse

**Use Case**: "What will NVDA's operating margin be in Q3 2025?"

**Architecture**:
```python
if retrieval_failed and calculation_failed:
    # Fallback to ML prediction
    ml_result = MLPredictor.predict_margin(ticker, period, margin_type)
    return {
        'answer': ml_result.value,
        'method': 'predicted',      # New method type
        'confidence': 0.70,         # Lower confidence
        'metadata': {
            'model': 'linear_regression',
            'training_data': ml_result.training_window,
            'uncertainty': ml_result.std_dev
        }
    }
```

**Benefits**: Answer queries even with incomplete data

**Risks**: Lower accuracy, needs extensive validation

### Phase 6: Cross-Company Benchmarking

**Concept**: Calculate relative metrics (vs industry average)

**Use Case**: "Is NVDA's operating margin above industry average?"

**Implementation**:
```python
def calculate_relative_margin(ticker, period, margin_type, benchmark='industry'):
    company_margin = query_margin(ticker, period, margin_type)
    industry_avg = get_industry_benchmark(ticker, margin_type)

    return {
        'company_margin': company_margin.value,
        'industry_avg': industry_avg,
        'difference': company_margin.value - industry_avg,
        'percentile': calculate_percentile(company_margin.value, industry_dist)
    }
```

### Phase 7: Time-Series Analysis

**Concept**: Calculate margin trends (YoY growth, volatility)

**Use Case**: "Is Tencent's operating margin improving?"

**Implementation**:
```python
def analyze_margin_trend(ticker, margin_type, periods=['2Q2024', '3Q2024', '4Q2024', '1Q2025', '2Q2025']):
    margins = [query_margin(ticker, p, margin_type) for p in periods]

    return {
        'trend': calculate_trend(margins),      # improving/declining/stable
        'yoy_change': margins[-1] - margins[0],
        'volatility': calculate_std_dev(margins),
        'forecast': predict_next_quarter(margins)
    }
```

---

## 9. Development Checklist

### Pre-Implementation
- [ ] Review this plan with project stakeholders
- [ ] Validate formula library against industry standards
- [ ] Confirm integration points with current architecture
- [ ] Estimate API cost impact (component extraction queries)
- [ ] Set up testing infrastructure (unit + integration tests)

### Phase 1: Core Infrastructure
- [ ] Create `FinancialCalculator` class
- [ ] Implement margin calculation methods
- [ ] Add Decimal precision handling
- [ ] Write unit tests (100% coverage)
- [ ] Validate against Excel/financial calculators

### Phase 2: Hybrid Processor
- [ ] Create `HybridQueryProcessor` class
- [ ] Implement retrieval-first logic
- [ ] Implement calculation fallback
- [ ] Add component extraction
- [ ] Write integration tests

### Phase 3: Integration & Testing
- [ ] Integrate with `ice_query_workflow.ipynb`
- [ ] Test with 11 portfolio datasets
- [ ] Validate with PIVF golden queries
- [ ] Benchmark retrieval vs calculation performance
- [ ] Fix any bugs discovered

### Phase 4: Documentation
- [ ] Write user guide (retrieved vs calculated)
- [ ] Write developer guide (adding formulas)
- [ ] Create analytics dashboard
- [ ] Document in Serena memory
- [ ] Update `CLAUDE.md` and `ICE_DEVELOPMENT_TODO.md`

---

## 10. References

### Related Documentation
- **Operating Margin Investigation**: `Serena memory: operating_margin_extraction_investigation_2025_10_26`
- **Ticker Linkage Fix**: `Serena memory: attachment_integration_fix_2025_10_24`
- **UDMA Architecture**: `ICE_ARCHITECTURE_IMPLEMENTATION_PLAN.md`
- **PIVF Validation**: `ICE_VALIDATION_FRAMEWORK.md`
- **Query Patterns**: `md_files/QUERY_PATTERNS.md`

### Financial Formula References
- GAAP (Generally Accepted Accounting Principles)
- IFRS (International Financial Reporting Standards)
- CFA Institute: Financial Analysis Standards
- Investopedia: Financial Ratio Formulas

### Technical References
- Python Decimal: https://docs.python.org/3/library/decimal.html
- LightRAG Documentation: `project_information/about_lightrag/`
- ICE Design Philosophy: `project_information/development_plans/.../Lean_ICE_Architecture.md`

---

**Last Updated**: 2025-10-26
**Next Review**: Week 8 Sprint Planning
**Owner**: ICE Development Team
**Status**: 📋 Strategic Plan (Pending Implementation)
