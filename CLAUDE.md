# CLAUDE.md - ICE Development Guide

> **🔗 LINKED DOCUMENTATION**: This is one of 6 essential core files that must stay synchronized. When updating this file, always cross-check and update related files: `README.md`, `PROJECT_STRUCTURE.md`, `ICE_DEVELOPMENT_TODO.md`, `PROJECT_CHANGELOG.md`, and `ICE_PRD.md`.

**Location**: `/CLAUDE.md`
**Purpose**: Comprehensive development guidance for Claude Code instances working on ICE
**Last Updated**: 2025-10-08
**Target Audience**: Claude Code AI and human developers

---

## 1. 🚀 QUICK REFERENCE

### Current Project Status
**Phase**: UDMA Integration Complete (6/6 weeks) ✅
**Completion**: 57% (73/128 tasks)
**Current Focus**: Execute test suites and validate integration quality
**Next Milestone**: Run integration tests → Execute PIVF validation → Performance benchmarking

**Recent Achievement**: ✅ Week 6 Complete - Comprehensive testing suite (3 test files, 1,724 lines) validating 6-week UDMA integration

### Essential Commands

**Quick Start (Simplified Architecture)**
```bash
# Environment setup
export OPENAI_API_KEY="sk-..." && cd updated_architectures/implementation

# Test configuration
python config.py

# Run complete system
python ice_simplified.py

# Architecture validation
cd ../tests && python test_architecture_structure.py
```

**Development Workflows**
```bash
# Knowledge graph building (interactive demo/testing)
jupyter notebook ice_building_workflow.ipynb

# Investment intelligence analysis (interactive demo/testing)
jupyter notebook ice_query_workflow.ipynb

# Debug mode with enhanced logging
export PYTHONPATH="${PYTHONPATH}:." && export ICE_DEBUG=1 && python src/simple_demo.py

# Run integration tests
python tests/test_email_graph_integration.py
```

**Testing & Validation**
```bash
# Core functionality tests
python src/ice_lightrag/test_basic.py && python test_api_key.py

# Week 3: SecureConfig validation
python updated_architectures/implementation/test_secure_config.py

# Week 3: Credential rotation utility
python updated_architectures/implementation/rotate_credentials.py --check

# Week 4: Query enhancement validation
python updated_architectures/implementation/test_week4.py

# Data source validation
jupyter notebook sandbox/python_notebook/ice_data_sources_demo_simple.ipynb

# Email integration tests
python tests/test_email_graph_integration.py
```

### Critical Files by Purpose

**Current Work**
- `updated_architectures/implementation/ice_simplified.py` - Main orchestrator (879 lines)
- `ice_building_workflow.ipynb` - Knowledge graph building demo/testing interface (Cell 7.5: provider switching)
- `ice_query_workflow.ipynb` - Investment analysis demo/testing interface (Cell 5.5: provider switching)

**Requirements & Planning**
- `ICE_PRD.md` - Complete product requirements and specifications
- `ICE_DEVELOPMENT_TODO.md` - Detailed task tracking (115 tasks, 43% complete)
- `ICE_ARCHITECTURE_IMPLEMENTATION_PLAN.md` - UDMA implementation guide (User-Directed Modular Architecture, Option 5)
- `archive/strategic_analysis/README.md` - Quick reference for all 5 architectural options analyzed

**Architecture & Implementation**
- `PROJECT_STRUCTURE.md` - Complete directory organization and file navigation
- `src/ice_lightrag/ice_rag_fixed.py` - JupyterSyncWrapper for LightRAG (Week 3: SecureConfig integrated)
- `src/ice_lightrag/model_provider.py` - Model provider factory (OpenAI/Ollama/Hybrid selection)
- `src/ice_lightrag/entity_categories.py` - Entity categorization patterns (9 categories)
- `src/ice_lightrag/relationship_categories.py` - Relationship categorization patterns (10 categories)
- `src/ice_lightrag/graph_categorization.py` - Graph analysis helper functions
- `ice_data_ingestion/secure_config.py` - Encrypted API key management (Week 3)
- `ice_data_ingestion/` - Production data framework (17,256 lines)
- `imap_email_ingestion_pipeline/` - Email processing pipeline (12,810 lines)
- `src/ice_core/` - Production orchestration modules (3,955 lines)

