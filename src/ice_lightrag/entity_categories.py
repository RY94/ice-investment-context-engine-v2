# Location: /src/ice_lightrag/entity_categories.py
# Purpose: Entity categorization patterns for ICE knowledge graph analysis
# Used by: graph_categorization.py, ice_building_workflow.ipynb Cell 10
# Last Updated: 2025-10-11

"""
Entity Categorization Patterns for ICE Investment Intelligence

This module defines pattern-based rules for categorizing entities extracted
from financial documents and stored in the LightRAG knowledge graph.

Categories are matched against entity names using keyword patterns.
The first matching category is assigned (order matters - specific to general).

Based on analysis of real ICE graph data:
- 165 entities analyzed
- 9 distinct categories identified
- Patterns validated against semiconductor portfolio (NVDA, TSMC, AMD, ASML)
"""

from typing import Dict, List

# Entity categorization patterns (checked in priority order)
ENTITY_PATTERNS: Dict[str, Dict[str, any]] = {

    # CATEGORY 1: Industry/Sector (Most Specific - Check First)
    'Industry/Sector': {
        'description': 'Industry and sector classifications (e.g., SECTOR: TECHNOLOGY, Industry: SEMICONDUCTORS)',
        'patterns': [
            'SECTOR:',
            'INDUSTRY:',
            'SECTOR ',
            'INDUSTRY '
        ],
        'examples': [
            'SECTOR: TECHNOLOGY',
            'Industry: SEMICONDUCTORS'
        ],
        'priority': 1  # Highest priority - most specific
    },

    # CATEGORY 2: Company
    'Company': {
        'description': 'Publicly traded companies and corporations',
        'patterns': [
            # Portfolio tickers
            'NVDA',
            'NVIDIA',
            'TSMC',
            'AMD',
            'ASML',
            # Corporate suffixes
            'CORPORATION',
            'INC',
            'LTD',
            'LIMITED',
            'GROUP',
            'COMPANY',
            'CORP'
        ],
        'examples': [
            'NVIDIA Corporation',
            'Taiwan Semiconductor Manufacturing Company',
            'Advanced Micro Devices Inc',
            'ASML Holding'
        ],
        'priority': 2
    },

    # CATEGORY 3: Financial Metric
    'Financial Metric': {
        'description': 'Financial metrics, KPIs, and performance indicators',
        'patterns': [
            # Ratios and multiples
            'RATIO',
            'PE ',
            'P/E',
            'EPS',
            'ROE',
            'ROI',
            # Market metrics
            'MARKET CAP',
            'MARKET VALUE',
            'REVENUE',
            'EARNINGS',
            'PROFIT',
            'MARGIN',
            # Stock metrics
            'MOVING AVERAGE',
            'WEEK HIGH',
            'WEEK LOW',
            'DAY HIGH',
            'DAY LOW',
            'PRICE TARGET',
            'SHARE PRICE',
            'STOCK PRICE',
            # Volume and trading
            'VOLUME',
            'SHARES OUTSTANDING',
            'FLOAT',
            # Valuation
            'VALUATION',
            'ENTERPRISE VALUE',
            'BOOK VALUE'
        ],
        'examples': [
            'Market Capitalization',
            'PE Ratio',
            'Revenue Per Share',
            '52 Week High',
            '200 Day Moving Average'
        ],
        'priority': 3
    },

    # CATEGORY 4: Technology/Product
    'Technology/Product': {
        'description': 'Technologies, products, and technical solutions',
        'patterns': [
            # Hardware
            'GPU',
            'CHIP',
            'PROCESSOR',
            'SEMICONDUCTOR',
            'SOC',
            'SYSTEM ON',
            # Brand names and product lines (avoid duplicates with Company category)
            'INTEL',       # Intel products (company name in Company category)
            'QUALCOMM',    # Qualcomm products (company name may be in Company category)
            'CORE',        # Intel Core i3/i5/i7/i9/Ultra
            'RYZEN',       # AMD Ryzen (AMD itself in Company category)
            'SNAPDRAGON',  # Qualcomm Snapdragon
            'ULTRA',       # Intel Core Ultra, AMD Ultra
            # Software/AI
            'AI ',
            'ARTIFICIAL INTELLIGENCE',
            'MACHINE LEARNING',
            'TECHNOLOGY',
            'SOFTWARE',
            # Products
            'PRODUCT',
            'SOLUTION',
            'PLATFORM',
            'ARCHITECTURE'
        ],
        'examples': [
            'Graphics Processing Units (GPUs)',
            'AI Technologies',
            'System on a Chip (SoC)',
            'Intel Core Ultra',
            'AMD Ryzen'
        ],
        'priority': 4
    },

    # CATEGORY 5: Market Infrastructure
    'Market Infrastructure': {
        'description': 'Stock exchanges, currencies, and market systems',
        'patterns': [
            # Exchanges
            'NASDAQ',
            'NYSE',
            'EXCHANGE',
            'STOCK MARKET',
            # Currencies
            'USD',
            'EUR',
            'CNY',
            'DOLLAR',
            'CURRENCY',
            # Market systems
            'INDEX',
            'COMPOSITE'
        ],
        'examples': [
            'NASDAQ',
            'USD',
            'New York Stock Exchange'
        ],
        'priority': 5
    },

    # CATEGORY 6: Geographic
    'Geographic': {
        'description': 'Countries, states, cities, and geographic locations',
        'patterns': [
            # Countries
            'CHINA',
            'TAIWAN',
            'NETHERLANDS',
            'UNITED STATES',
            'USA',
            'AMERICA',
            # States
            'CALIFORNIA',
            'TEXAS',
            'NEW YORK',
            # Cities
            'SANTA CLARA',
            'SAN JOSE',
            'SILICON VALLEY',
            'BEIJING',
            'TAIPEI'
        ],
        'examples': [
            'Santa Clara',
            'California',
            'China'
        ],
        'priority': 6
    },

    # CATEGORY 7: Regulation/Event
    'Regulation/Event': {
        'description': 'Regulatory actions, policies, and market events',
        'patterns': [
            'BAN',
            'REGULATION',
            'POLICY',
            'LAW',
            'COMPLIANCE',
            'RESTRICTION',
            'SANCTION',
            'EVENT',
            'RULING',
            'DECREE'
        ],
        'examples': [
            'Nvidia Ban',
            'Trade Restrictions',
            'Export Controls'
        ],
        'priority': 7
    },

    # CATEGORY 8: Media/Source
    'Media/Source': {
        'description': 'News sources, publications, and media outlets',
        'patterns': [
            'TIMES',
            'NEWS',
            'REPORT',
            'JOURNAL',
            'POST',
            'PRESS',
            'MEDIA',
            'PUBLICATION',
            'ENTERTAINMENT',
            'BLOOMBERG',
            'REUTERS',
            'FINANCIAL TIMES'
        ],
        'examples': [
            'Financial Times',
            'Yahoo Entertainment',
            'Bloomberg News'
        ],
        'priority': 8
    },

    # CATEGORY 9: Other (Fallback)
    'Other': {
        'description': 'Uncategorized entities (fallback category)',
        'patterns': [],  # Empty - catches everything not matched above
        'examples': [
            'Various entities not fitting specific categories'
        ],
        'priority': 9  # Lowest priority - fallback
    }
}

# Category display order (for reports and dashboards)
CATEGORY_DISPLAY_ORDER = [
    'Company',
    'Financial Metric',
    'Technology/Product',
    'Geographic',
    'Industry/Sector',
    'Market Infrastructure',
    'Regulation/Event',
    'Media/Source',
    'Other'
]
