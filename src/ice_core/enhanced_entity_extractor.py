# Location: /src/ice_core/enhanced_entity_extractor.py
# Purpose: Enhanced entity extraction with improved LLM prompts for better F1 score
# Why: Phase 2 optimization - achieve F1 score ≥0.85 through better precision/recall
# Relevant Files: entity_extractor.py, ice_system_manager.py, lightrag integration

"""
Enhanced Entity Extraction System for ICE

This module improves entity extraction precision and recall through:
1. Better LLM prompts with few-shot examples
2. Entity validation against knowledge graph
3. Confidence scoring and relationship extraction
4. Semantic similarity caching for performance

Target: F1 score ≥0.85 (current baseline: ~0.68)
"""

import os
import re
import json
import logging
import hashlib
from typing import Dict, List, Any, Optional, Tuple, Set
from datetime import datetime
from dataclasses import dataclass, field
import asyncio
from openai import OpenAI
from functools import lru_cache

# Centralized confidence config (Phase 2.8)
from updated_architectures.implementation.config import get_confidence

logger = logging.getLogger(__name__)


@dataclass
class ExtractedEntity:
    """Represents an extracted entity with metadata"""
    text: str  # The entity text as it appears
    normalized: str  # Normalized form (e.g., AAPL for Apple Inc.)
    type: str  # Entity type: company, ticker, person, metric, date, price
    confidence: float  # Confidence score 0-1
    context: str  # Surrounding context
    source_position: int  # Position in source text
    validated: bool = False  # Whether validated against knowledge graph
    kg_id: Optional[str] = None  # Knowledge graph entity ID if validated


@dataclass
class EntityRelationship:
    """Represents a relationship between entities"""
    source_entity: ExtractedEntity
    target_entity: ExtractedEntity
    relationship_type: str  # e.g., "CEO_of", "owns", "forecasts", "competes_with"
    confidence: float
    context: str