**Testing & Validation**
- `ICE_VALIDATION_FRAMEWORK.md` - PIVF with 20 golden queries and 9-dimensional scoring
- `tests/test_email_graph_integration.py` - Email integration validation
- `updated_architectures/implementation/test_secure_config.py` - Week 3 SecureConfig validation (145 lines)
- `updated_architectures/implementation/rotate_credentials.py` - Week 3 credential rotation utility (236 lines)
- `updated_architectures/implementation/test_week4.py` - Week 4 query enhancement validation (240 lines)
- `check/health_checks.py` - System health monitoring

### Current Sprint Priorities

> **⚠️ TODOWRITE MANDATORY RULES** (See Section 4.1 for complete details)
>
> Every TodoWrite list MUST include these final two todos:
> 1. 📋 Review & update 6 core files + 2 notebooks if changes warrant sync
> 2. 🧠 Update Serena server memory if work warrants documentation

**Week 6 Complete** ✅:
1. ✅ Created `test_integration.py` - 5 integration tests (251 lines) validating UDMA components
2. ✅ Created `test_pivf_queries.py` - 20 golden queries with 9-dimensional scoring (424 lines)
3. ✅ Created `benchmark_performance.py` - 4 performance metrics with targets (418 lines)
4. ✅ Validated notebook structures - Both notebooks verified (21 + 16 cells)
5. ✅ Synchronized 6 core files - All documentation updated for Week 6 completion

**Next Actions**:
- Run `python test_integration.py` to validate 5 integration tests
- Execute `python test_pivf_queries.py` for 20 golden query validation
- Run `python benchmark_performance.py` to measure performance metrics

---

## 2. 📋 DEVELOPMENT CONTEXT

### What is ICE?
**Investment Context Engine (ICE)** is a modular AI system serving as the cognitive backbone for boutique hedge fund workflows. It solves four critical pain points:
1. **Delayed Signal Capture** - Soft signals buried in filings, transcripts, news
2. **Low Insight Reusability** - Investment theses siloed in documents
3. **Inconsistent Decision Context** - Fragmented understanding across team
4. **Manual Triage Bottlenecks** - Slow manual context assembly

**For complete product requirements, user personas, and success metrics**: See `ICE_PRD.md`

### Current Architecture Strategy
**Architecture**: User-Directed Modular Architecture (UDMA) - Option 5 from strategic analysis
**Philosophy**: Simple Orchestration + Production Modules = Best of Both Worlds
**Decision Date**: 2025-01-22 (Finalized: 2025-10-05)

**For complete implementation guide**: See `ICE_ARCHITECTURE_IMPLEMENTATION_PLAN.md`
**For decision history**: See `archive/strategic_analysis/README.md` for all 5 options analyzed

```
ICE Simplified (Orchestrator)          Production Modules (Robust Code)
ice_simplified.py (879 lines)    →    ice_data_ingestion/ (17,256 lines)
    Simple coordination            →    imap_email_ingestion_pipeline/ (12,810 lines)
    Easy to understand             →    src/ice_core/ (3,955 lines)
    Imports from production ←──────────    Circuit breaker, retry, validation
    User-controlled enhancement ←──────   Manual testing decides integration
```

**Data Flow**:
```
3 Data Sources → LightRAG Knowledge Graph → Query Processing → Results
├── API/MCP (NewsAPI, Finnhub, Alpha Vantage, SEC EDGAR)
├── Email (Broker research, analyst reports with BUY/SELL signals)
└── All use robust_client with circuit breaker + retry logic
```

**Storage Architecture**: 2 types, 4 components
```
Vector Stores (3)                 Graph Store (1)
├── chunks_vdb      (text)       └── graph (NetworkX structure)
├── entities_vdb    (entities)        ├── Entity nodes
└── relationships_vdb (concepts)      └── Relationship edges

Current: NanoVectorDBStorage + NetworkXStorage (lightweight, JSON-based)
Production: QdrantVectorDBStorage + Neo4JStorage (scale for >10GB data)
Purpose: Enables LightRAG's dual-level retrieval (entities + relationships)
```

### Dual Notebooks: Demo/Testing Interfaces
**Purpose**: Interactive interfaces for end-to-end validation, aligned with production codebase

**`ice_building_workflow.ipynb`** - Knowledge Graph Construction
- Demonstrates document ingestion pipeline
- Tests entity extraction and relationship discovery
- Validates LightRAG graph building
- Entry point for interactive testing of data sources

