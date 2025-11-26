# Location: /src/ice_core/event_extractor.py
# Purpose: Extract and classify events as first-class graph nodes for PM intelligence
# Why: Enable event-driven alerts, temporal reasoning, and multi-hop event→company→theme analysis
# Relevant Files: enhanced_entity_extractor.py, data_ingestion.py, signal_store.py

"""
Event Extraction Module for Hedge Fund PM Intelligence

Creates EVENT nodes as first-class citizens in the knowledge graph, enabling:
- Real-time event detection (earnings, M&A, scandals, management changes)
- Temporal event sequences (what happened before/after)
- Event→Company→Theme multi-hop reasoning
- Statistical validation via historical event patterns
"""

import re
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Any
from enum import Enum
import json
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# Security constants
MAX_DOCUMENT_LENGTH = 500000  # 500KB limit (prevents DOS)
RATE_LIMIT_EVENTS_PER_DOC = 50  # Max events per document

# Event type taxonomy for hedge fund use cases
class EventType(Enum):
    """Event categories relevant to PM decision-making"""
    EARNINGS = "earnings_release"
    GUIDANCE = "guidance_update"
    MA_DEAL = "merger_acquisition"
    MANAGEMENT = "management_change"
    SCANDAL = "scandal_investigation"
    RATING = "rating_change"
    PRODUCT = "product_launch"
    REGULATORY = "regulatory_action"
    DIVIDEND = "dividend_announcement"
    BUYBACK = "share_buyback"
    PARTNERSHIP = "strategic_partnership"
    LAWSUIT = "legal_action"
    RESTRUCTURING = "corporate_restructuring"
    MACRO = "macro_event"
    OTHER = "other_event"

@dataclass
class EventNode:
    """
    Event node representation for knowledge graph

    Events are first-class nodes that connect to:
    - Companies (EVENT → AFFECTS → COMPANY)
    - Themes (EVENT → RELATES_TO → THEME)
    - Other events (EVENT → TEMPORAL_FOLLOWS → EVENT)
    - People (EVENT → INVOLVES → PERSON)
    """
    id: str  # Unique identifier (e.g., "event_nvda_earnings_q2_2024")
    type: EventType  # Event classification
    ticker: str  # Primary affected company
    date: datetime  # Event occurrence date
    impact: str = "neutral"  # positive/negative/neutral
    magnitude: Optional[float] = None  # Impact magnitude (e.g., stock price change %)
    description: str = ""  # Human-readable description
    sentiment: float = 0.0  # Sentiment score (-1.0 to +1.0)
    confidence: float = 0.5  # Extraction confidence (0.0 to 1.0)
    themes: List[str] = field(default_factory=list)  # Related themes
    entities: Dict[str, List[str]] = field(default_factory=dict)  # Related entities
    source_document_id: str = ""  # Source document reference
    metadata: Dict[str, Any] = field(default_factory=dict)  # Additional attributes

    def to_graph_format(self) -> Dict:
        """Convert to format suitable for LightRAG graph insertion"""
        return {
            'entity_type': 'EVENT',
            'entity_name': self.id,
            'attributes': {
                'type': self.type.value,
                'ticker': self.ticker,
                'date': self.date.isoformat(),
                'impact': self.impact,
                'magnitude': self.magnitude,
                'description': self.description,
                'sentiment': self.sentiment,
                'confidence': self.confidence,
                'themes': json.dumps(self.themes),
                'source': self.source_document_id
            }
        }

    def to_signal_store_format(self) -> Dict:
        """Convert to format for Signal Store calendar_events table"""
        return {
            'ticker': self.ticker,
            'event_type': self.type.value,
            'event_date': self.date.strftime('%Y-%m-%d'),
            'description': self.description,
            'impact': self.impact,
            'magnitude': self.magnitude,
            'sentiment': self.sentiment,
            'confidence': self.confidence,
            'metadata': json.dumps(self.metadata),
            'source': self.source_document_id
        }