class EnhancedEntityExtractor:
    """
    Enhanced entity extraction using optimized LLM prompts and validation

    Key improvements:
    1. Few-shot learning prompts for better accuracy
    2. Chain-of-thought reasoning for complex entities
    3. Knowledge graph validation
    4. Relationship extraction
    5. Confidence scoring
    """

    # Optimized prompt for financial entity extraction
    ENTITY_EXTRACTION_PROMPT = """You are an expert financial analyst extracting entities from investment documents.

STRICT EXTRACTION RULES:
1. Extract ONLY the entity itself, not descriptive phrases
2. For metrics: Include the NUMBER and its UNIT only (e.g., "$18.12B", "206%", "461,000")
3. For documents: Recognize filing types (10-K, 10-Q, 8-K, 13F, etc.) as DOCUMENT type
4. Keep entities atomic - do not combine multiple concepts
5. Percentages are METRIC type, not separate
6. Dollar amounts can be PRICE (stock prices) or METRIC (revenue, earnings, etc.) based on context

ENTITY TYPES:
- COMPANY: Business entities (Apple Inc., Microsoft, NVIDIA)
- TICKER: Stock symbols in parentheses or standalone capitals (AAPL, MSFT, NVDA)
- PERSON: Individual names with optional roles (Tim Cook|role:CEO, Warren Buffett, Jensen Huang|role:executive)
- METRIC: Numeric values with context (revenue, growth %, units, $amounts for business metrics)
- DATE: Time references (Q3 2024, September, 2024)
- PRICE: Stock prices, price targets ($195, $450 price target)
- PRODUCT: Product names (iPhone 15, Azure, Copilot)
- DOCUMENT: Filing types (13F, 10-K, 8-K)
- CATEGORY: Sectors, industries, themes (Technology|type:sector, Semiconductors|type:industry, AI Revolution|type:theme)
- EVENT: Business events (Earnings Q2 2024|type:earnings, CEO resignation|type:management, Merger|type:ma_deal)
- PORTFOLIO: Fund or portfolio references (Flagship Fund, Long/Short Portfolio, 15% position in NVDA)

Examples:
Text: "Warren Buffett's Berkshire Hathaway (BRK.B) disclosed a $5.1B stake in their 13F filing"
CORRECT Entities:
- Warren Buffett [PERSON]
- Berkshire Hathaway [COMPANY]
- BRK.B [TICKER]
- $5.1B [METRIC]
- 13F [DOCUMENT]

WRONG:
- "$5.1B stake" (includes extra word)
- "13F filing" (should be just "13F")

Text: "Tesla delivered 461,000 vehicles, missing by 10,000 units"
CORRECT Entities:
- Tesla [COMPANY]
- 461,000 [METRIC]
- 10,000 [METRIC]

WRONG:
- "461,000 vehicles" (includes descriptor)
- "10,000 units" (includes descriptor)

Now extract entities from this text:
{text}

Return JSON format:
{{
  "entities": [
    {{
      "text": "exact entity text",
      "type": "COMPANY|TICKER|PERSON|METRIC|DATE|PRICE|PRODUCT|DOCUMENT|CATEGORY|EVENT|PORTFOLIO",
      "normalized": "normalized form",
      "context": "surrounding 5-10 words",
      "confidence": 0.95,
      "metadata": {{}}  // Optional: role for PERSON, type for CATEGORY/EVENT
    }}
  ],
  "relationships": []
}}"""

    # Validation prompt for entity disambiguation
    VALIDATION_PROMPT = """Given the entity "{entity}" of type {entity_type} in context: "{context}"

Is this a valid financial entity? Consider:
1. Is it a real company/person/metric?
2. Is the context financial/investment related?
3. Should it be normalized differently?

Return JSON:
{{
  "valid": true/false,
  "normalized": "corrected form if needed",
  "confidence": 0.0-1.0,
  "reasoning": "brief explanation"
}}"""

    def __init__(self, api_key: Optional[str] = None, cache_size: int = 1000):
        """
        Initialize enhanced entity extractor

        Args:
            api_key: OpenAI API key (optional, uses env var if not provided)
            cache_size: Size of LRU cache for similarity matching
        """
        self.api_key = api_key or os.environ.get('OPENAI_API_KEY')
        self.cache_size = cache_size

        # Initialize OpenAI client
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key)
            self.llm_available = True
        else:
            logger.warning("No OpenAI API key provided - using regex fallback")
            self.llm_available = False
            self.client = None

        # Entity cache for deduplication
        self._entity_cache = {}

        # Similarity cache with LRU eviction
        self._get_similar_entity.cache_clear()

        # Compile regex patterns for fallback
        self._compile_regex_patterns()

        # Load reference data
        self._load_reference_data()

    def _compile_regex_patterns(self):
        """Compile regex patterns for fallback extraction"""
        # Ticker pattern: 1-5 uppercase letters, possibly with dots, often in parentheses
        self.ticker_pattern = re.compile(r'\(([A-Z]{1,5}(?:\.[A-Z]{1,2})?)\)|\b([A-Z]{2,5}(?:\.[A-Z]{1,2})?)\b')

        # Price pattern: $X, $X.XX, $XM, $XB, with more variations
        self.price_pattern = re.compile(r'\$[\d,]+(?:\.?\d*)?[MBKTmkb]?(?:illion|illion)?(?:\s+(?:billion|million|thousand))?')

        # Percentage pattern: X%, +X%, -X%
        self.percent_pattern = re.compile(r'[+-]?\d+(?:\.\d+)?%')

        # Revenue/metric pattern: captures numeric values with context
        self.metric_pattern = re.compile(
            r'(?:[\d,]+(?:\.\d+)?[MBKTmkb]?(?:illion)?(?:\s+(?:billion|million|thousand))?)'
            r'(?:\s*(?:in\s+)?(?:revenue|earnings|sales|profit|loss|income|growth|units?|vehicles?|deliveries))',
            re.IGNORECASE
        )

        # Date patterns - more comprehensive
        self.date_pattern = re.compile(
            r'\b(?:Q[1-4]\s+\d{4}|FY\s*\d{4}|H[12]\s+\d{4}|'
            r'\d{4}|\d{1,2}/\d{1,2}/\d{2,4}|'
            r'(?:January|February|March|April|May|June|July|August|September|October|November|December)'
            r'(?:\s+\d{1,2},?)?\s+\d{4}|'
            r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*(?:\s+\d{1,2},?)?\s+\d{4})\b',
            re.IGNORECASE
        )

        # Person pattern: Names with titles/context
        self.person_pattern = re.compile(
            r'(?:[A-Z][a-z]+(?:\s+[A-Z]\.)?(?:\s+[A-Z][a-z]+)+)'
            r'(?=\s*,?\s*(?:CEO|CFO|CTO|COO|President|Chairman|Director|founder|executive|analyst))|'
            r'(?:CEO|CFO|CTO|COO|President|Chairman)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)'
        )

        # Company pattern: Company names with common suffixes
        self.company_pattern = re.compile(
            r'(?:[A-Z][A-Za-z&\']*(?:\s+[A-Z][A-Za-z&\']*)*)'
            r'(?:\s+(?:Inc\.?|Corporation|Corp\.?|Company|Co\.?|LLC|Ltd\.?|Limited|Group|Holdings|'
            r'Technologies|Tech|Systems|Solutions|Partners|Capital|Ventures|Bank|Financial|Services))',
            re.IGNORECASE
        )

        # Category pattern: Sectors, industries, and themes
        self.category_pattern = re.compile(
            r'(?:Technology|Healthcare|Financials?|Energy|Consumer\s+(?:Discretionary|Staples)|'
            r'Industrials|Materials|Real\s+Estate|Utilities|Telecommunications)\s+(?:sector|industry)|'
            r'(?:AI|Artificial\s+Intelligence|Cloud\s+Computing|Cybersecurity|ESG|Semiconductors?|'
            r'Biotech|FinTech|E-?commerce|Supply\s+Chain|Inflation|Energy\s+Transition)\s*(?:theme|trend)?',
            re.IGNORECASE
        )

        # Event pattern: Business events
        self.event_pattern = re.compile(
            r'(?:Q[1-4]\s+\d{4}\s+earnings|earnings\s+(?:report|release|announcement)|'
            r'(?:CEO|CFO|CTO)\s+(?:resignation|appointment|departure)|management\s+(?:change|transition)|'
            r'merger|acquisition|M&A\s+(?:deal|transaction)|takeover|buyout|'
            r'guidance\s+(?:update|revision|raised|lowered)|'
            r'product\s+(?:launch|announcement|release)|'
            r'(?:SEC|regulatory)\s+(?:investigation|inquiry|filing)|scandal|lawsuit)',
            re.IGNORECASE
        )

        # Portfolio pattern: Fund and portfolio references
        self.portfolio_pattern = re.compile(
            r'(?:(?:Flagship|Core|Growth|Value|Long[/-]Short|Equity|Fixed\s+Income|Hedge)\s+(?:Fund|Portfolio))|'
            r'(?:\d+(?:\.\d+)?%\s+(?:position|stake|holding)\s+in\s+[A-Z]{1,5})|'
            r'(?:portfolio|fund)\s+(?:holding|position|allocation)',
            re.IGNORECASE
        )

    def _load_reference_data(self):
        """Load reference data for validation"""
        # Common financial metrics
        self.financial_metrics = {
            'revenue', 'earnings', 'ebitda', 'eps', 'p/e', 'peg',
            'margin', 'capex', 'opex', 'fcf', 'debt', 'assets',
            'market cap', 'enterprise value', 'dividend yield'
        }

        # Common relationship types
        self.relationship_types = {
            'CEO_OF', 'CFO_OF', 'WORKS_AT', 'OWNS', 'ACQUIRED_BY',
            'COMPETES_WITH', 'SUPPLIES_TO', 'PARTNER_OF', 'INVESTED_IN',
            'FORECASTS', 'ANALYZES', 'RATES', 'HEADQUARTERED_IN'
        }

    def extract_entities_llm(self, text: str) -> Dict[str, Any]:
        """
        Extract entities using LLM with optimized prompts

        Args:
            text: Input text to extract entities from

        Returns:
            Dict with extracted entities and relationships
        """
        if not self.llm_available:
            return self.extract_entities_regex(text)

        try:
            # Use GPT-4 for better accuracy
            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "You are an expert at extracting financial entities with high precision. ALWAYS return valid JSON."},
                    {"role": "user", "content": self.ENTITY_EXTRACTION_PROMPT.format(text=text[:3000])}  # Limit context
                ],
                temperature=0.1,  # Low temperature for consistency
                max_tokens=1500,
                response_format={"type": "json_object"}  # Force JSON output
            )

            # Parse response
            content = response.choices[0].message.content
            logger.debug(f"LLM response: {content[:200]}...")  # Debug logging
            result = json.loads(content)

            # Convert to ExtractedEntity objects
            entities = []
            for entity_dict in result.get('entities', []):
                entity = ExtractedEntity(
                    text=entity_dict['text'],
                    normalized=entity_dict.get('normalized', entity_dict['text']),
                    type=entity_dict['type'],
                    confidence=entity_dict.get('confidence', 0.9),
                    context=entity_dict.get('context', ''),
                    source_position=text.find(entity_dict['text'])
                )
                entities.append(entity)

            # Convert relationships
            relationships = []
            for rel_dict in result.get('relationships', []):
                # Find matching entities
                source = next((e for e in entities if e.text == rel_dict['source']), None)
                target = next((e for e in entities if e.text == rel_dict['target']), None)

                if source and target:
                    rel = EntityRelationship(
                        source_entity=source,
                        target_entity=target,
                        relationship_type=rel_dict['type'],
                        confidence=rel_dict.get('confidence', 0.8),
                        context=text[max(0, source.source_position-50):min(len(text), target.source_position+50)]
                    )
                    relationships.append(rel)

            return {
                'entities': entities,
                'relationships': relationships,
                'extraction_method': 'llm_enhanced'
            }

        except Exception as e:
            logger.error(f"LLM extraction failed: {e}, falling back to regex")
            return self.extract_entities_regex(text)

    def extract_entities_regex(self, text: str) -> Dict[str, Any]:
        """
        Fallback regex-based entity extraction

        Args:
            text: Input text

        Returns:
            Dict with extracted entities (no relationships in regex mode)
        """
        entities = []
        seen_entities = set()  # For deduplication

        # Helper to add unique entities
        def add_entity(entity_text, entity_type, confidence, position):
            key = (entity_text.lower(), entity_type)
            if key not in seen_entities:
                seen_entities.add(key)
                entities.append(ExtractedEntity(
                    text=entity_text,
                    normalized=entity_text,
                    type=entity_type,
                    confidence=confidence,
                    context=text[max(0, position-30):min(len(text), position+len(entity_text)+30)],
                    source_position=position
                ))

        # Extract companies FIRST (before tickers to provide context)
        for match in self.company_pattern.finditer(text):
            company = match.group().strip()
            add_entity(company, 'COMPANY', 0.75, match.start())

        # Extract tickers (with parentheses priority)
        for match in self.ticker_pattern.finditer(text):
            # Group 1 is ticker in parentheses, Group 2 is standalone ticker
            ticker = match.group(1) or match.group(2)
            if ticker:
                # Filter out common non-ticker acronyms
                if len(ticker) >= 2 and ticker not in {'CEO', 'CFO', 'CTO', 'IPO', 'M&A', 'AI', 'ML', 'US', 'UK', 'EU', 'IT'}:
                    # Higher confidence if in parentheses (Phase 2.8: centralized config)
                    confidence = get_confidence('extraction_medium') if match.group(1) else get_confidence('threshold_medium')
                    add_entity(ticker, 'TICKER', confidence, match.start())

        # Extract people
        for match in self.person_pattern.finditer(text):
            person = match.group().strip()
            # Clean up CEO/CFO prefix if captured
            for title in ['CEO', 'CFO', 'CTO', 'COO', 'President', 'Chairman']:
                if person.startswith(title + ' '):
                    person = person[len(title)+1:]
                    break
            if len(person) > 3:  # Filter out very short names
                add_entity(person, 'PERSON', get_confidence('threshold_high'), match.start())

        # Extract prices
        for match in self.price_pattern.finditer(text):
            price = match.group()
            add_entity(price, 'PRICE', get_confidence('extraction_high'), match.start())

        # Extract metrics (revenue/earnings with values)
        for match in self.metric_pattern.finditer(text):
            metric = match.group()
            add_entity(metric, 'METRIC', get_confidence('extraction_medium'), match.start())

        # Extract percentages as metrics (if not already captured)
        for match in self.percent_pattern.finditer(text):
            percent = match.group()
            # Check context to see if it's a meaningful metric
            context_start = max(0, match.start()-50)
            context = text[context_start:match.start()].lower()
            if any(word in context for word in ['increase', 'decrease', 'growth', 'decline', 'rose', 'fell', 'up', 'down', 'yoy', 'revenue', 'earnings', 'margin']):
                add_entity(percent, 'METRIC', get_confidence('threshold_high'), match.start())

        # Extract dates
        for match in self.date_pattern.finditer(text):
            date = match.group()
            # Normalize common date formats
            if date.isdigit() and len(date) == 4:  # Just a year
                add_entity(date, 'DATE', get_confidence('threshold_medium'), match.start())
            else:
                add_entity(date, 'DATE', get_confidence('extraction_medium'), match.start())

        # Extract categories (sectors, industries, themes)
        for match in self.category_pattern.finditer(text):
            category = match.group().strip()
            # Determine category type
            category_lower = category.lower()
            if 'sector' in category_lower:
                category_type = 'sector'
            elif 'industry' in category_lower:
                category_type = 'industry'
            else:
                category_type = 'theme'
            add_entity(f"{category}|type:{category_type}", 'CATEGORY', 0.8, match.start())

        # Extract events
        for match in self.event_pattern.finditer(text):
            event = match.group().strip()
            # Determine event type
            event_lower = event.lower()
            if 'earnings' in event_lower:
                event_type = 'earnings'
            elif any(x in event_lower for x in ['ceo', 'cfo', 'management', 'resignation', 'appointment']):
                event_type = 'management'
            elif any(x in event_lower for x in ['merger', 'acquisition', 'm&a', 'takeover']):
                event_type = 'ma_deal'
            elif 'guidance' in event_lower:
                event_type = 'guidance'
            elif 'product' in event_lower:
                event_type = 'product'
            elif any(x in event_lower for x in ['scandal', 'investigation', 'lawsuit']):
                event_type = 'regulatory'
            else:
                event_type = 'other'
            add_entity(f"{event}|type:{event_type}", 'EVENT', 0.75, match.start())

        # Extract portfolio references
        for match in self.portfolio_pattern.finditer(text):
            portfolio = match.group().strip()
            add_entity(portfolio, 'PORTFOLIO', 0.8, match.start())

        # Extract specific numeric values that might be metrics
        numeric_pattern = re.compile(r'[\d,]+(?:\.\d+)?[MBKTmkb]?(?:illion)?')
        for match in numeric_pattern.finditer(text):
            value = match.group()
            # Check if followed by units or metric terms
            following_text = text[match.end():min(len(text), match.end()+20)].lower()
            if any(unit in following_text for unit in ['vehicles', 'units', 'shares', 'employees', 'customers', 'subscribers']):
                add_entity(value + ' ' + following_text.split()[0], 'METRIC', 0.75, match.start())

        return {
            'entities': entities,
            'relationships': [],  # No relationship extraction in regex mode
            'extraction_method': 'regex_fallback'
        }

    async def validate_entity_against_kg(self, entity: ExtractedEntity, kg_query_func) -> ExtractedEntity:
        """
        Validate entity against knowledge graph

        Args:
            entity: Entity to validate
            kg_query_func: Function to query knowledge graph

        Returns:
            Entity with validation status updated
        """
        try:
            # Query knowledge graph for entity
            query = f"Find entity: {entity.normalized} type:{entity.type}"
            kg_result = await kg_query_func(query)

            if kg_result and kg_result.get('status') == 'success':
                # Check if entity exists in knowledge graph
                kg_entities = kg_result.get('entities', [])

                for kg_entity in kg_entities:
                    # Fuzzy match on normalized form
                    if self._fuzzy_match(entity.normalized, kg_entity.get('name', '')):
                        entity.validated = True
                        entity.kg_id = kg_entity.get('id')
                        entity.confidence = min(1.0, entity.confidence * 1.2)  # Boost confidence
                        break

        except Exception as e:
            logger.warning(f"KG validation failed for {entity.text}: {e}")

        return entity

    def _fuzzy_match(self, text1: str, text2: str, threshold: Optional[float] = None) -> bool:
        """
        Fuzzy string matching for entity validation

        Args:
            text1: First string
            text2: Second string
            threshold: Similarity threshold (0-1), defaults to config threshold_high

        Returns:
            True if strings are similar enough
        """
        # Default threshold from centralized config (Phase 2.8)
        if threshold is None:
            threshold = get_confidence('threshold_high')

        # Simple character-based similarity
        text1 = text1.lower().strip()
        text2 = text2.lower().strip()

        if text1 == text2:
            return True

        # Check if one is substring of other
        if text1 in text2 or text2 in text1:
            return True

        # Levenshtein distance (simplified)
        if len(text1) == 0 or len(text2) == 0:
            return False

        # Character overlap
        chars1 = set(text1)
        chars2 = set(text2)
        overlap = len(chars1 & chars2) / max(len(chars1), len(chars2))

        return overlap >= threshold

    @lru_cache(maxsize=1000)
    def _get_similar_entity(self, entity_text: str, entity_type: str) -> Optional[str]:
        """
        Cache for finding similar entities (semantic similarity)

        Args:
            entity_text: Entity text
            entity_type: Entity type

        Returns:
            Cached similar entity if found
        """
        cache_key = f"{entity_type}:{entity_text.lower()}"
        return self._entity_cache.get(cache_key)

    def calculate_f1_score(self, predicted: List[ExtractedEntity],
                          ground_truth: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Calculate F1 score for entity extraction

        Args:
            predicted: List of predicted entities
            ground_truth: List of ground truth entities

        Returns:
            Dict with precision, recall, and F1 score
        """
        # Convert to sets for comparison
        predicted_set = {(e.normalized.lower(), e.type) for e in predicted}
        truth_set = {(g['text'].lower(), g['type']) for g in ground_truth}

        # Calculate metrics
        true_positives = len(predicted_set & truth_set)
        false_positives = len(predicted_set - truth_set)
        false_negatives = len(truth_set - predicted_set)

        # Prevent division by zero
        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

        return {
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'true_positives': true_positives,
            'false_positives': false_positives,
            'false_negatives': false_negatives
        }

    def extract_entities(self, text: str, use_llm: bool = True) -> Dict[str, Any]:
        """
        Main entry point for entity extraction

        Args:
            text: Text to extract entities from
            use_llm: Whether to use LLM (True) or regex fallback (False)

        Returns:
            Dict with entities, relationships, and metadata
        """
        if use_llm and self.llm_available:
            # Call synchronous LLM extraction
            result = self.extract_entities_llm(text)
        else:
            result = self.extract_entities_regex(text)

        # Deduplicate entities
        result['entities'] = self._deduplicate_entities(result['entities'])

        # Add extraction timestamp
        result['extraction_time'] = datetime.now().isoformat()

        return result

    def _deduplicate_entities(self, entities: List[ExtractedEntity]) -> List[ExtractedEntity]:
        """
        Remove duplicate entities, keeping highest confidence version

        Args:
            entities: List of entities

        Returns:
            Deduplicated list
        """
        unique = {}

        for entity in entities:
            key = (entity.normalized.lower(), entity.type)

            if key not in unique or entity.confidence > unique[key].confidence:
                unique[key] = entity

        return list(unique.values())


# Convenience functions for integration
def create_enhanced_extractor(api_key: Optional[str] = None) -> EnhancedEntityExtractor:
    """
    Factory function to create enhanced entity extractor

    Args:
        api_key: Optional OpenAI API key

    Returns:
        EnhancedEntityExtractor instance
    """
    return EnhancedEntityExtractor(api_key=api_key)


def extract_entities_from_text(text: str, use_llm: bool = True) -> Dict[str, Any]:
    """
    Quick entity extraction function

    Args:
        text: Input text
        use_llm: Whether to use LLM

    Returns:
        Extraction results
    """
    extractor = create_enhanced_extractor()
    return extractor.extract_entities(text, use_llm=use_llm)


if __name__ == "__main__":
    # Test the enhanced extractor
    import os

    test_text = """
    NVIDIA (NVDA) reported Q3 2024 earnings yesterday, with CEO Jensen Huang announcing
    record revenue of $18.12B, up 206% year-over-year. The data center segment drove
    $14.51B in revenue. Analyst price targets range from $600 to $800, with Goldman Sachs
    maintaining a Buy rating. Microsoft (MSFT) and Amazon (AMZN) remain key customers.
    """

    print("Testing Enhanced Entity Extractor")
    print("="*50)

    # Test with LLM if available
    if os.environ.get('OPENAI_API_KEY'):
        print("Using LLM extraction...")
        result = extract_entities_from_text(test_text, use_llm=True)
    else:
        print("Using regex fallback (no API key)...")
        result = extract_entities_from_text(test_text, use_llm=False)

    print(f"\nExtracted {len(result['entities'])} entities:")
    for entity in result['entities']:
        print(f"  - {entity.text} ({entity.type}) [confidence: {entity.confidence:.2f}]")

    print(f"\nExtracted {len(result['relationships'])} relationships:")
    for rel in result['relationships']:
        print(f"  - {rel.source_entity.text} --{rel.relationship_type}--> {rel.target_entity.text}")

    print(f"\nExtraction method: {result['extraction_method']}")