**`ice_query_workflow.ipynb`** - Investment Intelligence Analysis
- Demonstrates 5 LightRAG query modes (local, global, hybrid, mix, naive)
- Tests multi-hop reasoning and confidence scoring
- Validates source attribution and citation chains
- Entry point for interactive portfolio analysis

**Synchronization Rule**: When modifying core ICE logic (data ingestion, query processing, graph building), update relevant notebook cells to reflect changes.

### Integration Status
**UDMA Implementation Phases** (See ICE_ARCHITECTURE_IMPLEMENTATION_PLAN.md for complete details):
- ✅ **Phase 0**: Foundation complete (modular structure, build scripts, governance)
- 🔄 **Phase 1**: Email integration in progress (enhanced documents, signal extraction)
- ⏳ **Phase 2+**: User-directed enhancements (manual testing decides what to integrate)

**6-Week Integration Tasks** (tactical execution within UDMA framework):
- ✅ **Week 1 Complete**: Data ingestion integration (3 sources → LightRAG)
- ✅ **Week 2 Complete**: Core orchestration (ICESystemManager)
- ✅ **Week 3 Complete**: Configuration upgrade (SecureConfig)
- ✅ **Week 4 Complete**: Query enhancement (ICEQueryProcessor with fallback logic)
- ✅ **Week 5 Complete**: Workflow notebook updates (80 lines, 57% code reduction)
- ✅ **Week 6 Complete**: Testing & validation (3 test files, 1,724 lines total)

---

## 3. 🛠️ CORE DEVELOPMENT WORKFLOWS

### Starting a New Development Session
1. **Read current status**: Check `ICE_DEVELOPMENT_TODO.md` for current sprint tasks
2. **Review recent changes**: Check `PROJECT_CHANGELOG.md` for latest updates
3. **Understand context**: Read relevant section in `ICE_PRD.md` for requirements
4. **Check file locations**: Use `PROJECT_STRUCTURE.md` to navigate codebase
5. **Set environment**: `export OPENAI_API_KEY="sk-..."` and any other required API keys

### Adding New Data Sources
**Always use production modules - don't reinvent the wheel**

```python
# DON'T: Simple implementation
response = requests.get(url, timeout=30)  # No retry, no circuit breaker

# DO: Use production robust client
from ice_data_ingestion.robust_client import RobustHTTPClient
client = RobustHTTPClient()
response = client.get(url)  # Circuit breaker + retry + connection pooling
```

**Workflow**:
1. Check `ice_data_ingestion/` for existing connectors
2. If connector exists, import and use it in `updated_architectures/implementation/data_ingestion.py`
3. If new source needed, create connector in `ice_data_ingestion/` following existing patterns
4. Create enhanced documents with inline metadata for LightRAG (see Email pipeline pattern)
5. Test with PIVF golden queries to validate integration

### Modifying Orchestration Logic
**File**: `updated_architectures/implementation/ice_simplified.py`

**Pattern**: Keep orchestration simple, delegate complexity to production modules

```python
# DON'T: Implement complex logic in orchestrator
class ICESimplified:
    def complex_query_processing(self, query):
        # 100 lines of query parsing, validation, fallback logic...

# DO: Delegate to production module
from src.ice_core.ice_query_processor import ICEQueryProcessor

class ICESimplified:
    def __init__(self):
        self.query_processor = ICEQueryProcessor(self.core)

    def analyze_portfolio(self, holdings):
        return self.query_processor.analyze_portfolio_risks(holdings)
```

### Notebook Development Workflow
**When to update notebooks**:
- Core data ingestion changes (update `ice_building_workflow.ipynb`)
- Query processing modifications (update `ice_query_workflow.ipynb`)
- New LightRAG features or modes
- Changes to analysis workflows

**How to update**:
1. Modify relevant production code first
2. Update corresponding notebook cells
3. Add markdown explanations for new features
4. Run entire notebook end-to-end to validate
5. Ensure notebook remains aligned with production codebase

### 6-File Synchronization Workflow
⚠️ **MANDATORY RULE**: See Section 4.1 'TodoWrite Requirements' for required final todos in every TodoWrite list.

**When to synchronize**: Creating new core files (documentation, architecture components, validation frameworks)