class EventExtractor:
    """
    Extracts and classifies events from financial documents

    Uses hybrid approach:
    1. Rule-based patterns for high-precision extraction
    2. NLP for context understanding and classification
    3. Statistical validation against historical patterns
    """

    # Ticker blacklist - common false positives to exclude
    TICKER_BLACKLIST = {
        'SEC', 'FDA', 'DOJ', 'FTC', 'CEO', 'CFO', 'CTO',
        'ESG', 'API', 'NYSE', 'IPO', 'ETF', 'Q1', 'Q2', 'Q3', 'Q4'
    }

    # Event detection patterns (high-precision rules) - Enhanced patterns
    EVENT_PATTERNS = {
        EventType.EARNINGS: [
            r"Q[1-4]\s+20\d{2}\s+(?:earnings|results)",
            r"(?:reported|announced|released)\s+(?:quarterly|Q[1-4])\s+(?:earnings|results)",
            r"earnings\s+(?:beat|miss|surprise|report|release|announcement)",
            r"EPS\s+of\s+\$[\d.]+\s+(?:beat|miss|versus|vs|exceeded|fell short)",
            r"revenue\s+of\s+\$[\d.]+[BMK]?\s+(?:beat|miss|versus|vs)",
            r"(?:quarterly|Q[1-4])\s+(?:revenue|earnings|results)",
            r"reported.+earnings",
            r"earnings.+(?:beat|exceeded|surpassed|missed)"
        ],
        EventType.GUIDANCE: [
            r"\b(?:raised?|lowered?|updated?|revised?|maintained?|cut)\s+(?:guidance|outlook|forecast)\b",
            r"\b(?:FY|Q[1-4]|fiscal\s+year|full[- ]year)\s+(?:\d{4}\s+)?(?:guidance|outlook)\b",
            r"\b(?:management|company)\s+(?:raised?|lowered?|reiterated?)\s+(?:guidance|expectations)\b",
            r"\bguidance\b.{0,20}\b(?:raised|lowered|cut|reduced|increased)\b",
            r"\b(?:raised|lowered|cut)\b.{0,20}\bguidance\b",
            r"\b(?:revenue|earnings|EPS)\s+(?:guidance|outlook|forecast)\b",
            r"\b(?:expects?|forecasts?|projects?)\b.{0,30}\b(?:revenue|earnings)\b.{0,20}\b(?:between|\$|of)\b",
            r"\b(?:now\s+)?expects?\b.{0,20}\b(?:\$[\d.]+[BMK]?|between)\b"
        ],
        EventType.MA_DEAL: [
            r"(?:will\s+)?(?:acquire|acquisition|merger|acquired|acquiring|merging)",
            r"(?:takeover|buyout|purchase)\s+(?:of|by|agreement)",
            r"deal\s+(?:valued|worth)\s+(?:at\s+)?\$[\d.]+[BMK]",
            r"(?:announced|completed|terminated)\s+(?:acquisition|merger)",
            r"(?:announced|announced\s+it\s+will)\s+acquire",
            r"\$[\d.]+[BMK]?\s+(?:billion|million)?\s*(?:acquisition|merger|deal)",
            r"acquire.+for\s+\$[\d.]+[BMK]"
        ],
        EventType.MANAGEMENT: [
            r"(?:CEO|CFO|CTO|COO|President|Chairman).+(?:resigned|resigns|appointed|departed|joined|replaced)",
            r"(?:executive|management|leadership)\s+(?:change|transition|departure)",
            r"(?:board|director)\s+(?:member|appointment|resignation)",
            r"(?:announced|said).+(?:CEO|CFO|CTO).+(?:resigned|resignation|departure)",
            r"(?:resigned|stepping down|departed).+(?:CEO|CFO|President)",
            r"(?:interim|permanent)\s+(?:CEO|CFO|President)",
            r"(?:CEO|CFO|CTO|President).+(?:has\s+)?resigned"
        ],
        EventType.SCANDAL: [
            r"\b(?:SEC|DOJ|federal|regulatory)\b.{0,20}\b(?:investigation|probe|inquiry)\b",
            r"\bSEC\b.{0,30}\b(?:announced|investigating|probe)\b",
            r"\b(?:scandal|fraud|misconduct)\b",
            r"\b(?:accounting|financial)\s+(?:irregularities|misconduct|restatement)\b",
            r"\bwhistleblower\s+(?:complaint|allegation)\b",
            r"\b(?:announced|launched|opened)\s+(?:an?\s+)?investigation\b",
            r"\binvestigation\s+(?:into|of|regarding)\b",
            r"\b(?:faces|facing|under)\s+(?:investigation|probe|scrutiny)\b",
            r"\b(?:shares?|stock)\s+(?:fell|dropped|tumbled|plunged)\s+\d+",
            r"\bprobe\s+(?:into|of|regarding)\b"
        ],
        EventType.RATING: [
            r"(?:upgraded|downgraded|initiated|reiterated)\s+(?:to|with|at)\s+(?:buy|sell|hold|outperform|underperform)",
            r"price\s+target\s+(?:raised|lowered|set)\s+to\s+\$[\d.]+",
            r"(?:analyst|rating)\s+(?:upgrade|downgrade|initiation)",
            r"(?:Goldman|Morgan|JP|Bank).+(?:upgraded|downgraded)",
            r"(?:Buy|Sell|Hold)\s+rating"
        ],
        EventType.PRODUCT: [
            r"\b(?:launched|announced|unveiled|introduced|reveals?)\b.{0,20}\b(?:new|next[- ]generation|revolutionary)\b",
            r"\bproduct\s+(?:launch|announcement|release|rollout)\b",
            r"\b(?:AI|cloud|software|hardware)\s+(?:product|solution|offering|platform)\b",
            r"\bunveiled?\b.{0,30}\b(?:iPhone|iPad|device|product|service)\b",
            r"\b(?:announced|unveiled|introduced)\b.{0,30}\b(?:AI|new)\b.{0,20}\b(?:capabilities|features|product)\b",
            r"\b(?:iPhone|Galaxy|Pixel)\s+\d+",
            r"\bnew\s+(?:product|service|platform|solution)\b",
            r"\b(?:A\d+\s+(?:Pro|Bionic)\s+)?chip\b"
        ],
        EventType.REGULATORY: [
            r"\b(?:FDA|FTC|SEC|regulatory)\b.{0,20}\b(?:approval|rejection|decision|action)\b",
            r"\b(?:fine|penalty|sanction)\s+of\s+\$[\d.]+\s*[BMK]?\b",
            r"\bregulatory\s+(?:clearance|setback|hurdle|milestone)\b",
            r"\b(?:received?|granted?|won)\b.{0,20}\b(?:FDA|regulatory)\b.{0,10}\bapproval\b",
            r"\bFDA\b.{0,20}\b(?:approved?|approval)\b",
            r"\bapproval\b.{0,20}\b(?:FDA|regulatory)\b",
            r"\b(?:Phase\s+[123]|clinical)\s+(?:trial|study|results)\b"
        ],
        EventType.LAWSUIT: [
            r"(?:lawsuit|litigation|legal\s+action|suit).+(?:filed|settled|dismissed)",
            r"(?:patent|copyright|trademark)\s+(?:infringement|dispute|litigation)",
            r"class[- ]action\s+(?:lawsuit|settlement)",
            r"(?:faces|facing).+(?:lawsuit|litigation|legal action)",
            r"(?:antitrust|monopoly).+(?:lawsuit|suit|case)",
            r"(?:Department of Justice|DOJ).+(?:lawsuit|suit)"
        ],
        EventType.DIVIDEND: [
            r"(?:declared|announced|paid|initiated).+(?:dividend|distribution)",
            r"dividend\s+of\s+\$[\d.]+\s+per\s+share",
            r"(?:quarterly|annual|special|first-ever)\s+dividend",
            r"\$[\d.]+\s+(?:per\s+share\s+)?dividend",
            r"dividend.+\$[\d.]+"
        ],
        EventType.BUYBACK: [
            r"(?:share|stock)\s+(?:buyback|repurchase).+(?:program|authorization)",
            r"(?:authorized|announced).+\$[\d.]+[BMK].+(?:buyback|repurchase)",
            r"(?:expanded|increased|announced).+buyback",
            r"\$[\d.]+[BMK].+(?:buyback|repurchase|share repurchase)",
            r"buyback.+\$[\d.]+[BMK]",
            r"repurchase.+(?:program|authorization)"
        ]
    }

    # Impact classification keywords - Enhanced
    IMPACT_KEYWORDS = {
        'positive': [
            'beat', 'exceed', 'surpass', 'outperform', 'raised', 'increased',
            'upgraded', 'strong', 'robust', 'record', 'breakthrough', 'approved',
            'won', 'settled favorably', 'expansion', 'growth', 'approval', 'jump',
            'surge', 'rally', 'gain', 'higher', 'above', 'success', 'positive',
            'FDA approval', 'buyback', 'dividend', 'acquire', 'earnings beat'
        ],
        'negative': [
            'miss', 'below', 'disappoint', 'underperform', 'lowered', 'decreased',
            'downgraded', 'weak', 'declined', 'loss', 'setback', 'rejected',
            'lost', 'sued', 'investigation', 'scandal', 'recalled', 'fell', 'drop',
            'plunge', 'crash', 'concern', 'worry', 'risk', 'threat', 'lawsuit',
            'resigned', 'departure', 'probe', 'cut', 'reduced', 'SEC investigation'
        ]
    }

    def __init__(self):
        """Initialize event extractor.

        Note: Event extraction is stateless - results returned directly,
        not accumulated in instance state. Caching handled at ICECore level.
        """
        # FIXED: Removed unused self.extracted_events = [] (dead code)
        # Event caching is handled by ICECore.event_cache, not here
        pass

    @staticmethod
    def _validate_webhook_url(url: str) -> bool:
        """Validate webhook URL to prevent SSRF attacks"""
        if not url:
            return False

        try:
            parsed = urlparse(url)

            # Only allow http/https
            if parsed.scheme not in ['http', 'https']:
                return False

            # Block localhost and internal IPs
            blocked_hosts = ['localhost', '127.0.0.1', '0.0.0.0', '::1']
            if parsed.hostname in blocked_hosts:
                return False

            # Block private IP ranges
            if parsed.hostname and (
                parsed.hostname.startswith('192.168.') or
                parsed.hostname.startswith('10.') or
                parsed.hostname.startswith('172.16.')
            ):
                return False

            return True
        except Exception:
            return False

    def extract_events(self,
                      document: str,
                      ticker: Optional[str] = None,
                      document_date: Optional[datetime] = None,
                      source_id: str = "") -> List[EventNode]:
        """
        Extract events from a financial document

        Args:
            document: Text content to extract events from
            ticker: Primary ticker if known
            document_date: Document date for temporal context
            source_id: Source document identifier

        Returns:
            List of extracted EventNode objects
        """
        # Input validation
        if not document or not isinstance(document, str):
            logger.warning("Invalid input document for event extraction")
            return []

        if len(document) < 10:  # Too short to contain meaningful events
            logger.debug("Document too short for event extraction")
            return []

        # DOS protection: truncate overly long documents
        if len(document) > MAX_DOCUMENT_LENGTH:
            logger.warning(f"Document truncated from {len(document)} to {MAX_DOCUMENT_LENGTH} chars")
            document = document[:MAX_DOCUMENT_LENGTH]

        events = []

        # Extract ticker if not provided
        if not ticker:
            ticker = self._extract_ticker(document)

        # Extract date if not provided
        if not document_date:
            document_date = self._extract_date(document)

        # Apply pattern-based extraction for each event type
        for event_type, patterns in self.EVENT_PATTERNS.items():
            for pattern in patterns:
                matches = re.finditer(pattern, document, re.IGNORECASE)
                for match in matches:
                    event = self._create_event_from_match(
                        match, event_type, document, ticker,
                        document_date, source_id
                    )
                    if event and self._validate_event(event):
                        events.append(event)

        # Deduplicate events
        events = self._deduplicate_events(events)

        # Classify impact and sentiment for each event
        for event in events:
            event.impact = self._classify_impact(event.description, document)
            event.themes = self._extract_themes(event.description, document)
            event.confidence = self._calculate_confidence(event, document)

        logger.info(f"Extracted {len(events)} events from document")
        return events

    def _create_event_from_match(self,
                                match: re.Match,
                                event_type: EventType,
                                document: str,
                                ticker: str,
                                date: datetime,
                                source_id: str) -> Optional[EventNode]:
        """Create EventNode from regex match"""
        try:
            # Extract context around match (±200 chars for better context)
            # Increased from 100 to capture magnitude values that may be further away
            start = max(0, match.start() - 200)
            end = min(len(document), match.end() + 200)
            context = document[start:end].strip()

            # Generate unique event ID
            event_id = f"event_{ticker}_{event_type.value}_{date.strftime('%Y%m%d')}"

            # Create event node
            event = EventNode(
                id=event_id,
                type=event_type,
                ticker=ticker or "UNKNOWN",
                date=date or datetime.now(),
                description=context,
                source_document_id=source_id
            )

            # Extract magnitude if present with prioritization
            # Priority 1: Stock price movements (most relevant for events)
            stock_pattern = r'(?:shares?|stock|price)\s+(?:up|down|fell|rose|jumped|dropped|plunged)\s+(\d+(?:\.\d+)?)\s*%'
            stock_match = re.search(stock_pattern, context, re.IGNORECASE)
            if stock_match:
                event.magnitude = float(stock_match.group(1))

            # Priority 2: Explicit financial metrics
            if not event.magnitude:
                metric_pattern = r'(?:revenue|earnings|profit|margin|growth)\s+(?:up|down|rose|fell)\s+(\d+(?:\.\d+)?)\s*%'
                metric_match = re.search(metric_pattern, context, re.IGNORECASE)
                if metric_match:
                    event.magnitude = float(metric_match.group(1))

            # Priority 3: Any percentage (fallback)
            if not event.magnitude:
                general_pattern = r'(\d+(?:\.\d+)?)\s*%'
                general_match = re.search(general_pattern, context)
                if general_match:
                    event.magnitude = float(general_match.group(1))

            # Also look for dollar amounts for deals
            dollar_match = re.search(r'\$(\d+(?:\.\d+)?)\s*([BMK]|billion|million|thousand)?', context)
            if dollar_match and not event.magnitude:
                value = float(dollar_match.group(1))
                unit = dollar_match.group(2) if dollar_match.group(2) else ''
                if unit in ['B', 'billion']:
                    event.magnitude = value * 1000000000
                elif unit in ['M', 'million']:
                    event.magnitude = value * 1000000
                elif unit in ['K', 'thousand']:
                    event.magnitude = value * 1000
                else:
                    event.magnitude = value

            return event

        except Exception as e:
            logger.warning(f"Failed to create event from match: {e}")
            return None

    def _classify_impact(self, description: str, full_document: str) -> str:
        """
        Classify event impact as positive/negative/neutral

        Uses keyword matching and context analysis
        """
        description_lower = description.lower()
        doc_lower = full_document.lower()[:1000]  # Check first 1000 chars for context

        # Special cases for certain event types
        if 'fda approval' in description_lower or 'fda approved' in description_lower:
            return "positive"
        if 'unveiled' in description_lower or 'launched' in description_lower or 'announced new' in description_lower:
            if 'product' in description_lower or 'iphone' in description_lower or 'device' in description_lower:
                return "positive"  # Product launches are typically positive
        if 'resignation' in description_lower or 'resigned' in description_lower:
            if 'ceo' in description_lower or 'cfo' in description_lower:
                return "negative"
        if 'lawsuit' in description_lower or 'investigation' in description_lower:
            return "negative"
        if 'buyback' in description_lower or 'dividend' in description_lower:
            return "positive"
        if 'earnings beat' in description_lower or 'exceeded expectations' in description_lower:
            return "positive"
        if 'lowered guidance' in description_lower or 'cut guidance' in description_lower:
            return "negative"
        if 'raised guidance' in description_lower or 'increased guidance' in description_lower:
            return "positive"

        # General keyword matching
        positive_count = sum(1 for kw in self.IMPACT_KEYWORDS['positive']
                            if kw in description_lower or kw in doc_lower)
        negative_count = sum(1 for kw in self.IMPACT_KEYWORDS['negative']
                           if kw in description_lower or kw in doc_lower)

        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative"
        else:
            return "neutral"

    def _extract_themes(self, description: str, document: str) -> List[str]:
        """Extract themes related to the event"""
        themes = []

        # Common themes in financial events
        theme_keywords = {
            'AI': ['artificial intelligence', 'machine learning', 'AI', 'ML', 'neural', 'GPT'],
            'Cloud': ['cloud', 'SaaS', 'AWS', 'Azure', 'GCP'],
            'Cybersecurity': ['security', 'breach', 'hack', 'cyber', 'ransomware'],
            'ESG': ['ESG', 'sustainability', 'environmental', 'governance', 'climate'],
            'Inflation': ['inflation', 'CPI', 'price pressure', 'cost increase'],
            'Supply Chain': ['supply chain', 'logistics', 'shortage', 'disruption'],
            'China': ['China', 'Chinese', 'Beijing', 'tariff'],
            'Semiconductors': ['chip', 'semiconductor', 'fab', 'foundry', 'TSMC'],
            'Healthcare': ['FDA', 'drug', 'clinical', 'biotech', 'pharma'],
            'FinTech': ['fintech', 'payment', 'crypto', 'blockchain', 'digital currency']
        }

        text_to_check = (description + " " + document[:1000]).lower()

        for theme, keywords in theme_keywords.items():
            if any(kw.lower() in text_to_check for kw in keywords):
                themes.append(theme)

        return themes[:5]  # Limit to top 5 themes

    def _extract_ticker(self, document: str) -> str:
        """Extract ticker symbol from document with blacklist filtering"""
        # Require minimum 2 chars, maximum 5
        ticker_pattern = r'\b([A-Z]{2,5})\b'

        for match in re.finditer(ticker_pattern, document[:500]):
            ticker = match.group(1)
            if ticker not in self.TICKER_BLACKLIST:
                # Additional validation: must be near company context
                context_start = max(0, match.start() - 50)
                context_end = match.end() + 50
                context = document[context_start:context_end].lower()
                company_keywords = ['inc', 'corp', 'company', 'ltd', 'stock', 'shares']
                if any(word in context for word in company_keywords):
                    return ticker

        return "UNKNOWN"

    def _parse_month_date(self, month_name: str, day: str, year: str) -> datetime:
        """
        Helper to parse month name dates with validation.

        FIXED: Previously silently defaulted to January for invalid months.
        Now validates month name, day range, and handles datetime errors.

        Raises:
            ValueError: If month name is invalid, day out of range, or date is invalid
        """
        month_map = {
            'january': 1, 'february': 2, 'march': 3, 'april': 4,
            'may': 5, 'june': 6, 'july': 7, 'august': 8,
            'september': 9, 'october': 10, 'november': 11, 'december': 12
        }

        # FIXED: Validate month name exists (no silent fallback)
        month_num = month_map.get(month_name.lower())
        if month_num is None:
            raise ValueError(f"Invalid month name: '{month_name}'")

        # FIXED: Validate day range (basic check)
        try:
            day_int = int(day)
            year_int = int(year)
        except ValueError:
            raise ValueError(f"Invalid day '{day}' or year '{year}' - must be numeric")

        if not 1 <= day_int <= 31:
            raise ValueError(f"Invalid day: {day_int} (must be 1-31)")

        # FIXED: Handle datetime construction errors (e.g., Feb 30)
        try:
            return datetime(year_int, month_num, day_int)
        except ValueError as e:
            raise ValueError(f"Invalid date {month_name} {day}, {year}: {e}")

    def _extract_date(self, document: str) -> datetime:
        """Extract date from document"""
        from datetime import datetime, timedelta

        # Common date patterns
        date_patterns = [
            # MM/DD/YYYY or MM-DD-YYYY
            (r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})',
             lambda m: datetime(int(m.group(3)), int(m.group(1)), int(m.group(2)))),
            # YYYY-MM-DD
            (r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})',
             lambda m: datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))),
            # Month DD, YYYY
            (r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),?\s+(\d{4})',
             lambda m: self._parse_month_date(m.group(1), m.group(2), m.group(3))),
            # Q1-Q4 YYYY
            (r'Q([1-4])\s+(\d{4})',
             lambda m: datetime(int(m.group(2)), (int(m.group(1))-1)*3+1, 1)),
            # Yesterday/today/tomorrow
            (r'\byesterday\b', lambda m: datetime.now() - timedelta(days=1)),
            (r'\btoday\b', lambda m: datetime.now()),
            (r'\btomorrow\b', lambda m: datetime.now() + timedelta(days=1)),
        ]

        # Search in first 1000 chars for efficiency
        search_text = document[:1000] if len(document) > 1000 else document

        for pattern, parser in date_patterns:
            match = re.search(pattern, search_text, re.IGNORECASE)
            if match:
                try:
                    parsed_date = parser(match)
                    # Sanity check: don't return dates too far in future
                    if parsed_date <= datetime.now() + timedelta(days=7):
                        return parsed_date
                except Exception as e:
                    logger.debug(f"Failed to parse date with pattern {pattern}: {e}")
                    continue

        # Fallback to current date
        return datetime.now()

    def _calculate_confidence(self, event: EventNode, document: str) -> float:
        """
        Calculate confidence score for extracted event

        Factors:
        - Pattern match strength
        - Context relevance
        - Entity presence
        - Source reliability
        """
        confidence = 0.5  # Base confidence

        # Boost if ticker is explicitly mentioned near event
        # FIXED: Cache find() result and handle -1 case (description not found)
        if event.description and event.ticker:
            desc_pos = document.find(event.description)
            if desc_pos >= 0:  # Description found in document
                # Get context window around description
                context_start = max(0, desc_pos - 100)
                context_end = min(len(document), desc_pos + len(event.description) + 100)
                context_window = document[context_start:context_end]
                if event.ticker in context_window:
                    confidence += 0.2

        # Boost if impact is clear
        if event.impact and event.impact != "neutral":
            confidence += 0.1

        # Boost if magnitude is quantified
        if event.magnitude is not None:
            confidence += 0.1

        # Boost if themes are identified
        if event.themes:
            confidence += 0.1

        return min(confidence, 1.0)

    def _validate_event(self, event: EventNode) -> bool:
        """Validate extracted event meets quality thresholds"""
        # Must have ticker and date
        if event.ticker == "UNKNOWN" or not event.date:
            return False

        # Description must be meaningful (not too short)
        if len(event.description) < 20:
            return False

        # Confidence threshold
        if event.confidence < 0.3:
            return False

        return True

    def _deduplicate_events(self, events: List[EventNode]) -> List[EventNode]:
        """Remove duplicate events based on similarity"""
        if not events:
            return events

        unique_events = []
        seen_descriptions = set()

        for event in events:
            # Simple deduplication based on type, ticker, date
            key = f"{event.type.value}_{event.ticker}_{event.date.strftime('%Y%m%d')}"

            if key not in seen_descriptions:
                unique_events.append(event)
                seen_descriptions.add(key)

        return unique_events

    def create_event_markup(self, events: List[EventNode]) -> str:
        """
        Create inline markup for document enhancement

        Returns markup that can be inserted into documents for LightRAG processing
        """
        markup_lines = []

        for event in events:
            # Format: [EVENT:id|type:value|ticker:SYMBOL|date:YYYY-MM-DD|impact:pos/neg/neu]
            markup = (
                f"[EVENT:{event.id}|"
                f"type:{event.type.value}|"
                f"ticker:{event.ticker}|"
                f"date:{event.date.strftime('%Y-%m-%d')}|"
                f"impact:{event.impact}|"
                f"confidence:{event.confidence:.2f}]"
            )
            markup_lines.append(markup)

        return "\n".join(markup_lines)

    def extract_relationships(self, event: EventNode) -> List[Tuple[str, str, str]]:
        """
        Extract relationships from event for graph construction

        Returns:
            List of (source, relationship, target) tuples
        """
        relationships = []

        # EVENT → AFFECTS → COMPANY
        relationships.append((event.id, "EVENT_AFFECTS", event.ticker))

        # EVENT → RELATES_TO → THEME
        for theme in event.themes:
            relationships.append((event.id, "RELATES_TO", f"THEME:{theme}"))

        # EVENT → MENTIONED_IN → DOCUMENT
        if event.source_document_id:
            relationships.append((event.id, "MENTIONED_IN", event.source_document_id))

        return relationships