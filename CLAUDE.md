# CLAUDE.md - ICE Development Guide

> **🔗 LINKED DOCUMENTATION**: This is one of 6 essential core files that must stay synchronized. When updating this file, always cross-check and update related files: `README.md`, `PROJECT_STRUCTURE.md`, `ICE_DEVELOPMENT_TODO.md`, `PROJECT_CHANGELOG.md`, and `ICE_PRD.md`.

**Location**: `/CLAUDE.md`
**Purpose**: Comprehensive development guidance for Claude Code instances working on ICE
**Last Updated**: 2025-10-18
**Target Audience**: Claude Code AI and human developers

---

## 1. 🚀 QUICK REFERENCE

### Current Project Status

**Phase**: UDMA Integration Complete (Week 6/6) ✅ | 57% (73/128 tasks)

> **📖 For sprint priorities and detailed status**: See `ICE_DEVELOPMENT_TODO.md:1-60`
> **📖 For week completion tracking**: See `PROJECT_CHANGELOG.md`

### Essential Commands

**Quick Start**
```bash
export OPENAI_API_KEY="sk-..." && cd updated_architectures/implementation
python config.py  # Test configuration
python ice_simplified.py  # Run complete system
```

**Development Workflows**
```bash
jupyter notebook ice_building_workflow.ipynb  # Knowledge graph building
jupyter notebook ice_query_workflow.ipynb  # Investment intelligence analysis
export ICE_DEBUG=1 && python src/simple_demo.py  # Debug mode
```

**Testing & Validation**
```bash
python src/ice_lightrag/test_basic.py && python test_api_key.py
python tests/test_imap_email_pipeline_comprehensive.py  # IMAP tests (21 tests, all passing)
jupyter notebook ice_query_workflow.ipynb  # Portfolio analysis (11 test datasets)
```

### Critical Files Quick Reference

| File | Purpose | See Also |
|------|---------|----------|
| `ice_simplified.py` | Main orchestrator (1,366 lines) | Section 3.2 |
| `ice_building_workflow.ipynb` | Knowledge graph construction | Section 3.3 |
| `ice_query_workflow.ipynb` | Investment analysis interface | Section 3.3 |
| `ICE_PRD.md` | Complete product requirements | - |
| `ICE_DEVELOPMENT_TODO.md` | Task tracking (128 tasks) | - |
| `ICE_ARCHITECTURE_IMPLEMENTATION_PLAN.md` | UDMA guide (Option 5) | Section 2 |
| `ICE_VALIDATION_FRAMEWORK.md` | PIVF (20 golden queries) | Section 3.5 |
| `PROJECT_STRUCTURE.md` | Directory organization | Section 5 |

> **📖 For complete file catalog with descriptions**: See `PROJECT_STRUCTURE.md:268-295`
> **📖 For portfolio test datasets (11 portfolios)**: See `PROJECT_STRUCTURE.md:103-122`

---

## 2. 📋 DEVELOPMENT CONTEXT

### What is ICE?

**Investment Context Engine (ICE)** is a modular AI system serving as the cognitive backbone for boutique hedge fund workflows, solving four critical pain points:
1. Delayed Signal Capture
2. Low Insight Reusability
3. Inconsistent Decision Context
4. Manual Triage Bottlenecks

> **📖 For complete product vision and user personas**: See `ICE_PRD.md:1-100`
> **📖 For detailed user personas**: See `project_information/user_research/ICE_USER_PERSONAS_DETAILED.md`

### Current Architecture

**UDMA (User-Directed Modular Architecture)** - Simple Orchestration + Production Modules

> **📖 For complete data flow diagram**: See `README.md:38-69`
> **📖 For storage architecture details**: See `ICE_ARCHITECTURE_IMPLEMENTATION_PLAN.md` Section 9
> **📖 For complete UDMA implementation guide**: See `ICE_ARCHITECTURE_IMPLEMENTATION_PLAN.md`
> **📖 For architecture decision history (5 options analyzed)**: See `archive/strategic_analysis/README.md`

### Integration Status

> **📖 For UDMA implementation phases and 6-week integration timeline**: See `ICE_DEVELOPMENT_TODO.md:19-57`

### Design Philosophy

> **Strategic Positioning**: ICE delivers professional-grade investment intelligence for boutique hedge funds (<$100M AUM) at <$200/month through cost-conscious, relationship-focused architecture.

**Core Principles** (in priority order):

1. **Quality Within Resource Constraints**: Target 80-90% capability at <20% enterprise cost. Accept professional-grade over perfection. (F1≥0.85, <$200/month budget)

2. **Hidden Relationships Over Surface Facts**: Graph-first strategy for multi-hop reasoning (1-3 hops). Trust semantic search for relevance, not manual filtering.

