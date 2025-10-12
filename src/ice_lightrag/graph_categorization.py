# Location: /src/ice_lightrag/graph_categorization.py
# Purpose: Helper functions for categorizing ICE knowledge graph entities and relationships
# Used by: ice_building_workflow.ipynb Cell 10 (check_graph_health)
# Last Updated: 2025-10-11

"""
Graph Categorization Module for ICE Investment Intelligence

This module provides helper functions for categorizing entities and relationships
in the LightRAG knowledge graph using pattern-based matching.

Key Features:
- Pattern-based categorization (no LLM calls, fast and deterministic)
- Priority-ordered matching (specific patterns checked before general ones)
- Single-pass analysis for efficiency
- Category distribution statistics

Usage Example:
    from src.ice_lightrag.graph_categorization import categorize_entities, categorize_relationships

    # Categorize entities
    entity_stats = categorize_entities(entities_data)
    # Returns: {'Company': 15, 'Financial Metric': 45, ...}

    # Categorize relationships
    rel_stats = categorize_relationships(relationships_data)
    # Returns: {'Financial': 40, 'Product/Tech': 25, ...}
"""

from typing import Dict, List, Tuple
from collections import Counter
import requests
import json
import logging
from .entity_categories import ENTITY_PATTERNS, CATEGORY_DISPLAY_ORDER as ENTITY_DISPLAY_ORDER
from .relationship_categories import (
    RELATIONSHIP_PATTERNS,
    CATEGORY_DISPLAY_ORDER as REL_DISPLAY_ORDER,
    extract_relationship_types
)

logger = logging.getLogger(__name__)

# Configuration constants
CATEGORIZATION_MODE = 'keyword'  # 'keyword' | 'hybrid' | 'llm'
HYBRID_CONFIDENCE_THRESHOLD = 0.70  # Minimum confidence for keyword matching before LLM fallback
OLLAMA_MODEL = 'qwen2.5:3b'  # Ollama model for hybrid/llm modes
OLLAMA_HOST = 'http://localhost:11434'  # Ollama service URL


def categorize_entity(entity_name: str, entity_content: str = '') -> str:
    """
    Categorize a single entity based on pattern matching.

    Patterns are checked in priority order (specific to general).
    First matching pattern determines the category.

    Args:
        entity_name: Name of the entity (e.g., "NVIDIA Corporation")
        entity_content: Optional content description for additional context

    Returns:
        Category name (e.g., "Company", "Financial Metric")
    """
    # Combine name and content for pattern matching
    text = f"{entity_name} {entity_content}".upper()

    # Check patterns in priority order (sorted by priority field)
    sorted_categories = sorted(
        ENTITY_PATTERNS.items(),
        key=lambda x: x[1].get('priority', 999)
    )

    for category_name, category_info in sorted_categories:
        patterns = category_info.get('patterns', [])

        # Empty patterns = fallback category (Other)
        if not patterns:
            return category_name

        # Check if any pattern matches
        for pattern in patterns:
            if pattern.upper() in text:
                return category_name

    # Fallback if no patterns matched (shouldn't happen if 'Other' is defined)
    return 'Other'


def categorize_relationship(relationship_content: str) -> str:
    """
    Categorize a single relationship based on relationship type patterns.

    Extracts relationship types from LightRAG content format and matches
    against predefined patterns.

    LightRAG Format:
        Line 1: src_id\\ttgt_id
        Line 2: relationship_type1,relationship_type2  <-- Matched here
        Line 3+: Description

    Args:
        relationship_content: Full relationship content from LightRAG

    Returns:
        Category name (e.g., "Financial", "Product/Tech")
    """
    # Extract relationship types (comma-separated keywords on line 2)
    rel_types = extract_relationship_types(relationship_content)

    if not rel_types:
        return 'Other'

    # Check patterns in priority order
    sorted_categories = sorted(
        RELATIONSHIP_PATTERNS.items(),
        key=lambda x: x[1].get('priority', 999)
    )

    for category_name, category_info in sorted_categories:
        patterns = category_info.get('patterns', [])

        # Empty patterns = fallback category (Other)
        if not patterns:
            return category_name

        # Check if any pattern matches
        for pattern in patterns:
            if pattern.lower() in rel_types.lower():
                return category_name

    return 'Other'


def categorize_entity_with_confidence(entity_name: str, entity_content: str = '') -> Tuple[str, float]:
    """
    Categorize entity with confidence score based on pattern priority.

    Confidence scoring:
    - 0.95: Priority 1-2 (Industry/Sector, Company) - highly specific patterns
    - 0.85: Priority 3-4 (Financial Metric, Technology/Product) - clear patterns
    - 0.75: Priority 5-7 (Market Infrastructure, Geographic, Regulation) - moderate patterns
    - 0.60: Priority 8-9 (Media/Source, Other) - weak or fallback patterns

    Args:
        entity_name: Name of the entity
        entity_content: Optional content description

    Returns:
        Tuple of (category_name, confidence_score)
    """
    text = f"{entity_name} {entity_content}".upper()
    sorted_categories = sorted(ENTITY_PATTERNS.items(), key=lambda x: x[1].get('priority', 999))

    for category_name, category_info in sorted_categories:
        patterns = category_info.get('patterns', [])
        priority = category_info.get('priority', 999)

        if not patterns:  # Fallback category (Other)
            return (category_name, 0.60)

        for pattern in patterns:
            if pattern.upper() in text:
                # Confidence based on priority level
                if priority <= 2:
                    confidence = 0.95
                elif priority <= 4:
                    confidence = 0.85
                elif priority <= 7:
                    confidence = 0.75
                else:
                    confidence = 0.60
                return (category_name, confidence)

    return ('Other', 0.60)