**The 6 Core Files**:
1. `PROJECT_STRUCTURE.md` - Add file to directory tree and critical files section
2. `CLAUDE.md` - Add reference to relevant section (this file)
3. `README.md` - Add to user-facing documentation
4. `PROJECT_CHANGELOG.md` - Add dated entry with files created/modified
5. `ICE_DEVELOPMENT_TODO.md` - Add/update related tasks
6. `ICE_PRD.md` - Update requirements or decision framework if applicable

**When synchronization applies**:
- ✅ New documentation files (*.md)
- ✅ New architectural components
- ✅ New validation frameworks
- ✅ New workflow notebooks
- ❌ NOT for temporary/test files in sandbox/
- ❌ NOT for minor bug fixes or code changes

**Verification Checklist**:
- [ ] PROJECT_STRUCTURE.md has file location and description
- [ ] CLAUDE.md references file in relevant section
- [ ] README.md includes user-facing description
- [ ] PROJECT_CHANGELOG.md has dated entry
- [ ] ICE_DEVELOPMENT_TODO.md tasks updated if needed
- [ ] ICE_PRD.md updated if requirements/decisions affected

### TodoWrite Mandatory Practice
**CRITICAL**: Every TodoWrite list must include a synchronization check as a final todo:

```
[ ] 📋 Review & update 6 core files + 2 notebooks if changes warrant synchronization
    - Core files: PROJECT_STRUCTURE.md, CLAUDE.md, README.md, PROJECT_CHANGELOG.md, ICE_DEVELOPMENT_TODO.md, ICE_PRD.md
    - Notebooks: ice_building_workflow.ipynb, ice_query_workflow.ipynb
    - Skip only if: bug fixes, minor code changes, temporary/test files
```

**Why**: Prevents documentation drift and ensures project coherence.
**When to skip**: Trivial bug fixes, test files in sandbox/, minor refactoring with no architectural impact.

### Serena Memory Update Mandatory Practice
⚠️ **MANDATORY RULE**: See Section 4.1 'TodoWrite Requirements' for required final todos in every TodoWrite list.

**CRITICAL**: When completing significant development work, the final TodoWrite step must include Serena memory update, after synchronisation check todo:

```
[ ] 🧠 Update Serena server memory if work warrants documentation
    - Use mcp__serena__write_memory for: architecture decisions, implementation patterns, debugging solutions
    - Memory names: Use descriptive names (e.g., 'week6_testing_patterns', 'email_integration_debugging')
    - Document: Key decisions, file locations, workflows, solutions to complex problems
    - Skip only if: Minor bug fixes, temporary code, work-in-progress, trivial changes
```

**Why**: Preserves institutional knowledge across Claude Code sessions and enables faster context restoration.

**What to document**:
- Architecture decisions and rationale
- Implementation patterns and conventions
- File locations and their purposes
- Common workflows and procedures
- Solutions to complex bugs or integration issues
- Performance optimization strategies

**What NOT to document**:
- Temporary or experimental code
- Minor bug fixes with no learning value
- Work-in-progress implementations
- Trivial changes or refactoring

### Testing and Validation
**Three-tier testing approach**:

1. **Unit Tests**: Component-level validation
   ```bash
   python tests/test_email_graph_integration.py  # Email integration
   python src/ice_lightrag/test_basic.py         # LightRAG core
   ```

2. **Integration Tests**: End-to-end workflow validation
   ```bash
   jupyter notebook ice_building_workflow.ipynb   # Data ingestion pipeline
   jupyter notebook ice_query_workflow.ipynb      # Query processing pipeline
   ```

3. **PIVF Validation**: Golden query benchmarking
   - Reference: `ICE_VALIDATION_FRAMEWORK.md`
   - 20 golden queries covering 1-3 hop reasoning
   - 9-dimensional scoring (faithfulness, depth, confidence, attribution, etc.)

### Debugging Integration Issues
**Common workflow**:
1. Check system health: `python check/health_checks.py`
2. Review logs: Check `logs/session_start.json`, `logs/pre_tool_use.json`
3. Validate data sources: Run `sandbox/python_notebook/ice_data_sources_demo_simple.ipynb`
4. Test isolated components: Use relevant notebook cells as entry points
5. Check production module status: Verify `ice_data_ingestion/`, `src/ice_core/` imports working

**LightRAG-specific debugging**:
- Storage location: `ice_lightrag/storage/` (vector DBs and graph data, root-level)
- Direct testing: `python src/ice_lightrag/quick_test.py`
- Query modes: Test with different modes (local, global, hybrid) to isolate issues
- **Note**: Environment variable `ICE_WORKING_DIR` is normalized by LightRAG (removes `./src/` prefix)

