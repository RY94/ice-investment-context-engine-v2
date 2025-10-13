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

# Month names for date entity detection
MONTH_NAMES = ['JANUARY', 'FEBRUARY', 'MARCH', 'APRIL', 'MAY', 'JUNE',
               'JULY', 'AUGUST', 'SEPTEMBER', 'OCTOBER', 'NOVEMBER', 'DECEMBER']


def _is_date_entity(entity_name: str) -> bool:
    """
    Check if entity name is a date using word boundary detection + digit requirement.

    A true date has BOTH:
    1. A complete month word (not substring)
    2. At least one digit (day/year)

    This avoids false positives:
    - "MAYBANK CORPORATION" (contains "MAY" substring → NO match, word boundary)
    - "APRIL TECHNOLOGIES" (contains "APRIL" word but no digit → NO match)
    - "October 2, 2025" (contains "OCTOBER" word + digits → MATCH)

    Args:
        entity_name: Name of the entity to check

    Returns:
        True if entity is a date (month word + digit), False otherwise
    """
    import re
    # Split on non-alphanumeric characters to get words
    words = set(re.split(r'[^A-Z]+', entity_name.upper()))
    has_month = any(month in words for month in MONTH_NAMES)
    has_digit = any(char.isdigit() for char in entity_name)
    return has_month and has_digit


