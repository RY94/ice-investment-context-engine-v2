# sample_data.py
# Clean, importable sample data for ICE Development Environment
# Extracted from ui_mockups/ice_ui_v17.py for reliable data loading
# Provides consistent dummy data for development, testing, and demonstration
# Data can be exported to Excel using create_excel_data.py → data/investment_data.xlsx

from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple

# Base timestamp for consistent relative dates
NOW = datetime.utcnow()

# Edge records: (source, target, edge_type, confidence, days_ago, is_contrarian)
EDGE_RECORDS: List[Tuple[str, str, str, float, int, bool]] = [
    ("NVDA", "TSMC", "depends_on", 0.90, 1, False),
    ("TSMC", "China", "manufactures_in", 0.75, 2, False),
    ("China", "Export Controls", "imposes", 0.80, 1, False),
    ("Export Controls", "Advanced Chips", "targets", 0.78, 3, False),
    ("Advanced Chips", "Data Center Revenue", "drives", 0.72, 7, False),
    ("Data Center Revenue", "NVDA", "linked_to", 0.70, 10, False),
    ("NVDA", "OEMs", "sells_to", 0.65, 14, True),
    ("OEMs", "Chinese Consumers", "serves", 0.60, 21, True),
    ("Chinese Consumers", "Spending Slowdown", "affected_by", 0.82, 2, False),
    ("Spending Slowdown", "NVDA", "pressures", 0.80, 1, False),
]

# Comprehensive ticker bundle with detailed metadata
TICKER_BUNDLE: Dict[str, Dict[str, Any]] = {
    "NVDA": {
        "meta": {"name": "NVIDIA", "sector": "Semis"},
        "priority": 92, 
        "recency_hours": 6, 
        "confidence": 0.91,
        "next_catalyst": {"type": "Earnings", "date": "2025-08-21"},
        "tldr": "Mgmt flagged China logistics; supplier TSMC constraints → AI infra risk.",
        "kpis": [
            {
                "name": "Data Center Revenue", 
                "last_seen": (NOW-timedelta(days=1)).date().isoformat(),
                "snippet": "Mgmt noted export logistics uncertainty around high-end GPUs.", 
                "evidence_count": 4
            },
            {
                "name": "Lead times", 
                "last_seen": (NOW-timedelta(days=5)).date().isoformat(),
                "snippet": "Lead times stabilizing; mix shift to H200 in H2.", 
                "evidence_count": 3
            },
        ],
        "themes": [
            {
                "name": "China Risk", 
                "confidence": 0.87, 
                "last_seen": (NOW-timedelta(hours=6)).date().isoformat()
            },
            {
                "name": "AI Infrastructure", 
                "confidence": 0.80, 
                "last_seen": (NOW-timedelta(days=2)).date().isoformat()
            },
            {
                "name": "Supply Chain", 
                "confidence": 0.76, 
                "last_seen": (NOW-timedelta(days=1)).date().isoformat()
            },
        ],
        "soft_signals": [
            {
                "date": (NOW-timedelta(hours=6)).date().isoformat(), 
                "polarity": "neg",
                "text": "Cautious on Asia ops; export permits under review.", 
                "source_id": "doc123"
            },
            {
                "date": (NOW-timedelta(days=2)).date().isoformat(), 
                "polarity": "uncertain",
                "text": "OEM reorder cadence softening in China region.", 
                "source_id": "doc456"
            },
        ],
        "paths_ranked": [{
            "path_id": "p001",
            "path_str": "NVDA → depends_on → TSMC → exposed_to → China Risk",
            "hop_count": 3, 
            "path_score": 0.92, 
            "confidence": 0.88,
            "last_seen": (NOW-timedelta(hours=6)).isoformat(),
            "hops": [
                {
                    "edge_type": "depends_on", 
                    "target": "TSMC", 
                    "confidence": 0.90,
                    "last_seen": (NOW-timedelta(days=1)).isoformat(), 
                    "evidence_count": 3
                },
                {
                    "edge_type": "exposed_to", 
                    "target": "China Risk", 
                    "confidence": 0.84,
                    "last_seen": (NOW-timedelta(hours=6)).isoformat(), 
                    "evidence_count": 3
                },
            ],
            "claims": [
                {
                    "id": "c001", 
                    "date": (NOW-timedelta(hours=6)).date().isoformat(),
                    "text": "Mgmt warned on export logistics", 
                    "source_id": "doc123"
                },
                {
                    "id": "c002", 
                    "date": (NOW-timedelta(days=1)).date().isoformat(),
                    "text": "TSMC noted capacity constraints", 
                    "source_id": "doc456"
                },
            ],
            "sources": ["doc123", "doc456", "doc789"],
        }],
        "diff_since_prev": {
            "new_claims": ["c001"],
            "new_edges": [{"edge_type": "exposed_to", "target": "China Risk"}],
            "confidence_delta": +0.06
        },
        "sources_ranked": [
            {
                "doc_id": "doc123", 
                "title": "Q2 call transcript", 
                "type": "transcript",
                "date": (NOW-timedelta(hours=6)).date().isoformat(), 
                "snippet": "...export logistics..."
            },
            {
                "doc_id": "doc456", 
                "title": "Supplier note", 
                "type": "broker_note",
                "date": (NOW-timedelta(days=1)).date().isoformat(), 
                "snippet": "...capacity constraints..."
            },
            {
                "doc_id": "doc789", 
                "title": "Reuters: export curbs", 
                "type": "news",
                "date": (NOW-timedelta(days=3)).date().isoformat(), 
                "snippet": "...curbs on advanced chips..."
            },
        ],
    }
}