---

## 4. 📐 DEVELOPMENT STANDARDS

### TodoWrite Requirements (MANDATORY)

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

**Why These Rules Exist**:
- **Synchronization**: Prevents documentation drift and ensures project coherence across 6 core files + 2 notebooks
- **Memory Update**: Preserves institutional knowledge across Claude Code sessions and enables faster context restoration

**When to Skip**:
- Trivial bug fixes with no architectural impact
- Test files in `sandbox/` or temporary development
- Minor refactoring that doesn't change workflows
- Work-in-progress implementations

**This is not optional.** These todos ensure documentation stays synchronized and institutional knowledge is preserved. See Section 3 for detailed workflow guidance on implementing these requirements.

### File Header Requirements
**Every file must start with these 4 comment lines**:
```python
# Location: /path/to/file.py
# Purpose: Clear description of what this file does
# Why: Business purpose and role in ICE architecture
# Relevant Files: file1.py, file2.py, file3.py
```

### Comment Principles
**Focus on thought process, not obvious syntax**:
```python
# DON'T: Obvious syntax comments
x = x + 1  # Increment x

# DO: Explain thought process and business logic
# Confidence threshold set to 0.7 based on PIVF validation showing
# accuracy >95% at this level while minimizing false positives
confidence_threshold = 0.7
```

**NEVER delete explanatory comments** unless they are demonstrably wrong or obsolete. Update comments instead of removing them.

### ICE-Specific Patterns

**1. Source Attribution** - Every fact must trace to source documents
```python
# All edges must include source metadata
edge_metadata = {
    "source_document_id": "email_12345",
    "confidence": 0.92,
    "timestamp": "2024-03-15T10:30:00Z",
    "extraction_method": "entity_extractor_v2"
}
```

**2. Confidence Scoring** - All extracted entities and relationships include confidence
```python
# Enhanced document format with inline confidence
"""
[TICKER:NVDA|confidence:0.95] [RATING:BUY|confidence:0.87]
Goldman Sachs analyst raised price target to [PRICE_TARGET:500|confidence:0.92]
"""
```

**3. Multi-hop Reasoning** - Support 1-3 hop graph traversal
```python
# Query patterns for different reasoning depths
query_1_hop = "Which suppliers does NVDA depend on?"  # Direct relationships
query_2_hop = "How does China risk impact NVDA through TSMC?"  # Causal chains
query_3_hop = "What portfolios are exposed to AI regulation via chip suppliers?"  # Multi-step
```

**4. MCP Compatibility** - Format outputs as structured JSON
```python
# All analysis results follow MCP-compatible structure
result = {
    "query": "...",
    "answer": "...",
    "sources": [...],
    "confidence": 0.85,
    "reasoning_chain": [...]
}
```

### Code Organization Principles
1. **Modularity**: Build lightweight, maintainable components
2. **Simplicity**: Favor straightforward solutions over complex architectures
3. **Reusability**: Import from production modules, don't duplicate code
4. **Traceability**: Every fact must have source attribution
5. **Security**: Never expose API keys or credentials in code/commits

### Protected Files - NEVER Delete or Move
**Critical files that must remain at project root**:
- `CLAUDE.md` (this file)
- `README.md`
- `ICE_PRD.md`
- `ICE_DEVELOPMENT_TODO.md`
- `PROJECT_STRUCTURE.md`
- `PROJECT_CHANGELOG.md`
- `ice_building_workflow.ipynb`
- `ice_query_workflow.ipynb`

**Before modifying protected files**:
1. Create timestamped backup in `archive/backups/`
2. Get explicit user confirmation
3. Validate cross-references remain intact after changes

---

## 5. 🗂️ FILE MANAGEMENT & NAVIGATION

### When to Check Which Documentation File

**`ICE_PRD.md`** - Product requirements and specifications
- What: Complete product vision, user personas, functional/non-functional requirements
- When: Starting new features, understanding user needs, validating requirements
- Contains: Problems solved, value propositions, success metrics, decision framework

**`ICE_DEVELOPMENT_TODO.md`** - Detailed task tracking
- What: 115 tasks across 5 phases with completion status
- When: Planning sprints, checking current tasks, tracking progress
- Contains: Current sprint priorities, phase breakdowns, integration roadmap

