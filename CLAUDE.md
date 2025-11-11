# CLAUDE.md - ICE Development Guide

> **🔗 LINKED DOCUMENTATION**: This is one of 8 essential core files that must stay synchronized. When updating this file, always cross-check and update related files: `ARCHITECTURE.md`, `README.md`, `PROJECT_STRUCTURE.md`, `ICE_DEVELOPMENT_TODO.md`, `PROJECT_CHANGELOG.md`, `ICE_PRD.md`, and `PROGRESS.md`.

**Location**: `/CLAUDE.md`
**Purpose**: Quick reference for Claude Code instances working on ICE
**Last Updated**: 2025-11-05
**Target Audience**: Claude Code AI and human developers

> **📖 For comprehensive implementation patterns**: See `CLAUDE_PATTERNS.md`
> **📖 For Docling/Crawl4AI integration details**: See `CLAUDE_INTEGRATIONS.md`
> **📖 For complete troubleshooting guide**: See `CLAUDE_TROUBLESHOOTING.md`

---

## 1. 🚀 QUICK REFERENCE

### 1.1 Current Project Status

**Phase**: UDMA Integration Complete (Week 6/6) ✅ | 65% (91/140 tasks)

> **📖 For sprint priorities and detailed status**: See `ICE_DEVELOPMENT_TODO.md:1-60`
> **📖 For week completion tracking**: See `PROJECT_CHANGELOG.md`

### 1.2 Essential Commands

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

**Temperature Configuration**
```bash
# Entity Extraction (default: 0.3, recommended: ≤0.2 for reproducibility)
export ICE_LLM_TEMPERATURE_ENTITY_EXTRACTION=0.3

# Query Answering (default: 0.5, range: 0.0-1.0)
export ICE_LLM_TEMPERATURE_QUERY_ANSWERING=0.5

# Temperature effects:
# - 0.0: Deterministic (same input → same output, compliance-friendly)
# - 0.3-0.5: Balanced (moderate creativity, mostly consistent)
# - 0.7-1.0: Creative (insights-focused, less reproducible)
```

**Testing & Validation**
```bash
python src/ice_lightrag/test_basic.py && python test_api_key.py
python tests/test_imap_email_pipeline_comprehensive.py  # IMAP tests (21 tests)
jupyter notebook ice_query_workflow.ipynb  # Portfolio analysis (11 test datasets)
```

### 1.3 Critical Files Quick Reference

| File | Purpose | See Also |
|------|---------|----------|
| `ice_simplified.py` | Main orchestrator (1,366 lines) | Section 3.2 |
| `ice_building_workflow.ipynb` | Knowledge graph construction | Section 3.2 |
| `ice_query_workflow.ipynb` | Investment analysis interface | Section 3.2 |
| `ICE_PRD.md` | Complete product requirements | - |
| `ICE_DEVELOPMENT_TODO.md` | Task tracking (140 tasks) | - |
| `ICE_ARCHITECTURE_IMPLEMENTATION_PLAN.md` | UDMA guide (Option 5) | Section 2 |
| `ICE_VALIDATION_FRAMEWORK.md` | PIVF (20 golden queries) | Section 3.3 |
| `PROJECT_STRUCTURE.md` | Directory organization | - |

> **📖 For complete file catalog**: See `PROJECT_STRUCTURE.md`

### 1.4 Session Start Checklist

**Choose your workflow based on task type**:

| Task Type | Read These Files First |
|-----------|------------------------|
| 🐛 **Bug fixing** | `PROGRESS.md` → `CLAUDE_TROUBLESHOOTING.md` → Relevant code |
| ✨ **New feature** | `ICE_PRD.md` → `CLAUDE_PATTERNS.md` → `ARCHITECTURE.md` |
| 🔌 **Integration work** | `CLAUDE_INTEGRATIONS.md` → Production module docs |
| 🏗️ **Architecture changes** | `ARCHITECTURE.md` → `ICE_ARCHITECTURE_IMPLEMENTATION_PLAN.md` |
| 🧪 **Testing/validation** | `ICE_VALIDATION_FRAMEWORK.md` → Test files |
| 📂 **File navigation** | `PROJECT_STRUCTURE.md` |
| 📊 **Understanding current state** | `PROGRESS.md` → `ICE_DEVELOPMENT_TODO.md` |

