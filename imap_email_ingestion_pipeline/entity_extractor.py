# imap_email_ingestion_pipeline/entity_extractor.py
# Intelligent entity extraction for financial emails and attachments
# Extracts tickers, companies, people, metrics, dates with confidence scoring
# RELEVANT FILES: attachment_processor.py, graph_builder.py, ice_integrator.py

import re
import logging
from typing import Dict, List, Any, Optional, Tuple, Set
from datetime import datetime, timedelta
import json
from pathlib import Path

# NLP imports
try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    logging.warning("spaCy not available - using regex-based extraction")

class EntityExtractor:
    def __init__(self, config_path: str = "./config"):
        self.logger = logging.getLogger(__name__)
        self.config_path = Path(config_path)
        self.config_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize NLP model if available
        self.nlp = None
        if SPACY_AVAILABLE:
            try:
                self.nlp = spacy.load("en_core_web_sm")
                self.logger.info("spaCy model loaded successfully")
            except OSError:
                self.logger.warning("spaCy English model not found - install with: python -m spacy download en_core_web_sm")
        
        # Load configuration data
        self.tickers = self._load_ticker_list()
        self.companies = self._load_company_aliases()
        self.financial_metrics = self._load_financial_patterns()
        self.sender_profiles = self._load_sender_profiles()
        
        # Regex patterns for financial entities
        self._compile_patterns()
    
    def _load_ticker_list(self) -> Set[str]:
        """Load known ticker symbols"""
        ticker_file = self.config_path / "tickers.json"
        
        if ticker_file.exists():
            try:
                with open(ticker_file, 'r') as f:
                    return set(json.load(f))
            except Exception as e:
                self.logger.warning(f"Failed to load ticker list: {e}")
        
        # Default major tickers if file doesn't exist
        default_tickers = {
            # Tech giants
            'AAPL', 'MSFT', 'GOOGL', 'GOOG', 'AMZN', 'TSLA', 'META', 'NFLX', 'NVDA', 'CRM',
            # Financial
            'JPM', 'BAC', 'WFC', 'GS', 'MS', 'C', 'BRK.B', 'V', 'MA', 'AXP',
            # Healthcare
            'JNJ', 'UNH', 'PFE', 'ABBV', 'MRK', 'TMO', 'ABT', 'LLY', 'DHR', 'BMY',
            # Consumer
            'PG', 'KO', 'PEP', 'WMT', 'HD', 'MCD', 'DIS', 'NKE', 'SBUX', 'COST',
            # Industrial
            'BA', 'CAT', 'GE', 'MMM', 'UPS', 'HON', 'RTX', 'LMT', 'UNP', 'FDX',
            # Energy
            'XOM', 'CVX', 'COP', 'SLB', 'EOG', 'PXD', 'KMI', 'OXY', 'PSX', 'VLO'
        }
        
        # Save default list
        try:
            with open(ticker_file, 'w') as f:
                json.dump(list(default_tickers), f, indent=2)
        except Exception as e:
            self.logger.warning(f"Failed to save ticker list: {e}")
        
        return default_tickers
    
    def _load_company_aliases(self) -> Dict[str, str]:
        """Load company name to ticker mappings"""
        alias_file = self.config_path / "company_aliases.json"
        
        if alias_file.exists():
            try:
                with open(alias_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.warning(f"Failed to load company aliases: {e}")
        
        # Default aliases
        default_aliases = {
            'apple': 'AAPL',
            'apple inc': 'AAPL',
            'microsoft': 'MSFT',
            'microsoft corporation': 'MSFT',
            'amazon': 'AMZN',
            'amazon.com': 'AMZN',
            'google': 'GOOGL',
            'alphabet': 'GOOGL',
            'tesla': 'TSLA',
            'tesla motors': 'TSLA',
            'nvidia': 'NVDA',
            'nvidia corporation': 'NVDA',
            'meta': 'META',
            'facebook': 'META',
            'netflix': 'NFLX',
            'jpmorgan': 'JPM',
            'jpmorgan chase': 'JPM',
            'bank of america': 'BAC',
            'goldman sachs': 'GS',
            'morgan stanley': 'MS',
            'berkshire hathaway': 'BRK.B',
            'johnson & johnson': 'JNJ',
            'coca cola': 'KO',
            'coca-cola': 'KO',
            'walmart': 'WMT',
            'boeing': 'BA',
            'exxon mobil': 'XOM',
            'exxonmobil': 'XOM'
        }
        
        try:
            with open(alias_file, 'w') as f:
                json.dump(default_aliases, f, indent=2)
        except Exception as e:
            self.logger.warning(f"Failed to save company aliases: {e}")
        
        return default_aliases
    
    def _load_financial_patterns(self) -> Dict[str, List[str]]:
        """Load financial metric patterns"""
        return {
            'price_targets': [
                r'price target.*?\$?(\d+(?:\.\d{2})?)',
                r'pt.*?\$?(\d+(?:\.\d{2})?)',
                r'target.*?\$?(\d+(?:\.\d{2})?)'
            ],
            'ratings': [
                r'\b(buy|sell|hold|outperform|underperform|overweight|underweight|neutral)\b',
                r'\b(strong buy|strong sell|market perform)\b',
                r'\b(initiated|upgraded|downgraded|maintained|reiterated)\b'
            ],
            'financials': [
                r'eps.*?\$?(\d+(?:\.\d{2})?)',
                r'earnings per share.*?\$?(\d+(?:\.\d{2})?)',
                r'revenue.*?\$?(\d+(?:\.\d+)?[bmk]?)',
                r'sales.*?\$?(\d+(?:\.\d+)?[bmk]?)',
                r'ebitda.*?\$?(\d+(?:\.\d+)?[bmk]?)',
                r'p/e ratio.*?(\d+(?:\.\d+)?)',
                r'pe.*?(\d+(?:\.\d+)?)',
                r'market cap.*?\$?(\d+(?:\.\d+)?[bmk]?)',
                r'guidance.*?\$?(\d+(?:\.\d+)?[bmk]?)'
            ],
            'percentages': [
                r'(\d+(?:\.\d+)?%)',
                r'(\d+(?:\.\d+)? percent)'
            ],
            'dates': [
                r'q[1-4] \d{4}',
                r'\d{4} q[1-4]',
                r'\d{1,2}/\d{1,2}/\d{2,4}',
                r'\d{4}-\d{2}-\d{2}',
                r'(january|february|march|april|may|june|july|august|september|october|november|december) \d{1,2},? \d{4}',
                r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec) \d{1,2},? \d{4}'
            ]
        }
    
    def _load_sender_profiles(self) -> Dict[str, Dict[str, Any]]:
        """Load sender reputation profiles"""
        profile_file = self.config_path / "sender_profiles.json"
        
        if profile_file.exists():
            try:
                with open(profile_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.warning(f"Failed to load sender profiles: {e}")
        
        # Default high-value senders
        default_profiles = {
            '@bloomberg.com': {
                'reputation': 95,
                'categories': ['news', 'market_data'],
                'priority_boost': 30
            },
            '@reuters.com': {
                'reputation': 90,
                'categories': ['news', 'analysis'],
                'priority_boost': 25
            },
            '@wsj.com': {
                'reputation': 90,
                'categories': ['news', 'analysis'],
                'priority_boost': 25
            },
            '@ft.com': {
                'reputation': 85,
                'categories': ['news', 'analysis'],
                'priority_boost': 20
            },
            '@cnbc.com': {
                'reputation': 80,
                'categories': ['news', 'commentary'],
                'priority_boost': 15
            },
            '@marketwatch.com': {
                'reputation': 75,
                'categories': ['news', 'market_data'],
                'priority_boost': 10
            },
            'research': {
                'reputation': 85,
                'categories': ['research', 'analysis'],
                'priority_boost': 20
            },
            'analyst': {
                'reputation': 80,
                'categories': ['research', 'analysis'],
                'priority_boost': 15
            }
        }
        
        try:
            with open(profile_file, 'w') as f:
                json.dump(default_profiles, f, indent=2)
        except Exception as e:
            self.logger.warning(f"Failed to save sender profiles: {e}")
        
        return default_profiles
    
    def _compile_patterns(self):
        """Compile regex patterns for performance"""
        self.compiled_patterns = {}
        
        for category, patterns in self.financial_metrics.items():
            self.compiled_patterns[category] = [
                re.compile(pattern, re.IGNORECASE) for pattern in patterns
            ]
        
        # Ticker pattern - match 1-5 letter codes that are likely tickers
        self.ticker_pattern = re.compile(
            r'\b([A-Z]{1,5}(?:\.[A-Z]{1,2})?)\b'
        )
        
        # Currency patterns
        self.currency_pattern = re.compile(
            r'\$[\d,]+(?:\.\d{2})?(?:[kmb](?:illion)?)?',
            re.IGNORECASE
        )
        
        # Email pattern for sender analysis
        self.email_pattern = re.compile(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        )
    
    def extract_entities(self, text: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Extract all entities from text with confidence scores"""
        if not text or not text.strip():
            return self._empty_result()
        
        text = text.strip()
        metadata = metadata or {}
        
        # Extract different entity types
        entities = {
            'tickers': self._extract_tickers(text),
            'companies': self._extract_companies(text),
            'people': self._extract_people(text),
            'financial_metrics': self._extract_financial_metrics(text),
            'dates': self._extract_dates(text),
            'prices': self._extract_prices(text),
            'ratings': self._extract_ratings(text),
            'topics': self._extract_topics(text),
            'sentiment': self._analyze_sentiment(text)
        }
        
        # Add context from metadata
        if metadata:
            entities['context'] = self._extract_context(metadata)
        
        # Calculate overall confidence
        entities['confidence'] = self._calculate_confidence(entities, text)
        
        return entities
    
    def _extract_tickers(self, text: str) -> List[Dict[str, Any]]:
        """Extract stock tickers with confidence scores"""
        tickers = []
        matches = self.ticker_pattern.findall(text)
        
        for match in matches:
            # Skip common false positives
            if match.upper() in ['THE', 'AND', 'FOR', 'WITH', 'FROM', 'THIS', 'THAT', 'ARE', 'HAS', 'WAS', 'CAN']:
                continue
            
            # Check if it's a known ticker
            if match.upper() in self.tickers:
                confidence = 0.95
                ticker_info = {
                    'ticker': match.upper(),
                    'confidence': confidence,
                    'source': 'known_ticker',
                    'context': self._get_surrounding_context(text, match)
                }
                tickers.append(ticker_info)
            elif len(match) <= 4 and match.isupper():
                # Possible ticker but not in known list
                confidence = 0.6
                ticker_info = {
                    'ticker': match.upper(),
                    'confidence': confidence,
                    'source': 'pattern_match',
                    'context': self._get_surrounding_context(text, match)
                }
                tickers.append(ticker_info)
        
        # Remove duplicates
        seen_tickers = set()
        unique_tickers = []
        for ticker in tickers:
            if ticker['ticker'] not in seen_tickers:
                unique_tickers.append(ticker)
                seen_tickers.add(ticker['ticker'])
        
        return unique_tickers
    
    def _extract_companies(self, text: str) -> List[Dict[str, Any]]:
        """Extract company names and map to tickers"""
        companies = []
        text_lower = text.lower()
        
        # Check company aliases
        for company_name, ticker in self.companies.items():
            if company_name in text_lower:
                confidence = 0.85
                company_info = {
                    'company': company_name.title(),
                    'ticker': ticker,
                    'confidence': confidence,
                    'source': 'alias_match',
                    'context': self._get_surrounding_context(text, company_name)
                }
                companies.append(company_info)
        
        # Use spaCy for additional entity extraction if available
        if self.nlp:
            try:
                doc = self.nlp(text)
                for ent in doc.ents:
                    if ent.label_ in ['ORG', 'PERSON'] and len(ent.text) > 3:
                        # Try to map organization names to tickers
                        org_lower = ent.text.lower()
                        mapped_ticker = None
                        for alias, ticker in self.companies.items():
                            if alias in org_lower or org_lower in alias:
                                mapped_ticker = ticker
                                break
                        
                        confidence = 0.7 if ent.label_ == 'ORG' else 0.5
                        company_info = {
                            'company': ent.text,
                            'ticker': mapped_ticker,
                            'confidence': confidence,
                            'source': 'nlp_extraction',
                            'entity_type': ent.label_
                        }
                        companies.append(company_info)
            except Exception as e:
                self.logger.warning(f"spaCy extraction failed: {e}")
        
        return companies
    
    def _extract_people(self, text: str) -> List[Dict[str, Any]]:
        """Extract person names"""
        people = []
        
        if self.nlp:
            try:
                doc = self.nlp(text)
                for ent in doc.ents:
                    if ent.label_ == 'PERSON' and len(ent.text.split()) >= 2:
                        person_info = {
                            'name': ent.text,
                            'confidence': 0.8,
                            'source': 'nlp_extraction',
                            'context': self._get_surrounding_context(text, ent.text)
                        }
                        people.append(person_info)
            except Exception as e:
                self.logger.warning(f"Person extraction failed: {e}")
        
        return people
    
    def _extract_financial_metrics(self, text: str) -> Dict[str, List[Dict[str, Any]]]:
        """Extract financial metrics and values"""
        metrics = {}
        
        for category, patterns in self.compiled_patterns.items():
            category_matches = []
            
            for pattern in patterns:
                matches = pattern.finditer(text)
                for match in matches:
                    metric_info = {
                        'value': match.group(1) if match.groups() else match.group(0),
                        'full_match': match.group(0),
                        'confidence': 0.8,
                        'source': 'regex_pattern',
                        'context': self._get_surrounding_context(text, match.group(0))
                    }
                    category_matches.append(metric_info)
            
            if category_matches:
                metrics[category] = category_matches
        
        return metrics
    
    def _extract_dates(self, text: str) -> List[Dict[str, Any]]:
        """Extract date mentions"""
        dates = []
        
        # Use spaCy for date extraction if available
        if self.nlp:
            try:
                doc = self.nlp(text)
                for ent in doc.ents:
                    if ent.label_ == 'DATE':
                        date_info = {
                            'date': ent.text,
                            'confidence': 0.8,
                            'source': 'nlp_extraction',
                            'context': self._get_surrounding_context(text, ent.text)
                        }
                        dates.append(date_info)
            except Exception as e:
                self.logger.warning(f"Date extraction failed: {e}")
        
        # Fallback to pattern matching
        for pattern in self.compiled_patterns.get('dates', []):
            matches = pattern.finditer(text)
            for match in matches:
                date_info = {
                    'date': match.group(0),
                    'confidence': 0.7,
                    'source': 'regex_pattern',
                    'context': self._get_surrounding_context(text, match.group(0))
                }
                dates.append(date_info)
        
        return dates
    
    def _extract_prices(self, text: str) -> List[Dict[str, Any]]:
        """Extract price mentions"""
        prices = []
        matches = self.currency_pattern.finditer(text)
        
        for match in matches:
            price_info = {
                'price': match.group(0),
                'confidence': 0.9,
                'source': 'currency_pattern',
                'context': self._get_surrounding_context(text, match.group(0))
            }
            prices.append(price_info)
        
        return prices
    
    def _extract_ratings(self, text: str) -> List[Dict[str, Any]]:
        """Extract analyst ratings and recommendations"""
        ratings = []
        
        if 'ratings' in self.compiled_patterns:
            for pattern in self.compiled_patterns['ratings']:
                matches = pattern.finditer(text)
                for match in matches:
                    rating_info = {
                        'rating': match.group(0).lower(),
                        'confidence': 0.85,
                        'source': 'rating_pattern',
                        'context': self._get_surrounding_context(text, match.group(0))
                    }
                    ratings.append(rating_info)
        
        return ratings
    
    def _extract_topics(self, text: str) -> List[str]:
        """Extract investment topics and themes"""
        topics = []
        text_lower = text.lower()
        
        topic_keywords = {
            'earnings': ['earnings', 'eps', 'quarterly results', 'guidance'],
            'merger_acquisition': ['merger', 'acquisition', 'buyout', 'takeover', 'm&a'],
            'dividend': ['dividend', 'div', 'yield', 'payout'],
            'ipo': ['ipo', 'initial public offering', 'going public'],
            'regulation': ['regulation', 'regulatory', 'sec', 'fda approval'],
            'technology': ['ai', 'artificial intelligence', 'cloud', 'software', 'tech'],
            'energy': ['oil', 'gas', 'renewable', 'energy', 'petroleum'],
            'healthcare': ['drug', 'pharmaceutical', 'clinical trial', 'fda'],
            'finance': ['bank', 'lending', 'credit', 'interest rate'],
            'retail': ['consumer', 'sales', 'retail', 'e-commerce']
        }
        
        for topic, keywords in topic_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                topics.append(topic)
        
        return topics
    
    def _analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyze investment sentiment"""
        text_lower = text.lower()
        
        bullish_terms = [
            'buy', 'bullish', 'positive', 'outperform', 'strong buy', 'upgrade',
            'raised', 'increased', 'beat', 'exceed', 'strong', 'growth', 'momentum'
        ]
        
        bearish_terms = [
            'sell', 'bearish', 'negative', 'underperform', 'strong sell', 'downgrade',
            'lowered', 'decreased', 'miss', 'weak', 'decline', 'concern', 'risk'
        ]
        
        bullish_score = sum(1 for term in bullish_terms if term in text_lower)
        bearish_score = sum(1 for term in bearish_terms if term in text_lower)
        
        if bullish_score > bearish_score:
            sentiment = 'bullish'
            confidence = min(0.9, 0.5 + (bullish_score - bearish_score) * 0.1)
        elif bearish_score > bullish_score:
            sentiment = 'bearish'
            confidence = min(0.9, 0.5 + (bearish_score - bullish_score) * 0.1)
        else:
            sentiment = 'neutral'
            confidence = 0.5
        
        return {
            'sentiment': sentiment,
            'confidence': confidence,
            'bullish_score': bullish_score,
            'bearish_score': bearish_score
        }
    
    def _extract_context(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Extract context information from metadata"""
        context = {}
        
        # Analyze sender
        sender = metadata.get('sender', '')
        if sender:
            sender_lower = sender.lower()
            for profile_key, profile_data in self.sender_profiles.items():
                if profile_key in sender_lower:
                    context['sender_profile'] = {
                        'reputation': profile_data['reputation'],
                        'categories': profile_data['categories'],
                        'priority_boost': profile_data.get('priority_boost', 0)
                    }
                    break
        
        # Extract urgency indicators
        subject = metadata.get('subject', '').lower()
        urgency_keywords = ['urgent', 'asap', 'immediate', 'breaking', 'flash', 'alert']
        
        context['urgency'] = any(keyword in subject for keyword in urgency_keywords)
        context['email_type'] = self._classify_email_type(subject, metadata.get('body', ''))
        
        return context
    
    def _classify_email_type(self, subject: str, body: str) -> str:
        """Classify the type of email based on content"""
        content = (subject + ' ' + body).lower()
        
        if any(term in content for term in ['research', 'analysis', 'report']):
            return 'research'
        elif any(term in content for term in ['alert', 'breaking', 'flash', 'urgent']):
            return 'alert'
        elif any(term in content for term in ['earnings', 'guidance', 'results']):
            return 'earnings'
        elif any(term in content for term in ['portfolio', 'holdings', 'position']):
            return 'portfolio'
        elif any(term in content for term in ['meeting', 'call', 'conference']):
            return 'communication'
        else:
            return 'general'
    
    def _get_surrounding_context(self, text: str, match: str, window: int = 50) -> str:
        """Get surrounding context for a match"""
        try:
            start_idx = text.lower().find(match.lower())
            if start_idx == -1:
                return ""
            
            context_start = max(0, start_idx - window)
            context_end = min(len(text), start_idx + len(match) + window)
            
            return text[context_start:context_end].strip()
        except Exception:
            return ""
    
    def _calculate_confidence(self, entities: Dict[str, Any], text: str) -> float:
        """Calculate overall extraction confidence"""
        try:
            confidence_factors = []
            
            # Text quality
            if len(text) > 100:
                confidence_factors.append(0.8)
            else:
                confidence_factors.append(0.5)
            
            # Entity extraction success
            ticker_count = len(entities.get('tickers', []))
            if ticker_count > 0:
                confidence_factors.append(0.9)
            
            company_count = len(entities.get('companies', []))
            if company_count > 0:
                confidence_factors.append(0.8)
            
            metrics_count = sum(len(metrics) for metrics in entities.get('financial_metrics', {}).values())
            if metrics_count > 0:
                confidence_factors.append(0.7)
            
            # Return average confidence
            return sum(confidence_factors) / len(confidence_factors) if confidence_factors else 0.5
            
        except Exception:
            return 0.5
    
    def _empty_result(self) -> Dict[str, Any]:
        """Return empty extraction result"""
        return {
            'tickers': [],
            'companies': [],
            'people': [],
            'financial_metrics': {},
            'dates': [],
            'prices': [],
            'ratings': [],
            'topics': [],
            'sentiment': {'sentiment': 'neutral', 'confidence': 0.0},
            'confidence': 0.0
        }
    
    def update_ticker_list(self, new_tickers: List[str]):
        """Update the ticker list with new symbols"""
        try:
            self.tickers.update(ticker.upper() for ticker in new_tickers)
            
            ticker_file = self.config_path / "tickers.json"
            with open(ticker_file, 'w') as f:
                json.dump(list(self.tickers), f, indent=2)
                
            self.logger.info(f"Updated ticker list with {len(new_tickers)} new symbols")
        except Exception as e:
            self.logger.error(f"Failed to update ticker list: {e}")
    
    def get_extraction_stats(self) -> Dict[str, Any]:
        """Get entity extraction statistics"""
        return {
            'known_tickers': len(self.tickers),
            'company_aliases': len(self.companies),
            'sender_profiles': len(self.sender_profiles),
            'nlp_available': self.nlp is not None,
            'pattern_categories': list(self.financial_metrics.keys())
        }