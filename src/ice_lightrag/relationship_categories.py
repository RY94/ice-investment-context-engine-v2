# Location: /src/ice_lightrag/relationship_categories.py
# Purpose: Relationship categorization patterns for ICE knowledge graph analysis
# Used by: graph_categorization.py, ice_building_workflow.ipynb Cell 10
# Last Updated: 2025-10-11

"""
Relationship Categorization Patterns for ICE Investment Intelligence

This module defines pattern-based rules for categorizing relationships between
entities in the LightRAG knowledge graph.

Relationships are categorized based on the relationship type field extracted
from LightRAG's content format:
```
src_id\ttgt_id
relationship_type1,relationship_type2
Description...
```

The second line contains comma-separated relationship types which are matched
against these patterns. First matching category is assigned (order matters).

Based on analysis of real ICE graph data:
- 139 relationships analyzed
- 10 distinct categories identified
- Validated against semiconductor portfolio relationships
"""

from typing import Dict, List

# Relationship categorization patterns (checked in priority order)
RELATIONSHIP_PATTERNS: Dict[str, Dict[str, any]] = {

    # CATEGORY 1: Financial (Most Common ~29%)
    'Financial': {
        'description': 'Financial performance, valuation, and stock metrics',
        'patterns': [
            'financial',
            'valuation',
            'metric',
            'stock performance',
            'stock trend',
            'performance',
            'market reaction',
            'price',
            'earnings',
            'revenue',
            'profit'
        ],
        'examples': [
            'financial performance → valuation',
            'financial metric → stock performance',
            'market reaction → stock performance'
        ],
        'priority': 1,
        'typical_percentage': 29
    },

    # CATEGORY 2: Regulatory (Specific and Important)
    'Regulatory': {
        'description': 'Regulatory actions, compliance, and policy impacts',
        'patterns': [
            'regulatory',
            'regulation',
            'compliance',
            'ban',
            'policy',
            'restriction',
            'sanction',
            'legal',
            'law'
        ],
        'examples': [
            'regulatory action → trade relations',
            'ban → compliance requirement'
        ],
        'priority': 2,
        'typical_percentage': 5
    },

    # CATEGORY 3: Supply Chain
    'Supply Chain': {
        'description': 'Manufacturing, supplier, and dependency relationships',
        'patterns': [
            'supplier',
            'manufacturing',
            'dependency',
            'supply',
            'production',
            'sourcing',
            'vendor',
            'procurement'
        ],
        'examples': [
            'manufacturing → dependency',
            'supplier relationship → sourcing'
        ],
        'priority': 3,
        'typical_percentage': 8
    },

    # CATEGORY 4: Product/Tech (~18%)
    'Product/Tech': {
        'description': 'Product development, technology innovation, and R&D',
        'patterns': [
            'product',
            'technology',
            'development',
            'innovation',
            'specialization',
            'research',
            'design',
            'engineering',
            'technical'
        ],
        'examples': [
            'product development → technology specialization',
            'technology innovation → R&D focus'
        ],
        'priority': 4,
        'typical_percentage': 18
    },

    # CATEGORY 5: Corporate (~11%)
    'Corporate': {
        'description': 'Corporate structure, ownership, and organizational relationships',
        'patterns': [
            'headquarters',
            'location',
            'ownership',
            'subsidiary',
            'parent company',
            'organizational',
            'corporate structure',
            'branch',
            'office'
        ],
        'examples': [
            'headquarters → location',
            'ownership → corporate structure'
        ],
        'priority': 5,
        'typical_percentage': 11
    },

    # CATEGORY 6: Industry (~10%)
    'Industry': {
        'description': 'Industry classification, sector focus, and business categorization',
        'patterns': [
            'industry',
            'sector',
            'classification',
            'business focus',
            'market segment',
            'vertical',
            'specialization'
        ],
        'examples': [
            'industry classification → product specialization',
            'business focus → sector impact'
        ],
        'priority': 6,
        'typical_percentage': 10
    },

    # CATEGORY 7: Market (~8%)
    'Market': {
        'description': 'Trading, currency, and market operations',
        'patterns': [
            'trading',
            'stock market',
            'public company',
            'exchange',
            'currency',
            'market',
            'listed',
            'ticker'
        ],
        'examples': [
            'public company → stock trading',
            'currency → financial reporting'
        ],
        'priority': 7,
        'typical_percentage': 8
    },

    # CATEGORY 8: Impact/Correlation (~7%)
    'Impact/Correlation': {
        'description': 'Causal relationships, impacts, and correlations',
        'patterns': [
            'impact',
            'affect',
            'influence',
            'correlation',
            'effect',
            'consequence',
            'result',
            'causation',
            'dependency'
        ],
        'examples': [
            'sector impact → technology development',
            'impact on industry → trade talks'
        ],
        'priority': 8,
        'typical_percentage': 7
    },

    # CATEGORY 9: Media/Analysis (~8%)
    'Media/Analysis': {
        'description': 'News reporting, media coverage, and analyst commentary',
        'patterns': [
            'reporting',
            'media',
            'analysis',
            'news',
            'publication',
            'coverage',
            'analyst',
            'commentary',
            'dissemination',
            'source'
        ],
        'examples': [
            'analysis → media reporting',
            'news dissemination → source of reporting'
        ],
        'priority': 9,
        'typical_percentage': 8
    },

    # CATEGORY 10: Other (Fallback ~6%)
    'Other': {
        'description': 'Uncategorized relationships (fallback category)',
        'patterns': [],  # Empty - catches everything not matched above
        'examples': [
            'Various relationships not fitting specific categories'
        ],
        'priority': 10,  # Lowest priority - fallback
        'typical_percentage': 6
    }
}

# Category display order (for reports and dashboards)
CATEGORY_DISPLAY_ORDER = [
    'Financial',
    'Product/Tech',
    'Corporate',
    'Industry',
    'Supply Chain',
    'Market',
    'Impact/Correlation',
    'Regulatory',
    'Media/Analysis',
    'Other'
]

# Relationship extraction helper
def extract_relationship_types(relationship_content: str) -> str:
    """
    Extract relationship types from LightRAG relationship content.

    LightRAG stores relationships in format:
    Line 1: src_id\\ttgt_id
    Line 2: relationship_type1,relationship_type2,...
    Line 3+: Description text

    Args:
        relationship_content: Full relationship content from LightRAG

    Returns:
        Comma-separated relationship types from line 2, or empty string
    """
    lines = relationship_content.split('\n')
    if len(lines) >= 2:
        return lines[1].strip().lower()
    return ''