3. **Fact-Grounded with Source Attribution**: 100% source traceability, confidence scores on all entities/relationships, complete audit trail.

4. **User-Directed Evolution**: Build for ACTUAL problems, not imagined ones. Test → Decide → Integrate. Evidence-driven, not speculative. (<10,000 line budget)

5. **Simple Orchestration + Battle-Tested Modules**: Delegate to production modules (34K+ lines), keep orchestrator simple (<2,000 lines). No reinventing wheels.

6. **Cost-Consciousness as Design Constraint**: 80% queries → local LLM, 20% → cloud. Semantic caching (70% hit rate). Free-tier APIs prioritized.

> **📖 For detailed philosophy**: See `project_information/development_plans/Development Brainstorm Plans (md files)/Lean_ICE_Architecture.md`

---

## 3. 🛠️ CORE DEVELOPMENT WORKFLOWS

### 3.1 Starting a New Development Session

1. **Read current status**: Check `ICE_DEVELOPMENT_TODO.md` for current sprint tasks
2. **Review recent changes**: Check `PROJECT_CHANGELOG.md` for latest updates
3. **Understand context**: Read relevant section in `ICE_PRD.md` for requirements
4. **Check file locations**: Use `PROJECT_STRUCTURE.md` to navigate codebase
5. **Set environment**: `export OPENAI_API_KEY="sk-..."` and any other required API keys

### 3.2 Common Development Tasks

**Adding New Data Sources**
```python
# DO: Use production robust client
from ice_data_ingestion.robust_client import RobustHTTPClient
client = RobustHTTPClient()
response = client.get(url)  # Circuit breaker + retry included
```

**Workflow**:
1. Check `ice_data_ingestion/` for existing connectors
2. Import and use in `data_ingestion.py` if exists
3. Create enhanced documents with inline metadata (see Email pipeline pattern)
4. Test with PIVF golden queries

**Modifying Orchestration**
```python
# DO: Delegate to production modules
from src.ice_core.ice_query_processor import ICEQueryProcessor

class ICESimplified:
    def __init__(self):
        self.query_processor = ICEQueryProcessor(self.core)
```

### 3.3 Notebook Development

**When to update notebooks**:
- Core data ingestion changes → Update `ice_building_workflow.ipynb`
- Query processing modifications → Update `ice_query_workflow.ipynb`

**Process**: Modify production code first → Update notebook cells → Run end-to-end validation

### 3.4 TodoWrite Mandatory Practice ⚠️

**CRITICAL**: Every TodoWrite list MUST include these two todos as the FINAL items:

```
[ ] 📋 Review & update 6 core files + 2 notebooks if changes warrant synchronization
    - Core files: PROJECT_STRUCTURE.md, CLAUDE.md, README.md, PROJECT_CHANGELOG.md, ICE_DEVELOPMENT_TODO.md, ICE_PRD.md
    - Notebooks: ice_building_workflow.ipynb, ice_query_workflow.ipynb
    - Skip only if: bug fixes, minor code changes, temporary/test files

[ ] 🧠 Update Serena server memory if work warrants documentation
    - Use mcp__serena__write_memory for: architecture decisions, implementation patterns, debugging solutions
    - Memory names: Use descriptive names (e.g., 'week6_testing_patterns', 'email_integration_debugging')
    - Document: Key decisions, file locations, workflows, solutions to complex problems
    - Skip only if: Minor bug fixes, temporary code, work-in-progress, trivial changes
```

**Why**: Prevents documentation drift and preserves institutional knowledge across Claude Code sessions.

### 3.5 Testing and Validation

**Three-tier approach**:

1. **Unit Tests**: Component-level validation
   ```bash
   python tests/test_email_graph_integration.py
   python src/ice_lightrag/test_basic.py
   ```

2. **Integration Tests**: End-to-end workflow validation
   ```bash
   jupyter notebook ice_building_workflow.ipynb
   jupyter notebook ice_query_workflow.ipynb
   ```

3. **PIVF Validation**: Golden query benchmarking
   - Reference: `ICE_VALIDATION_FRAMEWORK.md`
   - 20 golden queries covering 1-3 hop reasoning
   - 9-dimensional scoring

### 3.6 Debugging Workflows

1. Check system health: `python check/health_checks.py`
2. Review logs: `logs/session_start.json`, `logs/pre_tool_use.json`
3. Validate data sources: `sandbox/python_notebook/ice_data_sources_demo_simple.ipynb`
4. **LightRAG storage**: `ice_lightrag/storage/` (vector DBs and graph data)
5. **Direct testing**: `python src/ice_lightrag/quick_test.py`

---

