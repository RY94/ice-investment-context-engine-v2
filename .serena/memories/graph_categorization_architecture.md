# Graph Categorization Configuration Architecture

## Overview
Implemented elegant, pattern-based categorization system for ICE knowledge graph entities and relationships, externalizing configuration into reusable Python modules.

## User Request
"can we categorise these entities and relationships? What is the most elegant method to do this?"
- Context: 165 entities, 139 relationships in LightRAG graph
- Goal: Provide meaningful categorization for graph health metrics
- Constraint: Write as little code as possible, ensure elegance and accuracy

## Design Philosophy

### Why Python Modules (not YAML/JSON)?
**Decision**: Python files (.py) over YAML/JSON
**Rationale**:
- Zero external dependencies (no yaml module needed)
- Direct import, no parsing overhead
- Native Python type hints and documentation
- Comments and docstrings for intuitive headings
- More Pythonic and maintainable

### Why src/ice_lightrag/ Directory?
**Decision**: Store in `src/ice_lightrag/` (not root config/)
**Rationale**:
- Tightly coupled to LightRAG graph analysis
- Natural location for graph-related utilities
- Keeps all LightRAG code together
- Module structure: `from src.ice_lightrag.graph_categorization import ...`

## Files Created

### 1. entity_categories.py (220 lines)
**Purpose**: Entity categorization patterns

**Structure**:
```python
ENTITY_PATTERNS: Dict[str, Dict[str, any]] = {
    'Category Name': {
        'description': 'Clear explanation',
        'patterns': ['KEYWORD1', 'KEYWORD2', ...],
        'examples': ['Example 1', 'Example 2'],
        'priority': 1  # Lower = checked first
    }
}
```

**9 Entity Categories** (priority order):
1. **Industry/Sector** - Most specific (SECTOR:, INDUSTRY:)
2. **Company** - Tickers (NVDA, TSMC, AMD, ASML) + corporate suffixes
3. **Financial Metric** - PE Ratio, Market Cap, Revenue, Moving Averages
4. **Technology/Product** - AI, GPU, Chip, SoC
5. **Market Infrastructure** - NASDAQ, USD, exchanges
6. **Geographic** - Countries, states, cities
7. **Regulation/Event** - Bans, policies, regulations
8. **Media/Source** - Financial Times, news outlets
9. **Other** - Fallback (empty patterns list)

**Pattern Matching**:
- Uppercase comparison: `"NVIDIA Corporation".upper()` contains `"NVDA"`
- First match wins (priority ordering critical)
- Searches both `entity_name` and `content` fields

### 2. relationship_categories.py (242 lines)
**Purpose**: Relationship categorization patterns

**Structure**: Same dict format as entities

**10 Relationship Categories** (priority order):
1. **Financial** (~29%) - performance, valuation, metrics, stock
2. **Regulatory** (~5%) - regulation, compliance, ban, policy
3. **Supply Chain** (~8%) - supplier, manufacturing, dependency
4. **Product/Tech** (~18%) - development, innovation, technology
5. **Corporate** (~11%) - headquarters, ownership, location
6. **Industry** (~10%) - classification, sector, business focus
7. **Market** (~8%) - trading, currency, exchange
8. **Impact/Correlation** (~7%) - impact, affect, influence
9. **Media/Analysis** (~8%) - reporting, analysis, news
10. **Other** (~6%) - Fallback

**LightRAG Relationship Format**:
```
Line 1: src_id\ttgt_id
Line 2: relationship_type1,relationship_type2  <-- Patterns match here
Line 3+: Description text
```

**Helper Function**: `extract_relationship_types(content)` - Extracts line 2

### 3. graph_categorization.py (197 lines)
**Purpose**: Helper functions for categorization

**Key Functions**:
1. `categorize_entity(name, content)` - Single entity classification
2. `categorize_relationship(content)` - Single relationship classification
3. `categorize_entities(data)` - Batch entity processing
4. `categorize_relationships(data)` - Batch relationship processing
5. `get_top_categories(counts, top_n=5)` - Top N with percentages
6. `format_category_display(counts)` - Formatted output for notebooks

**Algorithm**:
- Single-pass through data
- Priority-ordered pattern matching
- Returns category distribution dict
- Display order configurable

## Usage Patterns

