# /Users/royyeo/Library/CloudStorage/OneDrive-NationalUniversityofSingapore/Capstone Project/ice_data_ingestion/news_processor.py
# News data processor for ICE knowledge graph integration
# Converts financial news articles into graph edges and entities for LightRAG processing
# RELEVANT FILES: news_apis.py, src/ice_lightrag/ice_rag.py, UI/ice_ui_v17.py, __init__.py

"""
News Processor for ICE Knowledge Graph Integration

This module processes financial news articles from various APIs and converts them into
graph-ready format for the ICE LightRAG system. It extracts entities, relationships,
and sentiment signals to build the investment knowledge graph.

Key Functions:
- Entity extraction from news content (companies, people, places, topics)
- Relationship identification (dependencies, impacts, mentions, correlations)
- Sentiment-driven edge weighting
- Temporal decay for edge freshness
- Source attribution and traceability

Graph Edge Types Generated:
- mentions: When news article discusses a ticker/company
- impacts: When news suggests causal relationships
- correlates_with: When multiple entities mentioned in same context
- exposed_to: Risk/opportunity exposure relationships
- sentiment_affects: Sentiment-driven market impacts

Integration Points:
- LightRAG document processing pipeline
- ICE knowledge graph structure
- Streamlit UI for real-time updates
- Investment analysis workflows
"""

from typing import Dict, List, Optional, Any, Tuple, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import logging
import re
import json
from pathlib import Path
import hashlib

from .news_apis import NewsArticle, NewsAPIProvider, SentimentScore

logger = logging.getLogger(__name__)

@dataclass
class GraphEntity:
    """Represents an entity in the ICE knowledge graph"""
    name: str
    entity_type: str  # company, person, topic, risk, kpi, etc.
    ticker: Optional[str] = None
    aliases: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'type': self.entity_type,
            'ticker': self.ticker,
            'aliases': list(self.aliases),
            'metadata': self.metadata
        }

@dataclass
class GraphEdge:
    """Represents a relationship edge in the ICE knowledge graph"""
    source_entity: str
    target_entity: str
    relationship_type: str  # mentions, impacts, depends_on, exposed_to, etc.
    weight: float  # 0.0 to 1.0
    days_ago: int
    is_positive: bool
    confidence_score: float  # 0.0 to 1.0
    source_doc_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'source': self.source_entity,
            'target': self.target_entity,
            'type': self.relationship_type,
            'weight': self.weight,
            'days_ago': self.days_ago,
            'is_positive': self.is_positive,
            'confidence': self.confidence_score,
            'source_doc_id': self.source_doc_id,
            'metadata': self.metadata
        }

