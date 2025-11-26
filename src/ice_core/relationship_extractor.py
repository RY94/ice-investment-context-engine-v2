# Location: /src/ice_core/relationship_extractor.py
# Purpose: Extract structured relationships between entities for knowledge graph construction
# Why: Enable competitive intelligence, risk analysis, and multi-hop reasoning in PM workflows
# Relevant Files: enhanced_entity_extractor.py, event_extractor.py, data_ingestion.py

"""
Relationship Extraction Module for ICE Knowledge Graph

Implements simplified relationship taxonomy (7 core types vs 15) to maintain elegance
while enabling sophisticated graph queries for hedge fund PM intelligence.

Core Relationships:
1. RELATED_TO - Generic relationship with type attribute
2. HOLDS - Portfolio → Company relationships
3. EMPLOYED_BY - Person → Company relationships
4. CATEGORY_OF - Company → Category (sector/industry/theme)
5. EVENT_AFFECTS - Event → Company/Theme relationships
6. MENTIONED_IN - Entity → Document relationships
7. TEMPORAL_FOLLOWS - Event → Event sequences
"""

import re
import logging
import sys
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import json

# Add project root to path for config import
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from updated_architectures.implementation.config import get_confidence

logger = logging.getLogger(__name__)


@dataclass
class Relationship:
    """Represents a relationship between two entities"""
    source: str  # Source entity ID/name
    relationship_type: str  # One of the 7 core types
    target: str  # Target entity ID/name
    attributes: Dict[str, Any]  # Additional metadata (e.g., type for RELATED_TO)
    confidence: float = 0.5  # Confidence score (0.0 to 1.0)
    context: str = ""  # Surrounding text context
    source_document: str = ""  # Document where relationship was found