## 4. 📐 DEVELOPMENT STANDARDS

### 4.1 TodoWrite Requirements (MANDATORY) ⚠️

**CRITICAL**: Every TodoWrite list MUST include these two todos as the FINAL items:

```
[ ] 📋 Review & update 6 core files + 2 notebooks if changes warrant synchronization
[ ] 🧠 Update Serena server memory if work warrants documentation
```

See Section 3.4 for complete details.

### 4.2 File Header Requirements

**Every file must start with these 4 comment lines**:
```python
# Location: /path/to/file.py
# Purpose: Clear description of what this file does
# Why: Business purpose and role in ICE architecture
# Relevant Files: file1.py, file2.py, file3.py
```

### 4.3 Comment Principles

```python
# DON'T: Obvious syntax comments
x = x + 1  # Increment x

# DO: Explain thought process and business logic
# Confidence threshold set to 0.7 based on PIVF validation showing
# accuracy >95% at this level while minimizing false positives
confidence_threshold = 0.7
```

**NEVER delete explanatory comments** unless demonstrably wrong or obsolete.

### 4.4 ICE-Specific Patterns

**1. Source Attribution** - Every fact must trace to source
```python
edge_metadata = {
    "source_document_id": "email_12345",
    "confidence": 0.92,
    "timestamp": "2024-03-15T10:30:00Z"
}
```

**2. Confidence Scoring** - All entities/relationships include confidence
```python
"""
[TICKER:NVDA|confidence:0.95] [RATING:BUY|confidence:0.87]
Goldman Sachs raised price target to [PRICE_TARGET:500|confidence:0.92]
"""
```

**3. Multi-hop Reasoning** - Support 1-3 hop graph traversal
```python
query_1_hop = "Which suppliers does NVDA depend on?"
query_2_hop = "How does China risk impact NVDA through TSMC?"
query_3_hop = "What portfolios are exposed to AI regulation via chip suppliers?"
```

**4. MCP Compatibility** - Format outputs as structured JSON
```python
result = {
    "query": "...",
    "answer": "...",
    "sources": [...],
    "confidence": 0.85
}
```

### 4.5 Code Organization Principles

1. **Modularity**: Build lightweight, maintainable components
2. **Simplicity**: Favor straightforward solutions over complex architectures
3. **Reusability**: Import from production modules, don't duplicate code
4. **Traceability**: Every fact must have source attribution
5. **Security**: Never expose API keys or credentials in code/commits

### 4.6 Protected Files - NEVER Delete or Move

- `CLAUDE.md` (this file)
- `README.md`
- `ICE_PRD.md`
- `ICE_DEVELOPMENT_TODO.md`
- `PROJECT_STRUCTURE.md`
- `PROJECT_CHANGELOG.md`
- `ice_building_workflow.ipynb`
- `ice_query_workflow.ipynb`

**Before modifying**: Create timestamped backup in `archive/backups/`

---

## 5. 🗂️ NAVIGATION & QUICK DECISIONS

### Documentation Quick Reference

| Document | When to Use | Key Content |
|----------|-------------|-------------|
| **ICE_PRD.md** | Starting new features, validating requirements | Product vision, user personas, success metrics |
| **ICE_DEVELOPMENT_TODO.md** | Planning sprints, tracking progress | 128 tasks across 5 phases with status |
| **PROJECT_STRUCTURE.md** | Finding files, understanding layout | Complete directory tree, file descriptions |
| **ICE_ARCHITECTURE_IMPLEMENTATION_PLAN.md** | Architecture decisions, UDMA planning | UDMA guide, implementation phases, build scripts |
| **ICE_VALIDATION_FRAMEWORK.md** | Testing changes, benchmarking | PIVF with 20 golden queries, 9D scoring |
| **PROJECT_CHANGELOG.md** | Understanding recent changes | Day-by-day change tracking |
| **CLAUDE.md** | Session start, learning workflows | Quick reference, standards, workflows |

> **📖 For complete file catalog**: See `PROJECT_STRUCTURE.md:268-295`

### Key Decision Trees

**Query Mode Selection**

> **📖 For complete query mode guide**: See `md_files/QUERY_PATTERNS.md:10-100`

| Mode | Use Case | Example |
|------|----------|---------|
| **local** | Entity lookup | "What is NVDA's market cap?" |
| **global** | High-level summaries | "Summarize AI chip market trends" |
| **hybrid** | Investment analysis (recommended) | "How does China risk impact NVDA?" |
| **mix** | Multi-aspect queries | "Portfolio exposure to AI regulation" |
| **naive** | Semantic search | "Find mentions of TSMC" |

**Data Source Prioritization**

