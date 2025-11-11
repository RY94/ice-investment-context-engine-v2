# ICE Coding Patterns Reference

> **Purpose**: Comprehensive implementation patterns for ICE development
> **Audience**: Claude Code AI instances and human developers
> **When to Use**: Reference when implementing new features or debugging code
> **Parent Doc**: `CLAUDE.md` (core daily workflows)

**Last Updated**: 2025-11-05
**Status**: Active reference document

---

## 📋 Pattern Overview

ICE follows specific coding patterns to ensure consistency, traceability, and quality across all implementations. These patterns are **mandatory** for all new code.

### Quick Reference

1. **Source Attribution** - Every fact traces to source document
2. **Confidence Scoring** - All entities/relationships scored (0.0-1.0)
3. **Multi-hop Reasoning** - Support 1-3 hop graph traversal
4. **MCP Compatibility** - Structured JSON outputs
5. **SOURCE Markers** - Embedded attribution for statistics
6. **Crawl4AI Hybrid URL Fetching** - Smart routing for web scraping
7. **Two-Layer Entity Extraction** - Validated + automatic extraction

---

## Pattern 1: Source Attribution

**Requirement**: Every fact and inference must trace back to a verifiable source document.

**Implementation**:
```python
# Edge metadata structure
edge_metadata = {
    "source_document_id": "email_12345",
    "confidence": 0.92,
    "timestamp": "2024-03-15T10:30:00Z"
}

# Node metadata structure
node_metadata = {
    "source": "email_12345",
    "extracted_by": "EntityExtractor",
    "validation_method": "TickerValidator",
    "confidence": 0.95
}

# Full document attribution
document = {
    "content": "...",
    "metadata": {
        "source_type": "email_attachment",
        "email_uid": "12345",
        "sender": "analyst@firm.com",
        "date": "2024-03-15",
        "original_filename": "research_report.pdf"
    }
}
```

**Why**: Regulatory compliance, audit trails, answer traceability

**Validation**: Every query response should show source documents

---

## Pattern 2: Confidence Scoring

**Requirement**: All entities and relationships include confidence scores (0.0-1.0 scale).

**Implementation**:
```python
# Inline markup for enhanced documents
"""
[TICKER:NVDA|confidence:0.95] [RATING:BUY|confidence:0.87]
Goldman Sachs raised price target to [PRICE_TARGET:500|confidence:0.92]

Analyst [PERSON:John Smith|confidence:0.88] expects
[METRIC:Revenue|confidence:0.85] of [VALUE:10.5B|currency:USD|confidence:0.90]
"""

# Entity extraction output
entities = {
    "tickers": [
        {"symbol": "NVDA", "confidence": 0.95, "source": "EntityExtractor"},
        {"symbol": "TSMC", "confidence": 0.83, "source": "TickerValidator"}
    ],
    "ratings": [
        {"ticker": "NVDA", "rating": "BUY", "confidence": 0.87, "analyst": "GS"}
    ]
}

# Relationship scoring
relationship = {
    "source": "NVDA",
    "target": "TSMC",
    "type": "SUPPLIER_DEPENDENCY",
    "confidence": 0.78,
    "evidence_count": 3
}
```

**Confidence Ranges**:
- **0.90-1.00**: High confidence (EntityExtractor + TickerValidator validated)
- **0.80-0.89**: Good confidence (EntityExtractor validated)
- **0.50-0.79**: Medium confidence (LightRAG automatic extraction)
- **0.00-0.49**: Low confidence (needs manual review)

**Why**: Filter false positives, prioritize high-quality signals, gradual quality improvement

---

## Pattern 3: Multi-hop Reasoning

**Requirement**: Support 1-3 hop graph traversal for investment intelligence queries.

**Implementation**:
```python
# 1-hop queries (direct relationships)
query_1_hop = "Which suppliers does NVDA depend on?"
# Expected answer: [TSMC, Samsung, SK Hynix]

# 2-hop queries (causal chains)
query_2_hop = "How does China regulatory risk impact NVDA through TSMC?"
# Expected reasoning: China → TSMC operations → NVDA supply chain

# 3-hop queries (complex portfolio analysis)
query_3_hop = "What portfolios are exposed to AI regulation via chip suppliers?"
# Expected reasoning: AI regulation → Chip suppliers → Portfolio holdings

# Graph traversal implementation
def multi_hop_query(start_entity, max_hops=3):
    """
    Traverse graph from start_entity up to max_hops.
    Returns: List of entities and relationships discovered.
    """
    visited = set()
    results = []

    def traverse(entity, current_hop):
        if current_hop > max_hops or entity in visited:
            return
        visited.add(entity)

        # Get relationships for current entity
        relationships = graph.get_relationships(entity)
        results.extend(relationships)

        # Recurse to connected entities
        for rel in relationships:
            next_entity = rel.target if rel.source == entity else rel.source
            traverse(next_entity, current_hop + 1)

    traverse(start_entity, 1)
    return results
```

