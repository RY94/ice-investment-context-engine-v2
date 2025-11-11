# Location: /src/ice_core/temporal_enhancer.py
# Purpose: Enhance entities and edges with comprehensive temporal metadata for trend analysis
# Why: Enables temporal queries, trend detection, and time-based filtering in the knowledge graph
# Relevant Files: graph_builder.py, ice_query_processor.py, ingestion_manifest.py

"""
Temporal Enhancement Module for ICE Knowledge Graph

Adds comprehensive temporal metadata to entities and edges:
- Valid time periods (valid_from/valid_to)
- Temporal relationships (precedes, follows, during)
- Freshness indicators
- Trend detection capabilities
- Quarter/year aggregation support
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional, Tuple
import re
from dateutil.parser import parse as parse_date
from dateutil.relativedelta import relativedelta

logger = logging.getLogger(__name__)


class TemporalEnhancer:
    """
    Add rich temporal metadata to graph entities and edges.

    Enables queries like:
    - "What was NVDA's margin in Q2 2024?"
    - "How has risk sentiment changed over time?"
    - "Show trend of analyst ratings for AMD"
    """

    def __init__(self):
        """Initialize temporal enhancer with configuration."""
        self.current_time = datetime.now(timezone.utc)

        # Freshness thresholds (in days)
        self.freshness_thresholds = {
            'very_fresh': 7,      # Less than 1 week old
            'fresh': 30,          # Less than 1 month old
            'moderate': 90,       # Less than 3 months old
            'stale': 365,         # Less than 1 year old
            'very_stale': None    # Older than 1 year
        }

        # Quarter definitions
        self.quarters = {
            'Q1': (1, 3),
            'Q2': (4, 6),
            'Q3': (7, 9),
            'Q4': (10, 12)
        }

    def enhance_entity(self, entity: Dict[str, Any],
                      source_date: Optional[datetime] = None,
                      context: Optional[str] = None) -> Dict[str, Any]:
        """
        Enhance entity with temporal metadata.

        Args:
            entity: Entity dict to enhance
            source_date: Date from source document
            context: Text context for extracting temporal references

        Returns:
            Enhanced entity with temporal metadata
        """
        try:
            # Initialize temporal metadata
            temporal_meta = {
                'valid_from': source_date.isoformat() if source_date else self.current_time.isoformat(),
                'valid_to': None,  # None means currently valid
                'temporal_type': self._classify_temporal_type(entity),
                'freshness': self._calculate_freshness(source_date),
                'age_days': self._calculate_age_days(source_date),
                'is_current': True
            }

            # Extract temporal context from surrounding text
            if context:
                temporal_context = self._extract_temporal_context(context)
                temporal_meta.update(temporal_context)

            # Add quarter/year if financial metric
            if entity.get('type') == 'metric' or 'margin' in str(entity.get('properties', {})).lower():
                period = self._extract_reporting_period(context, source_date)
                if period:
                    temporal_meta['reporting_period'] = period
                    temporal_meta['quarter'] = period.get('quarter')
                    temporal_meta['fiscal_year'] = period.get('year')

            # Handle version tracking for entities that change over time
            if entity.get('type') in ['metric', 'rating', 'price_target']:
                temporal_meta['version'] = 1  # Will increment on updates
                temporal_meta['supersedes'] = None  # Link to previous version
                temporal_meta['superseded_by'] = None  # Link to newer version

            # Add temporal metadata to entity
            if 'metadata' not in entity:
                entity['metadata'] = {}
            entity['metadata']['temporal'] = temporal_meta

            # Update properties with key temporal fields
            if 'properties' not in entity:
                entity['properties'] = {}
            entity['properties']['last_updated'] = self.current_time.isoformat()
            entity['properties']['freshness_score'] = self._calculate_freshness_score(source_date)

            return entity

        except Exception as e:
            logger.warning(f"Failed to enhance entity temporally: {e}")
            return entity

    def enhance_edge(self, edge: Dict[str, Any],
                    source_date: Optional[datetime] = None,
                    relationship_context: Optional[str] = None) -> Dict[str, Any]:
        """
        Enhance edge with temporal metadata.

        Args:
            edge: Edge dict to enhance
            source_date: Date when relationship was observed
            relationship_context: Context about the relationship

        Returns:
            Enhanced edge with temporal metadata
        """
        try:
            # Calculate temporal properties
            age_days = self._calculate_age_days(source_date)

            temporal_props = {
                'observed_at': source_date.isoformat() if source_date else self.current_time.isoformat(),
                'days_ago': age_days,
                'is_recent': age_days <= 30,
                'is_current': age_days <= 7,
                'freshness': self._calculate_freshness(source_date),
                'temporal_confidence': self._calculate_temporal_confidence(age_days)
            }

            # Detect temporal edge types
            if edge.get('type') in ['precedes', 'follows', 'during']:
                temporal_props['is_temporal_edge'] = True
                temporal_props['temporal_distance_days'] = self._calculate_temporal_distance(edge)

            # For causal relationships, add lag information
            if edge.get('type') in ['causes', 'correlates_with', 'impacts']:
                lag = self._extract_lag_period(relationship_context)
                if lag:
                    temporal_props['lag_days'] = lag['days']
                    temporal_props['lag_description'] = lag['description']

            # Add change detection for evolving relationships
            if edge.get('type') in ['competes_with', 'supplies_to', 'depends_on']:
                temporal_props['relationship_strength_trend'] = self._detect_relationship_trend(edge)

            # Update edge properties
            if 'properties' not in edge:
                edge['properties'] = {}
            edge['properties'].update(temporal_props)

            # Adjust edge weight based on freshness
            if 'weight' in edge:
                edge['weight'] = edge['weight'] * temporal_props['temporal_confidence']

            return edge

        except Exception as e:
            logger.warning(f"Failed to enhance edge temporally: {e}")
            return edge

    def create_temporal_edges(self, entities: List[Dict[str, Any]],
                            existing_edges: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Create additional temporal edges between entities.

        Args:
            entities: List of entities
            existing_edges: Existing edges in graph

        Returns:
            New temporal edges to add
        """
        temporal_edges = []

        try:
            # Group entities by type and time
            metrics_by_time = {}
            events_by_time = {}

            for entity in entities:
                if entity.get('type') == 'metric':
                    date_key = entity.get('metadata', {}).get('temporal', {}).get('valid_from')
                    if date_key:
                        if date_key not in metrics_by_time:
                            metrics_by_time[date_key] = []
                        metrics_by_time[date_key].append(entity)

                elif entity.get('type') == 'event':
                    date_key = entity.get('metadata', {}).get('temporal', {}).get('valid_from')
                    if date_key:
                        if date_key not in events_by_time:
                            events_by_time[date_key] = []
                        events_by_time[date_key].append(entity)

            # Create temporal sequence edges for metrics
            sorted_metric_dates = sorted(metrics_by_time.keys())
            for i in range(len(sorted_metric_dates) - 1):
                current_date = sorted_metric_dates[i]
                next_date = sorted_metric_dates[i + 1]

                for current_metric in metrics_by_time[current_date]:
                    for next_metric in metrics_by_time[next_date]:
                        # Only link same metric types
                        if current_metric.get('properties', {}).get('metric_type') == \
                           next_metric.get('properties', {}).get('metric_type'):

                            temporal_edge = {
                                'id': f"{current_metric['id']}_precedes_{next_metric['id']}",
                                'source': current_metric['id'],
                                'target': next_metric['id'],
                                'type': 'METRIC_EVOLVED',
                                'properties': {
                                    'temporal_type': 'sequence',
                                    'time_delta_days': self._calculate_date_diff(current_date, next_date),
                                    'metric_type': current_metric.get('properties', {}).get('metric_type'),
                                    'is_temporal_edge': True
                                },
                                'weight': 0.7
                            }
                            temporal_edges.append(temporal_edge)

            # Create correlation edges for events happening close in time
            for date, events in events_by_time.items():
                if len(events) > 1:
                    for i, event1 in enumerate(events):
                        for event2 in events[i+1:]:
                            correlation_edge = {
                                'id': f"{event1['id']}_correlates_{event2['id']}",
                                'source': event1['id'],
                                'target': event2['id'],
                                'type': 'TEMPORALLY_CORRELATED',
                                'properties': {
                                    'temporal_type': 'correlation',
                                    'occurred_on': date,
                                    'is_temporal_edge': True
                                },
                                'weight': 0.5,
                                'bidirectional': True
                            }
                            temporal_edges.append(correlation_edge)

        except Exception as e:
            logger.error(f"Failed to create temporal edges: {e}")

        return temporal_edges

    def _classify_temporal_type(self, entity: Dict[str, Any]) -> str:
        """Classify entity's temporal nature."""
        entity_type = entity.get('type', '')

        if entity_type in ['metric', 'price_target', 'rating']:
            return 'point_in_time'  # Valid at specific time
        elif entity_type in ['company', 'person']:
            return 'persistent'  # Valid over long periods
        elif entity_type == 'event':
            return 'instantaneous'  # Happens at specific moment
        else:
            return 'unknown'

    def _calculate_freshness(self, source_date: Optional[datetime]) -> str:
        """Calculate freshness category."""
        if not source_date:
            return 'unknown'

        age_days = self._calculate_age_days(source_date)

        for category, threshold in self.freshness_thresholds.items():
            if threshold is None or age_days <= threshold:
                return category

        return 'very_stale'

    def _calculate_age_days(self, source_date: Optional[datetime]) -> int:
        """Calculate age in days."""
        if not source_date:
            return 0

        # Ensure timezone awareness
        if source_date.tzinfo is None:
            source_date = source_date.replace(tzinfo=timezone.utc)

        delta = self.current_time - source_date
        return max(0, delta.days)

    def _calculate_freshness_score(self, source_date: Optional[datetime]) -> float:
        """
        Calculate freshness score (0.0 to 1.0).

        Uses exponential decay with half-life of 30 days.
        """
        if not source_date:
            return 0.5  # Unknown freshness

        age_days = self._calculate_age_days(source_date)
        half_life = 30  # Days

        # Exponential decay formula
        score = 0.5 ** (age_days / half_life)
        return round(score, 3)

    def _calculate_temporal_confidence(self, age_days: int) -> float:
        """
        Calculate confidence adjustment based on age.

        More recent = higher confidence.
        """
        if age_days <= 7:
            return 1.0
        elif age_days <= 30:
            return 0.9
        elif age_days <= 90:
            return 0.7
        elif age_days <= 365:
            return 0.5
        else:
            return 0.3

    def _extract_temporal_context(self, text: str) -> Dict[str, Any]:
        """Extract temporal references from text."""
        context = {}

        # Quarter patterns
        quarter_pattern = r'\b(Q[1-4])\s*(\d{4}|\d{2})\b'
        quarter_match = re.search(quarter_pattern, text)
        if quarter_match:
            context['quarter_reference'] = quarter_match.group(0)
            context['extracted_quarter'] = quarter_match.group(1)
            year = quarter_match.group(2)
            if len(year) == 2:
                year = '20' + year
            context['extracted_year'] = int(year)

        # Relative time patterns
        relative_patterns = {
            r'last\s+(week|month|quarter|year)': 'past',
            r'next\s+(week|month|quarter|year)': 'future',
            r'current\s+(week|month|quarter|year)': 'current',
            r'year[\-\s]to[\-\s]date': 'ytd',
            r'quarter[\-\s]to[\-\s]date': 'qtd'
        }

        for pattern, temporal_type in relative_patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                context['temporal_reference_type'] = temporal_type
                break

        return context

    def _extract_reporting_period(self, text: Optional[str],
                                 source_date: Optional[datetime]) -> Optional[Dict[str, Any]]:
        """Extract financial reporting period."""
        if not text:
            return None

        period = {}

        # Try to extract from text first
        quarter_pattern = r'(Q[1-4])\s*(\d{4})'
        match = re.search(quarter_pattern, text)

        if match:
            period['quarter'] = match.group(1)
            period['year'] = int(match.group(2))
            period['period_string'] = f"{match.group(1)} {match.group(2)}"
        elif source_date:
            # Infer from date
            quarter_num = (source_date.month - 1) // 3 + 1
            period['quarter'] = f"Q{quarter_num}"
            period['year'] = source_date.year
            period['period_string'] = f"Q{quarter_num} {source_date.year}"
            period['inferred'] = True

        return period if period else None

    def _extract_lag_period(self, text: Optional[str]) -> Optional[Dict[str, Any]]:
        """Extract lag period from causal relationships."""
        if not text:
            return None

        lag_patterns = [
            (r'(\d+)\s*day', 'days'),
            (r'(\d+)\s*week', 'weeks'),
            (r'(\d+)\s*month', 'months'),
            (r'(\d+)\s*quarter', 'quarters'),
            (r'(\d+)\s*year', 'years')
        ]

        for pattern, unit in lag_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = int(match.group(1))

                # Convert to days
                days_map = {
                    'days': 1,
                    'weeks': 7,
                    'months': 30,
                    'quarters': 90,
                    'years': 365
                }

                return {
                    'days': value * days_map[unit],
                    'description': f"{value} {unit}",
                    'unit': unit,
                    'value': value
                }

        return None

    def _calculate_temporal_distance(self, edge: Dict[str, Any]) -> int:
        """Calculate temporal distance for temporal edges."""
        # This would need access to entity temporal metadata
        # Simplified version returns default
        return 0

    def _detect_relationship_trend(self, edge: Dict[str, Any]) -> str:
        """Detect trend in relationship strength over time."""
        # This would need historical edge data
        # Simplified version returns neutral
        return 'stable'

    def _calculate_date_diff(self, date1_str: str, date2_str: str) -> int:
        """Calculate difference in days between two date strings."""
        try:
            date1 = parse_date(date1_str)
            date2 = parse_date(date2_str)
            return abs((date2 - date1).days)
        except:
            return 0