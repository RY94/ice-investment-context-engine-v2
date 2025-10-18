# Test Queries Dataset - ICE Validation

**Created**: 2025-10-14
**File**: `test_queries.csv` (project root)
**Purpose**: Structured test query dataset for systematic ICE validation

## Overview

Created 12 test queries covering all 3 user personas and 5 LightRAG query modes for reproducible ICE validation.

## Structure

**CSV Columns**:
```
query_id, persona, query, complexity, recommended_mode, use_case
```

**Distribution**:
- **Personas**: Portfolio Manager (3), Research Analyst (4), Junior Analyst (5)
- **Complexity**: Simple/1-hop (6), Medium/2-hop (4), Complex/3-hop (2)
- **Modes**: local (4), global (4), hybrid (2), mix (2), naive (1)

## Query Breakdown

**Basic Portfolio (Q1-Q2)** - Junior Analyst
- Q1: Portfolio size/listing (local, simple)
- Q2: Sector diversification (local, simple)

**Portfolio Manager (Q3-Q5)** - Strategic
- Q3: Top 3 risks (global, medium)
- Q4: China regulatory impact on tech holdings (hybrid, complex/3-hop)
- Q5: Growth outlook rankings (mix, medium)

**Research Analyst (Q6-Q9)** - Deep-dive
- Q6: TSMC customer concentration risk (local, simple)
- Q7: Semiconductor supply chain evolution (global, medium)
- Q8: NVDA success/failure exposure (hybrid, medium)
- Q9: TSMC-NVDA-AMD competitive dynamics (mix, complex/3-hop)

**Junior Analyst (Q10-Q12)** - Monitoring
- Q10: Most important portfolio developments today (global, medium)
- Q11: BUY/SELL recommendations for NVDA (local, simple)
- Q12: Latest AI chip competition news (naive, simple)

## Usage in Notebooks

```python
import pandas as pd

# Load test queries
df = pd.read_csv('test_queries.csv')

# Run all queries
for idx, row in df.iterrows():
    result = ice.core.query(row['query'], mode=row['recommended_mode'])
    print(f"{row['query_id']}: {result['answer'][:200]}...")
```

## Documentation Updates

**Files updated** (following 6-file synchronization workflow):
1. `PROJECT_STRUCTURE.md` - Added to Core Project Files (line 28)
2. `CLAUDE.md` - Added to Testing & Validation section (2 locations)
3. `PROJECT_CHANGELOG.md` - Changelog #41 entry

**Files not updated** (rationale):
- `README.md` - Not user-facing (development/testing artifact)
- `ICE_PRD.md` - No requirements change
- `ICE_DEVELOPMENT_TODO.md` - Asset creation, not task tracking
- Notebooks - No code changes needed (queries loaded via pd.read_csv())

## Design Decisions

**Source**: Queries derived from `ICE_USER_PERSONAS_DETAILED.md`
- Portfolio Manager: Lines 40-43 (key use cases)
- Research Analyst: Lines 71-75 (key use cases)
- Junior Analyst: Lines 103-107 (key use cases)

**Alignment**: Complements `ICE_VALIDATION_FRAMEWORK.md` (PIVF)
- PIVF has 20 golden queries for 9-dimensional scoring
- test_queries.csv has 12 queries for persona/mode coverage
- Both support systematic validation

**Workflow**: Easy integration with `ice_query_workflow.ipynb`
- Load CSV with pandas
- Iterate through queries
- Track success rates and response times
- Generate validation reports

## Future Enhancements

Potential additions:
- Add expected answer patterns for automated validation
- Add query difficulty ratings (beginner/intermediate/advanced)
- Expand to 20+ queries for comprehensive coverage
- Add temporal queries (e.g., "changes over last quarter")
- Add negative test cases (edge cases, malformed queries)
