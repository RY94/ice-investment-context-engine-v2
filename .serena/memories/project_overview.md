# ICE (Investment Context Engine) - Project Overview

## Purpose
ICE is a modular, lightweight AI system designed as the cognitive backbone for hedge fund core workflows including:
- Idea generation
- Equity research  
- Portfolio monitoring
- Risk management
- Investor communications

ICE addresses critical pain points faced by lean boutique hedge funds through an AI-powered **Investment Knowledge Graph** that continuously learns and evolves.

## Current Status (Updated: 2025-01-22)
- **Version**: ICE 2.0 - Integrated Architecture (Simple Orchestration + Production Modules)
- **Development Phase**: Phase 2 - Architecture Integration (6-week roadmap)
- **Progress**: 39% complete (45/115 tasks) - Expanded scope with comprehensive integration
- **Primary Interfaces**: 
  - `ice_building_workflow.ipynb` - Knowledge graph construction workflow
  - `ice_query_workflow.ipynb` - Investment intelligence analysis workflow
  - `ice_simplified.py` - Production orchestrator (to be integrated with production modules)

## Recent Milestones ✅
- **Product Requirements Document Created** (2025-01-22): Unified PRD consolidating fragmented requirements
  - `ICE_PRD.md` - Single source of truth for Claude Code instances
  - Product vision, user personas, functional/non-functional requirements
  - Success metrics, decision framework, scope boundaries
  - Eliminates navigation across 5+ documentation files
- **Architecture Integration Plan Created** (2025-01-22): 6-week roadmap for production module integration
- **Email Pipeline Phase 1 Complete** (2025-01-22): Enhanced document generation with inline metadata
  - 27/27 unit tests passing
  - Ticker extraction >95% accuracy
  - Confidence preservation validated
  - Single LightRAG graph approach confirmed
- **Week 1 Integration Complete**: 3 data sources → LightRAG
  - API/MCP sources (NewsAPI, Finnhub, Alpha Vantage, FMP)
  - Email pipeline (74 sample emails with enhanced documents)
  - SEC EDGAR connector (async filing retrieval)
  - 26 documents successfully ingested to LightRAG

## Key Features
- AI-powered Investment Knowledge Graph using LightRAG
- Real-time data ingestion from 15+ financial APIs + Email + SEC filings
- 6 query modes for different analysis types (local, global, hybrid, mix, naive, kg)
- Enhanced document metadata (inline confidence scores, source attribution)
- MCP-compatible JSON output for tool interoperability
- Local LLM support for cost optimization ($0-7/month vs $50-200/month)
- Robust error handling with circuit breaker and retry mechanisms
- Encrypted API key management (SecureConfig)

## Architecture Strategy
**Integrated Architecture**: Simple Orchestration + Production Modules (34K+ lines)
- Keep simple, understandable orchestration (`ice_simplified.py`)
- Import and use robust production modules (no code duplication)
- 3 major production modules:
  1. `ice_data_ingestion/` (17,256 lines) - API clients, robust framework, SEC connector
  2. `imap_email_ingestion_pipeline/` (12,810 lines) - CORE data source, email intelligence
  3. `src/ice_core/` (3,955 lines) - System orchestration, query processing

## Validation Framework
- **PIVF** (Portfolio Intelligence Validation Framework)
- 20 golden queries for comprehensive quality assessment
- 9-dimensional scoring (5 technical + 4 business quality dimensions)
- Modified Option 4 decision framework with F1-score gates
- Progressive validation workflow (Smoke 5min → Core 30min → Deep 2hr)

## Integration Roadmap (6 Weeks)
- ✅ **Week 1 COMPLETE**: Data Ingestion (robust_client + email + SEC sources) - 26 docs in LightRAG
- **Week 2 (CURRENT)**: Core Orchestration (use ICESystemManager with health monitoring)
- **Week 3**: Configuration (upgrade to SecureConfig for encrypted keys)
- **Week 4**: Query Enhancement (use ICEQueryProcessor with fallbacks)
- **Week 5**: Workflow Notebooks (demonstrate integrated features)
- **Week 6**: Testing & Validation (end-to-end integration tests)

## Target Users
Boutique hedge funds and investment professionals needing intelligent financial analysis and research automation.

## Critical Documentation Files
- **`ICE_PRD.md`** - 🆕 Unified Product Requirements Document (single source of truth for Claude Code instances)
- `ARCHITECTURE_INTEGRATION_PLAN.md` - 6-week integration roadmap
- `ICE_VALIDATION_FRAMEWORK.md` - PIVF quality assessment framework
- `ICE_DEVELOPMENT_TODO.md` - 115-task comprehensive roadmap (39% complete)
- `PROJECT_CHANGELOG.md` - Detailed change tracking
- `CLAUDE.md` - Development guidance for Claude Code
- `README.md` - User-facing project documentation
- `PROJECT_STRUCTURE.md` - Complete directory organization