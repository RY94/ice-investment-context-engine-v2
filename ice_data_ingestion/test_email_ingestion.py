# /Users/royyeo/Library/CloudStorage/OneDrive-NationalUniversityofSingapore/Capstone Project/ice_data_ingestion/test_email_ingestion.py
# Comprehensive test scenarios for unified email ingestion module
# Tests edge cases, error handling, and investment-specific extraction
# RELEVANT FILES: email_ingestion_unified.py, test_scenarios.py, robust_client.py

"""
Test Suite for Email Ingestion Module

Comprehensive tests covering:
- Connection resilience and retry logic
- Edge case handling (malformed data, large attachments)
- Investment entity extraction accuracy
- Deduplication and state persistence
- Performance under load
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import email
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import json
import imaplib
import ssl

from email_ingestion_unified import (
    EmailIngestionClient,
    EmailMetadata,
    EmailContent,
    ProcessedEmail,
    EmailIngestionState
)


class TestEmailIngestionState(unittest.TestCase):
    """Test state persistence and recovery"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.state_file = Path(self.temp_dir) / "test_state.json"

    def test_state_initialization(self):
        """Test state initialization with no existing file"""
        state = EmailIngestionState(self.state_file)
        self.assertIsNotNone(state.state)
        self.assertIn('folder_uids', state.state)
        self.assertIn('processed_message_ids', state.state)

    def test_state_persistence(self):
        """Test saving and loading state"""
        state = EmailIngestionState(self.state_file)

        # Add some data
        state.update_uid("INBOX", "12345")
        state.mark_processed("<msg123@example.com>")
        state.add_failed({"msg_id": "789", "error": "test error"})

        # Save and reload
        state.save()
        new_state = EmailIngestionState(self.state_file)

        # Verify persistence
        self.assertEqual(new_state.get_last_uid("INBOX"), "12345")
        self.assertTrue(new_state.is_processed("<msg123@example.com>"))
        self.assertEqual(len(new_state.state.get('failed_emails', [])), 1)

    def test_deduplication(self):
        """Test message deduplication"""
        state = EmailIngestionState(self.state_file)

        # Mark as processed
        state.mark_processed("<duplicate@example.com>")
        self.assertTrue(state.is_processed("<duplicate@example.com>"))
        self.assertFalse(state.is_processed("<new@example.com>"))