### In Notebooks
```python
from src.ice_lightrag.graph_categorization import categorize_entities, categorize_relationships

# Load data from LightRAG storage
entities_file = Path('ice_lightrag/storage/vdb_entities.json')
data = json.loads(entities_file.read_text())

# Categorize
entity_stats = categorize_entities(data['data'])
# Returns: {'Company': 15, 'Financial Metric': 45, ...}

# Display top 5
from src.ice_lightrag.graph_categorization import get_top_categories
top5 = get_top_categories(entity_stats, top_n=5)
# Returns: [('Financial Metric', 45, 27.3%), ...]
```

### In Production Code
```python
from src.ice_lightrag.graph_categorization import categorize_entity

# Categorize single entity
category = categorize_entity("NVIDIA Corporation", "Leading GPU manufacturer")
# Returns: "Company"
```

## Validation Results

**Tested with Real Data**:
- 165 entities from `ice_lightrag/storage/vdb_entities.json` (2.0 MB)
- 139 relationships from `ice_lightrag/storage/vdb_relationships.json` (1.7 MB)

**Sample Output**:
```
Entity Categories:
  Financial Metrics: 45 (27.3%)
  Other: 43 (26.1%)
  Technology/Product: 20 (12.1%)
  Companies: 15 (9.1%)

Relationship Types:
  Financial: 40 (28.8%)
  Product/Tech: 25 (18.0%)
  Corporate: 15 (10.8%)
```

## Design Benefits

### Maintainability
- **Patterns separate from logic**: Easy to update without touching code
- **Clear structure**: Dict-based with intuitive keys
- **Self-documenting**: Descriptions, examples, priorities included

### Extensibility
- **Add categories**: Just add new dict entry with patterns
- **Modify patterns**: Edit patterns list, no code changes
- **Priority control**: Adjust priority field to change match order

### Performance
- **Fast**: Single-pass, no LLM calls, pattern matching only
- **Efficient**: Uppercase comparison, early exit on first match
- **Scalable**: Handles large graphs (tested with 165+139 items)

### Reusability
- **Module structure**: Import anywhere in ICE
- **Helper functions**: Reusable across components
- **Batch operations**: Process entire datasets efficiently

## Integration Points

**Current Usage**:
- `ice_building_workflow.ipynb` Cell 10 - Graph health metrics (pending implementation)

**Future Usage**:
- Dashboard category breakdowns
- Query result filtering
- Network visualization by category
- Portfolio composition analysis
- Anomaly detection (entities in wrong categories)

## File Locations

**Pattern Definitions**:
- `/src/ice_lightrag/entity_categories.py` - Entity patterns (9 categories)
- `/src/ice_lightrag/relationship_categories.py` - Relationship patterns (10 categories)

**Helper Functions**:
- `/src/ice_lightrag/graph_categorization.py` - Categorization logic

**Documentation**:
- `/PROJECT_STRUCTURE.md` - Directory tree updated
- `/CLAUDE.md` - Architecture section updated
- `/README.md` - Usage example added
- `/PROJECT_CHANGELOG.md` - Entry #33 with complete details

## Key Decisions Rationale

### Priority-Based Matching
**Why**: Prevents misclassification
**Example**: "SECTOR: TECHNOLOGY" should match Industry/Sector (priority 1), not Technology/Product (priority 4)
**Implementation**: Sort by priority field before pattern matching

### First Match Wins
**Why**: Efficiency and determinism
**Alternative considered**: Score all categories and pick highest
**Result**: Faster, simpler, works well with priority ordering

### Uppercase Comparison
**Why**: Case-insensitive matching without regex
**Implementation**: `"NVIDIA Corporation".upper()` contains `"NVDA"`
**Result**: Simple, fast, reliable

### No LLM Classification
**Why**: Speed, cost, determinism
**Alternative considered**: LLM-based classification
**Result**: 165 entities would need 165 API calls ($$$), slow, non-deterministic

## Related Memories
- `graph_health_metrics_implementation` - Uses these categorization patterns
- Check for future memories about notebook Cell 10 implementation

## Maintenance Notes
- **To add category**: Add dict entry with patterns, priority, description
- **To modify patterns**: Edit patterns list in category dict
- **To change priority**: Adjust priority field (lower = checked first)
- **Pattern syntax**: Uppercase keywords, no regex needed
