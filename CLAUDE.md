# CLAUDE.md - ICE Development Guide

> **🔗 LINKED DOCUMENTATION**: This is one of 8 essential core files that must stay synchronized. When updating this file, always cross-check and update related files: `ARCHITECTURE.md`, `README.md`, `PROJECT_STRUCTURE.md`, `ICE_DEVELOPMENT_TODO.md`, `PROJECT_CHANGELOG.md`, `ICE_PRD.md`, and `PROGRESS.md`.

**Location**: `/CLAUDE.md`
**Purpose**: Quick reference for Claude Code instances working on ICE
**Last Updated**: 2025-11-26
**Target Audience**: Claude Code AI and human developers

> **📖 For comprehensive implementation patterns**: See `CLAUDE_PATTERNS.md`
> **📖 For Docling/Crawl4AI integration details**: See `CLAUDE_INTEGRATIONS.md`
> **📖 For complete troubleshooting guide**: See `CLAUDE_TROUBLESHOOTING.md`

---

## ⚠️ SESSION STATE RULE (READ EVERY TIME)

**Before ending ANY session or when completing significant work, you MUST:**

1. **Update `PROGRESS.md`** → "🎯 ACTIVE WORK (This Session)" section with:
   - What was accomplished
   - Current blockers (if any)
   - Next 3-5 actions for continuation

2. **Create/update Serena memory** (`mcp__serena__write_memory`) if:
   - Implementation work was done
   - Architecture decisions were made
   - Complex debugging was solved

**Why this matters**: If Claude Code crashes mid-work, the next instance runs `/resume` which reads these files. **Stale files = broken recovery. This is YOUR responsibility.**

**Recovery command**: `/resume` - Use this at session start after a crash or to continue previous work.

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

**Phase 1 Feature: Manifest-Based Ingestion**
```python
# In ice_building_workflow.ipynb Cell 15 (ingestion cell)
USE_MANIFEST = True   # Phase 1: Smart deduplication, 5-20x faster re-runs
USE_MANIFEST = False  # Legacy: Full re-ingestion (for A/B testing)
```
- **Manifest mode**: Prevents duplicates, tracks portfolio changes, incremental updates
- **Legacy mode**: Complete rebuild every time (use for baseline comparison)
- **Performance**: 80-95% deduplication rate on second run onwards
- **See**: Notebook documentation cell before Cell 15 for detailed explanation