class TestEmailIngestionClient(unittest.TestCase):
    """Test main email ingestion client"""

    def setUp(self):
        self.client = EmailIngestionClient()

    @patch('imaplib.IMAP4_SSL')
    def test_connection_success(self, mock_imap):
        """Test successful IMAP connection"""
        mock_instance = MagicMock()
        mock_imap.return_value = mock_instance
        mock_instance.login.return_value = ('OK', [])

        result = self.client.connect("test@example.com", "password")
        self.assertTrue(result)
        mock_instance.login.assert_called_once_with("test@example.com", "password")

    @patch('imaplib.IMAP4_SSL')
    def test_connection_failure_retry(self, mock_imap):
        """Test connection retry on failure"""
        mock_imap.side_effect = [Exception("Connection failed"), MagicMock()]

        result = self.client.connect("test@example.com", "password")
        self.assertFalse(result)  # Should fail after retries

    @patch('imaplib.IMAP4_SSL')
    def test_oauth_authentication(self, mock_imap):
        """Test OAuth2 authentication"""
        mock_instance = MagicMock()
        mock_imap.return_value = mock_instance

        result = self.client.connect("test@example.com", "oauth_token", use_oauth=True)
        mock_instance.authenticate.assert_called_once_with('XOAUTH2', unittest.mock.ANY)

    def test_metadata_extraction(self):
        """Test comprehensive metadata extraction"""
        # Create test email message
        msg = email.message.EmailMessage()
        msg['Subject'] = 'URGENT: AAPL Earnings Beat Expectations'
        msg['From'] = 'research@bloomberg.com'
        msg['To'] = 'investor@example.com'
        msg['Date'] = 'Mon, 1 Jan 2024 10:00:00 +0000'
        msg['Message-ID'] = '<unique123@bloomberg.com>'
        msg['Importance'] = 'High'

        metadata = self.client._extract_metadata(msg, "123", "INBOX")

        # Verify metadata
        self.assertEqual(metadata.subject, 'URGENT: AAPL Earnings Beat Expectations')
        self.assertEqual(metadata.sender_category, 'news')
        self.assertTrue(metadata.contains_tickers)
        self.assertGreater(metadata.priority, 50)  # High priority
        self.assertEqual(metadata.importance, 'high')

    def test_content_extraction_plain_text(self):
        """Test content extraction from plain text email"""
        msg = email.message.EmailMessage()
        msg.set_content("""
        Apple (AAPL) reported Q4 earnings of $1.29 per share, beating estimates by 5%.
        Revenue came in at $90.1 billion, up 8% YoY.

        We maintain our BUY rating with a price target of $200.

        Key metrics:
        - iPhone sales: +12%
        - Services revenue: $20B
        - Gross margin: 43.5%
        """)

        content = self.client._extract_content(msg)

        # Verify extraction
        self.assertIn('AAPL', content.tickers)
        self.assertTrue(any('1.29' in p['value'] for p in content.price_mentions))
        self.assertIn('5', content.percentages)
        self.assertTrue(any('BUY' in r['rating'] for r in content.ratings))
        self.assertIn('earnings', content.topics)
        self.assertGreater(content.sentiment['bullish'], 0)

    def test_content_extraction_html_email(self):
        """Test content extraction from HTML email"""
        msg = email.message.EmailMessage()
        msg.add_alternative("""
        <html>
            <body>
                <h2>Market Update</h2>
                <table>
                    <tr><th>Stock</th><th>Price</th><th>Change</th></tr>
                    <tr><td>MSFT</td><td>$380.50</td><td>+2.3%</td></tr>
                    <tr><td>GOOGL</td><td>$140.25</td><td>-1.2%</td></tr>
                </table>
                <p>Visit our <a href="https://research.example.com">research portal</a></p>
            </body>
        </html>
        """, subtype='html')

        content = self.client._extract_content(msg)

        # Verify extraction
        self.assertIn('MSFT', content.tickers)
        self.assertIn('GOOGL', content.tickers)
        self.assertTrue(len(content.embedded_tables) > 0)
        self.assertTrue(len(content.links) > 0)
        self.assertEqual(content.links[0]['url'], 'https://research.example.com')

    def test_malformed_header_handling(self):
        """Test handling of malformed email headers"""
        # Test various malformed headers
        test_cases = [
            b'=?UTF-8?B?bWFsZm9ybWVk',  # Incomplete base64
            'Subject with \x00 null bytes',
            '=?UNKNOWN-ENCODING?Q?test?=',
            None,
            ''
        ]

        for test_value in test_cases:
            result = self.client._decode_header_safe(test_value)
            self.assertIsInstance(result, str)
            self.assertNotIn('\x00', result)  # No null bytes

    def test_attachment_processing(self):
        """Test attachment extraction and processing"""
        msg = email.message.EmailMessage()
        msg['Subject'] = 'Research Report'

        # Add text attachment
        msg.add_attachment(
            b'Quarterly earnings data...',
            maintype='text',
            subtype='plain',
            filename='earnings.txt'
        )

        # Add PDF attachment (mock)
        msg.add_attachment(
            b'%PDF-1.4 mock pdf content',
            maintype='application',
            subtype='pdf',
            filename='report.pdf'
        )

        content = self.client._extract_content(msg)

        # Verify attachments
        self.assertEqual(len(content.attachments), 2)
        self.assertEqual(content.attachments[0]['filename'], 'earnings.txt')
        self.assertIn('extracted_text', content.attachments[0])
        self.assertEqual(content.attachments[1]['filename'], 'report.pdf')

    def test_large_email_handling(self):
        """Test handling of large emails with many attachments"""
        msg = email.message.EmailMessage()
        msg['Subject'] = 'Large Report Package'

        # Add large body
        large_text = "x" * 1000000  # 1MB of text
        msg.set_content(large_text)

        # Add multiple attachments
        for i in range(20):
            msg.add_attachment(
                b'attachment content',
                maintype='application',
                subtype='octet-stream',
                filename=f'file_{i}.dat'
            )

        # Process should not crash
        content = self.client._extract_content(msg)
        self.assertEqual(len(content.attachments), 20)
        self.assertLessEqual(len(content.summary), 250)  # Summary is limited

    def test_thread_reconstruction(self):
        """Test email thread tracking"""
        # First email
        msg1 = email.message.EmailMessage()
        msg1['Message-ID'] = '<msg1@example.com>'
        msg1['Subject'] = 'Initial inquiry'

        # Reply
        msg2 = email.message.EmailMessage()
        msg2['Message-ID'] = '<msg2@example.com>'
        msg2['In-Reply-To'] = '<msg1@example.com>'
        msg2['References'] = '<msg1@example.com>'
        msg2['Subject'] = 'Re: Initial inquiry'

        metadata1 = self.client._extract_metadata(msg1, "1", "INBOX")
        metadata2 = self.client._extract_metadata(msg2, "2", "INBOX")

        self.assertEqual(metadata2.in_reply_to, '<msg1@example.com>')
        self.assertIn('<msg1@example.com>', metadata2.references)

    def test_ticker_extraction_edge_cases(self):
        """Test ticker extraction with edge cases"""
        test_cases = [
            ("Buy AAPL at $150", ["AAPL"]),
            ("CEO announced IPO plans", []),  # IPO should be filtered
            ("MSFT.O and GOOGL.N are trending", ["MSFT", "GOOGL"]),
            ("The NYSE and NASDAQ indices", []),  # Exchanges filtered
            ("FB is now META", ["FB", "META"]),
            ("A B C D E", ["A", "B", "C", "D", "E"]),  # Single letters
        ]

        for text, expected in test_cases:
            tickers = self.client._extract_tickers(text)
            for ticker in expected:
                self.assertIn(ticker, tickers)

    def test_investment_sentiment_analysis(self):
        """Test investment sentiment detection"""
        test_cases = [
            ("Strong buy recommendation, upgrade to outperform", "bullish"),
            ("Sell immediately, major concerns about guidance", "bearish"),
            ("Maintain hold, neutral outlook", "neutral"),
            ("Mixed signals with both risks and opportunities", "neutral")
        ]

        for text, expected_sentiment in test_cases:
            sentiment = self.client._analyze_sentiment(text)
            self.assertGreater(
                sentiment[expected_sentiment],
                max(sentiment[s] for s in sentiment if s != expected_sentiment) * 0.8
            )

    def test_priority_calculation(self):
        """Test email priority calculation"""
        # High priority email
        msg_high = email.message.EmailMessage()
        msg_high['Subject'] = 'URGENT: Breaking News - TSLA Halted'
        msg_high['From'] = 'alerts@bloomberg.com'
        msg_high['Importance'] = 'High'

        priority_high = self.client._calculate_priority(
            msg_high['Subject'],
            msg_high['From'],
            msg_high
        )

        # Low priority email
        msg_low = email.message.EmailMessage()
        msg_low['Subject'] = 'Weekly newsletter'
        msg_low['From'] = 'info@randomsite.com'

        priority_low = self.client._calculate_priority(
            msg_low['Subject'],
            msg_low['From'],
            msg_low
        )

        self.assertGreater(priority_high, 70)
        self.assertLess(priority_low, 30)

    def test_quoted_text_removal(self):
        """Test removal of quoted reply text"""
        text_with_quotes = """
        This is the new content.

        Here's my response.

        On Jan 1, 2024 someone wrote:
        > This is quoted text
        > Should be removed
        """

        cleaned = self.client._remove_quoted_text(text_with_quotes)
        self.assertNotIn("> This is quoted", cleaned)
        self.assertNotIn("Should be removed", cleaned)
        self.assertIn("This is the new content", cleaned)

    def test_encoding_detection(self):
        """Test character encoding detection and handling"""
        # Various encodings
        test_strings = [
            "UTF-8: café ☕".encode('utf-8'),
            "Latin-1: café".encode('latin-1'),
            "Windows-1252: smart "quotes"".encode('windows-1252', errors='ignore'),
            "ASCII: plain text".encode('ascii')
        ]

        for encoded in test_strings:
            # Should handle without crashing
            msg = email.message.EmailMessage()
            msg.set_payload(encoded)
            content = self.client._extract_content(msg)
            self.assertIsInstance(content.body_text, str)

    def test_date_extraction(self):
        """Test date mention extraction"""
        text = """
        Earnings call scheduled for January 15, 2024.
        Q4 results due on 2024-01-31.
        Previous guidance from 12/01/2023 remains unchanged.
        """

        dates = self.client._extract_dates(text)
        self.assertGreater(len(dates), 0)  # Should find at least one date

    def test_quality_score_calculation(self):
        """Test email quality scoring"""
        # High quality email
        metadata_high = EmailMetadata(
            uid="1",
            message_id="<real@bloomberg.com>",
            subject="AAPL Earnings",
            sender="research@bloomberg.com",
            recipients=["user@example.com"],
            date=datetime.now(),
            contains_research=True,
            sender_category="news"
        )

        content_high = EmailContent(
            body_text="Detailed analysis " * 50,
            tickers=["AAPL", "MSFT"],
            companies=["Apple Inc.", "Microsoft Corp"],
            price_mentions=[{"value": "150.00"}],
            attachments=[{"filename": "report.pdf"}]
        )

        score_high = self.client._calculate_quality_score(metadata_high, content_high)

        # Low quality email
        metadata_low = EmailMetadata(
            uid="2",
            message_id="<generated-2@local>",
            subject="Hi",
            sender="random@gmail.com",
            recipients=["user@example.com"],
            date=datetime.now(),
            sender_category="personal"
        )

        content_low = EmailContent(body_text="Short message")

        score_low = self.client._calculate_quality_score(metadata_low, content_low)

        self.assertGreater(score_high, 0.8)
        self.assertLess(score_low, 0.6)

    @patch.object(EmailIngestionClient, 'ensure_connection')
    @patch.object(EmailIngestionClient, '_process_single_email')
    def test_batch_processing(self, mock_process, mock_ensure):
        """Test batch email processing"""
        mock_ensure.return_value = True

        # Mock IMAP responses
        self.client.imap = MagicMock()
        self.client.imap.select.return_value = ('OK', [])
        self.client.imap.search.return_value = ('OK', [b'1 2 3 4 5'])

        # Mock processing
        mock_process.return_value = ProcessedEmail(
            metadata=MagicMock(),
            content=MagicMock(),
            processing_timestamp=datetime.now(),
            quality_score=0.8
        )

        # Process batch
        results = self.client.fetch_emails_batch(batch_size=2)

        # Should process all 5 emails in batches
        self.assertEqual(mock_process.call_count, 5)
        self.assertEqual(len(results), 5)

    def test_retry_failed_emails(self):
        """Test retry mechanism for failed emails"""
        # Add failed emails to state
        self.client.state.add_failed({
            'msg_id': '123',
            'folder': 'INBOX',
            'error': 'Test error'
        })

        with patch.object(self.client, '_process_single_email') as mock_process:
            mock_process.return_value = MagicMock()

            results = self.client.retry_failed_emails()

            mock_process.assert_called_once()
            self.assertEqual(len(results), 1)

    def test_statistics_tracking(self):
        """Test statistics collection"""
        # Simulate processing
        self.client.stats['emails_processed'] = 100
        self.client.stats['emails_failed'] = 5
        self.client.stats['attachments_processed'] = 25

        stats = self.client.get_statistics()

        self.assertEqual(stats['emails_processed'], 100)
        self.assertEqual(stats['emails_failed'], 5)
        self.assertEqual(stats['attachments_processed'], 25)
        self.assertIn('state', stats)


