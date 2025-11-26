# Location: /src/ice_core/real_time_monitor.py
# Purpose: Real-time monitoring daemon for continuous market intelligence gathering
# Why: Enable proactive alerting for hedge fund PMs on critical market events
# Relevant Files: event_extractor.py, data_ingestion.py, signal_store.py

"""
Real-Time Monitoring Module for ICE

Provides continuous monitoring of market events through:
1. NewsAPI polling (5-minute intervals)
2. SEC EDGAR polling (15-minute intervals)
3. Alert prioritization and delivery
4. Incremental graph updates

Alert Priority Levels:
- CRITICAL: Requires immediate attention (portfolio holdings affected)
- HIGH: Important market event (sector/theme exposure)
- MEDIUM: Notable but not urgent (competitor news)
- LOW: Background intelligence (industry trends)
"""

import asyncio
import json
import logging
import os
import smtplib
import time
import requests  # Phase 2.7B Option 1: For Slack webhook delivery
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
import threading
import queue

# Import ICE modules
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.ice_core.event_extractor import EventExtractor, EventNode, EventType
from src.ice_core.enhanced_entity_extractor import EnhancedEntityExtractor
from updated_architectures.implementation.data_ingestion import DataIngester
from updated_architectures.implementation.signal_store import SignalStore

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AlertPriority(Enum):
    """Alert priority levels for event classification"""
    CRITICAL = "critical"  # Portfolio holdings affected, major earnings miss/beat
    HIGH = "high"         # Sector/theme exposure, M&A, management changes
    MEDIUM = "medium"     # Competitor news, regulatory updates
    LOW = "low"           # Industry trends, general market news


class AlertChannel(Enum):
    """Available alert delivery channels"""
    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"
    LOG = "log"  # Default fallback


@dataclass
class Alert:
    """Represents a real-time alert"""
    id: str
    timestamp: datetime
    priority: AlertPriority
    event: EventNode
    message: str
    source: str
    tickers: List[str]
    metadata: Dict = field(default_factory=dict)
    delivered: bool = False
    delivery_channels: List[AlertChannel] = field(default_factory=list)


class NewsAPIPoller:
    """Polls NewsAPI for real-time financial news"""

    def __init__(self, api_key: str, interval_seconds: int = 300, max_seen_items: int = 10000):
        """
        Initialize NewsAPI poller

        Args:
            api_key: NewsAPI API key
            interval_seconds: Polling interval (default 5 minutes)
            max_seen_items: Maximum number of seen items to track (default 10000)
        """
        self.api_key = api_key
        self.interval = interval_seconds
        self.last_poll = datetime.now() - timedelta(seconds=interval_seconds)
        self.seen_articles: Set[str] = set()
        self.max_seen_items = max_seen_items
        self.data_ingestion = DataIngester()

    def _cleanup_seen_items(self):
        """Cleanup old seen items if set grows too large"""
        if len(self.seen_articles) > self.max_seen_items:
            # Keep only the most recent 80% of max size
            items_to_keep = int(self.max_seen_items * 0.8)
            # Convert to list, sort by timestamp in ID, keep recent ones
            sorted_items = sorted(list(self.seen_articles))
            self.seen_articles = set(sorted_items[-items_to_keep:])
            logger.info(f"Cleaned up seen articles: kept {items_to_keep} of {len(sorted_items)}")

    async def poll(self, tickers: List[str]) -> List[Dict]:
        """
        Poll NewsAPI for latest articles

        Args:
            tickers: List of tickers to monitor

        Returns:
            List of new articles since last poll
        """
        current_time = datetime.now()

        # Check if enough time has passed
        if (current_time - self.last_poll).seconds < self.interval:
            return []

        new_articles = []

        try:
            # Use existing DataIngestion method for consistency
            for ticker in tickers:
                # Fetch news for last hour to ensure we don't miss anything
                from_date = (current_time - timedelta(hours=1)).strftime('%Y-%m-%d')
                to_date = current_time.strftime('%Y-%m-%d')

                # Fetch news through data ingestion
                articles = self.data_ingestion.fetch_company_news_concurrent(
                    symbol=ticker,
                    limit=10,  # Get latest 10 articles
                    use_concurrent=False  # Don't use concurrent for single ticker
                )

                # Filter out already seen articles
                for article in articles:
                    article_id = f"{article.get('url', '')}_{article.get('publishedAt', '')}"
                    if article_id not in self.seen_articles:
                        self.seen_articles.add(article_id)
                        article['ticker'] = ticker  # Add ticker context
                        new_articles.append(article)

            # Cleanup if needed
            self._cleanup_seen_items()

            self.last_poll = current_time
            logger.info(f"NewsAPI poll completed: {len(new_articles)} new articles")

        except Exception as e:
            logger.error(f"NewsAPI polling error: {e}")

        return new_articles


