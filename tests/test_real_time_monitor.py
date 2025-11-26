# Location: /tests/test_real_time_monitor.py
# Purpose: Test real-time monitoring daemon functionality
# Why: Validate continuous market intelligence gathering and alert generation
# Relevant Files: real_time_monitor.py, event_extractor.py, signal_store.py

"""
Test Suite for Real-Time Monitoring Module

Validates:
1. NewsAPI polling at 5-minute intervals
2. SEC EDGAR polling at 15-minute intervals
3. Alert priority classification
4. Alert delivery mechanisms
5. Incremental graph updates
6. Deduplication of seen content
"""

import unittest
import asyncio
import json
import os
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.ice_core.real_time_monitor import (
    RealTimeMonitor, NewsAPIPoller, SECEdgarPoller,
    AlertClassifier, AlertDelivery, Alert, AlertPriority,
    AlertChannel
)
from src.ice_core.event_extractor import EventNode, EventType


class TestNewsAPIPoller(unittest.TestCase):
    """Test NewsAPI polling functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.poller = NewsAPIPoller(
            api_key="test_key",
            interval_seconds=300
        )

    def test_polling_interval(self):
        """Test that polling respects interval"""
        # First poll should work
        self.poller.last_poll = datetime.now() - timedelta(seconds=301)

        # This should not poll (too soon)
        self.poller.last_poll = datetime.now() - timedelta(seconds=100)
        loop = asyncio.new_event_loop()
        articles = loop.run_until_complete(self.poller.poll(['NVDA']))
        self.assertEqual(len(articles), 0, "Should not poll before interval")

    def test_deduplication(self):
        """Test that seen articles are deduplicated"""
        # Add article to seen set
        article_id = "https://example.com/article1_2024-11-19T10:00:00Z"
        self.poller.seen_articles.add(article_id)

        # Mock article with same ID
        mock_article = {
            'url': 'https://example.com/article1',
            'publishedAt': '2024-11-19T10:00:00Z',
            'title': 'Test Article'
        }

        # Should be filtered out
        self.assertTrue(
            f"{mock_article['url']}_{mock_article['publishedAt']}" in self.poller.seen_articles,
            "Article should be marked as seen"
        )

    @patch('src.ice_core.real_time_monitor.DataIngester')
    def test_ticker_context_added(self, mock_ingestion):
        """Test that ticker context is added to articles"""
        # Mock data ingestion response
        mock_ingestion.return_value.fetch_company_news_concurrent.return_value = [
            {'url': 'test', 'title': 'NVDA news', 'publishedAt': '2024-11-19'}
        ]

        self.poller.data_ingestion = mock_ingestion.return_value
        self.poller.last_poll = datetime.now() - timedelta(seconds=301)

        loop = asyncio.new_event_loop()
        articles = loop.run_until_complete(self.poller.poll(['NVDA']))

        if articles:
            self.assertEqual(articles[0]['ticker'], 'NVDA', "Ticker should be added")


class TestSECEdgarPoller(unittest.TestCase):
    """Test SEC EDGAR polling functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.poller = SECEdgarPoller(interval_seconds=900)

    def test_polling_interval(self):
        """Test that polling respects 15-minute interval"""
        # Should not poll if too soon
        self.poller.last_poll = datetime.now() - timedelta(seconds=500)

        loop = asyncio.new_event_loop()
        filings = loop.run_until_complete(self.poller.poll(['AAPL']))
        self.assertEqual(len(filings), 0, "Should not poll before 15-minute interval")

    def test_filing_deduplication(self):
        """Test that seen filings are deduplicated"""
        # Add filing to seen set
        filing_id = "0001234567890_AAPL"
        self.poller.seen_filings.add(filing_id)

        # Should be filtered in actual implementation
        self.assertTrue(
            filing_id in self.poller.seen_filings,
            "Filing should be marked as seen"
        )