class RelationshipExtractor:
    """
    Extracts structured relationships between entities

    Uses pattern matching and NLP to identify relationships
    and classify them into the simplified 7-type taxonomy
    """

    # Core relationship types (simplified from 15 to 7)
    RELATIONSHIP_TYPES = {
        'RELATED_TO': 'Generic relationship with type attribute',
        'HOLDS': 'Portfolio holds company position',
        'EMPLOYED_BY': 'Person employed by company',
        'CATEGORY_OF': 'Company belongs to category',
        'EVENT_AFFECTS': 'Event affects company/theme',
        'MENTIONED_IN': 'Entity mentioned in document',
        'TEMPORAL_FOLLOWS': 'Event follows another event'
    }

    # Sub-types for RELATED_TO (stored in attributes)
    RELATED_TO_SUBTYPES = [
        'competitor', 'supplier', 'customer', 'partner',
        'subsidiary', 'parent', 'investor', 'advisor',
        'correlates_with', 'alternative_to'
    ]

    # Relationship detection patterns
    RELATIONSHIP_PATTERNS = {
        # Competitive relationships
        'competitor': [
            r"({company1})\s+(?:competes with|competitor of|rivals?)\s+({company2})",
            r"({company1})\s+and\s+({company2})\s+(?:compete|are competitors)",
            r"competition\s+(?:between|from)\s+({company1})\s+and\s+({company2})",
            r"({company1})\s+vs\.?\s+({company2})"
        ],
        # Supply chain relationships
        'supplier': [
            r"({company1})\s+(?:supplies|supplies to|supplier (?:of|to))\s+({company2})",
            r"({company2})\s+(?:sources from|buys from|procures from)\s+({company1})",
            r"({company1})\s+(?:is a|as a)\s+(?:key |major |primary )?supplier"
        ],
        'customer': [
            r"({company1})\s+(?:customer of|client of|buys from)\s+({company2})",
            r"({company2})\s+(?:sells to|supplies)\s+({company1})",
            r"({company1})\s+(?:is a|as a)\s+(?:key |major |largest )?customer"
        ],
        # Corporate structure
        'subsidiary': [
            r"({company1})\s+(?:subsidiary of|owned by|unit of)\s+({company2})",
            r"({company2})\s+(?:owns|acquired|parent of)\s+({company1})",
            r"({company1}),\s+a\s+({company2})\s+(?:subsidiary|company|unit)"
        ],
        # Partnership
        'partner': [
            r"({company1})\s+(?:partners with|partnership with|allied with)\s+({company2})",
            r"strategic\s+(?:partnership|alliance)\s+between\s+({company1})\s+and\s+({company2})",
            r"({company1})\s+and\s+({company2})\s+(?:collaborate|team up|join forces)"
        ],
        # Investment relationships
        'investor': [
            r"({company1})\s+(?:invests in|invested in|stake in)\s+({company2})",
            r"({company1})\s+(?:holds|owns)\s+(?:\d+%|stake|position)\s+(?:in|of)\s+({company2})",
            r"({company2})\s+(?:backed by|funded by)\s+({company1})"
        ],
        # Employment relationships
        'employment': [
            r"({person})\s+(?:CEO|CFO|CTO|President|Chairman)\s+(?:of|at)\s+({company})",
            r"({person})\s+(?:works at|employed by|joined)\s+({company})",
            r"({company})\s+(?:appointed|hired|named)\s+({person})",
            r"({person}),\s+(?:CEO|CFO|executive)\s+of\s+({company})"
        ],
        # Portfolio holdings
        'holdings': [
            r"({portfolio})\s+(?:holds|owns)\s+(?:position in|stake in)?\s*({company})",
            r"({portfolio})\s+(?:portfolio includes|invested in)\s+({company})",
            r"(\d+%)\s+(?:position|stake|holding)\s+in\s+({company})",
            r"({portfolio})\s+(?:long|short)\s+({company})"
        ]
    }

    def __init__(self):
        """Initialize relationship extractor"""
        self.extracted_relationships = []

    def extract_relationships(self,
                            text: str,
                            entities: List[Dict[str, Any]],
                            document_id: str = "") -> List[Relationship]:
        """
        Extract relationships from text given extracted entities

        Args:
            text: Document text
            entities: List of extracted entities with type and text
            document_id: Source document identifier

        Returns:
            List of extracted Relationship objects
        """
        relationships = []

        # Create entity lookup for efficient matching
        company_entities = [e for e in entities if e.get('type') == 'COMPANY']
        person_entities = [e for e in entities if e.get('type') == 'PERSON']
        portfolio_entities = [e for e in entities if e.get('type') == 'PORTFOLIO']
        event_entities = [e for e in entities if e.get('type') == 'EVENT']

        # Extract competitive relationships
        relationships.extend(self._extract_competitive_relationships(text, company_entities, document_id))

        # Extract supply chain relationships
        relationships.extend(self._extract_supply_chain_relationships(text, company_entities, document_id))

        # Extract employment relationships
        relationships.extend(self._extract_employment_relationships(text, person_entities, company_entities, document_id))

        # Extract portfolio holdings
        relationships.extend(self._extract_portfolio_relationships(text, portfolio_entities, company_entities, document_id))

        # Extract event relationships
        relationships.extend(self._extract_event_relationships(text, event_entities, company_entities, document_id))

        # Extract category relationships
        relationships.extend(self._extract_category_relationships(entities, document_id))

        # Deduplicate relationships
        relationships = self._deduplicate_relationships(relationships)

        logger.info(f"Extracted {len(relationships)} relationships from document")
        return relationships

    def _extract_competitive_relationships(self,
                                         text: str,
                                         companies: List[Dict],
                                         doc_id: str) -> List[Relationship]:
        """Extract competitive relationships between companies"""
        relationships = []

        for pattern in self.RELATIONSHIP_PATTERNS['competitor']:
            # Simple pattern matching for company pairs
            matches = re.finditer(pattern.replace('{company1}', r'([A-Z][A-Za-z&\s]+)')
                                        .replace('{company2}', r'([A-Z][A-Za-z&\s]+)'),
                                 text, re.IGNORECASE)

            for match in matches:
                company1 = match.group(1).strip()
                company2 = match.group(2).strip() if match.lastindex >= 2 else None

                if company2 and company1 != company2:
                    # Check if both companies are in our entity list
                    if any(c['text'] in company1 for c in companies) and \
                       any(c['text'] in company2 for c in companies):
                        rel = Relationship(
                            source=company1,
                            relationship_type='RELATED_TO',
                            target=company2,
                            attributes={'type': 'competitor'},
                            confidence=get_confidence('relationship_competitive'),
                            context=text[max(0, match.start()-50):min(len(text), match.end()+50)],
                            source_document=doc_id
                        )
                        relationships.append(rel)

        return relationships

    def _extract_supply_chain_relationships(self,
                                          text: str,
                                          companies: List[Dict],
                                          doc_id: str) -> List[Relationship]:
        """Extract supplier/customer relationships"""
        relationships = []

        # Extract supplier relationships
        for pattern in self.RELATIONSHIP_PATTERNS['supplier']:
            pattern_regex = pattern.replace('{company1}', r'([A-Z][A-Za-z&\s]+)')
            pattern_regex = pattern_regex.replace('{company2}', r'([A-Z][A-Za-z&\s]+)')
            matches = re.finditer(pattern_regex, text, re.IGNORECASE)

            for match in matches:
                if match.lastindex >= 2:
                    supplier = match.group(1).strip()
                    customer = match.group(2).strip()

                    rel = Relationship(
                        source=supplier,
                        relationship_type='RELATED_TO',
                        target=customer,
                        attributes={'type': 'supplier'},
                        confidence=get_confidence('relationship_supplier'),
                        context=text[max(0, match.start()-50):min(len(text), match.end()+50)],
                        source_document=doc_id
                    )
                    relationships.append(rel)

        return relationships

    def _extract_employment_relationships(self,
                                        text: str,
                                        persons: List[Dict],
                                        companies: List[Dict],
                                        doc_id: str) -> List[Relationship]:
        """Extract person-company employment relationships"""
        relationships = []

        for pattern in self.RELATIONSHIP_PATTERNS['employment']:
            pattern_regex = pattern.replace('{person}', r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)')
            pattern_regex = pattern_regex.replace('{company}', r'([A-Z][A-Za-z&\s]+)')
            matches = re.finditer(pattern_regex, text, re.IGNORECASE)

            for match in matches:
                if match.lastindex >= 2:
                    person = match.group(1).strip()
                    company = match.group(2).strip()

                    # Extract role if present
                    role_match = re.search(r'(CEO|CFO|CTO|President|Chairman|Director)',
                                         text[match.start():match.end()], re.IGNORECASE)
                    role = role_match.group(1) if role_match else 'employee'

                    rel = Relationship(
                        source=person,
                        relationship_type='EMPLOYED_BY',
                        target=company,
                        attributes={'role': role},
                        confidence=get_confidence('relationship_employment'),
                        context=text[max(0, match.start()-50):min(len(text), match.end()+50)],
                        source_document=doc_id
                    )
                    relationships.append(rel)

        return relationships

    def _extract_portfolio_relationships(self,
                                       text: str,
                                       portfolios: List[Dict],
                                       companies: List[Dict],
                                       doc_id: str) -> List[Relationship]:
        """Extract portfolio holding relationships"""
        relationships = []

        for pattern in self.RELATIONSHIP_PATTERNS['holdings']:
            pattern_regex = pattern.replace('{portfolio}', r'([A-Za-z\s]+(?:Fund|Portfolio))')
            pattern_regex = pattern_regex.replace('{company}', r'([A-Z]{1,5}|\w+\s+(?:Inc|Corp|Ltd))')
            matches = re.finditer(pattern_regex, text, re.IGNORECASE)

            for match in matches:
                if match.lastindex >= 2:
                    portfolio = match.group(1).strip()
                    company = match.group(2).strip()

                    # Extract position size if mentioned
                    size_match = re.search(r'(\d+(?:\.\d+)?)\s*%',
                                         text[max(0, match.start()-20):match.end()+20])
                    position_size = float(size_match.group(1))/100 if size_match else None

                    rel = Relationship(
                        source=portfolio,
                        relationship_type='HOLDS',
                        target=company,
                        attributes={'position_size': position_size, 'entry_date': None},
                        confidence=get_confidence('relationship_portfolio'),
                        context=text[max(0, match.start()-50):min(len(text), match.end()+50)],
                        source_document=doc_id
                    )
                    relationships.append(rel)

        return relationships

    def _extract_event_relationships(self,
                                   text: str,
                                   events: List[Dict],
                                   companies: List[Dict],
                                   doc_id: str) -> List[Relationship]:
        """Extract event-company relationships"""
        relationships = []

        for event in events:
            event_text = event.get('text', '')
            event_type = event.get('metadata', {}).get('type', 'other')

            # Find companies mentioned near the event
            for company in companies:
                company_text = company.get('text', '')

                # Check if company is mentioned within 100 chars of event
                event_pos = text.find(event_text)
                company_pos = text.find(company_text)

                if event_pos >= 0 and company_pos >= 0:
                    distance = abs(event_pos - company_pos)
                    if distance < 200:  # Within reasonable proximity
                        rel = Relationship(
                            source=event_text,
                            relationship_type='EVENT_AFFECTS',
                            target=company_text,
                            attributes={'event_type': event_type, 'proximity': distance},
                            confidence=get_confidence('relationship_event_close') if distance < 100 else get_confidence('relationship_event_distant'),
                            context=text[max(0, min(event_pos, company_pos)-50):
                                       min(len(text), max(event_pos, company_pos)+50)],
                            source_document=doc_id
                        )
                        relationships.append(rel)

        return relationships

    def _extract_category_relationships(self,
                                      entities: List[Dict],
                                      doc_id: str) -> List[Relationship]:
        """Extract company-category relationships"""
        relationships = []

        companies = [e for e in entities if e.get('type') == 'COMPANY']
        categories = [e for e in entities if e.get('type') == 'CATEGORY']

        # Simple heuristic: link companies to categories mentioned in same document
        # In production, would use more sophisticated co-occurrence analysis
        for company in companies:
            for category in categories:
                # Parse category type from metadata
                category_meta = category.get('text', '')
                if '|type:' in category_meta:
                    category_name, category_type = category_meta.split('|type:')
                else:
                    category_name = category_meta
                    category_type = 'unknown'

                # Create relationship with lower confidence since it's document-level
                rel = Relationship(
                    source=company.get('text', ''),
                    relationship_type='CATEGORY_OF',
                    target=category_name,
                    attributes={'category_type': category_type},
                    confidence=get_confidence('relationship_category'),
                    context="Document-level association",
                    source_document=doc_id
                )
                relationships.append(rel)

        return relationships

    def _deduplicate_relationships(self, relationships: List[Relationship]) -> List[Relationship]:
        """Remove duplicate relationships, keeping highest confidence"""
        unique = {}

        for rel in relationships:
            # Create unique key
            key = (rel.source.lower(), rel.relationship_type, rel.target.lower())

            if key not in unique or rel.confidence > unique[key].confidence:
                unique[key] = rel

        return list(unique.values())

    def create_graph_triples(self, relationships: List[Relationship]) -> List[Tuple[str, str, str]]:
        """
        Convert relationships to graph triples (source, relationship, target)

        Returns:
            List of (source, relationship, target) tuples for graph construction
        """
        triples = []

        for rel in relationships:
            # For RELATED_TO, include subtype in relationship name
            if rel.relationship_type == 'RELATED_TO':
                rel_type = f"RELATED_TO_{rel.attributes.get('type', 'generic').upper()}"
            else:
                rel_type = rel.relationship_type

            triples.append((rel.source, rel_type, rel.target))

        return triples

    def to_signal_store_format(self, relationships: List[Relationship]) -> List[Dict]:
        """
        Convert relationships to Signal Store format

        Returns:
            List of dicts ready for Signal Store insertion
        """
        signal_store_records = []

        for rel in relationships:
            record = {
                'source_entity': rel.source,
                'target_entity': rel.target,
                'relationship_type': rel.relationship_type,
                'relationship_category': self._get_category(rel),
                'confidence': rel.confidence,
                'attributes': json.dumps(rel.attributes),
                'context': rel.context[:500],  # Truncate context
                'source_document': rel.source_document,
                'extraction_date': datetime.now().isoformat()
            }
            signal_store_records.append(record)

        return signal_store_records

    def _get_category(self, relationship: Relationship) -> str:
        """Get relationship category for Signal Store"""
        if relationship.relationship_type == 'RELATED_TO':
            subtype = relationship.attributes.get('type', 'generic')
            if subtype in ['competitor', 'alternative_to']:
                return 'COMPETITIVE'
            elif subtype in ['supplier', 'customer']:
                return 'SUPPLY_CHAIN'
            elif subtype in ['subsidiary', 'parent']:
                return 'CORPORATE'
            elif subtype in ['partner', 'investor']:
                return 'STRATEGIC'
            else:
                return 'OTHER'
        elif relationship.relationship_type == 'EMPLOYED_BY':
            return 'GOVERNANCE'
        elif relationship.relationship_type == 'HOLDS':
            return 'PORTFOLIO'
        elif relationship.relationship_type == 'CATEGORY_OF':
            return 'THEMATIC'
        elif relationship.relationship_type == 'EVENT_AFFECTS':
            return 'EVENT_DRIVEN'
        else:
            return 'OTHER'