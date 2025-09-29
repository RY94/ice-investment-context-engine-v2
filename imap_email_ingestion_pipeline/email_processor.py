# imap_email_ingestion_pipeline/email_processor.py
# Email content processor and entity extractor for ICE system
# Processes email content and extracts investment-relevant information
# RELEVANT FILES: ice_lightrag/ice_rag.py, email_connector.py

import re
from typing import Dict, List, Any
import logging

class EmailProcessor:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Common financial patterns
        self.ticker_pattern = re.compile(r'\b[A-Z]{1,5}\b')
        self.price_pattern = re.compile(r'\$[\d,]+\.?\d*')
        self.percent_pattern = re.compile(r'\d+\.?\d*%')
        
        # Investment keywords
        self.investment_keywords = {
            'bullish': ['buy', 'bullish', 'positive', 'outperform', 'strong buy'],
            'bearish': ['sell', 'bearish', 'negative', 'underperform', 'strong sell'],
            'neutral': ['hold', 'neutral', 'maintain', 'unchanged'],
            'events': ['earnings', 'guidance', 'merger', 'acquisition', 'ipo', 'dividend']
        }
    
    def process_email(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process email and extract structured information"""
        try:
            processed = {
                'id': email_data['id'],
                'metadata': {
                    'subject': email_data['subject'],
                    'from': email_data['from'],
                    'date': email_data['date']
                },
                'content': {
                    'body': email_data['body'],
                    'summary': self._summarize_content(email_data['body'])
                },
                'entities': self._extract_entities(email_data['body']),
                'sentiment': self._analyze_sentiment(email_data['body']),
                'topics': self._extract_topics(email_data['body'])
            }
            
            return processed
            
        except Exception as e:
            self.logger.error(f"Processing failed for email {email_data.get('id', 'unknown')}: {e}")
            return {'error': str(e)}
    
    def _extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract financial entities from email text"""
        entities = {
            'tickers': [],
            'prices': [],
            'percentages': [],
            'companies': []
        }
        
        # Find tickers (simple pattern - could be enhanced)
        tickers = self.ticker_pattern.findall(text)
        entities['tickers'] = list(set([t for t in tickers if 2 <= len(t) <= 5]))
        
        # Find prices
        entities['prices'] = self.price_pattern.findall(text)
        
        # Find percentages
        entities['percentages'] = self.percent_pattern.findall(text)
        
        return entities
    
    def _analyze_sentiment(self, text: str) -> Dict[str, int]:
        """Simple keyword-based sentiment analysis"""
        sentiment = {'bullish': 0, 'bearish': 0, 'neutral': 0}
        text_lower = text.lower()
        
        for sentiment_type, keywords in self.investment_keywords.items():
            if sentiment_type in sentiment:
                for keyword in keywords:
                    sentiment[sentiment_type] += text_lower.count(keyword)
        
        return sentiment
    
    def _extract_topics(self, text: str) -> List[str]:
        """Extract investment topics from email"""
        topics = []
        text_lower = text.lower()
        
        for keyword in self.investment_keywords['events']:
            if keyword in text_lower:
                topics.append(keyword)
        
        return list(set(topics))
    
    def _summarize_content(self, text: str) -> str:
        """Create simple summary (first 200 chars)"""
        return text[:200] + "..." if len(text) > 200 else text