class EntityExtractor:
    """Extracts and standardizes entities from news content"""
    
    def __init__(self):
        # Common financial entities and patterns
        self.ticker_pattern = re.compile(r'\b[A-Z]{1,5}\b(?=\s|$|[.,!?])')
        self.company_patterns = [
            re.compile(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:Inc|Corp|Corporation|Company|Ltd|Limited|LLC|AG|SA|SE|PLC)\b'),
            re.compile(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:Group|Holdings|Partners|Ventures|Capital|Fund|Management)\b'),
        ]
        
        # Financial topics and themes
        self.financial_topics = {
            'AI', 'Artificial Intelligence', 'Machine Learning', 'Cryptocurrency', 'Bitcoin', 'Blockchain',
            'China Risk', 'Supply Chain', 'Inflation', 'Interest Rates', 'Federal Reserve', 'FDA Approval',
            'Earnings', 'Revenue', 'Guidance', 'M&A', 'Merger', 'Acquisition', 'IPO', 'Restructuring',
            'Regulation', 'Compliance', 'ESG', 'Climate Change', 'Energy Transition', 'Cybersecurity'
        }
        
        # Risk keywords
        self.risk_keywords = {
            'risk', 'exposure', 'vulnerability', 'threat', 'concern', 'uncertainty', 'volatility',
            'downturn', 'recession', 'crisis', 'disruption', 'challenge', 'headwind', 'pressure'
        }
        
        # Opportunity keywords  
        self.opportunity_keywords = {
            'opportunity', 'growth', 'expansion', 'innovation', 'breakthrough', 'upside', 'potential',
            'momentum', 'recovery', 'improvement', 'strength', 'advantage', 'tailwind', 'catalyst'
        }
    
    def extract_tickers(self, text: str) -> Set[str]:
        """Extract ticker symbols from text"""
        tickers = set()
        
        # Find ticker patterns
        matches = self.ticker_pattern.findall(text)
        
        # Filter out common false positives
        common_words = {'THE', 'AND', 'FOR', 'ARE', 'BUT', 'NOT', 'YOU', 'ALL', 'CAN', 'HER', 'WAS', 'ONE', 'OUR', 'OUT', 'DAY', 'GET', 'HAS', 'HIM', 'HIS', 'HOW', 'ITS', 'NEW', 'NOW', 'OLD', 'SEE', 'TWO', 'WHO', 'BOY', 'DID', 'USE', 'WAY', 'SHE', 'MAY', 'SAY'}
        
        for match in matches:
            if match not in common_words and len(match) <= 5:
                tickers.add(match)
        
        return tickers
    
    def extract_companies(self, text: str) -> Set[str]:
        """Extract company names from text"""
        companies = set()
        
        for pattern in self.company_patterns:
            matches = pattern.findall(text)
            companies.update(matches)
        
        return companies
    
    def extract_topics(self, text: str) -> Set[str]:
        """Extract financial topics and themes"""
        topics = set()
        text_lower = text.lower()
        
        for topic in self.financial_topics:
            if topic.lower() in text_lower:
                topics.add(topic)
        
        return topics
    
    def extract_sentiment_entities(self, text: str, sentiment_score: Optional[float]) -> Tuple[Set[str], Set[str]]:
        """Extract risk and opportunity entities based on sentiment and keywords"""
        risks = set()
        opportunities = set()
        text_lower = text.lower()
        
        # Look for risk-related content
        for keyword in self.risk_keywords:
            if keyword in text_lower:
                # Extract context around risk keyword
                context_match = re.search(rf'(\w+(?:\s+\w+){{0,3}})\s+{keyword}', text_lower)
                if context_match:
                    risk_context = context_match.group(1).title()
                    risks.add(f"{risk_context} Risk")
        
        # Look for opportunity-related content
        for keyword in self.opportunity_keywords:
            if keyword in text_lower:
                context_match = re.search(rf'(\w+(?:\s+\w+){{0,3}})\s+{keyword}', text_lower)
                if context_match:
                    opportunity_context = context_match.group(1).title()
                    opportunities.add(f"{opportunity_context} Opportunity")
        
        return risks, opportunities