def categorize_entity(entity_name: str, entity_content: str = '') -> str:
    """
    Categorize a single entity based on two-phase pattern matching.

    Two-Phase Matching Strategy:
    - Phase 1: Match against entity_name only (high precision)
    - Phase 2: Match against entity_name + entity_content (broader context)

    This prevents content "noise" (company names, keywords in descriptions)
    from causing false positive matches in higher-priority categories.

    Patterns are checked in priority order (specific to general).
    First matching pattern determines the category.

    Args:
        entity_name: Name of the entity (e.g., "NVIDIA Corporation")
        entity_content: Optional content description for additional context

    Returns:
        Category name (e.g., "Company", "Financial Metric")
    """
    # Sort categories by priority once
    sorted_categories = sorted(
        ENTITY_PATTERNS.items(),
        key=lambda x: x[1].get('priority', 999)
    )

    # PHASE 1: Check entity_name ONLY (high precision)
    name_upper = entity_name.upper()

    # Early return for date entities (temporal metadata, not investment entities)
    if _is_date_entity(entity_name):
        return 'Other'

    for category_name, category_info in sorted_categories:
        patterns = category_info.get('patterns', [])

        # Skip fallback category in Phase 1
        if not patterns:
            continue

        # Check if any pattern matches the entity name
        for pattern in patterns:
            if pattern.upper() in name_upper:
                return category_name

    # PHASE 2: Check entity_name + entity_content (fallback for ambiguous cases)
    text = f"{entity_name} {entity_content}".upper()
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
    Categorize entity with confidence score using two-phase pattern matching.

    Two-Phase Matching Strategy:
    - Phase 1: Match against entity_name only (high precision, high confidence)
    - Phase 2: Match against entity_name + entity_content (broader context, lower confidence)

    This prevents content "noise" from causing false positive matches.

    Confidence scoring:
    - Phase 1 matches (entity_name only - high precision):
      - 0.95: Priority 1-2 (Industry/Sector, Company) - highly specific patterns
      - 0.85: Priority 3-4 (Financial Metric, Technology/Product) - clear patterns
      - 0.75: Priority 5-7 (Market Infrastructure, Geographic, Regulation) - moderate patterns
      - 0.60: Priority 8-9 (Media/Source, Other) - weak or fallback patterns
    - Phase 2 matches (entity_name + entity_content - lower precision, fallback):
      - 0.85: Priority 1-2 (reduced by 0.10 due to content noise)
      - 0.75: Priority 3-4 (reduced by 0.10 due to content noise)
      - 0.65: Priority 5-7 (reduced by 0.10 due to content noise)
      - 0.50: Priority 8-9 (reduced by 0.10 due to content noise)

    Args:
        entity_name: Name of the entity
        entity_content: Optional content description

    Returns:
        Tuple of (category_name, confidence_score)
    """
    sorted_categories = sorted(ENTITY_PATTERNS.items(), key=lambda x: x[1].get('priority', 999))

    # PHASE 1: Check entity_name ONLY (high precision)
    name_upper = entity_name.upper()

    # Early return for date entities (temporal metadata, not investment entities)
    if _is_date_entity(entity_name):
        return ('Other', 0.50)

    for category_name, category_info in sorted_categories:
        patterns = category_info.get('patterns', [])
        priority = category_info.get('priority', 999)

        # Skip fallback category in Phase 1
        if not patterns:
            continue

        for pattern in patterns:
            if pattern.upper() in name_upper:
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

    # PHASE 2: Check entity_name + entity_content (fallback for ambiguous cases)
    text = f"{entity_name} {entity_content}".upper()
    for category_name, category_info in sorted_categories:
        patterns = category_info.get('patterns', [])
        priority = category_info.get('priority', 999)

        if not patterns:  # Fallback category (Other)
            return (category_name, 0.50)

        for pattern in patterns:
            if pattern.upper() in text:
                # Phase 2 confidence: Lower than Phase 1 (reduced by 0.10 due to content noise)
                if priority <= 2:
                    confidence = 0.85  # was 0.95
                elif priority <= 4:
                    confidence = 0.75  # was 0.85
                elif priority <= 7:
                    confidence = 0.65  # was 0.75
                else:
                    confidence = 0.50  # was 0.60
                return (category_name, confidence)

    return ('Other', 0.50)


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

    # Step 3: Low confidence - use LLM with full context
    try:
        # Include ALL 9 categories (including 'Other') for LLM fallback
        # so it can legitimately choose 'Other' for non-investment entities
        category_list = ', '.join(ENTITY_DISPLAY_ORDER)

        # Include entity_content if available to give LLM more context
        if entity_content:
            prompt = (
                f"Categorize this entity into ONE category.\n"
                f"Entity: {entity_name}\n"
                f"Context: {entity_content}\n"
                f"Categories: {category_list}\n"
                f"Note: 'Other' is for non-investment entities (dates, events, generic terms).\n"
                f"Answer with ONLY the category name, nothing else."
            )
        else:
            prompt = (
                f"Categorize this entity into ONE category.\n"
                f"Entity: {entity_name}\n"
                f"Categories: {category_list}\n"
                f"Note: 'Other' is for non-investment entities (dates, events, generic terms).\n"
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


def categorize_entity_llm_only(
    entity_name: str,
    entity_content: str = '',
    model: str = OLLAMA_MODEL
) -> Tuple[str, float]:
    """
    Pure LLM categorization using local Ollama model (no preprocessing).

    Uses Ollama LLM for ALL entities with NO rule-based preprocessing.
    This includes dates, which other methods handle with _is_date_entity().

    Useful for benchmarking true LLM accuracy vs keyword/hybrid approaches.
    May categorize dates differently than keyword methods (by design).

    Args:
        entity_name: Name of the entity
        entity_content: Optional content description
        model: Ollama model to use (default: OLLAMA_MODEL constant)

    Returns:
        Tuple of (category_name, confidence_score)
        - Returns ('Other', 0.50) if LLM call fails or returns invalid category
        - Returns (category, 0.90) for successful LLM categorization
    """
    try:
        # Include ALL 9 categories (including 'Other') so LLM can legitimately
        # categorize non-investment entities like dates as 'Other'
        category_list = ', '.join(ENTITY_DISPLAY_ORDER)

        # Include entity_content if available for better LLM context
        if entity_content:
            prompt = (
                f"Categorize this entity into ONE category.\n"
                f"Entity: {entity_name}\n"
                f"Context: {entity_content}\n"
                f"Categories: {category_list}\n"
                f"Note: 'Other' is for non-investment entities (dates, events, generic terms).\n"
                f"Answer with ONLY the category name, nothing else."
            )
        else:
            prompt = (
                f"Categorize this entity into ONE category.\n"
                f"Entity: {entity_name}\n"
                f"Categories: {category_list}\n"
                f"Note: 'Other' is for non-investment entities (dates, events, generic terms).\n"
                f"Answer with ONLY the category name, nothing else."
            )

        llm_category = _call_ollama(prompt, model=model)

        # Validate LLM response is a known category
        if llm_category in ENTITY_DISPLAY_ORDER:
            return (llm_category, 0.90)  # High confidence for LLM results
        else:
            logger.warning(f"LLM returned invalid category '{llm_category}', returning 'Other'")
            return ('Other', 0.50)

    except Exception as e:
        logger.warning(f"Pure LLM categorization failed: {e}")
        return ('Other', 0.50)


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