**`PROJECT_STRUCTURE.md`** - Directory organization and file locations
- What: Complete directory tree, file descriptions, organization principles
- When: Looking for specific files, understanding codebase layout, navigation
- Contains: File locations, directory purposes, integration status, data flow

**`ICE_ARCHITECTURE_IMPLEMENTATION_PLAN.md`** - UDMA implementation guide
- What: Complete User-Directed Modular Architecture (UDMA) implementation strategy
- When: Working on architecture decisions, understanding UDMA phases, planning integrations
- Contains: Three foundational principles, implementation phases, build scripts, governance framework
- **Also Known As**: Option 5 from strategic analysis
- **Archived Decision History**: See `archive/strategic_analysis/README.md` for all 5 options analyzed

**`ICE_VALIDATION_FRAMEWORK.md`** - Testing and quality assurance
- What: PIVF with 20 golden queries, 9-dimensional scoring, validation methodology
- When: Testing changes, validating features, benchmarking performance
- Contains: Golden queries, scoring dimensions, acceptance criteria

**`PROJECT_CHANGELOG.md`** - Development history
- What: Day-by-day change tracking, feature additions, bug fixes
- When: Understanding recent changes, reviewing implementation decisions
- Contains: Dated entries, files modified, problem/solution descriptions

**`CLAUDE.md`** (this file) - Development guidance
- What: Comprehensive guide for Claude Code development
- When: Starting sessions, learning workflows, understanding standards
- Contains: Quick reference, workflows, standards, decision framework

**`project_information/user_research/ICE_USER_PERSONAS_DETAILED.md`** - Detailed user personas
- What: Complete persona profiles with background, goals, pain points, use cases
- When: Product planning, understanding user needs in depth, stakeholder presentations
- Contains: Portfolio Manager Sarah, Research Analyst David, Junior Analyst Alex (97 lines)

### Primary Development Files

**Orchestration & Main Interfaces**
- `updated_architectures/implementation/ice_simplified.py` - Main orchestrator (879 lines)
- `ice_building_workflow.ipynb` - Knowledge graph building interface
- `ice_query_workflow.ipynb` - Investment analysis interface

**Production Modules (Import from these)**
- `ice_data_ingestion/` - Data framework with robust client, connectors, validation
- `imap_email_ingestion_pipeline/` - Email processing with signal extraction
- `src/ice_core/` - Orchestration, query processing, graph building utilities
- `src/ice_lightrag/ice_rag_fixed.py` - JupyterSyncWrapper for LightRAG
- `src/ice_lightrag/model_provider.py` - Model provider factory (OpenAI/Ollama/Hybrid)

**Testing & Validation**
- `tests/test_email_graph_integration.py` - Email integration tests
- `src/ice_lightrag/test_basic.py` - Core functionality tests (includes provider tests)
- `sandbox/python_notebook/ice_data_sources_demo_simple.ipynb` - Data source validation

**Configuration & Setup**
- `updated_architectures/implementation/config.py` - Environment configuration
- `src/ice_lightrag/model_provider.py` - LLM provider selection (OpenAI/Ollama/Hybrid)
- `setup/local_llm_setup.py` - Ollama integration for cost optimization
- `.env` - API keys and environment variables (never commit)

### Documentation Structure

**Core Documentation** (Project root)
- `README.md` - End-user project overview
- `CLAUDE.md` - Development guidance (this file)
- `ICE_PRD.md` - Product requirements
- `ICE_DEVELOPMENT_TODO.md` - Task tracking
- `PROJECT_STRUCTURE.md` - Directory guide
- `PROJECT_CHANGELOG.md` - Change history

**Technical Documentation** (md_files/)
- `md_files/LIGHTRAG_SETUP.md` - LightRAG configuration guide
- `md_files/LOCAL_LLM_GUIDE.md` - Ollama setup and optimization
- `md_files/OLLAMA_TEST_RESULTS.md` - Comprehensive Ollama integration test results (hybrid mode validated)
- `md_files/QUERY_PATTERNS.md` - Query strategies and patterns

**Planning Documents** (project_information/)
- `project_information/development_plans/` - Development roadmaps
- `project_information/about_lightrag/` - LightRAG workflow guides
- `project_information/proposals/` - Capstone proposals

---

## 6. 🎯 DECISION FRAMEWORK