**Every session**: Check `PROGRESS.md` for current work, blockers, and next actions.

### 1.5 TodoWrite Mandatory Practice ⚠️

**CRITICAL**: Every TodoWrite list MUST include these two todos as the FINAL items:

```
[ ] 📋 Review & update 8 core files + 2 notebooks if changes warrant synchronization
    - Core files: ARCHITECTURE.md, PROGRESS.md, PROJECT_STRUCTURE.md, CLAUDE.md, README.md, PROJECT_CHANGELOG.md, ICE_DEVELOPMENT_TODO.md, ICE_PRD.md
    - ARCHITECTURE.md: Update only on architecture changes (stable north star)
    - PROGRESS.md: ALWAYS update with session state (active work, blockers, next 3-5 actions)
    - Other 6 files: Update only on milestones
    - Notebooks: ice_building_workflow.ipynb, ice_query_workflow.ipynb
    - Skip only if: bug fixes, minor code changes, temporary/test files

[ ] 🧠 Update Serena server memory if work warrants documentation
    - Use mcp__serena__write_memory for: architecture decisions, implementation patterns, debugging solutions
    - Memory names: Use descriptive names (e.g., 'week6_testing_patterns', 'email_integration_debugging')
    - Document: Key decisions, file locations, workflows, solutions to complex problems
    - Skip only if: Minor bug fixes, temporary code, work-in-progress, trivial changes
```

**Why**: Prevents documentation drift and preserves institutional knowledge across Claude Code sessions.

---

## 2. 📋 DEVELOPMENT CONTEXT

### What is ICE?

**Investment Context Engine (ICE)** - Modular AI system serving as cognitive backbone for boutique hedge funds (<$100M AUM), solving delayed signal capture, low insight reusability, inconsistent decision context, and manual triage bottlenecks.

> **📖 For complete product vision and user personas**: See `ICE_PRD.md:1-100`
> **📖 For detailed user personas**: See `project_information/user_research/ICE_USER_PERSONAS_DETAILED.md`

### Current Architecture

**UDMA (User-Directed Modular Architecture)** - Simple Orchestration + Production Modules

> **📖 For complete data flow diagram**: See `README.md:38-69`
> **📖 For complete UDMA implementation guide**: See `ICE_ARCHITECTURE_IMPLEMENTATION_PLAN.md`
> **📖 For architecture decision history (5 options analyzed)**: See `archive/strategic_analysis/README.md`

### Design Philosophy

**Strategic Positioning**: Professional-grade investment intelligence for boutique hedge funds at <$200/month through cost-conscious, relationship-focused architecture.

**Core Principles**: (1) Quality within resource constraints (F1≥0.85, <$200/month), (2) Hidden relationships over surface facts (graph-first, 1-3 hops), (3) Fact-grounded with source attribution (100% traceability), (4) User-directed evolution (evidence-driven), (5) Simple orchestration + battle-tested modules (<2,000 lines orchestrator), (6) Cost-consciousness as design constraint (80% local LLM, semantic caching).

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

**Adding New Data Sources** - See `CLAUDE_PATTERNS.md` Pattern 1-2 for source attribution and confidence scoring

**Modifying Orchestration** - Delegate to production modules (see `CLAUDE_PATTERNS.md` for code organization principles)

**Notebook Development**:
- Core data ingestion changes → Update `ice_building_workflow.ipynb`
- Query processing modifications → Update `ice_query_workflow.ipynb`
- **Process**: Modify production code first → Update notebook cells → Run end-to-end validation

### 3.3 Testing and Validation

**Three-tier approach**:
1. **Unit Tests**: `python tests/test_email_graph_integration.py`
2. **Integration Tests**: Run both notebooks end-to-end
3. **PIVF Validation**: 20 golden queries covering 1-3 hop reasoning (see `ICE_VALIDATION_FRAMEWORK.md`)

---

## 4. 📐 DEVELOPMENT STANDARDS

### 4.1 File Header Requirements

**Every file must start with these 4 comment lines**:
```python
# Location: /path/to/file.py
# Purpose: Clear description of what this file does
# Why: Business purpose and role in ICE architecture
# Relevant Files: file1.py, file2.py, file3.py
```

### 4.2 Comment Principles