**Temperature & Lookback Configuration**
```bash
# Temperature: entity=0.3 (≤0.2 for reproducibility), query=0.5 (0.0=deterministic, 1.0=creative)
export ICE_LLM_TEMPERATURE_ENTITY_EXTRACTION=0.3
export ICE_LLM_TEMPERATURE_QUERY_ANSWERING=0.5

# Lookback: news=7d, financial=90d (reduce for 60-70% API cost savings)
export ICE_NEWS_LOOKBACK_DAYS=7
export ICE_FINANCIAL_LOOKBACK_DAYS=90
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
| `ice_simplified.py` | Main orchestrator (4,061 lines) | Section 3.2 |
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

### 3.4 Temporal Enhancement Workflows

For temporal features (freshness scoring, YoY/QoQ, trend detection, event-driven analysis):
- **Architecture & Code Examples**: See `ARCHITECTURE.md` → "Temporal Architecture" section (lines 193-522)
- **Testing**: `python -m pytest tests/test_temporal_features_comprehensive.py -v`
- **Notebook Demos**: Cells 70-78 in `ice_building_workflow.ipynb`
- **Serena Memories**: 5 comprehensive temporal enhancement guides

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

### 4.6 Protected Custom Bookmarks Comment - Strictly NEVER Delete or Move these navigation markers.

  - # AQ1, # SW2, # DE3, # FR4, # GT5, # hy6
  - Used for cmd+f navigation - treat as sacred landmarks


**Before modifying**: Create timestamped backup in `archive/backups/`

### 4.7 Architecture Change Protocol ⚠️

**CRITICAL**: When implementing architecture changes, you MUST update `ARCHITECTURE.md` and `ICE_PRD.md` BEFORE completing your work.

**What qualifies as architecture changes** (MUST update ARCHITECTURE.md):
- ✅ **New design patterns**: quality-based selection, context-aware routing, resilience strategies
- ✅ **Core design principles**: cost optimization, graceful degradation, data flow changes
- ✅ **Major refactors**: Changes to system behavior, component responsibilities, integration patterns
- ✅ **New invariants/contracts**: API contracts, data schemas, error handling policies
- ✅ **Significant data flow changes**: New data sources, processing pipelines, storage architectures

**What does NOT require ARCHITECTURE.md update** (document elsewhere):
- ❌ Bug fixes (unless they reveal architectural issues requiring design changes)
- ❌ Minor optimizations (performance tweaks, code cleanup)
- ❌ Implementation details (goes in code comments, not architecture docs)
- ❌ Temporary/experimental features (not production-ready)

**Required Process**:
1. ✅ Make code changes
2. ✅ Update `ARCHITECTURE.md` with new section or modify existing section
3. ✅ Update "Last Updated" date and summary at top of ARCHITECTURE.md
4. ✅ Add cross-references to related files (code locations, Serena memories)
5. ✅ Include ARCHITECTURE.md in commit/documentation update

**Example Qualifying Changes**:
- Multi-Source News Aggregation (Nov 22): New design pattern → Added full section to ARCHITECTURE.md
- Temporal Enhancement (Nov 18): New data flow → Added temporal architecture section
- Content-Addressable Deduplication (Nov 21): Core principle change → Updated deduplication section

**Enforcement**: This is part of the mandatory TodoWrite checklist ("📋 Review & update 8 core files")

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


---

## 8. 📦 WORK PHASE ARCHIVAL WORKFLOW

> **When to archive**: Phase complete (all tasks done, tests passing, docs updated, production-ready)
> **What archives**: Phase tracking files, temporary analysis (*_FIXES.md, CRITICAL_*.md), test logs
> **What stays**: 8 core files, production code, Serena memories

### Archive Process

**1. Setup** (customize per phase):
```bash
PHASE_ID="phase_2_7b"  # e.g., feature_xyz, experiment_123
TRACKING_FILE="REFINEMENT_PLAN_STATUS.md"
COMPLETION_DATE=$(date +%Y_%m_%d)
ARCHIVE_BASE="archive/${PHASE_ID}"
```

**2. Create structure & move files**:
```bash
mkdir -p "${ARCHIVE_BASE}"/{working_docs,test_results}
mv "${TRACKING_FILE}" "${ARCHIVE_BASE}/${PHASE_ID^^}_COMPLETE_${COMPLETION_DATE}.md"
mv CRITICAL_*.md *_FIXES.md *_ANALYSIS*.md "${ARCHIVE_BASE}/working_docs/" 2>/dev/null
```

**3. Create archive README** containing: phase summary, duration, deliverables, key files modified

**4. Run phase tests & save results**:
```bash
python3 -m pytest tests/test_${PHASE_ID}*.py -v > "${ARCHIVE_BASE}/test_results/results_${COMPLETION_DATE}.log" 2>&1
```

**5. Verification checklist**:
- [ ] Main tracking file archived with timestamp
- [ ] Archive README.md created
- [ ] Working docs moved to archive
- [ ] Root clean (only 8 core files + production code remain)

**6. Update permanent docs & commit**:
- Update PROGRESS.md (session entry), ICE_DEVELOPMENT_TODO.md (mark complete)
- `git add archive/${PHASE_ID}/ && git commit -m "Archive: ${PHASE_ID} Complete"`

### Root Directory Policy

**Always keep**: README, CLAUDE, ARCHITECTURE, PROJECT_STRUCTURE, PROJECT_CHANGELOG, ICE_DEVELOPMENT_TODO, ICE_PRD, PROGRESS
**During active work**: + Phase tracking files, temporary analysis
**After completion**: Archive everything except 8 core files → `archive/phase_*/`

---

**Applies to**: Refinements, features, prototypes, experiments, research phases
**Does NOT apply to**: Bug fixes, minor tweaks, documentation-only changes