class RelationshipExtractor:
    """Extracts relationships between entities from news content"""
    
    def __init__(self):
        # Relationship patterns
        self.dependency_patterns = [
            re.compile(r'(\w+)\s+(?:depends on|relies on|needs|requires)\s+(\w+)', re.IGNORECASE),
            re.compile(r'(\w+)\s+(?:supplier|vendor|partner)\s+(\w+)', re.IGNORECASE),
        ]
        
        self.impact_patterns = [
            re.compile(r'(\w+)\s+(?:affects|impacts|influences|drives)\s+(\w+)', re.IGNORECASE),
            re.compile(r'(\w+)\s+(?:could|may|might)\s+(?:hurt|harm|benefit|help)\s+(\w+)', re.IGNORECASE),
        ]
        
        self.competition_patterns = [
            re.compile(r'(\w+)\s+(?:competes with|rivals|versus)\s+(\w+)', re.IGNORECASE),
            re.compile(r'(\w+)\s+(?:and|vs\.?)\s+(\w+)\s+(?:competition|rival)', re.IGNORECASE),
        ]
    
    def extract_dependencies(self, text: str, entities: Set[str]) -> List[Tuple[str, str, float]]:
        """Extract dependency relationships"""
        dependencies = []
        
        for pattern in self.dependency_patterns:
            matches = pattern.findall(text)
            for source, target in matches:
                if source in entities and target in entities:
                    dependencies.append((source, target, 0.8))  # High confidence for explicit dependencies
        
        return dependencies
    
    def extract_impacts(self, text: str, entities: Set[str]) -> List[Tuple[str, str, float]]:
        """Extract impact relationships"""
        impacts = []
        
        for pattern in self.impact_patterns:
            matches = pattern.findall(text)
            for source, target in matches:
                if source in entities and target in entities:
                    impacts.append((source, target, 0.6))  # Medium confidence for impacts
        
        return impacts
    
    def extract_mentions(self, text: str, entities: Set[str]) -> List[Tuple[str, str, float]]:
        """Extract co-mention relationships"""
        mentions = []
        entity_list = list(entities)
        
        # Create mention relationships between entities appearing in same article
        for i, entity1 in enumerate(entity_list):
            for entity2 in entity_list[i+1:]:
                if entity1.lower() in text.lower() and entity2.lower() in text.lower():
                    mentions.append((entity1, entity2, 0.4))  # Lower confidence for co-mentions
        
        return mentions

