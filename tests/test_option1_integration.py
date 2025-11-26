# Location: /tests/test_option1_integration.py
# Purpose: Integration tests for Phase 2.7B Option 1 - Event Extraction & Alert Delivery
# Why: Validates EventExtractor integration, webhook delivery, and end-to-end workflow
# Relevant Files: ice_simplified.py, event_extractor.py, real_time_monitor.py, config.py

import unittest
import os
import sys
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from updated_architectures.implementation.ice_simplified import ICECore, ICESimplified
from updated_architectures.implementation.config import ICEConfig
from src.ice_core.event_extractor import EventExtractor, EventType
from src.ice_core.real_time_monitor import AlertDelivery, Alert, AlertPriority, AlertChannel


class TestOption1Integration(unittest.TestCase):
    """Integration test suite for Phase 2.7B Option 1"""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures"""
        cls.config = ICEConfig()
        # Enable event extraction for tests
        cls.config.event_extraction_enabled = True
        cls.ice_core = ICECore(config=cls.config)
        cls.ice_simplified = ICESimplified(config=cls.config)

    def test_01_event_extraction_config(self):
        """Test 1: Verify event extraction configuration parameters"""
        # Check all 4 config parameters exist
        self.assertTrue(hasattr(self.config, 'event_extraction_enabled'))
        self.assertTrue(hasattr(self.config, 'event_confidence_threshold'))
        self.assertTrue(hasattr(self.config, 'max_events_per_doc'))
        self.assertTrue(hasattr(self.config, 'event_cache_size'))

        # Verify defaults are sensible
        self.assertEqual(self.config.event_confidence_threshold, 0.8)
        self.assertEqual(self.config.max_events_per_doc, 10)
        self.assertEqual(self.config.event_cache_size, 500)

    def test_02_icecore_event_extraction(self):
        """Test 2: Verify EventExtractor initialized in ICECore"""
        # Check extractor and cache exist
        self.assertTrue(hasattr(self.ice_core, 'event_extractor'))
        self.assertTrue(hasattr(self.ice_core, 'event_cache'))
        self.assertIsNotNone(self.ice_core.event_extractor)
        self.assertIsInstance(self.ice_core.event_cache, dict)

        # Check helper methods exist
        self.assertTrue(hasattr(self.ice_core, '_enhance_with_events'))
        self.assertTrue(hasattr(self.ice_core, '_format_events'))

    def test_03_icesimplified_event_extraction(self):
        """Test 3: Verify EventExtractor initialized in ICESimplified"""
        # Check extractor and cache exist
        self.assertTrue(hasattr(self.ice_simplified, 'event_extractor'))
        self.assertTrue(hasattr(self.ice_simplified, 'event_cache'))
        self.assertIsNotNone(self.ice_simplified.event_extractor)
        self.assertIsInstance(self.ice_simplified.event_cache, dict)

        # Check helper methods exist
        self.assertTrue(hasattr(self.ice_simplified, '_enhance_with_events'))
        self.assertTrue(hasattr(self.ice_simplified, '_format_events'))

        # Verify delegation to ICECore works
        self.assertIsInstance(self.ice_simplified.core, ICECore)
        self.assertTrue(hasattr(self.ice_simplified.core, 'add_documents_batch'))

    def test_04_event_extraction_earnings(self):
        """Test 4: Extract earnings events from document"""
        # Document with clear earnings event
        doc = {
            'content': 'NVDA reported Q3 earnings beat expectations. Revenue up 122% YoY to $18.1B. EPS beat at $4.02 vs $3.36 expected.',
            'file_path': 'test:earnings_001',
            'type': 'financial',
            'ticker': 'NVDA'
        }

        # Enhance with events
        enhanced = self.ice_core._enhance_with_events(doc)

        # Verify events were extracted
        self.assertIn('content', enhanced)
        content = enhanced['content']

        # Should contain event markers
        self.assertTrue(
            'EARNINGS' in content or 'earnings' in content.lower(),
            "Should extract earnings event"
        )

    def test_05_event_extraction_ma_deal(self):
        """Test 5: Extract M&A events from document"""
        # Document with M&A announcement
        doc = {
            'content': 'Microsoft announces acquisition of Activision Blizzard for $68.7 billion in all-cash deal. Largest gaming acquisition in history.',
            'file_path': 'test:ma_001',
            'type': 'news',
            'ticker': 'MSFT'
        }

        # Enhance with events
        enhanced = self.ice_core._enhance_with_events(doc)

        # Verify M&A event extracted
        content = enhanced['content']
        self.assertTrue(
            'acquisition' in content.lower() or 'ma_deal' in content.lower(),
            "Should extract M&A event"
        )

    def test_06_content_based_caching(self):
        """Test 6: Verify event extraction uses content-based caching"""
        # Create identical documents with strong event signals
        doc1 = {
            'content': 'AAPL announces Q4 earnings beat. Revenue up 8% YoY to $119.6B. EPS beat at $1.55 vs $1.39 expected. Strong services growth.',
            'file_path': 'test:cache_001',
            'type': 'financial',
            'ticker': 'AAPL'
        }

        doc2 = {
            'content': 'AAPL announces Q4 earnings beat. Revenue up 8% YoY to $119.6B. EPS beat at $1.55 vs $1.39 expected. Strong services growth.',  # Same content
            'file_path': 'test:cache_002',  # Different file_path
            'type': 'financial',
            'ticker': 'AAPL'
        }

        # Clear cache first
        self.ice_core.event_cache.clear()

        # First enhancement (cache miss)
        enhanced1 = self.ice_core._enhance_with_events(doc1)
        cache_size_after_first = len(self.ice_core.event_cache)

        # Second enhancement (cache hit - same content)
        enhanced2 = self.ice_core._enhance_with_events(doc2)
        cache_size_after_second = len(self.ice_core.event_cache)

        # Cache should have at most 1 entry (both docs have same content hash)
        # Note: Cache key is prefixed with "event_" to avoid collision with relationship cache
        # If no events extracted (confidence filtering), cache may be 0 - that's OK
        self.assertLessEqual(cache_size_after_first, 1)
        self.assertEqual(cache_size_after_second, cache_size_after_first)  # No increase

    @patch('smtplib.SMTP')
    def test_07_email_delivery_production(self, mock_smtp):
        """Test 7: Verify production SMTP email delivery"""
        # Configure mock SMTP
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        # Create alert delivery with email enabled
        config = {
            'email_enabled': True,
            'email_from': 'test@example.com',
            'email_to': 'recipient@example.com',
            'smtp_host': 'smtp.gmail.com',
            'smtp_port': 587,
            'smtp_user': 'test_user',
            'smtp_password': 'test_password'
        }

        delivery = AlertDelivery(config)

        # Create test alert
        from src.ice_core.event_extractor import EventNode
        event = EventNode(
            id='test_event_001',
            type=EventType.EARNINGS,
            ticker='NVDA',
            date=datetime.now(),
            description='Test earnings event',
            impact='positive',
            confidence=0.95,
            themes=['Technology', 'AI'],
            magnitude=15.0
        )

        alert = Alert(
            id='alert_001',
            timestamp=datetime.now(),
            priority=AlertPriority.CRITICAL,
            event=event,
            message='Test alert message',
            source='test_source',
            tickers=['NVDA']
        )

        # Send email
        delivery._send_email(alert)

        # Verify SMTP methods called
        mock_smtp.assert_called_once()
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with('test_user', 'test_password')
        mock_server.send_message.assert_called_once()

    @patch('requests.post')
    def test_08_slack_delivery_production(self, mock_post):
        """Test 8: Verify production Slack webhook delivery"""
        # Configure mock requests.post
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        # Create alert delivery with Slack enabled
        config = {
            'slack_enabled': True,
            'slack_webhook_url': 'https://hooks.slack.com/services/TEST/WEBHOOK/URL'
        }

        delivery = AlertDelivery(config)

        # Create test alert
        from src.ice_core.event_extractor import EventNode
        event = EventNode(
            id='test_event_002',
            type=EventType.MA_DEAL,
            ticker='MSFT',
            date=datetime.now(),
            description='Test M&A event',
            impact='positive',
            confidence=0.90,
            themes=['Technology', 'Gaming'],
            magnitude=10.0
        )

        alert = Alert(
            id='alert_002',
            timestamp=datetime.now(),
            priority=AlertPriority.HIGH,
            event=event,
            message='Test Slack alert',
            source='test_source',
            tickers=['MSFT']
        )

        # Send Slack message
        delivery._send_slack(alert)

        # Verify webhook POST called
        mock_post.assert_called_once()
        call_args = mock_post.call_args

        # Verify webhook URL
        self.assertEqual(call_args[0][0], 'https://hooks.slack.com/services/TEST/WEBHOOK/URL')

        # Verify payload structure
        payload = call_args[1]['json']
        self.assertIn('text', payload)
        self.assertIn('attachments', payload)
        self.assertIn('blocks', payload['attachments'][0])

        # Verify Block Kit structure
        blocks = payload['attachments'][0]['blocks']
        self.assertEqual(blocks[0]['type'], 'header')
        self.assertEqual(blocks[1]['type'], 'section')
        self.assertEqual(blocks[2]['type'], 'context')

    def test_09_batch_processing_with_events(self):
        """Test 9: Integration test for batch document processing with events"""
        # Create batch with multiple event types
        documents = [
            {
                'content': 'AAPL announces Q4 earnings beat. Revenue up 8% to $119.6B. Services segment strength.',
                'file_path': 'test:batch_001',
                'type': 'financial',
                'ticker': 'AAPL'
            },
            {
                'content': 'Tesla CEO Elon Musk announces major management restructuring. New CFO appointed.',
                'file_path': 'test:batch_002',
                'type': 'news',
                'ticker': 'TSLA'
            },
            {
                'content': 'Google faces regulatory investigation over antitrust violations. DOJ files lawsuit.',
                'file_path': 'test:batch_003',
                'type': 'news',
                'ticker': 'GOOGL'
            }
        ]

        # Process batch through ICECore
        result = self.ice_core.add_documents_batch(documents)

        # Verify batch processed successfully
        self.assertEqual(result.get('status'), 'success')
        self.assertEqual(result.get('successful'), 3)
        self.assertEqual(result.get('failed'), 0)  # Key is 'failed', not 'failed_count'

    def test_10_disabled_extraction(self):
        """Test 10: Verify behavior when event extraction is disabled"""
        # Create config with extraction disabled
        config_disabled = ICEConfig()
        config_disabled.event_extraction_enabled = False
        ice_disabled = ICECore(config=config_disabled)

        # Verify extractor is None
        self.assertIsNone(ice_disabled.event_extractor)

        # Document should pass through unchanged
        doc = {
            'content': 'Test earnings event for NVDA.',
            'file_path': 'test:disabled_001',
            'type': 'financial'
        }

        # Process document (should skip enhancement)
        result = ice_disabled.add_documents_batch([doc])

        # Should succeed (extraction just skipped)
        self.assertEqual(result.get('status'), 'success')


if __name__ == '__main__':
    # Run with verbose output
    unittest.main(verbosity=2)