**Query Mode Selection**:
- **1-hop**: `local` mode (document-focused)
- **2-hop**: `hybrid` mode (semantic + graph)
- **3-hop**: `mix` mode (adaptive reasoning)

**Why**: Discover non-obvious investment connections, portfolio risk analysis

---

## Pattern 4: MCP Compatibility

**Requirement**: All query outputs must be structured JSON compatible with Model Context Protocol.

**Implementation**:
```python
# Standard query response format
result = {
    "query": "What is NVDA's latest rating?",
    "answer": "Goldman Sachs upgraded NVDA to BUY with $500 price target on March 15, 2024.",
    "sources": [
        {
            "document_id": "email_12345",
            "type": "email_attachment",
            "filename": "GS_NVDA_upgrade.pdf",
            "relevance": 0.95
        }
    ],
    "confidence": 0.87,
    "reasoning_path": [
        {"entity": "NVDA", "hop": 1},
        {"entity": "Goldman Sachs", "hop": 1},
        {"relationship": "RATED_BY", "hop": 1}
    ],
    "metadata": {
        "query_mode": "hybrid",
        "processing_time": 2.3,
        "entities_examined": 15
    }
}

# Signal Store structured response
signal_result = {
    "query_type": "STRUCTURED_RATING",
    "ticker": "NVDA",
    "data": {
        "analyst": "Goldman Sachs",
        "rating": "BUY",
        "price_target": 500.0,
        "date": "2024-03-15",
        "confidence": 0.87
    },
    "source": {
        "email_uid": "12345",
        "filename": "GS_NVDA_upgrade.pdf"
    }
}
```

**Why**: Standardized output format, MCP server integration, consistent UX

---

## Pattern 5: SOURCE Markers

**Requirement**: Embed source attribution that survives LightRAG storage for statistics tracking.

**Implementation**:
```python
# Data layer: Tag documents with source
document = {
    'content': '...',
    'source': 'fmp',  # Financial Modeling Prep
    'metadata': {...}
}

# Orchestrator: Embed SOURCE markers in content
# This markup survives LightRAG's document processing
content_with_marker = f"[SOURCE:FMP|SYMBOL:NVDA]\n{original_content}"

# Alternative sources: newsapi, sec_edgar, email, url_pdf, bloomberg, etc.
sources = {
    'fmp': 'Financial Modeling Prep API',
    'newsapi': 'NewsAPI financial news',
    'sec_edgar': 'SEC EDGAR filings',
    'email': 'Email body content',
    'email_attachment': 'Email attachment (PDF/Excel)',
    'url_pdf': 'URL-linked PDF research report',
    'bloomberg': 'Bloomberg Terminal data'
}

# Statistics layer: Parse markers for source breakdown
import re

def extract_source_stats(documents):
    """Parse SOURCE markers to generate statistics."""
    source_counts = {}

    for doc in documents:
        match = re.search(r'\[SOURCE:(\w+)\|', doc.content)
        if match:
            source = match.group(1).lower()
            source_counts[source] = source_counts.get(source, 0) + 1

    return source_counts

# Example output:
# {'fmp': 45, 'newsapi': 23, 'sec_edgar': 12, 'email': 71, 'url_pdf': 38}
```

**Usage in Notebooks**:
```python
# ice_building_workflow.ipynb Cell 28
# Display source breakdown pie chart
import matplotlib.pyplot as plt

source_stats = extract_source_stats(ingestion_result['documents'])
plt.pie(source_stats.values(), labels=source_stats.keys(), autopct='%1.1f%%')
plt.title('Data Source Distribution')
plt.show()
```

**Why**: Track data source contribution, validate ingestion completeness, cost attribution

---

## Pattern 6: Crawl4AI Hybrid URL Fetching

**Requirement**: Smart routing between simple HTTP and browser automation for URL processing.