class SECEdgarPoller:
    """Polls SEC EDGAR for new filings"""

    def __init__(self, interval_seconds: int = 900, max_seen_items: int = 5000):
        """
        Initialize SEC EDGAR poller

        Args:
            interval_seconds: Polling interval (default 15 minutes)
            max_seen_items: Maximum number of seen items to track (default 5000)
        """
        self.interval = interval_seconds
        self.last_poll = datetime.now() - timedelta(seconds=interval_seconds)
        self.seen_filings: Set[str] = set()
        self.max_seen_items = max_seen_items
        self.data_ingestion = DataIngester()

    def _cleanup_seen_items(self):
        """Cleanup old seen items if set grows too large"""
        if len(self.seen_filings) > self.max_seen_items:
            items_to_keep = int(self.max_seen_items * 0.8)
            sorted_items = sorted(list(self.seen_filings))
            self.seen_filings = set(sorted_items[-items_to_keep:])
            logger.info(f"Cleaned up seen filings: kept {items_to_keep} of {len(sorted_items)}")

    async def poll(self, tickers: List[str]) -> List[Dict]:
        """
        Poll SEC EDGAR for new filings

        Args:
            tickers: List of tickers to monitor

        Returns:
            List of new filings since last poll
        """
        current_time = datetime.now()

        # Check if enough time has passed
        if (current_time - self.last_poll).seconds < self.interval:
            return []

        new_filings = []

        try:
            for ticker in tickers:
                # Fetch recent SEC filings
                filings = self.data_ingestion.fetch_sec_filings(
                    symbol=ticker,
                    limit=5  # Check last 5 filings
                )

                # Filter out already seen filings
                for filing in filings:
                    filing_id = f"{filing.get('accessionNumber', '')}_{ticker}"
                    if filing_id not in self.seen_filings:
                        self.seen_filings.add(filing_id)
                        filing['ticker'] = ticker
                        new_filings.append(filing)

            # Cleanup if needed
            self._cleanup_seen_items()

            self.last_poll = current_time
            logger.info(f"SEC EDGAR poll completed: {len(new_filings)} new filings")

        except Exception as e:
            logger.error(f"SEC EDGAR polling error: {e}")

        return new_filings


class AlertClassifier:
    """Classifies events and generates prioritized alerts"""

    def __init__(self, portfolio_tickers: List[str], sector_exposures: Dict[str, float]):
        """
        Initialize alert classifier

        Args:
            portfolio_tickers: List of tickers in portfolio
            sector_exposures: Dict of sector/theme to exposure percentage
        """
        self.portfolio_tickers = set(portfolio_tickers)
        self.sector_exposures = sector_exposures
        self.event_extractor = EventExtractor()

    def classify_event(self, event: EventNode, source_data: Dict) -> Alert:
        """
        Classify event and generate alert

        Args:
            event: Extracted event node
            source_data: Original source data

        Returns:
            Alert with appropriate priority
        """
        # Determine priority based on event characteristics
        priority = self._calculate_priority(event)

        # Generate alert message
        message = self._generate_message(event, priority)

        # Create alert
        alert = Alert(
            id=f"alert_{event.id}_{int(time.time())}",
            timestamp=datetime.now(),
            priority=priority,
            event=event,
            message=message,
            source=source_data.get('url', 'unknown'),
            tickers=[event.ticker] if event.ticker else [],
            metadata={
                'confidence': event.confidence,
                'themes': event.themes,
                'impact': event.impact,
                'magnitude': event.magnitude
            }
        )

        # Determine delivery channels based on priority
        alert.delivery_channels = self._get_delivery_channels(priority)

        return alert

    def _calculate_priority(self, event: EventNode) -> AlertPriority:
        """Calculate alert priority based on event characteristics"""

        # CRITICAL: Portfolio holdings with high impact events
        if event.ticker in self.portfolio_tickers:
            if event.type in [EventType.EARNINGS, EventType.SCANDAL, EventType.MA_DEAL]:
                if event.impact == "negative" and event.magnitude and event.magnitude > 5:
                    return AlertPriority.CRITICAL
                elif event.impact == "positive" and event.magnitude and event.magnitude > 10:
                    return AlertPriority.CRITICAL

            # HIGH: Other portfolio events
            return AlertPriority.HIGH

        # HIGH: Sector/theme exposure affected
        for theme in event.themes:
            if theme in self.sector_exposures and self.sector_exposures[theme] > 0.1:
                return AlertPriority.HIGH

        # MEDIUM: Significant market events
        if event.type in [EventType.REGULATORY, EventType.MANAGEMENT, EventType.LAWSUIT]:
            return AlertPriority.MEDIUM

        # LOW: General market intelligence
        return AlertPriority.LOW

    def _generate_message(self, event: EventNode, priority: AlertPriority) -> str:
        """Generate human-readable alert message"""

        priority_emoji = {
            AlertPriority.CRITICAL: "🚨",
            AlertPriority.HIGH: "⚠️",
            AlertPriority.MEDIUM: "📊",
            AlertPriority.LOW: "ℹ️"
        }

        impact_str = ""
        if event.magnitude:
            impact_str = f" ({event.impact} {event.magnitude:.1f}%)"

        message = (
            f"{priority_emoji[priority]} {priority.value.upper()} ALERT\n"
            f"Ticker: {event.ticker or 'N/A'}\n"
            f"Event: {event.type.value}{impact_str}\n"
            f"Themes: {', '.join(event.themes)}\n"
            f"Confidence: {event.confidence:.2f}\n"
            f"Details: {event.description[:200]}..."
        )

        return message

    def _get_delivery_channels(self, priority: AlertPriority) -> List[AlertChannel]:
        """Determine delivery channels based on priority"""

        if priority == AlertPriority.CRITICAL:
            return [AlertChannel.EMAIL, AlertChannel.SLACK, AlertChannel.LOG]
        elif priority == AlertPriority.HIGH:
            return [AlertChannel.SLACK, AlertChannel.LOG]
        elif priority == AlertPriority.MEDIUM:
            return [AlertChannel.LOG]
        else:
            return [AlertChannel.LOG]