# Portfolio holdings data
PORTFOLIO_ROWS: List[Dict[str, Any]] = [
    {
        "Ticker": "NVDA", 
        "Name": "Nvidia", 
        "Sector": "Semis", 
        "Alert Priority": 92,
        "What Changed": "Export curbs expanded → DC GPU slowdown (cited)",
        "Top Causal Path": "NVDA → TSMC → China Risk (3 src)",
        "Themes": "AI infra • .8 • 2d | China policy • .6 • 1d",
        "KPIs": "Datacenter Rev • 1d | Lead times • 5d",
        "Soft Signal": "⚠️ mgmt cautious on China", 
        "Recency": "6h", 
        "Confidence": "0.91 (3 src)"
    },
    {
        "Ticker": "AAPL", 
        "Name": "Apple", 
        "Sector": "Consumer Tech", 
        "Alert Priority": 76,
        "What Changed": "iPhone SE delays → Q3 topline risk (cited)",
        "Top Causal Path": "AAPL → Foxconn → China lockdown (2 src)",
        "Themes": "Consumer sentiment • .7 • 3d", 
        "KPIs": "Unit sales • 2d",
        "Soft Signal": "⚠️ weak Asia demand flagged", 
        "Recency": "18h", 
        "Confidence": "0.82 (2 src)"
    },
    {
        "Ticker": "MSFT", 
        "Name": "Microsoft", 
        "Sector": "Software", 
        "Alert Priority": 73,
        "What Changed": "Azure bookings downshift → Cloud growth risk",
        "Top Causal Path": "MSFT → Azure → CapEx Pullback (2 src)",
        "Themes": "Cloud slowdown • .6 • 2d", 
        "KPIs": "Azure NRR • 1d",
        "Soft Signal": "⚠️ hiring freeze in cloud ops", 
        "Recency": "12h", 
        "Confidence": "0.79 (2 src)"
    },
    {
        "Ticker": "AMZN", 
        "Name": "Amazon", 
        "Sector": "E-commerce", 
        "Alert Priority": 68,
        "What Changed": "Prime sign-ups lag seasonal norm → Demand drag",
        "Top Causal Path": "AMZN → Consumer Spend → Macro Weakness (2 src)",
        "Themes": "US consumer • .5 • 4d", 
        "KPIs": "Prime subs • 2d",
        "Soft Signal": "⚠️ CSAT complaints trending up", 
        "Recency": "2d", 
        "Confidence": "0.76 (2 src)"
    },
    {
        "Ticker": "GOOGL", 
        "Name": "Alphabet", 
        "Sector": "Digital Ads", 
        "Alert Priority": 70,
        "What Changed": "Ad budgets trimmed → Rev softness",
        "Top Causal Path": "GOOGL → SMB Ad Spend → Macro Risk (2 src)",
        "Themes": "Ad slowdown • .6 • 3d", 
        "KPIs": "Ad RPM • 1d",
        "Soft Signal": "⚠️ internal memo on cost cuts", 
        "Recency": "1d", 
        "Confidence": "0.78 (2 src)"
    }
]