class NewsProcessor:
    """Main processor for converting news articles to graph data"""
    
    def __init__(self, cache_dir: str = "user_data/news_processing"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.entity_extractor = EntityExtractor()
        self.relationship_extractor = RelationshipExtractor()
        
        # Entity standardization cache
        self.entity_cache = self._load_entity_cache()
    
    def _load_entity_cache(self) -> Dict[str, GraphEntity]:
        """Load previously extracted entities from cache"""
        cache_file = self.cache_dir / "entity_cache.json"
        if not cache_file.exists():
            return {}
        
        try:
            with open(cache_file, 'r') as f:
                cache_data = json.load(f)
            
            entities = {}
            for key, data in cache_data.items():
                entity = GraphEntity(
                    name=data['name'],
                    entity_type=data['type'],
                    ticker=data.get('ticker'),
                    aliases=set(data.get('aliases', [])),
                    metadata=data.get('metadata', {})
                )
                entities[key] = entity
            
            return entities
            
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Failed to load entity cache: {e}")
            return {}
    
    def _save_entity_cache(self):
        """Save entity cache to disk"""
        cache_file = self.cache_dir / "entity_cache.json"
        
        cache_data = {}
        for key, entity in self.entity_cache.items():
            cache_data[key] = entity.to_dict()
        
        try:
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save entity cache: {e}")
    
    def _generate_doc_id(self, article: NewsArticle) -> str:
        """Generate unique document ID for an article"""
        content_hash = hashlib.md5(f"{article.url}_{article.published_at}".encode()).hexdigest()[:8]
        return f"{article.provider.value}_{content_hash}"
    
    def _calculate_temporal_weight(self, published_at: datetime) -> Tuple[float, int]:
        """Calculate temporal weight and days_ago for an article"""
        now = datetime.now()
        if published_at.tzinfo is None:
            published_at = published_at.replace(tzinfo=None)
        if now.tzinfo is not None:
            now = now.replace(tzinfo=None)
        
        time_diff = now - published_at
        days_ago = max(0, time_diff.days)
        
        # Exponential decay: weight decreases over time
        # Recent news (< 1 day): weight ~1.0
        # Week old news: weight ~0.5
        # Month old news: weight ~0.1
        decay_factor = 0.1  # Controls decay rate
        temporal_weight = max(0.1, 1.0 * (1 - decay_factor) ** days_ago)
        
        return temporal_weight, days_ago
    
    def process_article(self, article: NewsArticle) -> Tuple[List[GraphEntity], List[GraphEdge]]:
        """Process a single news article into graph entities and edges"""
        entities = []
        edges = []
        
        # Generate document ID
        doc_id = self._generate_doc_id(article)
        
        # Extract all text content
        full_text = f"{article.title} {article.content}"
        
        # Extract entities
        tickers = self.entity_extractor.extract_tickers(full_text)
        companies = self.entity_extractor.extract_companies(full_text)
        topics = self.entity_extractor.extract_topics(full_text)
        risks, opportunities = self.entity_extractor.extract_sentiment_entities(full_text, article.sentiment_score)
        
        # Create entity objects
        all_entity_names = set()
        
        # Process tickers
        for ticker in tickers:
            entity_key = f"ticker_{ticker}"
            if entity_key not in self.entity_cache:
                self.entity_cache[entity_key] = GraphEntity(
                    name=ticker,
                    entity_type="ticker",
                    ticker=ticker,
                    metadata={"first_seen": datetime.now().isoformat()}
                )
            entities.append(self.entity_cache[entity_key])
            all_entity_names.add(ticker)
        
        # Process companies
        for company in companies:
            entity_key = f"company_{company.lower()}"
            if entity_key not in self.entity_cache:
                self.entity_cache[entity_key] = GraphEntity(
                    name=company,
                    entity_type="company",
                    metadata={"first_seen": datetime.now().isoformat()}
                )
            entities.append(self.entity_cache[entity_key])
            all_entity_names.add(company)
        
        # Process topics
        for topic in topics:
            entity_key = f"topic_{topic.lower()}"
            if entity_key not in self.entity_cache:
                self.entity_cache[entity_key] = GraphEntity(
                    name=topic,
                    entity_type="topic",
                    metadata={"first_seen": datetime.now().isoformat()}
                )
            entities.append(self.entity_cache[entity_key])
            all_entity_names.add(topic)
        
        # Process risks
        for risk in risks:
            entity_key = f"risk_{risk.lower()}"
            if entity_key not in self.entity_cache:
                self.entity_cache[entity_key] = GraphEntity(
                    name=risk,
                    entity_type="risk",
                    metadata={"first_seen": datetime.now().isoformat()}
                )
            entities.append(self.entity_cache[entity_key])
            all_entity_names.add(risk)
        
        # Process opportunities
        for opportunity in opportunities:
            entity_key = f"opportunity_{opportunity.lower()}"
            if entity_key not in self.entity_cache:
                self.entity_cache[entity_key] = GraphEntity(
                    name=opportunity,
                    entity_type="opportunity",
                    metadata={"first_seen": datetime.now().isoformat()}
                )
            entities.append(self.entity_cache[entity_key])
            all_entity_names.add(opportunity)
        
        # Calculate temporal properties
        temporal_weight, days_ago = self._calculate_temporal_weight(article.published_at)
        
        # Extract relationships
        dependencies = self.relationship_extractor.extract_dependencies(full_text, all_entity_names)
        impacts = self.relationship_extractor.extract_impacts(full_text, all_entity_names)
        mentions = self.relationship_extractor.extract_mentions(full_text, all_entity_names)
        
        # Create edges
        confidence = article.confidence if article.confidence else 0.7
        is_positive = article.sentiment_score > 0 if article.sentiment_score else True
        
        # Dependency edges
        for source, target, rel_confidence in dependencies:
            edge = GraphEdge(
                source_entity=source,
                target_entity=target,
                relationship_type="depends_on",
                weight=temporal_weight * rel_confidence,
                days_ago=days_ago,
                is_positive=is_positive,
                confidence_score=confidence * rel_confidence,
                source_doc_id=doc_id,
                metadata={
                    "article_title": article.title,
                    "article_url": article.url,
                    "provider": article.provider.value,
                    "sentiment_score": article.sentiment_score
                }
            )
            edges.append(edge)
        
        # Impact edges
        for source, target, rel_confidence in impacts:
            edge = GraphEdge(
                source_entity=source,
                target_entity=target,
                relationship_type="impacts",
                weight=temporal_weight * rel_confidence,
                days_ago=days_ago,
                is_positive=is_positive,
                confidence_score=confidence * rel_confidence,
                source_doc_id=doc_id,
                metadata={
                    "article_title": article.title,
                    "article_url": article.url,
                    "provider": article.provider.value,
                    "sentiment_score": article.sentiment_score
                }
            )
            edges.append(edge)
        
        # Mention edges (co-occurrence)
        for source, target, rel_confidence in mentions:
            edge = GraphEdge(
                source_entity=source,
                target_entity=target,
                relationship_type="mentions",
                weight=temporal_weight * rel_confidence * 0.5,  # Lower weight for mentions
                days_ago=days_ago,
                is_positive=is_positive,
                confidence_score=confidence * rel_confidence * 0.5,
                source_doc_id=doc_id,
                metadata={
                    "article_title": article.title,
                    "article_url": article.url,
                    "provider": article.provider.value,
                    "sentiment_score": article.sentiment_score
                }
            )
            edges.append(edge)
        
        # Create direct ticker-to-news edges for main ticker
        if article.ticker and article.ticker in all_entity_names:
            for entity_name in all_entity_names:
                if entity_name != article.ticker:
                    edge = GraphEdge(
                        source_entity=article.ticker,
                        target_entity=entity_name,
                        relationship_type="exposed_to" if "risk" in entity_name.lower() else "mentions",
                        weight=temporal_weight * confidence,
                        days_ago=days_ago,
                        is_positive=is_positive,
                        confidence_score=confidence,
                        source_doc_id=doc_id,
                        metadata={
                            "article_title": article.title,
                            "article_url": article.url,
                            "provider": article.provider.value,
                            "sentiment_score": article.sentiment_score
                        }
                    )
                    edges.append(edge)
        
        return entities, edges
    
    def process_articles(self, articles: List[NewsArticle]) -> Tuple[List[GraphEntity], List[GraphEdge]]:
        """Process multiple articles into graph data"""
        all_entities = []
        all_edges = []
        
        for article in articles:
            try:
                entities, edges = self.process_article(article)
                all_entities.extend(entities)
                all_edges.extend(edges)
            except Exception as e:
                logger.warning(f"Failed to process article {article.title}: {e}")
                continue
        
        # Save entity cache
        self._save_entity_cache()
        
        logger.info(f"Processed {len(articles)} articles into {len(all_entities)} entities and {len(all_edges)} edges")
        return all_entities, all_edges
    
    def export_to_lightrag_format(self, articles: List[NewsArticle]) -> str:
        """Export articles as text document for LightRAG processing"""
        doc_parts = []
        
        for article in articles:
            # Create structured document format for LightRAG
            doc_content = f"""
FINANCIAL NEWS ARTICLE
Title: {article.title}
Source: {article.source} ({article.provider.value})
Date: {article.published_at.strftime('%Y-%m-%d %H:%M:%S')}
URL: {article.url}
Ticker: {article.ticker or 'N/A'}
Sentiment: {article.sentiment_score or 'N/A'} ({article.sentiment_label.name if article.sentiment_label else 'N/A'})
Confidence: {article.confidence or 'N/A'}

Content:
{article.content}

Keywords: {', '.join(article.keywords) if article.keywords else 'N/A'}
Entities: {', '.join(article.entities) if article.entities else 'N/A'}

---
"""
            doc_parts.append(doc_content)
        
        return '\n'.join(doc_parts)
    
    def get_entity_statistics(self) -> Dict[str, Any]:
        """Get statistics about processed entities"""
        entity_types = {}
        for entity in self.entity_cache.values():
            entity_types[entity.entity_type] = entity_types.get(entity.entity_type, 0) + 1
        
        return {
            'total_entities': len(self.entity_cache),
            'entity_types': entity_types,
            'cache_location': str(self.cache_dir / "entity_cache.json")
        }