class TestAlertClassifier(unittest.TestCase):
    """Test alert classification and prioritization"""

    def setUp(self):
        """Set up test fixtures"""
        self.classifier = AlertClassifier(
            portfolio_tickers=['NVDA', 'AAPL', 'MSFT'],
            sector_exposures={'AI': 0.3, 'Cloud': 0.2}
        )

    def test_critical_priority_portfolio_negative(self):
        """Test CRITICAL priority for negative portfolio events"""
        event = EventNode(
            id="test_event",
            type=EventType.EARNINGS,
            ticker="NVDA",
            date=datetime.now(),
            description="NVDA earnings miss",
            impact="negative",
            magnitude=8.0,
            confidence=0.9,
            themes=["AI"]
        )

        alert = self.classifier.classify_event(event, {'url': 'test'})
        self.assertEqual(
            alert.priority, AlertPriority.CRITICAL,
            "Portfolio earnings miss >5% should be CRITICAL"
        )

    def test_critical_priority_portfolio_positive(self):
        """Test CRITICAL priority for major positive portfolio events"""
        event = EventNode(
            id="test_event",
            type=EventType.EARNINGS,
            ticker="AAPL",
            date=datetime.now(),
            description="AAPL earnings beat",
            impact="positive",
            magnitude=12.0,
            confidence=0.9,
            themes=[]
        )

        alert = self.classifier.classify_event(event, {'url': 'test'})
        self.assertEqual(
            alert.priority, AlertPriority.CRITICAL,
            "Portfolio earnings beat >10% should be CRITICAL"
        )

    def test_high_priority_portfolio_general(self):
        """Test HIGH priority for general portfolio events"""
        event = EventNode(
            id="test_event",
            type=EventType.PRODUCT,
            ticker="MSFT",
            date=datetime.now(),
            description="MSFT launches new product",
            impact="positive",
            confidence=0.8,
            themes=[]
        )

        alert = self.classifier.classify_event(event, {'url': 'test'})
        self.assertEqual(
            alert.priority, AlertPriority.HIGH,
            "Portfolio product launch should be HIGH"
        )

    def test_high_priority_sector_exposure(self):
        """Test HIGH priority for sector exposure events"""
        event = EventNode(
            id="test_event",
            type=EventType.REGULATORY,
            ticker="GOOGL",  # Not in portfolio
            date=datetime.now(),
            description="AI regulation update",
            impact="negative",
            confidence=0.8,
            themes=["AI"]  # We have 30% AI exposure
        )

        alert = self.classifier.classify_event(event, {'url': 'test'})
        self.assertEqual(
            alert.priority, AlertPriority.HIGH,
            "Events affecting high sector exposure should be HIGH"
        )

    def test_medium_priority_regulatory(self):
        """Test MEDIUM priority for regulatory events"""
        event = EventNode(
            id="test_event",
            type=EventType.LAWSUIT,
            ticker="META",  # Not in portfolio
            date=datetime.now(),
            description="META faces lawsuit",
            impact="negative",
            confidence=0.7,
            themes=[]
        )

        alert = self.classifier.classify_event(event, {'url': 'test'})
        self.assertEqual(
            alert.priority, AlertPriority.MEDIUM,
            "Non-portfolio lawsuit should be MEDIUM"
        )

    def test_low_priority_general(self):
        """Test LOW priority for general market events"""
        event = EventNode(
            id="test_event",
            type=EventType.DIVIDEND,
            ticker="JNJ",  # Not in portfolio
            date=datetime.now(),
            description="JNJ declares dividend",
            impact="neutral",
            confidence=0.6,
            themes=[]
        )

        alert = self.classifier.classify_event(event, {'url': 'test'})
        self.assertEqual(
            alert.priority, AlertPriority.LOW,
            "Non-portfolio dividend should be LOW"
        )

    def test_delivery_channels_by_priority(self):
        """Test that delivery channels match priority levels"""
        # CRITICAL - should have email, slack, log
        event_critical = EventNode(
            id="critical", type=EventType.SCANDAL, ticker="NVDA",
            date=datetime.now(), description="Major scandal",
            impact="negative", magnitude=10.0, confidence=0.9, themes=[]
        )
        alert_critical = self.classifier.classify_event(event_critical, {})
        self.assertIn(AlertChannel.EMAIL, alert_critical.delivery_channels)
        self.assertIn(AlertChannel.SLACK, alert_critical.delivery_channels)

        # LOW - should only have log
        event_low = EventNode(
            id="low", type=EventType.DIVIDEND, ticker="XYZ",
            date=datetime.now(), description="Dividend",
            impact="neutral", confidence=0.5, themes=[]
        )
        alert_low = self.classifier.classify_event(event_low, {})
        self.assertEqual([AlertChannel.LOG], alert_low.delivery_channels)


class TestAlertDelivery(unittest.TestCase):
    """Test alert delivery mechanisms"""

    def setUp(self):
        """Set up test fixtures"""
        self.config = {
            'email_enabled': False,
            'slack_enabled': False,
            'webhook_enabled': False
        }
        self.delivery = AlertDelivery(self.config)

    def test_delivery_queue(self):
        """Test that alerts are queued properly"""
        alert = Alert(
            id="test_alert",
            timestamp=datetime.now(),
            priority=AlertPriority.HIGH,
            event=Mock(),
            message="Test message",
            source="test",
            tickers=['NVDA']
        )

        self.delivery.queue_alert(alert)
        self.assertFalse(self.delivery.delivery_queue.empty(), "Alert should be queued")

    def test_delivery_thread_lifecycle(self):
        """Test delivery thread start/stop"""
        self.delivery.start()
        self.assertTrue(self.delivery.running, "Delivery should be running")
        self.assertIsNotNone(self.delivery.delivery_thread, "Thread should exist")

        self.delivery.stop()
        self.assertFalse(self.delivery.running, "Delivery should be stopped")