# Watchlist tracking data
WATCHLIST_ROWS: List[Dict[str, Any]] = [
    {
        "Ticker": "COIN", 
        "Name": "Coinbase", 
        "Sector": "Crypto", 
        "Alert Priority": 81,
        "What Changed": "SEC lawsuit update → fee model risk (cited)",
        "Top Causal Path": "COIN → SEC Action → Fee Revenue (2 src)",
        "Themes": "Regulatory • .7 • 1d", 
        "KPIs": "Volume • 2d",
        "Soft Signal": "⚠️ legal risk in internal memo", 
        "Recency": "14h", 
        "Confidence": "0.85 (2 src)"
    },
    {
        "Ticker": "TSLA", 
        "Name": "Tesla", 
        "Sector": "Auto", 
        "Alert Priority": 78,
        "What Changed": "Recall filing → Delivery disruption risk",
        "Top Causal Path": "TSLA → Recall → Q3 ASP (3 src)",
        "Themes": "EV demand • .6 • 2d", 
        "KPIs": "Deliveries • 1d",
        "Soft Signal": "⚠️ social sentiment down", 
        "Recency": "8h", 
        "Confidence": "0.83 (3 src)"
    },
    {
        "Ticker": "BABA", 
        "Name": "Alibaba", 
        "Sector": "China E-com", 
        "Alert Priority": 85,
        "What Changed": "New export regs → Logistics bottleneck",
        "Top Causal Path": "BABA → CN Exports → Revenue Risk (4 src)",
        "Themes": "China macro • .9 • 1d", 
        "KPIs": "GMV • 1d",
        "Soft Signal": "⚠️ mgmt guided lower", 
        "Recency": "6h", 
        "Confidence": "0.90 (4 src)"
    },
    {
        "Ticker": "SNOW", 
        "Name": "Snowflake", 
        "Sector": "SaaS", 
        "Alert Priority": 67,
        "What Changed": "Consumption softness → FY guide at risk",
        "Top Causal Path": "SNOW → Cloud budgets → Usage (2 src)",
        "Themes": "Cloud slowdown • .6 • 2d", 
        "KPIs": "DBNRR • 3d",
        "Soft Signal": "⚠️ layoffs rumor", 
        "Recency": "20h", 
        "Confidence": "0.75 (2 src)"
    }
]


def get_all_sample_data() -> Dict[str, Any]:
    """
    Get all sample data in a single dictionary for easy access.
    
    Returns:
        Dictionary containing all sample data structures
    """
    return {
        'edge_records': EDGE_RECORDS,
        'ticker_bundle': TICKER_BUNDLE,
        'portfolio_rows': PORTFOLIO_ROWS,
        'watchlist_rows': WATCHLIST_ROWS,
        'timestamp': NOW
    }


def validate_data_integrity() -> Dict[str, bool]:
    """
    Validate the integrity of all sample data structures.
    
    Returns:
        Dictionary with validation results for each data structure
    """
    results = {}
    
    # Validate edge records
    try:
        assert len(EDGE_RECORDS) > 0, "EDGE_RECORDS should not be empty"
        for edge in EDGE_RECORDS:
            assert len(edge) == 6, f"Edge should have 6 elements: {edge}"
            assert isinstance(edge[3], float) and 0 <= edge[3] <= 1, f"Confidence should be 0-1: {edge[3]}"
        results['edge_records'] = True
    except Exception as e:
        results['edge_records'] = False
        print(f"Edge records validation failed: {e}")
    
    # Validate ticker bundle
    try:
        assert len(TICKER_BUNDLE) > 0, "TICKER_BUNDLE should not be empty"
        for ticker, data in TICKER_BUNDLE.items():
            assert 'meta' in data, f"Missing meta for {ticker}"
            assert 'priority' in data, f"Missing priority for {ticker}"
            assert 'confidence' in data, f"Missing confidence for {ticker}"
        results['ticker_bundle'] = True
    except Exception as e:
        results['ticker_bundle'] = False
        print(f"Ticker bundle validation failed: {e}")
    
    # Validate portfolio rows
    try:
        assert len(PORTFOLIO_ROWS) > 0, "PORTFOLIO_ROWS should not be empty"
        required_cols = ['Ticker', 'Name', 'Sector', 'Alert Priority']
        for row in PORTFOLIO_ROWS:
            for col in required_cols:
                assert col in row, f"Missing column {col} in portfolio row"
        results['portfolio_rows'] = True
    except Exception as e:
        results['portfolio_rows'] = False
        print(f"Portfolio rows validation failed: {e}")
    
    # Validate watchlist rows
    try:
        assert len(WATCHLIST_ROWS) > 0, "WATCHLIST_ROWS should not be empty"
        required_cols = ['Ticker', 'Name', 'Sector', 'Alert Priority']
        for row in WATCHLIST_ROWS:
            for col in required_cols:
                assert col in row, f"Missing column {col} in watchlist row"
        results['watchlist_rows'] = True
    except Exception as e:
        results['watchlist_rows'] = False
        print(f"Watchlist rows validation failed: {e}")
    
    return results


# Run validation on import
if __name__ == "__main__":
    print("Sample data validation:")
    results = validate_data_integrity()
    for key, valid in results.items():
        status = "✅" if valid else "❌"
        print(f"{status} {key}: {'Valid' if valid else 'Invalid'}")
    
    print(f"\nData summary:")
    print(f"- Edge records: {len(EDGE_RECORDS)}")
    print(f"- Ticker bundles: {len(TICKER_BUNDLE)}")
    print(f"- Portfolio rows: {len(PORTFOLIO_ROWS)}")
    print(f"- Watchlist rows: {len(WATCHLIST_ROWS)}")
else:
    # Silent validation on import
    validate_data_integrity()