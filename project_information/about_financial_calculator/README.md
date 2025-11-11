# Financial Calculator Module

**Purpose**: Strategic planning and implementation tracking for ICE's hybrid query system combining transparent retrieval with tool-augmented deterministic calculations.

**Status**: Planning Phase
**Priority**: Medium (Post-MVP, Week 8-9)
**Related Issue**: Operating margin query non-determinism

---

## Problem Statement

LightRAG's LLM performs on-the-fly financial calculations (e.g., Operating Margin = Operating Profit / Revenue × 100) instead of retrieving pre-extracted MARGIN tags. This emergent behavior is:
- ❌ Non-deterministic (different rounding, different formulas)
- ❌ Non-auditable (no source attribution for calculated values)
- ❌ Violates ICE's fact-grounded principle

## Proposed Solution

**Hybrid Approach**: Combine Solution 2 (transparency) + Solution 3 (deterministic tools)

```
Retrieval-First Strategy:
  1. Search for MARGIN tags in graph → If found, return (confidence: 0.95)
  2. If not found, extract components (Operating Profit, Revenue)
  3. Use Python Decimal calculator → Return (confidence: 0.90)
  4. Always tag response: [RETRIEVED] or [CALCULATED]
```

**Benefits**:
- ✅ Deterministic (same inputs = same output)
- ✅ Transparent (user knows method used)
- ✅ Auditable (formula + inputs + sources preserved)
- ✅ Cost-efficient (prefer cached retrieval over calculation)

---

## Documentation

| File | Purpose | Status |
|------|---------|--------|
| `FINANCIAL_CALCULATOR_STRATEGIC_PLAN.md` | Complete strategic plan (10 sections) | ✅ Complete |
| `IMPLEMENTATION_GUIDE.md` | Step-by-step developer guide | 📋 Pending |
| `FORMULA_LIBRARY.md` | Financial formula specifications | 📋 Pending |
| `TESTING_STRATEGY.md` | Test cases and validation approach | 📋 Pending |

---

## Implementation Timeline

**Week 8** (Post-MVP):
- Days 1-2: Core `FinancialCalculator` module
- Days 3-4: `HybridQueryProcessor` orchestrator

**Week 9** (Integration):
- Days 1-2: Integration with `ice_query_workflow.ipynb`
- Day 3: Documentation and analytics

**Total Effort**: 3-4 developer days

---

## Key Design Decisions

1. **Retrieval-First**: Always prefer MARGIN tags (faster, higher confidence)
2. **Deterministic Tools**: Python Decimal calculations (not LLM math)
3. **Unified Response**: Same format for retrieved and calculated results
4. **Confidence Scoring**: Retrieved (0.95) > Calculated (0.90)

See `FINANCIAL_CALCULATOR_STRATEGIC_PLAN.md` Section 4 for complete rationale.

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Retrieval Rate | ≥70% |
| Calculation Accuracy | 100% (deterministic) |
| Query Success Rate | ≥95% |
| Response Time | <2s |

---

## Related Work

- **Investigation**: `Serena memory: operating_margin_extraction_investigation_2025_10_26`
- **Architecture**: `ICE_ARCHITECTURE_IMPLEMENTATION_PLAN.md` (UDMA alignment)
- **Validation**: `ICE_VALIDATION_FRAMEWORK.md` (PIVF golden queries)

---

**Created**: 2025-10-26
**Next Action**: Review strategic plan in Week 8 sprint planning