def _call_ollama(prompt: str, model: str = "qwen2.5:3b", host: str = "http://localhost:11434") -> str:
    """
    Direct Ollama API call for categorization (lightweight, no ModelProvider dependency).

    Args:
        prompt: Categorization prompt
        model: Ollama model name (default: qwen2.5:3b)
        host: Ollama service URL

    Returns:
        Model response text (category name)

    Raises:
        RuntimeError: If Ollama call fails
    """
    try:
        response = requests.post(
            f"{host}/api/generate",
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=10
        )
        response.raise_for_status()
        return response.json()["response"].strip()
    except Exception as e:
        logger.error(f"Ollama call failed: {e}")
        raise RuntimeError(f"Ollama categorization failed: {e}")


def categorize_entity_hybrid(
    entity_name: str,
    entity_content: str = '',
    confidence_threshold: float = 0.70,
    use_llm: bool = True
) -> Tuple[str, float]:
    """
    Hybrid categorization: keyword matching with LLM fallback for ambiguous cases.

    Pipeline:
    1. Try keyword matching first
    2. If confidence < threshold, use Ollama for better accuracy
    3. Return (category, confidence)

    Args:
        entity_name: Name of the entity
        entity_content: Optional content description
        confidence_threshold: Minimum confidence for keyword match (default: 0.70)
        use_llm: Enable LLM fallback (default: True)

    Returns:
        Tuple of (category_name, confidence_score)
    """
    # Step 1: Try keyword matching
    category, confidence = categorize_entity_with_confidence(entity_name, entity_content)

    # Step 2: If high confidence or LLM disabled, return keyword result
    if confidence >= confidence_threshold or not use_llm:
        return (category, confidence)

    # Step 3: Low confidence - use LLM
    try:
        category_list = ', '.join([c for c in ENTITY_DISPLAY_ORDER if c != 'Other'])
        prompt = (
            f"Categorize this financial entity into ONE category.\n"
            f"Entity: {entity_name}\n"
            f"Categories: {category_list}\n"
            f"Answer with ONLY the category name, nothing else."
        )
        llm_category = _call_ollama(prompt)

        # Validate LLM response is a known category
        if llm_category in ENTITY_DISPLAY_ORDER:
            return (llm_category, 0.90)  # High confidence for LLM results
        else:
            logger.warning(f"LLM returned invalid category '{llm_category}', using keyword result")
            return (category, confidence)

    except Exception as e:
        logger.warning(f"LLM fallback failed, using keyword result: {e}")
        return (category, confidence)


def categorize_entities(entities_data: List[Dict]) -> Dict[str, int]:
    """
    Categorize multiple entities and return category distribution.

    Args:
        entities_data: List of entity dicts with 'entity_name' and 'content' fields

    Returns:
        Dictionary mapping category names to counts
        Example: {'Company': 15, 'Financial Metric': 45, ...}
    """
    categories = []

    for entity in entities_data:
        name = entity.get('entity_name', '')
        content = entity.get('content', '')
        category = categorize_entity(name, content)
        categories.append(category)

    # Count occurrences
    category_counts = Counter(categories)

    # Return in display order with zero counts for missing categories
    result = {}
    for category in ENTITY_DISPLAY_ORDER:
        result[category] = category_counts.get(category, 0)

    return result


def categorize_relationships(relationships_data: List[Dict]) -> Dict[str, int]:
    """
    Categorize multiple relationships and return category distribution.

    Args:
        relationships_data: List of relationship dicts with 'content' field

    Returns:
        Dictionary mapping category names to counts
        Example: {'Financial': 40, 'Product/Tech': 25, ...}
    """
    categories = []

    for relationship in relationships_data:
        content = relationship.get('content', '')
        category = categorize_relationship(content)
        categories.append(category)

    # Count occurrences
    category_counts = Counter(categories)

    # Return in display order with zero counts for missing categories
    result = {}
    for category in REL_DISPLAY_ORDER:
        result[category] = category_counts.get(category, 0)

    return result


def get_top_categories(
    category_counts: Dict[str, int],
    top_n: int = 5,
    min_count: int = 1
) -> List[Tuple[str, int, float]]:
    """
    Get top N categories by count with percentages.

    Args:
        category_counts: Dictionary of category counts from categorize_entities/relationships
        top_n: Number of top categories to return (default: 5)
        min_count: Minimum count to include (default: 1)

    Returns:
        List of tuples: [(category_name, count, percentage), ...]
        Sorted by count (descending)

    Example:
        >>> counts = {'Company': 15, 'Financial Metric': 45, 'Other': 105}
        >>> get_top_categories(counts, top_n=2)
        [('Other', 105, 63.6), ('Financial Metric', 45, 27.3)]
    """
    total = sum(category_counts.values())

    if total == 0:
        return []

    # Filter by min_count and calculate percentages
    results = []
    for category, count in category_counts.items():
        if count >= min_count:
            percentage = (count / total) * 100
            results.append((category, count, percentage))

    # Sort by count (descending) and take top N
    results.sort(key=lambda x: x[1], reverse=True)
    return results[:top_n]


def format_category_display(
    category_counts: Dict[str, int],
    total_count: int,
    top_n: int = 5
) -> str:
    """
    Format category distribution for display in notebook.

    Args:
        category_counts: Dictionary of category counts
        total_count: Total number of entities/relationships
        top_n: Number of top categories to show (default: 5)

    Returns:
        Formatted string for display

    Example Output:
        Financial Metrics: 45 (27.3%)
        Other: 43 (26.1%)
        Technology/Product: 20 (12.1%)
    """
    top_categories = get_top_categories(category_counts, top_n=top_n)

    lines = []
    for category, count, percentage in top_categories:
        lines.append(f"    {category}: {count} ({percentage:.1f}%)")

    return '\n'.join(lines)