### Query Mode Selection
**LightRAG supports 5 query modes** - choose based on query type:

| Mode | Use Case | Example Query | When to Use |
|------|----------|---------------|-------------|
| **local** | Entity lookup, direct facts | "What is NVDA's market cap?" | Simple factual queries |
| **global** | High-level summaries | "Summarize AI chip market trends" | Broad overview needed |
| **hybrid** | Investment analysis (recommended) | "How does China risk impact NVDA?" | Most investment queries |
| **mix** | Complex multi-aspect queries | "Portfolio exposure to AI regulation" | Multi-dimensional analysis |
| **naive** | Simple semantic search | "Find mentions of TSMC" | Keyword-based search |

**Default recommendation**: Use `hybrid` mode for investment queries (combines semantic search + keyword + graph traversal).

### Data Source Prioritization
**Three data sources feed into single LightRAG graph**:

1. **API/MCP Sources** (`ice_data_ingestion/`)
   - When: Real-time market data, financial metrics, news
   - Examples: NewsAPI, Finnhub, Alpha Vantage, SEC EDGAR
   - Latency: Low (API calls)
   - Cost: Medium (API rate limits)

2. **Email Sources** (`imap_email_ingestion_pipeline/`)
   - When: Broker research, analyst reports, investment signals
   - Examples: Goldman Sachs reports, BUY/SELL recommendations
   - Latency: Medium (email processing + entity extraction)
   - Cost: Low (one-time extraction)

3. **SEC Filings** (`ice_data_ingestion/sec_edgar_connector`)
   - When: Regulatory filings, financial statements, management commentary
   - Examples: 10-K, 10-Q, 8-K filings
   - Latency: High (document processing)
   - Cost: Low (publicly available)

**Priority Order**:
- For real-time signals: API/MCP → Email → SEC
- For deep research: Email → SEC → API/MCP
- For regulatory compliance: SEC → Email → API/MCP

### Notebook vs Script Development

**Use Notebooks** (`ice_building_workflow.ipynb`, `ice_query_workflow.ipynb`):
- Interactive testing and validation
- End-to-end workflow demonstration
- Debugging with intermediate outputs
- Experimenting with new features
- Training and documentation

**Use Scripts** (`ice_simplified.py`, production modules):
- Production orchestration logic
- Automated pipelines
- Performance-critical code
- API integrations
- Scheduled tasks

**Both**: Notebooks call production scripts for actual logic (stay aligned with codebase).

### When to Create vs Modify Files

**Create New File** when:
- ✅ New data connector for a different source
- ✅ New validation framework or test suite
- ✅ New architectural component (e.g., new query processor)
- ✅ New documentation for distinct topic

**Modify Existing File** when:
- ✅ Extending current functionality
- ✅ Bug fixes or optimizations
- ✅ Adding features to existing components
- ✅ Updating documentation with new info

**Before creating new files**:
1. Check for existing similar files in `PROJECT_STRUCTURE.md`
2. If similar file exists, consider extending it instead
3. If creating new file, follow 6-file synchronization workflow
4. Archive old files with timestamp suffix (e.g., `old_file_20250122.py`)

### When to Use Production Modules vs Simple Code

**Use Production Modules** from `ice_data_ingestion/`, `src/ice_core/`:
- ✅ HTTP requests (use `robust_client.RobustHTTPClient`)
- ✅ API integrations (use existing connectors)
- ✅ Data validation (use `data_validator.py`)
- ✅ Orchestration logic (use `ICESystemManager`)
- ✅ Query processing (use `ICEQueryProcessor`)
- ✅ Configuration (use `SecureConfig` for API keys)

**Use Simple Code** in `ice_simplified.py`:
- ✅ Coordination and orchestration (delegate complexity)
- ✅ Workflow sequencing
- ✅ High-level business logic
- ✅ Main entry points

**Principle**: **Simple orchestration + production modules** = maintainable architecture. Don't duplicate robust features that already exist in production modules.

---

## 7. 🔧 TROUBLESHOOTING & COMMON ISSUES

### Environment Setup Issues

**API Key Not Found**
```bash
# Error: OpenAI API key not set
# Solution:
export OPENAI_API_KEY="sk-your-api-key-here"

# Verify:
python test_api_key.py
```

**LightRAG Import Error**
```bash
# Error: No module named 'lightrag'
# Solution:
cd src/ice_lightrag && python setup.py && cd ../..

# Verify:
python src/ice_lightrag/test_basic.py
```