```python
# DON'T: Obvious syntax comments
x = x + 1  # Increment x

# DO: Explain thought process and business logic
# Confidence threshold set to 0.7 based on PIVF validation showing
# accuracy >95% at this level while minimizing false positives
confidence_threshold = 0.7
```

**NEVER delete explanatory comments** unless demonstrably wrong or obsolete.

### 4.3 ICE-Specific Patterns

**All 7 patterns with comprehensive examples**: See `CLAUDE_PATTERNS.md`
1. Source Attribution - Every fact must trace to source
2. Confidence Scoring - All entities/relationships include confidence
3. Multi-hop Reasoning - Support 1-3 hop graph traversal
4. MCP Compatibility - Format outputs as structured JSON
5. SOURCE Markers - Document source attribution for statistics tracking
6. Crawl4AI Hybrid URL Fetching - Smart routing for web scraping (6-tier classification)
7. Two-Layer Entity Extraction - Validated entities with quality scores

> **📖 For code examples and testing patterns**: See `CLAUDE_PATTERNS.md`

### 4.4 Code Organization Principles

1. **Modularity**: Build lightweight, maintainable components
2. **Simplicity**: Favor straightforward solutions over complex architectures
3. **Reusability**: Import from production modules, don't duplicate code
4. **Traceability**: Every fact must have source attribution
5. **Security**: Never expose API keys or credentials in code/commits

### 4.5 Protected Files - NEVER Delete or Move

- `CLAUDE.md` (this file)
- `README.md`
- `ICE_PRD.md`
- `ICE_DEVELOPMENT_TODO.md`
- `PROJECT_STRUCTURE.md`
- `PROJECT_CHANGELOG.md`
- `ice_building_workflow.ipynb`
- `ice_query_workflow.ipynb`

### 4.6 Protected Custom Bookmarks Comment - NEVER Delete or Move these navigation markers

  - # AQ1, # SW2, # DE3, # FR4, # GT5, # hy6
  - Used for cmd+f navigation - treat as sacred landmarks


**Before modifying**: Create timestamped backup in `archive/backups/`

---

## 5. 🗂️ NAVIGATION QUICK LINKS

**Core Docs**: `ICE_PRD.md`, `ICE_DEVELOPMENT_TODO.md`, `PROJECT_STRUCTURE.md`, `ICE_ARCHITECTURE_IMPLEMENTATION_PLAN.md`, `ICE_VALIDATION_FRAMEWORK.md`, `PROJECT_CHANGELOG.md`

**Specialized Details**: Query modes (`md_files/QUERY_PATTERNS.md`), Data source prioritization (`ICE_ARCHITECTURE_IMPLEMENTATION_PLAN.md`), Development strategies (`PROJECT_STRUCTURE.md`), LightRAG workflows (`project_information/about_lightrag/`)

---

## 6. 🔧 TROUBLESHOOTING

See `CLAUDE_TROUBLESHOOTING.md` for complete guide (10 sections, 50+ solutions, quick reference table).

**Top 3 Quick Fixes**:
1. API Key: `export OPENAI_API_KEY="sk-..." && python test_api_key.py`
2. LightRAG: `cd src/ice_lightrag && python setup.py && cd ../..`
3. Imports: `export PYTHONPATH="${PYTHONPATH}:."`

---

## 7. 📄 SPECIALIZED DOCUMENTATION

**Load these on-demand** (each has "When to Load" in header):

**CLAUDE_PATTERNS.md** (~400 lines)
- **Use for**: Implementing features, writing code, pattern compliance
- **Contains**: All 7 ICE patterns with code examples, testing guidance

**CLAUDE_INTEGRATIONS.md** (~450 lines)
- **Use for**: Docling/Crawl4AI work, document processing, integration configs
- **Contains**: Switchable architecture guides, 6-tier URL classification, troubleshooting

**CLAUDE_TROUBLESHOOTING.md** (~350 lines)
- **Use for**: Debugging errors, performance issues, data quality problems
- **Contains**: Quick debugging workflow, 50+ issue-solution pairs, validation commands

---

**Last Updated**: 2025-11-05
**Backup**: `archive/backups/CLAUDE_20251105_pre_streamlining.md`
**This Version**: Optimized for effectiveness - added session checklist, improved TodoWrite visibility, removed redundancy
**Maintenance**: Update this file when major workflows, architecture, or standards change
