# imap_email_ingestion_pipeline/contextual_signal_extractor.py
# Contextual Signal Extractor - Only extracts trading signals when they actually exist
# Critical asymmetric value component for hedge fund email processing
# RELEVANT FILES: ultra_refined_email_processor.py, intelligent_link_processor.py, entity_extractor.py

import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum

class SignalType(Enum):
    """Types of trading signals we can extract"""
    RECOMMENDATION = "recommendation"
    TARGET_PRICE = "target_price"
    RATING_CHANGE = "rating_change"
    PRICE_MOVE = "price_move"
    EARNINGS_REACTION = "earnings_reaction"

@dataclass
class TradingSignal:
    """Structured trading signal extracted from email"""
    signal_type: SignalType
    ticker: Optional[str]
    company: Optional[str]
    action: str  # BUY, SELL, HOLD, UPGRADE, DOWNGRADE
    value: Optional[str]  # Price, rating, percentage
    currency: Optional[str]
    confidence: float
    context: str  # Surrounding text for verification
    source_text: str  # Original text that matched

@dataclass
class ExtractionResult:
    """Result of signal extraction from email"""
    signals: List[TradingSignal]
    has_signals: bool
    extraction_confidence: float
    processing_time: float

class ContextualSignalExtractor:
    """
    ASYMMETRIC VALUE COMPONENT: Contextual Signal Extraction
    Only extracts trading signals when they actually exist in the email content.
    Prevents hallucination and ensures high-quality signal detection.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__ + ".ContextualSignalExtractor")
        
        # Comprehensive patterns for different signal types
        self.patterns = {
            # Trading recommendations with tickers
            SignalType.RECOMMENDATION: {
                'trigger_words': ['buy', 'sell', 'hold', 'initiate', 'maintain', 'reiterate'],
                'patterns': [
                    # "BUY NVDA" or "BUY NVDA at $450"
                    r'\b(BUY|SELL|HOLD)\s+([A-Z]{2,5}|\d{4}\.HK|[A-Z]+\s*[A-Z]*)\s*(?:at\s*(\$|SGD|HKD|USD)\s*(\d+(?:\.\d+)?))?',
                    # "Initiate AAPL with BUY"
                    r'(?:initiate|maintain|reiterate)\s+([A-Z]{2,5}|\d{4}\.HK|[A-Z]+)\s+with\s+(BUY|SELL|HOLD)',
                    # "NVDA - BUY (Target: $500)"
                    r'([A-Z]{2,5}|\d{4}\.HK)\s*[-–]\s*(BUY|SELL|HOLD)(?:\s*\(Target:\s*(\$|SGD|HKD)\s*(\d+(?:\.\d+)?)\))?'
                ]
            },
            
            # Target price changes
            SignalType.TARGET_PRICE: {
                'trigger_words': ['target price', 'tp', 'price target', 'pt', 'target'],
                'patterns': [
                    # "TP raised to SGD10" or "Target Price: $450"
                    r'(?:TP|Target Price|Price Target|PT)[\s:]*(?:raised|increased|lifted|set|cut|lowered)?\s*(?:to|at)?\s*(\$|SGD|HKD|USD|RMB)\s*(\d+(?:\.\d+)?)',
                    # "Target: $450 (from $400)"
                    r'Target:\s*(\$|SGD|HKD|USD)\s*(\d+(?:\.\d+)?)\s*(?:\(from\s*\$?\s*(\d+(?:\.\d+)?)\))?',
                    # Company specific: "NVDA target raised to $500"
                    r'([A-Z]{2,5}|\d{4}\.HK)\s+target\s+(?:raised|lifted|increased|cut|lowered)\s+to\s+(\$|SGD|HKD|USD)\s*(\d+(?:\.\d+)?)'
                ]
            },
            
            # Rating changes  
            SignalType.RATING_CHANGE: {
                'trigger_words': ['upgrade', 'downgrade', 'raised', 'cut', 'lowered', 'improved'],
                'patterns': [
                    # "UPGRADE to BUY from HOLD"
                    r'(UPGRADE|DOWNGRADE)\s+(?:to\s+)?(BUY|SELL|HOLD)\s*(?:from\s+(BUY|SELL|HOLD))?',
                    # "Rating raised to BUY"
                    r'(?:rating|recommendation)\s+(?:raised|lifted|upgraded|cut|lowered|downgraded)\s+to\s+(BUY|SELL|HOLD)',
                    # Company specific: "AAPL upgraded to BUY"
                    r'([A-Z]{2,5}|\d{4}\.HK)\s+(?:upgraded|downgraded|raised|cut)\s+to\s+(BUY|SELL|HOLD)'
                ]
            }
        }
        
        # Common ticker patterns for recognition
        self.ticker_patterns = [
            r'\b[A-Z]{2,5}\b',  # AAPL, MSFT, etc.
            r'\b\d{4}\.HK\b',   # Hong Kong stocks: 0700.HK
            r'\b[A-Z]{2,4}\s+[A-Z]{2}\b'  # Some international formats
        ]
        
        # Currency patterns
        self.currency_map = {
            '$': 'USD',
            'USD': 'USD', 
            'SGD': 'SGD',
            'HKD': 'HKD',
            'RMB': 'RMB',
            'CNY': 'CNY'
        }
        
        self.logger.info("Contextual Signal Extractor initialized")
    
    def extract_signals(self, email_content: str, email_metadata: Dict[str, Any] = None) -> ExtractionResult:
        """
        Extract trading signals from email content only if they actually exist
        
        Args:
            email_content: The email body text
            email_metadata: Optional metadata (sender, subject, etc.)
            
        Returns:
            ExtractionResult with found signals (empty if none exist)
        """
        start_time = datetime.now()
        
        try:
            # Clean and normalize content
            normalized_content = self._normalize_content(email_content)
            
            # Extract all signal types
            all_signals = []
            
            for signal_type, config in self.patterns.items():
                # Only proceed if trigger words are found
                if self._has_trigger_words(normalized_content, config['trigger_words']):
                    signals = self._extract_signal_type(normalized_content, signal_type, config)
                    all_signals.extend(signals)
            
            # Calculate overall confidence
            overall_confidence = self._calculate_overall_confidence(all_signals, normalized_content)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            result = ExtractionResult(
                signals=all_signals,
                has_signals=len(all_signals) > 0,
                extraction_confidence=overall_confidence,
                processing_time=processing_time
            )
            
            if all_signals:
                self.logger.info(f"Extracted {len(all_signals)} signals with confidence {overall_confidence:.2f}")
            else:
                self.logger.debug("No trading signals found in email content")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error extracting signals: {e}")
            processing_time = (datetime.now() - start_time).total_seconds()
            return ExtractionResult(
                signals=[],
                has_signals=False,
                extraction_confidence=0.0,
                processing_time=processing_time
            )
    
    def _normalize_content(self, content: str) -> str:
        """Normalize email content for pattern matching"""
        # Remove extra whitespace and line breaks
        normalized = re.sub(r'\s+', ' ', content)
        
        # Handle common email artifacts
        normalized = re.sub(r'=\n', '', normalized)  # Remove line breaks in quoted-printable
        normalized = re.sub(r'\[.*?\]', '', normalized)  # Remove bracketed text like [cid:image001.png]
        
        return normalized.strip()
    
    def _has_trigger_words(self, content: str, trigger_words: List[str]) -> bool:
        """Check if content contains any trigger words for signal type"""
        content_lower = content.lower()
        return any(word.lower() in content_lower for word in trigger_words)
    
    def _extract_signal_type(self, content: str, signal_type: SignalType, config: Dict[str, Any]) -> List[TradingSignal]:
        """Extract signals of a specific type"""
        signals = []
        
        for pattern in config['patterns']:
            matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
            
            for match in matches:
                signal = self._create_signal_from_match(match, signal_type, content)
                if signal:
                    signals.append(signal)
        
        return signals
    
    def _create_signal_from_match(self, match: re.Match, signal_type: SignalType, content: str) -> Optional[TradingSignal]:
        """Create a TradingSignal from regex match"""
        try:
            groups = match.groups()
            match_text = match.group(0)
            
            # Get context around the match
            start = max(0, match.start() - 50)
            end = min(len(content), match.end() + 50)
            context = content[start:end].strip()
            
            # Extract components based on signal type
            if signal_type == SignalType.RECOMMENDATION:
                action = groups[0] if groups[0] else (groups[1] if len(groups) > 1 else None)
                ticker = groups[1] if len(groups) > 1 and groups[1] else (groups[0] if groups[0] and groups[0] not in ['BUY', 'SELL', 'HOLD'] else None)
                currency = groups[2] if len(groups) > 2 else None
                value = groups[3] if len(groups) > 3 else None
                
            elif signal_type == SignalType.TARGET_PRICE:
                currency = groups[0] if groups else None
                value = groups[1] if len(groups) > 1 else None
                ticker = groups[2] if len(groups) > 2 else None
                action = "TARGET_PRICE"
                
            elif signal_type == SignalType.RATING_CHANGE:
                action = groups[0] if groups else None
                new_rating = groups[1] if len(groups) > 1 else None
                old_rating = groups[2] if len(groups) > 2 else None
                ticker = groups[3] if len(groups) > 3 else None
                value = f"{new_rating} (from {old_rating})" if old_rating else new_rating
                currency = None
            
            else:
                return None
            
            # Clean up ticker if found
            if ticker:
                ticker = self._clean_ticker(ticker)
            
            # Calculate confidence for this signal
            confidence = self._calculate_signal_confidence(match_text, context, signal_type)
            
            return TradingSignal(
                signal_type=signal_type,
                ticker=ticker,
                company=None,  # Will be filled by company resolution later
                action=action.upper() if action else "UNKNOWN",
                value=value,
                currency=self.currency_map.get(currency, currency) if currency else None,
                confidence=confidence,
                context=context,
                source_text=match_text
            )
            
        except Exception as e:
            self.logger.warning(f"Failed to create signal from match: {e}")
            return None
    
    def _clean_ticker(self, ticker: str) -> str:
        """Clean and normalize ticker symbol"""
        if not ticker:
            return None
        
        # Remove extra whitespace
        ticker = ticker.strip().upper()
        
        # Handle common ticker formats
        if re.match(r'^\d{4}\.HK$', ticker):  # Hong Kong format
            return ticker
        elif re.match(r'^[A-Z]{2,5}$', ticker):  # Standard US format
            return ticker
        else:
            # Try to extract ticker from longer text
            ticker_match = re.search(r'\b([A-Z]{2,5})\b', ticker)
            return ticker_match.group(1) if ticker_match else ticker
    
    def _calculate_signal_confidence(self, match_text: str, context: str, signal_type: SignalType) -> float:
        """Calculate confidence score for extracted signal"""
        confidence = 0.5  # Base confidence
        
        # Boost confidence for clear patterns
        if signal_type == SignalType.RECOMMENDATION:
            if re.search(r'\b(BUY|SELL|HOLD)\b', match_text, re.IGNORECASE):
                confidence += 0.3
            if re.search(r'\b[A-Z]{2,5}\b', match_text):  # Has ticker
                confidence += 0.2
        
        elif signal_type == SignalType.TARGET_PRICE:
            if re.search(r'\$\s*\d+', match_text):  # Has price
                confidence += 0.3
            if re.search(r'(?:raised|cut|target)', match_text, re.IGNORECASE):
                confidence += 0.2
        
        elif signal_type == SignalType.RATING_CHANGE:
            if re.search(r'(?:upgrade|downgrade)', match_text, re.IGNORECASE):
                confidence += 0.4
        
        # Penalize if context looks like false positive
        if re.search(r'(?:unsubscribe|privacy|legal)', context, re.IGNORECASE):
            confidence -= 0.3
        
        return min(1.0, max(0.0, confidence))
    
    def _calculate_overall_confidence(self, signals: List[TradingSignal], content: str) -> float:
        """Calculate overall confidence for all extracted signals"""
        if not signals:
            return 0.0
        
        # Average individual confidences
        avg_confidence = sum(signal.confidence for signal in signals) / len(signals)
        
        # Boost if multiple consistent signals
        if len(signals) > 1:
            avg_confidence += 0.1
        
        # Boost if content looks like research/trading content
        if re.search(r'(?:research|analysis|recommendation|target)', content, re.IGNORECASE):
            avg_confidence += 0.1
        
        return min(1.0, avg_confidence)
    
    def format_signals_for_output(self, extraction_result: ExtractionResult) -> Dict[str, Any]:
        """Format extraction result for JSON serialization"""
        if not extraction_result.has_signals:
            return {
                'has_trading_signals': False,
                'extraction_confidence': extraction_result.extraction_confidence,
                'processing_time': extraction_result.processing_time,
                'signal_count': 0
            }
        
        return {
            'has_trading_signals': True,
            'extraction_confidence': extraction_result.extraction_confidence,
            'processing_time': extraction_result.processing_time,
            'signal_count': len(extraction_result.signals),
            'signals': [asdict(signal) for signal in extraction_result.signals],
            'summary': self._generate_signals_summary(extraction_result.signals)
        }
    
    def _generate_signals_summary(self, signals: List[TradingSignal]) -> Dict[str, Any]:
        """Generate a summary of extracted signals"""
        summary = {
            'recommendations': [],
            'target_prices': [],
            'rating_changes': [],
            'tickers_mentioned': set()
        }
        
        for signal in signals:
            if signal.ticker:
                summary['tickers_mentioned'].add(signal.ticker)
            
            if signal.signal_type == SignalType.RECOMMENDATION:
                summary['recommendations'].append({
                    'ticker': signal.ticker,
                    'action': signal.action,
                    'confidence': signal.confidence
                })
            elif signal.signal_type == SignalType.TARGET_PRICE:
                summary['target_prices'].append({
                    'ticker': signal.ticker,
                    'price': signal.value,
                    'currency': signal.currency,
                    'confidence': signal.confidence
                })
            elif signal.signal_type == SignalType.RATING_CHANGE:
                summary['rating_changes'].append({
                    'ticker': signal.ticker,
                    'change': signal.action,
                    'new_rating': signal.value,
                    'confidence': signal.confidence
                })
        
        summary['tickers_mentioned'] = list(summary['tickers_mentioned'])
        return summary