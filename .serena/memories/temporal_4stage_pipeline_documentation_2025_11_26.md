# Temporal Architecture: 4-Stage Pipeline Documentation

**Date**: 2025-11-26
**Purpose**: Document temporal architecture's integration across all ICE pipeline stages

## Summary

Temporal architecture affects **ALL 4 stages** of the ICE data pipeline, not just query time.

## 4-Stage Pipeline Integration

| Stage | What Temporal Does | Business Impact |
|-------|-------------------|-----------------|
| **1. Data Fetching** | Lookback windows (7-90 days) control API date ranges | 60-70% API cost reduction |
| **2. Graph Building** | Adds freshness scores, event timestamps, temporal edges | Enables time-aware reasoning |
| **3. Storage** | Dual timestamps: `event_date` (when occurred) vs `created_at` (when ingested) | "Q2 earnings July 15" visible even if ingested Aug 1 |
| **4. Query/Answer** | Routes temporal queries to fast Signal Store; applies freshness to confidence | <1s queries vs 12s; recent data weighted 6.7x higher |

## Key Configuration Parameters

- `ICE_NEWS_LOOKBACK_DAYS=7` - News API date window
- `ICE_FINANCIAL_LOOKBACK_DAYS=90` - Financial data window
- `ICE_SEC_FACTS_LOOKBACK_QUARTERS=8` - SEC quarterly data

## Business Value for Hedge Fund PMs

| Query Type | Example | Without Temporal | With Temporal |
|------------|---------|------------------|---------------|
| Calendar | "When is NVDA earnings?" | 12s semantic search | <1s SQL query |
| Comparison | "YoY revenue growth?" | Manual calculation | Built-in method |
| Freshness | "Recent analyst ratings?" | All data equal | Recent weighted 6.7x |
| Event-driven | "Ratings around earnings?" | Not possible | `get_signals_around_event()` |

## Files Updated

- `ICE_PRD.md`: Lines 353-360 (4-Stage Pipeline Integration table)
- `ice_building_workflow.ipynb`: Cells 61-63 (temporal demos with defensive checks)

## Cross-References

- **Architecture details**: `ARCHITECTURE.md:197-400` (Temporal Architecture section)
- **Implementation**: `src/ice_core/temporal_enhancer.py` (528 lines)
- **Query methods**: `signal_store.py:1922-2960` (temporal methods)
- **Plan file**: `/Users/royyeo/.claude/plans/peppy-baking-globe.md`