**Jupyter Kernel Issues**
```bash
# Error: Kernel not found or crashes
# Solution: Install ipykernel and register kernel
pip install ipykernel
python -m ipykernel install --user --name=ice_env

# Use kernel in notebook: Kernel → Change Kernel → ice_env
```

### Integration Errors

**Module Import Failures**
```python
# Error: Cannot import from ice_data_ingestion
# Check PYTHONPATH:
export PYTHONPATH="${PYTHONPATH}:."

# Verify:
python -c "from ice_data_ingestion import robust_client; print('OK')"
```

**Email Connector Not Found**
```python
# Error: No module named 'imap_email_ingestion_pipeline'
# Check file location:
ls imap_email_ingestion_pipeline/email_connector.py

# Verify:
python -c "from imap_email_ingestion_pipeline.email_connector import EmailConnector; print('OK')"
```

**LightRAG Storage Corruption**
```bash
# If LightRAG storage becomes corrupted:
rm -rf ice_lightrag/storage/*
# Re-run building workflow to recreate graph
jupyter notebook ice_building_workflow.ipynb
```

### Performance Issues

**Slow Query Response**
- Check hop depth (limit to 3 max)
- Use `local` mode for simple lookups instead of `hybrid`
- Reduce confidence threshold if too restrictive
- Check if LightRAG storage is too large (>1GB may need optimization)

**Memory Issues**
```bash
# Set NumExpr threads for large graphs:
export NUMEXPR_MAX_THREADS=14

# Monitor memory usage:
python check/health_checks.py
```

**API Rate Limiting**
- Use `robust_client` with circuit breaker (automatically handles retries)
- Check rate limits in connector config
- Consider caching responses in `storage/cache/`

### Data Quality Issues

**Missing Citations/Sources**
- Verify source attribution in enhanced documents
- Check that `source_document_id` is included in all edges
- Run validation: `python tests/test_email_graph_integration.py`

**Low Confidence Scores**
- Review entity extraction accuracy
- Check if enhanced document format is correct
- Validate extraction method against PIVF benchmarks

**Inconsistent Entity Extraction**
- Use production `EntityExtractor` from email pipeline
- Verify confidence thresholds (should be >0.7 for high precision)
- Check inline metadata format: `[TICKER:NVDA|confidence:0.95]`

### Debug Commands Reference

```bash
# System health check
python check/health_checks.py

# Validate all data sources
jupyter notebook sandbox/python_notebook/ice_data_sources_demo_simple.ipynb

# Test email integration
python tests/test_email_graph_integration.py

# LightRAG quick test
python src/ice_lightrag/quick_test.py

# Enable debug logging
export ICE_DEBUG=1
python updated_architectures/implementation/ice_simplified.py

# Check logs
cat logs/session_start.json | python -m json.tool
cat logs/pre_tool_use.json | python -m json.tool
```

---

## 📚 Additional Resources

### Detailed Technical Guides
- **[LightRAG Setup & Configuration](md_files/LIGHTRAG_SETUP.md)** - Complete LightRAG setup, financial optimizations, query parameters
- **[Local LLM Guide](md_files/LOCAL_LLM_GUIDE.md)** - Ollama setup, hybrid configurations, cost optimization, provider switching methods (3 approaches)
- **[Query Patterns](md_files/QUERY_PATTERNS.md)** - Query strategies, performance optimization, financial use cases

### Architecture Documentation
- **[UDMA Implementation Plan](ICE_ARCHITECTURE_IMPLEMENTATION_PLAN.md)** - User-Directed Modular Architecture (Option 5) complete guide
- **[Architecture Decision History](archive/strategic_analysis/README.md)** - Quick reference for all 5 options analyzed
- **[Validation Framework](ICE_VALIDATION_FRAMEWORK.md)** - PIVF with 20 golden queries and scoring methodology

### LightRAG Workflow Guides
- **[Building Workflow Guide](project_information/about_lightrag/lightrag_building_workflow.md)** - Document ingestion pipeline details
- **[Query Workflow Guide](project_information/about_lightrag/lightrag_query_workflow.md)** - Query processing and retrieval strategies

---

**Last Updated**: 2025-10-11
**Backup**: Previous version saved to `archive/backups/CLAUDE_20251008.md`
**Maintenance**: Update this file when major workflows, architecture, or standards change