class TestEdgeCases(unittest.TestCase):
    """Test extreme edge cases and error conditions"""

    def setUp(self):
        self.client = EmailIngestionClient()

    def test_empty_email(self):
        """Test handling of completely empty email"""
        msg = email.message.EmailMessage()

        # Should not crash
        metadata = self.client._extract_metadata(msg, "1", "INBOX")
        content = self.client._extract_content(msg)

        self.assertIsNotNone(metadata)
        self.assertIsNotNone(content)
        self.assertEqual(content.body_text, "")

    def test_circular_references(self):
        """Test handling of circular email references"""
        msg = email.message.EmailMessage()
        msg['Message-ID'] = '<circular@example.com>'
        msg['In-Reply-To'] = '<circular@example.com>'  # Points to itself
        msg['References'] = '<circular@example.com>'

        # Should not cause infinite loop
        metadata = self.client._extract_metadata(msg, "1", "INBOX")
        self.assertEqual(metadata.message_id, '<circular@example.com>')

    def test_massive_recipient_list(self):
        """Test handling of emails with huge recipient lists"""
        recipients = ', '.join([f'user{i}@example.com' for i in range(1000)])

        msg = email.message.EmailMessage()
        msg['To'] = recipients[:500]  # Truncate for header limit
        msg['Cc'] = recipients[500:]

        metadata = self.client._extract_metadata(msg, "1", "INBOX")
        self.assertGreater(len(metadata.recipients), 0)

    def test_binary_content_in_text(self):
        """Test handling of binary data in text fields"""
        msg = email.message.EmailMessage()
        msg.set_content(b'\x00\x01\x02\x03\xff\xfe\xfd', maintype='text', subtype='plain')

        # Should not crash
        content = self.client._extract_content(msg)
        self.assertIsInstance(content.body_text, str)

    def test_deeply_nested_multipart(self):
        """Test handling of deeply nested multipart messages"""
        msg = email.message.EmailMessage()
        current = msg

        # Create deep nesting
        for i in range(10):
            part = email.message.EmailMessage()
            part.set_content(f"Level {i}")
            current.attach(part)
            current = part

        # Should handle without stack overflow
        content = self.client._extract_content(msg)
        self.assertIsNotNone(content)