class AlertDelivery:
    """Handles alert delivery to various channels"""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize alert delivery system

        Args:
            config: Configuration for delivery channels
        """
        self.config = config
        self.delivery_queue = queue.Queue()
        self.delivery_thread = None
        self.running = False

    def start(self):
        """Start delivery thread"""
        self.running = True
        self.delivery_thread = threading.Thread(target=self._delivery_worker)
        self.delivery_thread.daemon = True
        self.delivery_thread.start()
        logger.info("Alert delivery system started")

    def stop(self):
        """Stop delivery thread"""
        self.running = False
        if self.delivery_thread:
            self.delivery_thread.join(timeout=5)
        logger.info("Alert delivery system stopped")

    def queue_alert(self, alert: Alert):
        """Queue alert for delivery"""
        self.delivery_queue.put(alert)

    def _delivery_worker(self):
        """Worker thread for alert delivery"""
        while self.running:
            try:
                # Get alert from queue with timeout
                alert = self.delivery_queue.get(timeout=1)

                # Deliver to each channel
                for channel in alert.delivery_channels:
                    try:
                        if channel == AlertChannel.EMAIL:
                            self._send_email(alert)
                        elif channel == AlertChannel.SLACK:
                            self._send_slack(alert)
                        elif channel == AlertChannel.WEBHOOK:
                            self._send_webhook(alert)
                        elif channel == AlertChannel.LOG:
                            self._log_alert(alert)
                    except Exception as e:
                        logger.error(f"Failed to deliver alert to {channel}: {e}")

                alert.delivered = True

            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Alert delivery error: {e}")

    def _send_email(self, alert: Alert):
        """
        Send alert via email using SMTP (Phase 2.7B Option 1)

        Production SMTP implementation with TLS security.
        Supports Gmail, Outlook, and custom SMTP servers.
        """
        if not self.config.get('email_enabled'):
            return

        try:
            # Build email message
            msg = MIMEMultipart()
            msg['From'] = self.config.get('email_from', os.getenv('SMTP_FROM'))
            msg['To'] = self.config.get('email_to', os.getenv('SMTP_TO'))
            msg['Subject'] = f"ICE Alert: {alert.priority.value.upper()} - {alert.event.ticker or 'Market Event'}"

            msg.attach(MIMEText(alert.message, 'plain'))

            # Get SMTP configuration
            smtp_host = self.config.get('smtp_host', os.getenv('SMTP_HOST', 'smtp.gmail.com'))
            smtp_port = int(self.config.get('smtp_port', os.getenv('SMTP_PORT', '587')))
            smtp_user = self.config.get('smtp_user', os.getenv('SMTP_USER'))
            smtp_password = self.config.get('smtp_password', os.getenv('SMTP_PASSWORD'))

            # Validate required credentials
            if not smtp_user or not smtp_password:
                logger.error("SMTP credentials not configured (SMTP_USER, SMTP_PASSWORD)")
                return

            # Send via SMTP with TLS
            # FIXED: Use SSL context for certificate verification (prevents MITM)
            import ssl
            ssl_context = ssl.create_default_context()
            with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
                server.starttls(context=ssl_context)  # Upgrade to TLS with cert verification
                server.login(smtp_user, smtp_password)
                server.send_message(msg)

            logger.info(f"✅ Email alert sent to {msg['To']}: {alert.id}")

        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP authentication failed: {e} (check SMTP_USER/SMTP_PASSWORD)")
        except smtplib.SMTPException as e:
            logger.error(f"SMTP error: {e}")
        except Exception as e:
            logger.error(f"Email delivery failed: {e}")

    @staticmethod
    def _escape_slack_mrkdwn(text: str) -> str:
        """
        Escape special Slack mrkdwn characters to prevent injection attacks.

        SECURITY FIX: Prevents injection of <!channel>, <@user>, malicious links.
        Slack mrkdwn treats < > & as special characters for mentions/links.
        """
        if not text:
            return ""
        # Escape & first (so we don't double-escape < and >)
        text = text.replace('&', '&amp;')
        # Escape < and > which enable mentions/links
        text = text.replace('<', '&lt;')
        text = text.replace('>', '&gt;')
        return text

    def _send_slack(self, alert: Alert):
        """
        Send alert to Slack using webhooks (Phase 2.7B Option 1)

        Production Slack webhook implementation with rich formatting.
        Supports Slack Incoming Webhooks and color-coded alerts.
        """
        if not self.config.get('slack_enabled'):
            return

        try:
            # Get Slack webhook URL
            webhook_url = self.config.get('slack_webhook_url', os.getenv('SLACK_WEBHOOK_URL'))

            if not webhook_url:
                logger.error("Slack webhook URL not configured (SLACK_WEBHOOK_URL)")
                return

            # Map priority to Slack color codes
            priority_colors = {
                AlertPriority.CRITICAL: "#ff0000",  # Red
                AlertPriority.HIGH: "#ff9900",      # Orange
                AlertPriority.MEDIUM: "#36a64f",    # Green
                AlertPriority.LOW: "#808080"        # Gray
            }

            # Build Slack payload with Block Kit formatting
            payload = {
                "text": f"ICE Alert: {alert.priority.value.upper()}",  # Fallback text
                "attachments": [
                    {
                        "color": priority_colors.get(alert.priority, "#808080"),
                        "blocks": [
                            {
                                "type": "header",
                                "text": {
                                    "type": "plain_text",
                                    "text": f"{alert.priority.value.upper()} Alert: {alert.event.ticker or 'Market Event'}"
                                }
                            },
                            {
                                "type": "section",
                                "text": {
                                    "type": "mrkdwn",
                                    # SECURITY FIX: Escape user-controlled content to prevent injection
                                    "text": self._escape_slack_mrkdwn(alert.message)
                                }
                            },
                            {
                                "type": "context",
                                "elements": [
                                    {
                                        "type": "mrkdwn",
                                        # SECURITY FIX: Escape source content
                                        "text": f"*Source:* {self._escape_slack_mrkdwn(alert.source[:100] if alert.source else '')}"
                                    },
                                    {
                                        "type": "mrkdwn",
                                        "text": f"*Alert ID:* {alert.id}"
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }

            # Send webhook POST request
            response = requests.post(
                webhook_url,
                json=payload,
                timeout=10,
                headers={'Content-Type': 'application/json'}
            )

            # Check response status
            if response.status_code == 200:
                logger.info(f"✅ Slack alert sent: {alert.id}")
            else:
                # SECURITY FIX: Don't log response.text (may contain sensitive info or webhook URL)
                logger.error(f"Slack webhook failed: HTTP {response.status_code}")

        except requests.exceptions.RequestException as e:
            logger.error(f"Slack webhook request failed: {e}")
        except Exception as e:
            logger.error(f"Slack delivery failed: {e}")

    def _send_webhook(self, alert: Alert):
        """
        Send alert to generic webhook endpoint (Phase 2.7B Option 1 Fix).

        FIXED: Previously empty - just logged without sending.
        Now actually sends HTTP POST to configured webhook URL.
        """
        if not self.config.get('webhook_enabled'):
            return

        try:
            # Get webhook URL from config or environment
            webhook_url = self.config.get('webhook_url', os.getenv('WEBHOOK_URL'))

            if not webhook_url:
                logger.warning("Generic webhook URL not configured (WEBHOOK_URL)")
                return

            # Build webhook payload with alert data
            payload = {
                'alert_id': alert.id,
                'priority': alert.priority.value,
                'ticker': getattr(alert, 'ticker', None) or (alert.event.ticker if hasattr(alert, 'event') and alert.event else None),
                'message': alert.message,
                'timestamp': alert.timestamp.isoformat() if hasattr(alert, 'timestamp') and alert.timestamp else None,
                'source': alert.source[:200] if hasattr(alert, 'source') and alert.source else None
            }

            # Send webhook POST request
            response = requests.post(
                webhook_url,
                json=payload,
                timeout=10,
                headers={'Content-Type': 'application/json'}
            )

            # Check response status
            if response.status_code == 200:
                logger.info(f"✅ Webhook alert sent: {alert.id}")
            else:
                # FIXED: Don't log response.text (may contain sensitive info)
                logger.error(f"Webhook failed: HTTP {response.status_code}")

        except requests.exceptions.RequestException as e:
            logger.error(f"Webhook request failed: {e}")
        except Exception as e:
            logger.error(f"Webhook delivery failed: {e}")

    def _log_alert(self, alert: Alert):
        """Log alert to file/console"""
        logger.info(f"\n{'-'*60}\n{alert.message}\n{'-'*60}")


class RealTimeMonitor:
    """Main real-time monitoring orchestrator"""

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize real-time monitor

        Args:
            config_path: Path to configuration file
        """
        self.config = self._load_config(config_path)
        self.running = False

        # Initialize components
        self.news_poller = NewsAPIPoller(
            api_key=self.config.get('newsapi_key', os.getenv('NEWS_API_KEY')),
            interval_seconds=self.config.get('news_interval', 300)
        )

        self.sec_poller = SECEdgarPoller(
            interval_seconds=self.config.get('sec_interval', 900)
        )

        self.alert_classifier = AlertClassifier(
            portfolio_tickers=self.config.get('portfolio_tickers', []),
            sector_exposures=self.config.get('sector_exposures', {})
        )

        self.alert_delivery = AlertDelivery(self.config.get('delivery', {}))

        self.event_extractor = EventExtractor()
        self.signal_store = SignalStore()

        # Track processed items
        self.processed_items: Set[str] = set()

    def _load_config(self, config_path: Optional[str]) -> Dict:
        """Load configuration from file or use defaults"""

        default_config = {
            'portfolio_tickers': ['NVDA', 'MSFT', 'AAPL', 'GOOGL', 'META'],
            'sector_exposures': {
                'AI': 0.3,
                'Cloud': 0.2,
                'Healthcare': 0.15,
                'Financials': 0.1
            },
            'news_interval': 300,  # 5 minutes
            'sec_interval': 900,   # 15 minutes
            'delivery': {
                'email_enabled': False,
                'slack_enabled': False,
                'webhook_enabled': False
            }
        }

        if config_path and os.path.exists(config_path):
            with open(config_path, 'r') as f:
                loaded_config = json.load(f)
                default_config.update(loaded_config)

        return default_config

    async def start(self):
        """Start real-time monitoring"""
        self.running = True
        self.alert_delivery.start()

        logger.info("Real-time monitor started")
        logger.info(f"Monitoring tickers: {self.config['portfolio_tickers']}")
        logger.info(f"News interval: {self.config['news_interval']}s")
        logger.info(f"SEC interval: {self.config['sec_interval']}s")

        # Create monitoring tasks
        tasks = [
            asyncio.create_task(self._news_monitoring_loop()),
            asyncio.create_task(self._sec_monitoring_loop()),
            asyncio.create_task(self._graph_update_loop())
        ]

        try:
            await asyncio.gather(*tasks)
        except KeyboardInterrupt:
            logger.info("Monitor interrupted")
        finally:
            await self.stop()

    async def stop(self):
        """Stop real-time monitoring"""
        self.running = False
        self.alert_delivery.stop()
        logger.info("Real-time monitor stopped")

    async def _news_monitoring_loop(self):
        """Continuous news monitoring loop"""
        while self.running:
            try:
                # Poll for new articles
                articles = await self.news_poller.poll(self.config['portfolio_tickers'])

                # Process new articles
                for article in articles:
                    await self._process_news_article(article)

                # Sleep until next poll
                await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"News monitoring error: {e}")
                await asyncio.sleep(10)

    async def _sec_monitoring_loop(self):
        """Continuous SEC filing monitoring loop"""
        while self.running:
            try:
                # Poll for new filings
                filings = await self.sec_poller.poll(self.config['portfolio_tickers'])

                # Process new filings
                for filing in filings:
                    await self._process_sec_filing(filing)

                # Sleep until next poll
                await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"SEC monitoring error: {e}")
                await asyncio.sleep(10)

    async def _graph_update_loop(self):
        """Periodic graph update loop"""
        while self.running:
            try:
                # Update graph every 30 minutes
                await asyncio.sleep(1800)

                # Trigger incremental graph update
                await self._update_knowledge_graph()

            except Exception as e:
                logger.error(f"Graph update error: {e}")

    async def _process_news_article(self, article: Dict):
        """Process news article and generate alerts"""

        try:
            # Extract text content
            text = f"{article.get('title', '')} {article.get('description', '')}"
            ticker = article.get('ticker')

            # Extract events
            events = self.event_extractor.extract_events(
                text=text,
                ticker=ticker,
                document_date=datetime.fromisoformat(article.get('publishedAt', '').replace('Z', '+00:00'))
            )

            # Generate alerts for significant events
            for event in events:
                if event.confidence > 0.7:  # Only high-confidence events
                    alert = self.alert_classifier.classify_event(event, article)

                    # Queue for delivery
                    self.alert_delivery.queue_alert(alert)

                    # Store in signal store
                    self._store_event_signal(event, article)

        except Exception as e:
            logger.error(f"Article processing error: {e}")

    async def _process_sec_filing(self, filing: Dict):
        """Process SEC filing and generate alerts"""

        try:
            ticker = filing.get('ticker')

            # Create high-priority event for certain filing types
            filing_type = filing.get('form', '')

            if filing_type in ['8-K', '10-Q', '10-K']:
                # Create filing event
                event = EventNode(
                    id=f"sec_{ticker}_{filing.get('accessionNumber', '')}",
                    type=EventType.REGULATORY,
                    ticker=ticker,
                    date=datetime.now(),
                    description=f"New {filing_type} filing: {filing.get('primaryDocument', '')}",
                    impact="neutral",
                    confidence=1.0,
                    themes=["Regulatory", "Compliance"]
                )

                # Generate alert
                alert = self.alert_classifier.classify_event(event, filing)

                # For 8-K, elevate priority
                if filing_type == '8-K':
                    alert.priority = AlertPriority.HIGH

                # Queue for delivery
                self.alert_delivery.queue_alert(alert)

                # Store in signal store
                self._store_event_signal(event, filing)

        except Exception as e:
            logger.error(f"Filing processing error: {e}")

    def _store_event_signal(self, event: EventNode, source: Dict):
        """Store event in signal store for persistence"""

        try:
            self.signal_store.add_signal(
                signal_type='event',
                ticker=event.ticker,
                timestamp=event.date,
                data={
                    'event_type': event.type.value,
                    'impact': event.impact,
                    'magnitude': event.magnitude,
                    'confidence': event.confidence,
                    'themes': event.themes,
                    'description': event.description,
                    'source_url': source.get('url', ''),
                    'source_type': 'news' if 'title' in source else 'filing'
                },
                source=source.get('url', 'real-time-monitor')
            )

        except Exception as e:
            logger.error(f"Signal storage error: {e}")

    async def _update_knowledge_graph(self):
        """Trigger incremental knowledge graph update"""

        try:
            # Get recent signals from signal store
            recent_signals = self.signal_store.get_signals_since(
                datetime.now() - timedelta(hours=1)
            )

            # Convert to graph updates (simplified)
            logger.info(f"Updating knowledge graph with {len(recent_signals)} new signals")

            # Would integrate with LightRAG here for actual graph updates

        except Exception as e:
            logger.error(f"Graph update error: {e}")


async def main():
    """Main entry point for real-time monitor"""

    # Load configuration
    config_path = os.getenv('ICE_MONITOR_CONFIG', 'config/monitor.json')

    # Create and start monitor
    monitor = RealTimeMonitor(config_path)

    try:
        await monitor.start()
    except KeyboardInterrupt:
        print("\nShutting down monitor...")
        await monitor.stop()


if __name__ == "__main__":
    # Run the monitor
    asyncio.run(main())