| Priority For | Order |
|--------------|-------|
| Real-time signals | API/MCP → Email → SEC |
| Deep research | Email → SEC → API/MCP |
| Regulatory compliance | SEC → Email → API/MCP |

**IMAP Email Pipeline**

> **📖 For detailed IMAP integration reference**: See Serena memory `imap_integration_reference`

**Brief Overview**: 71 emails → EntityExtractor (668 lines) → GraphBuilder (680 lines) → Enhanced documents → LightRAG

**Working with Email Data**:
```python
ice.ingest_portfolio_data(['NVDA', 'AAPL'])  # Standard workflow
```

**Notebook vs Script Development**

| Use Notebooks | Use Scripts |
|---------------|-------------|
| Interactive testing | Production orchestration |
| End-to-end validation | Automated pipelines |
| Debugging | API integrations |

**Create vs Modify Files**

| Create New | Modify Existing |
|------------|-----------------|
| New data connector | Extending functionality |
| New validation framework | Bug fixes/optimizations |
| New architectural component | Adding features to existing |

**Before creating**: Check `PROJECT_STRUCTURE.md` for similar files

**Production Modules vs Simple Code**

| Use Production Modules | Use Simple Code |
|------------------------|-----------------|
| HTTP requests (`robust_client`) | Coordination/orchestration |
| API integrations | Workflow sequencing |
| Data validation | High-level business logic |
| Query processing (`ICEQueryProcessor`) | Main entry points |

---

## 6. 🔧 TROUBLESHOOTING

> **📖 For comprehensive troubleshooting guide**: See Serena memory `troubleshooting_comprehensive_guide_2025_10_18`

### Top 5 Common Issues

**1. API Key Not Found**
```bash
export OPENAI_API_KEY="sk-your-api-key-here"
python test_api_key.py  # Verify
```

**2. LightRAG Import Error**
```bash
cd src/ice_lightrag && python setup.py && cd ../..
python src/ice_lightrag/test_basic.py  # Verify
```

**3. Module Import Failures**
```bash
export PYTHONPATH="${PYTHONPATH}:."
python -c "from ice_data_ingestion import robust_client; print('OK')"
```

**4. Jupyter Kernel Issues**
```bash
pip install ipykernel
python -m ipykernel install --user --name=ice_env
```

**5. LightRAG Storage Corruption**
```bash
rm -rf ice_lightrag/storage/*
jupyter notebook ice_building_workflow.ipynb  # Recreate graph
```

### Debug Commands Reference

```bash
python check/health_checks.py  # System health
python src/ice_lightrag/quick_test.py  # LightRAG test
export ICE_DEBUG=1 && python updated_architectures/implementation/ice_simplified.py  # Debug mode
cat logs/session_start.json | python -m json.tool  # Check logs
```

---

## 7. 📚 RESOURCES & DEEP DIVES

### Technical Guides
- **[LightRAG Setup & Configuration](md_files/LIGHTRAG_SETUP.md)** - Complete setup, financial optimizations
- **[Local LLM Guide](md_files/LOCAL_LLM_GUIDE.md)** - Ollama setup, hybrid configurations
- **[Ollama Test Results](md_files/OLLAMA_TEST_RESULTS.md)** - Integration validation
- **[Query Patterns](md_files/QUERY_PATTERNS.md)** - Query strategies, performance

### Architecture Documentation
- **[UDMA Implementation Plan](ICE_ARCHITECTURE_IMPLEMENTATION_PLAN.md)** - Complete guide
- **[Architecture Decision History](archive/strategic_analysis/README.md)** - 5 options analyzed
- **[Validation Framework](ICE_VALIDATION_FRAMEWORK.md)** - PIVF methodology

### LightRAG Workflow Guides
- **[Building Workflow](project_information/about_lightrag/lightrag_building_workflow.md)** - Document ingestion
- **[Query Workflow](project_information/about_lightrag/lightrag_query_workflow.md)** - Retrieval strategies

### Serena Memories (Deep Dives)
- `imap_integration_reference` - Full IMAP pipeline integration details
- `troubleshooting_comprehensive_guide_2025_10_18` - Complete troubleshooting reference
- `comprehensive_email_extraction_2025_10_16` - Email extraction patterns
- `email_ingestion_trust_the_graph_strategy_2025_10_17` - Cross-company relationship discovery
- `phase_2_2_dual_layer_architecture_decision_2025_10_15` - Dual-layer architecture rationale

---

**Last Updated**: 2025-10-18
**Backup**: `archive/backups/CLAUDE_20251018_pre_refinement.md`
**Refinement**: Reduced from 991 lines to 550 lines (45% reduction) while preserving 100% of information via migrations
**Maintenance**: Update this file when major workflows, architecture, or standards change