class TestPerformance(unittest.TestCase):
    """Test performance characteristics"""

    def setUp(self):
        self.client = EmailIngestionClient()

    def test_large_batch_memory_usage(self):
        """Test memory efficiency with large batches"""
        # Create 100 test emails
        emails = []
        for i in range(100):
            msg = email.message.EmailMessage()
            msg['Subject'] = f'Test email {i}'
            msg['Message-ID'] = f'<msg{i}@test.com>'
            msg.set_content(f'Content {i}' * 100)
            emails.append(msg)

        # Process should handle efficiently
        for msg in emails:
            metadata = self.client._extract_metadata(msg, str(len(emails)), "INBOX")
            content = self.client._extract_content(msg)

            # Verify basic extraction
            self.assertIsNotNone(metadata)
            self.assertIsNotNone(content)

    def test_parallel_processing(self):
        """Test parallel processing capabilities"""
        from concurrent.futures import ThreadPoolExecutor

        def process_email(i):
            msg = email.message.EmailMessage()
            msg['Subject'] = f'Parallel test {i}'
            msg.set_content(f'Content {i}')
            return self.client._extract_content(msg)

        # Process in parallel
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(process_email, i) for i in range(20)]
            results = [f.result() for f in futures]

        self.assertEqual(len(results), 20)
        for result in results:
            self.assertIsNotNone(result)


if __name__ == '__main__':
    # Run tests with verbosity
    unittest.main(verbosity=2)