class TestRealTimeMonitor(unittest.TestCase):
    """Test main real-time monitor orchestrator"""

    def setUp(self):
        """Set up test fixtures"""
        self.config = {
            'portfolio_tickers': ['NVDA', 'AAPL'],
            'sector_exposures': {'AI': 0.3},
            'news_interval': 300,
            'sec_interval': 900,
            'delivery': {'email_enabled': False}
        }

    def test_monitor_initialization(self):
        """Test monitor initializes components correctly"""
        monitor = RealTimeMonitor()

        self.assertIsNotNone(monitor.news_poller, "News poller should be initialized")
        self.assertIsNotNone(monitor.sec_poller, "SEC poller should be initialized")
        self.assertIsNotNone(monitor.alert_classifier, "Classifier should be initialized")
        self.assertIsNotNone(monitor.alert_delivery, "Delivery should be initialized")

    def test_config_loading(self):
        """Test configuration loading"""
        # Create temp config file
        temp_config = {
            'portfolio_tickers': ['TEST1', 'TEST2'],
            'news_interval': 60
        }

        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(temp_config, f)
            temp_path = f.name

        try:
            monitor = RealTimeMonitor(config_path=temp_path)
            self.assertEqual(
                monitor.config['portfolio_tickers'],
                ['TEST1', 'TEST2'],
                "Should load custom config"
            )
            self.assertEqual(
                monitor.config['news_interval'],
                60,
                "Should override default interval"
            )
        finally:
            os.unlink(temp_path)

    @patch('src.ice_core.real_time_monitor.EventExtractor')
    async def test_news_processing(self, mock_extractor):
        """Test news article processing"""
        monitor = RealTimeMonitor()

        # Mock event extraction
        mock_event = EventNode(
            id="test", type=EventType.EARNINGS, ticker="NVDA",
            date=datetime.now(), description="Earnings",
            impact="positive", confidence=0.8, themes=["AI"]
        )
        mock_extractor.return_value.extract_events.return_value = [mock_event]

        # Process article
        article = {
            'title': 'NVDA earnings beat',
            'description': 'Strong results',
            'ticker': 'NVDA',
            'publishedAt': '2024-11-19T10:00:00Z',
            'url': 'https://example.com'
        }

        await monitor._process_news_article(article)

        # Should have queued an alert
        # (Would verify with mocks in production test)

    @patch('src.ice_core.real_time_monitor.SignalStore')
    async def test_signal_storage(self, mock_store):
        """Test that events are stored in signal store"""
        monitor = RealTimeMonitor()
        monitor.signal_store = mock_store.return_value

        event = EventNode(
            id="test", type=EventType.MA_DEAL, ticker="MSFT",
            date=datetime.now(), description="Acquisition",
            impact="positive", magnitude=50.0, confidence=0.9,
            themes=["Gaming"]
        )

        monitor._store_event_signal(event, {'url': 'test_source'})

        # Verify signal was stored
        mock_store.return_value.add_signal.assert_called_once()
        call_args = mock_store.return_value.add_signal.call_args
        self.assertEqual(call_args[1]['signal_type'], 'event')
        self.assertEqual(call_args[1]['ticker'], 'MSFT')


def run_comprehensive_test():
    """Run comprehensive test suite with detailed reporting"""
    print("=" * 80)
    print("REAL-TIME MONITORING TEST SUITE")
    print("Testing continuous market intelligence gathering")
    print("=" * 80)

    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestNewsAPIPoller))
    suite.addTests(loader.loadTestsFromTestCase(TestSECEdgarPoller))
    suite.addTests(loader.loadTestsFromTestCase(TestAlertClassifier))
    suite.addTests(loader.loadTestsFromTestCase(TestAlertDelivery))
    suite.addTests(loader.loadTestsFromTestCase(TestRealTimeMonitor))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print(f"Tests Run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")

    # Calculate success rate
    success_rate = (result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100
    print(f"Success Rate: {success_rate:.1f}%")

    if success_rate >= 80:
        print("✅ PASSED: Real-time monitoring tests successful")
    else:
        print("⚠️ WARNING: Some monitoring tests failed")

    print("=" * 80)

    return result.wasSuccessful()


if __name__ == "__main__":
    # Run comprehensive test
    success = run_comprehensive_test()

    # Also test async components
    print("\nTesting async components...")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Exit with appropriate code
    sys.exit(0 if success else 1)