**Implementation**:
```python
# Environment configuration (switchable)
export USE_CRAWL4AI_LINKS=true   # Enable hybrid approach
export USE_CRAWL4AI_LINKS=false  # Disable (simple HTTP only, default)
export CRAWL4AI_TIMEOUT=60       # Timeout per page (seconds)
export CRAWL4AI_HEADLESS=true    # Run browser in background

# URL Rate Limiting (added 2025-11-05 for robustness)
export URL_RATE_LIMIT_DELAY=1.0      # Seconds between requests per domain
export URL_CONCURRENT_DOWNLOADS=3     # Max concurrent downloads

# Configuration in config.py
self.use_crawl4ai_links = os.getenv('USE_CRAWL4AI_LINKS', 'false').lower() == 'true'
self.crawl4ai_timeout = int(os.getenv('CRAWL4AI_TIMEOUT', '60'))
self.rate_limit_delay = float(os.getenv('URL_RATE_LIMIT_DELAY', '1.0'))
self.concurrent_downloads = int(os.getenv('URL_CONCURRENT_DOWNLOADS', '3'))

# 6-Tier URL Classification System
tiers = {
    1: "Direct PDF links (DBS, UBS)",           # Simple HTTP
    2: "Token-authenticated (SEC EDGAR)",       # Simple HTTP with auth
    3: "JavaScript-rendered (Goldman, MS)",     # Crawl4AI required
    4: "Premium portals (Bloomberg, Reuters)",  # Crawl4AI required
    5: "Paywalled content (WSJ, FT)",          # Crawl4AI required
    6: "Skip (social media, tracking)"          # Always skip
}

# Smart routing logic
async def fetch_url(url, tier):
    if tier in [1, 2]:
        # Simple HTTP (fast, free, always works)
        content = await self._download_with_retry(session, url)
    elif tier in [3, 4, 5] and self.use_crawl4ai:
        # Browser automation (slower, resource-intensive, premium content)
        content = await self._fetch_with_crawl4ai(url)
    else:
        # Graceful degradation
        try:
            content = await self._download_with_retry(session, url)
        except:
            if self.use_crawl4ai:
                content = await self._fetch_with_crawl4ai(url)
            else:
                logger.warning(f"URL tier {tier} requires Crawl4AI enablement")
    return content

# Success Criteria (4 Levels)
# Level 1: URLs extracted from email bodies ✅
# Level 2: Content downloaded (HTTP or Crawl4AI) ⚠️
# Level 3: Text/tables extracted via Docling ✅
# Level 4: Entities/relationships ingested ✅
```

**Cache Management**:
```bash
# Clear cache for testing
rm -rf data/link_cache/*

# Check cache status
ls -lh data/link_cache/
```

**Integration Files**:
- `config.py`: Configuration toggles
- `intelligent_link_processor.py`: Smart routing logic (103 lines)
- `ultra_refined_email_processor.py`: Email URL extraction

**Documentation**: `md_files/CRAWL4AI_INTEGRATION_PLAN.md`
**Memories**: `crawl4ai_hybrid_integration_plan_2025_10_21`, `crawl4ai_enablement_notebook_2025_11_04`

**Why**: Handle premium research portals, avoid simple HTTP failures, cost-conscious (only use when needed)

---

## Pattern 7: Two-Layer Entity Extraction

**Requirement**: Combine validated (high confidence) and automatic (lower confidence) entity extraction.

**Implementation**:
```python
# Layer 1: EntityExtractor + TickerValidator (HIGH confidence 0.85-0.95)
from imap_email_ingestion_pipeline.entity_extractor import EntityExtractor
from imap_email_ingestion_pipeline.ticker_validator import TickerValidator

extractor = EntityExtractor()
validator = TickerValidator()

# Extract entities
entities = extractor.extract_entities(text, metadata={'source': 'email'})

# Filter false positives (I, NOT, BUY, SELL, etc.)
filtered_entities = validator.filter_tickers(entities)

# Result: High confidence entities
# {
#   'tickers': [{'symbol': 'NVDA', 'confidence': 0.95}],
#   'ratings': [{'ticker': 'NVDA', 'rating': 'BUY', 'confidence': 0.87}]
# }

# Layer 2: LightRAG automatic extraction (LOW confidence 0.50-0.65)
# Runs automatically during LightRAG document ingestion
# No manual intervention required

# Query-time filtering by confidence threshold
high_conf_entities = [e for e in entities if e['confidence'] >= 0.80]
medium_conf_entities = [e for e in entities if 0.50 <= e['confidence'] < 0.80]

# Use high confidence for investment decisions
# Use medium confidence for exploration
```

**TickerValidator Filters** (5 integration points in data_ingestion.py):
1. Email body entities
2. Email attachment entities
3. URL PDF entities
4. Graph nodes
5. Final consolidated entities

**False Positive Examples**:
- Common words: I, NOT, A, IT, AND, OR, FOR
- Financial terms: BUY, SELL, HOLD, RATING, TARGET
- Single letters: Q, E, Y (except valid tickers)

**Integration**:
- **Files**: `ticker_validator.py` (validation logic), `tests/test_ticker_validator.py` (30+ test cases)
- **Impact**: 70% noise reduction on URL PDF entity extraction
- **Usage**: Cell 30.5 in `ice_building_workflow.ipynb` (confidence filtering demo)
- **Memories**: `ticker_validator_noise_reduction_2025_11_04`, `confidence_filtering_two_layer_2025_11_04`

**Why**: Precision vs recall trade-off, gradual quality improvement, user-directed validation

---

## Code Organization Principles

### 1. Modularity
Build lightweight, maintainable components with clear responsibilities.

```python
# DON'T: Monolithic class doing everything
class ICESystem:
    def fetch_data(self): ...
    def extract_entities(self): ...
    def build_graph(self): ...
    def query_graph(self): ...

# DO: Separate components
class DataIngester: ...
class EntityExtractor: ...
class GraphBuilder: ...
class QueryProcessor: ...
```

### 2. Simplicity
Favor straightforward solutions over complex architectures.

```python
# DON'T: Premature optimization
class CachedRetryableHTTPClientWithCircuitBreaker: ...

# DO: Simple + composable
client = RobustHTTPClient()  # Already has all features
```

### 3. Reusability
Import from production modules, don't duplicate code.

```python
# DON'T: Reinvent
def my_http_get(url):
    response = requests.get(url, timeout=30)
    return response.json()

# DO: Use production code
from ice_data_ingestion.robust_client import RobustHTTPClient
client = RobustHTTPClient()
response = client.get(url)  # Circuit breaker + retry + pooling
```

### 4. Traceability
Every fact must have source attribution (Pattern 1).

### 5. Security
Never expose API keys or credentials in code/commits.

```python
# DON'T: Hardcode secrets
api_key = "sk-1234567890abcdef"

# DO: Use SecureConfig
from ice_data_ingestion.secure_config import SecureConfig
config = SecureConfig()
api_key = config.get_credential("openai_api_key")  # AES-256 encrypted
```

---

## When to Use Each Pattern

| Pattern | Use When | Skip When |
|---------|----------|-----------|
| **1. Source Attribution** | Always (mandatory) | Never |
| **2. Confidence Scoring** | All entity/relationship extraction | N/A |
| **3. Multi-hop Reasoning** | Portfolio analysis, risk queries | Simple lookups |
| **4. MCP Compatibility** | All query responses | Internal processing |
| **5. SOURCE Markers** | Data ingestion | Query processing |
| **6. Crawl4AI** | Premium portals, JS sites | Direct PDF links |
| **7. Two-Layer Extraction** | Email/URL processing | API data (already structured) |

---

## Testing Patterns

**Unit Tests**:
```python
def test_source_attribution():
    """Verify all entities have source metadata."""
    entities = extractor.extract_entities(sample_text)
    for entity in entities:
        assert 'source' in entity
        assert 'confidence' in entity

def test_confidence_filtering():
    """Verify confidence thresholds work correctly."""
    high_conf = [e for e in entities if e['confidence'] >= 0.80]
    assert len(high_conf) > 0
    assert all(e['confidence'] >= 0.80 for e in high_conf)
```

**Integration Tests**:
```python
def test_multi_hop_reasoning():
    """Verify 2-hop query returns correct reasoning path."""
    result = ice.query(
        "How does China risk impact NVDA through TSMC?",
        mode="hybrid"
    )
    assert "TSMC" in result['reasoning_path']
    assert len(result['sources']) > 0
    assert result['confidence'] > 0.7
```

---

## Related Documentation

- **CLAUDE.md** - Core daily workflows (parent document)
- **CLAUDE_INTEGRATIONS.md** - Docling and Crawl4AI details
- **ICE_PRD.md** - Product requirements and design principles
- **ICE_ARCHITECTURE_IMPLEMENTATION_PLAN.md** - UDMA architecture
- **ICE_VALIDATION_FRAMEWORK.md** - PIVF golden queries
- **Serena Memories** - Implementation-specific details

---

**Last Updated**: 2025-11-05
**Maintained By**: Claude Code + Roy Yeo
**Version**: 1.0
