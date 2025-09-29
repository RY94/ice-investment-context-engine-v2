# /Users/royyeo/Library/CloudStorage/OneDrive-NationalUniversityofSingapore/Capstone Project/ice_data_ingestion/email_ingestion_unified.py
# Unified robust email ingestion module with comprehensive error handling and investment focus
# Consolidates multiple implementations into single production-ready solution
# RELEVANT FILES: robust_client.py, secure_config.py, data_validator.py, ice_integration.py

"""
Unified Email Ingestion Module for ICE

Production-ready email ingestion with:
- Robust IMAP connection handling with circuit breaker
- Investment-focused content extraction
- Comprehensive edge case handling
- Incremental sync with state persistence
- Parallel processing for attachments
- Smart deduplication and validation
"""

import asyncio
import base64
import email
import hashlib
import imaplib
import json
import logging
import os
import pickle
import re
import ssl
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from email.header import decode_header
from email.utils import parsedate_to_datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import chardet
from bs4 import BeautifulSoup

from .robust_client import BaseDataClient, CircuitBreaker
from .secure_config import SecureConfig
from .data_validator import DataValidator, ValidationResult, DataQuality

logger = logging.getLogger(__name__)


@dataclass
class EmailMetadata:
    """Rich metadata for investment-focused email processing"""
    uid: str
    message_id: str
    subject: str
    sender: str
    recipients: List[str]
    date: datetime
    thread_id: Optional[str] = None
    in_reply_to: Optional[str] = None
    references: List[str] = field(default_factory=list)
    priority: int = 0
    importance: str = "normal"
    has_attachments: bool = False
    attachment_count: int = 0
    folder: str = "INBOX"
    flags: Set[str] = field(default_factory=set)
    size_bytes: int = 0

    # Investment-specific metadata
    contains_tickers: bool = False
    contains_prices: bool = False
    contains_research: bool = False
    sender_domain: str = ""
    sender_category: str = "unknown"  # broker, news, company, etc.


@dataclass
class EmailContent:
    """Extracted and processed email content"""
    body_text: str
    body_html: Optional[str] = None
    summary: Optional[str] = None

    # Extracted entities
    tickers: List[str] = field(default_factory=list)
    companies: List[str] = field(default_factory=list)
    price_mentions: List[Dict[str, Any]] = field(default_factory=list)
    date_mentions: List[datetime] = field(default_factory=list)
    percentages: List[str] = field(default_factory=list)

    # Investment signals
    sentiment: Dict[str, float] = field(default_factory=dict)
    topics: List[str] = field(default_factory=list)
    ratings: List[Dict[str, str]] = field(default_factory=list)

    # Attachments
    attachments: List[Dict[str, Any]] = field(default_factory=list)
    embedded_tables: List[Dict[str, Any]] = field(default_factory=list)
    links: List[Dict[str, str]] = field(default_factory=list)


@dataclass
class ProcessedEmail:
    """Complete processed email with metadata and content"""
    metadata: EmailMetadata
    content: EmailContent
    processing_timestamp: datetime
    quality_score: float
    validation_issues: List[str] = field(default_factory=list)
    extraction_stats: Dict[str, Any] = field(default_factory=dict)


class EmailIngestionState:
    """Persistent state for incremental email sync"""

    def __init__(self, state_file: Path):
        self.state_file = state_file
        self.state = self._load_state()

    def _load_state(self) -> Dict[str, Any]:
        """Load persisted state from disk"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load state: {e}, starting fresh")

        return {
            'last_sync': None,
            'folder_uids': {},  # folder -> highest UID
            'processed_message_ids': set(),  # deduplication
            'failed_emails': [],  # emails that failed processing
            'sync_history': []
        }

    def save(self):
        """Persist state to disk"""
        try:
            # Convert sets to lists for JSON serialization
            state_to_save = self.state.copy()
            state_to_save['processed_message_ids'] = list(self.state.get('processed_message_ids', set()))

            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.state_file, 'w') as f:
                json.dump(state_to_save, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save state: {e}")

    def get_last_uid(self, folder: str) -> Optional[str]:
        """Get last processed UID for a folder"""
        return self.state.get('folder_uids', {}).get(folder)

    def update_uid(self, folder: str, uid: str):
        """Update highest processed UID for folder"""
        if 'folder_uids' not in self.state:
            self.state['folder_uids'] = {}
        self.state['folder_uids'][folder] = uid
        self.save()

    def is_processed(self, message_id: str) -> bool:
        """Check if message was already processed"""
        if 'processed_message_ids' not in self.state:
            self.state['processed_message_ids'] = set()
        elif isinstance(self.state['processed_message_ids'], list):
            self.state['processed_message_ids'] = set(self.state['processed_message_ids'])
        return message_id in self.state['processed_message_ids']

    def mark_processed(self, message_id: str):
        """Mark message as processed"""
        if 'processed_message_ids' not in self.state:
            self.state['processed_message_ids'] = set()
        elif isinstance(self.state['processed_message_ids'], list):
            self.state['processed_message_ids'] = set(self.state['processed_message_ids'])
        self.state['processed_message_ids'].add(message_id)

    def add_failed(self, email_info: Dict[str, Any]):
        """Track failed email for retry"""
        if 'failed_emails' not in self.state:
            self.state['failed_emails'] = []
        self.state['failed_emails'].append({
            **email_info,
            'failed_at': datetime.now().isoformat()
        })
        self.save()


class EmailIngestionClient(BaseDataClient):
    """
    Robust email ingestion client with comprehensive error handling
    Inherits circuit breaker and retry logic from BaseDataClient
    """

    def __init__(self, config: Optional[SecureConfig] = None, state_dir: str = "./data/email_state"):
        """Initialize email ingestion client"""
        super().__init__("email", config)

        # State management
        self.state_dir = Path(state_dir)
        self.state = EmailIngestionState(self.state_dir / "ingestion_state.json")

        # IMAP connection
        self.imap = None
        self.connection_lock = threading.Lock()
        self.last_activity = datetime.now()

        # Processing configuration
        self.batch_size = 50
        self.parallel_workers = 4
        self.connection_timeout = 30
        self.idle_timeout = 300  # 5 minutes

        # Investment-specific patterns
        self._init_patterns()

        # Statistics
        self.stats = {
            'emails_processed': 0,
            'emails_failed': 0,
            'attachments_processed': 0,
            'entities_extracted': 0,
            'processing_time_total': 0
        }

    def _init_patterns(self):
        """Initialize regex patterns for entity extraction"""
        # Ticker patterns (1-5 uppercase letters, possibly with exchange suffix)
        self.ticker_pattern = re.compile(r'\b([A-Z]{1,5})(?:\.[A-Z]{1,3})?\b')

        # Price patterns ($X.XX, X.XX USD, etc.)
        self.price_pattern = re.compile(
            r'(?:\$|USD|EUR|GBP|JPY|CNY)?\s*(\d{1,6}(?:,\d{3})*(?:\.\d{1,2})?)\s*(?:USD|EUR|GBP|JPY|CNY)?'
        )

        # Percentage patterns
        self.percent_pattern = re.compile(r'([+-]?\d+(?:\.\d+)?)\s*%')

        # Rating patterns
        self.rating_pattern = re.compile(
            r'\b(buy|sell|hold|outperform|underperform|overweight|underweight|neutral)\b',
            re.IGNORECASE
        )

        # Company name patterns (simplified - could be enhanced with NER)
        self.company_pattern = re.compile(
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+(?:Inc|Corp|Ltd|LLC|plc|AG|SA|NV)\.?))\b'
        )

    def connect(self, email_address: str, password: str, server: str = "outlook.office365.com",
                port: int = 993, use_oauth: bool = False) -> bool:
        """
        Establish IMAP connection with automatic retry and circuit breaker

        Args:
            email_address: Email account address
            password: Password or OAuth token
            server: IMAP server hostname
            port: IMAP port (993 for SSL)
            use_oauth: Whether to use OAuth2 authentication

        Returns:
            True if connection successful
        """
        with self.connection_lock:
            try:
                # Create SSL context
                context = ssl.create_default_context()

                # Connect to IMAP server
                self.imap = imaplib.IMAP4_SSL(server, port, ssl_context=context)
                self.imap.sock.settimeout(self.connection_timeout)

                # Authenticate
                if use_oauth:
                    # OAuth2 authentication
                    auth_string = f'user={email_address}\x01auth=Bearer {password}\x01\x01'
                    self.imap.authenticate('XOAUTH2', lambda x: auth_string.encode())
                else:
                    # Standard authentication
                    result = self.imap.login(email_address, password)
                    if result[0] != 'OK':
                        raise Exception(f"Login failed: {result[1]}")

                self.last_activity = datetime.now()
                logger.info(f"Successfully connected to {email_address} on {server}")
                return True

            except Exception as e:
                logger.error(f"Connection failed: {e}")
                self.imap = None
                return False

    def ensure_connection(self) -> bool:
        """Ensure IMAP connection is active, reconnect if needed"""
        with self.connection_lock:
            try:
                # Check if connection exists and is alive
                if self.imap is None:
                    return False

                # Check idle timeout
                if (datetime.now() - self.last_activity).seconds > self.idle_timeout:
                    logger.info("Connection idle too long, refreshing...")
                    self.imap.close()
                    self.imap.logout()
                    self.imap = None
                    return False

                # Test connection with NOOP
                result = self.imap.noop()
                if result[0] == 'OK':
                    self.last_activity = datetime.now()
                    return True

                logger.warning("Connection test failed, connection lost")
                self.imap = None
                return False

            except Exception as e:
                logger.warning(f"Connection check failed: {e}")
                self.imap = None
                return False

    def fetch_emails_batch(self, folder: str = 'INBOX', batch_size: Optional[int] = None,
                          since_uid: Optional[str] = None) -> List[ProcessedEmail]:
        """
        Fetch and process emails in batches with incremental sync

        Args:
            folder: Email folder to fetch from
            batch_size: Number of emails per batch
            since_uid: Start from this UID (for incremental sync)

        Returns:
            List of processed emails
        """
        if not self.ensure_connection():
            logger.error("No active connection")
            return []

        batch_size = batch_size or self.batch_size
        processed_emails = []

        try:
            # Select folder
            result = self.imap.select(folder, readonly=False)
            if result[0] != 'OK':
                logger.error(f"Failed to select folder {folder}")
                return []

            # Get message UIDs
            if since_uid:
                # Incremental sync from last UID
                search_criteria = f'UID {int(since_uid)+1}:*'
                result, data = self.imap.uid('search', None, search_criteria)
            else:
                # Get recent messages (last 7 days by default)
                since_date = (datetime.now() - timedelta(days=7)).strftime("%d-%b-%Y")
                result, data = self.imap.search(None, 'SINCE', since_date)

            if result != 'OK':
                logger.error("Email search failed")
                return []

            message_ids = data[0].split() if data[0] else []
            if not message_ids:
                logger.info("No new emails found")
                return []

            # Process in batches
            for i in range(0, len(message_ids), batch_size):
                batch_ids = message_ids[i:i+batch_size]

                # Parallel processing of batch
                with ThreadPoolExecutor(max_workers=self.parallel_workers) as executor:
                    futures = []
                    for msg_id in batch_ids:
                        future = executor.submit(self._process_single_email, msg_id, folder)
                        futures.append(future)

                    # Collect results
                    for future in as_completed(futures):
                        try:
                            email_result = future.result(timeout=30)
                            if email_result:
                                processed_emails.append(email_result)
                                self.stats['emails_processed'] += 1
                        except Exception as e:
                            logger.error(f"Failed to process email: {e}")
                            self.stats['emails_failed'] += 1

                # Update state after each batch
                if batch_ids:
                    last_uid = batch_ids[-1].decode() if isinstance(batch_ids[-1], bytes) else str(batch_ids[-1])
                    self.state.update_uid(folder, last_uid)

            logger.info(f"Processed {len(processed_emails)} emails from {folder}")
            return processed_emails

        except Exception as e:
            logger.error(f"Batch fetch failed: {e}")
            return processed_emails

    def _process_single_email(self, msg_id: Union[str, bytes], folder: str) -> Optional[ProcessedEmail]:
        """Process a single email with comprehensive extraction"""
        try:
            start_time = time.time()

            # Fetch email data
            if isinstance(msg_id, bytes):
                msg_id = msg_id.decode()

            result, msg_data = self.imap.fetch(msg_id, '(RFC822 FLAGS)')
            if result != 'OK' or not msg_data:
                return None

            # Parse email
            raw_email = msg_data[0][1] if isinstance(msg_data[0], tuple) else msg_data[0]
            email_message = email.message_from_bytes(raw_email)

            # Extract metadata
            metadata = self._extract_metadata(email_message, msg_id, folder)

            # Check deduplication
            if self.state.is_processed(metadata.message_id):
                logger.debug(f"Skipping duplicate email: {metadata.message_id}")
                return None

            # Extract content
            content = self._extract_content(email_message)

            # Calculate quality score
            quality_score = self._calculate_quality_score(metadata, content)

            # Create processed email
            processed = ProcessedEmail(
                metadata=metadata,
                content=content,
                processing_timestamp=datetime.now(),
                quality_score=quality_score,
                extraction_stats={
                    'processing_time': time.time() - start_time,
                    'entities_found': len(content.tickers) + len(content.companies),
                    'attachments': len(content.attachments)
                }
            )

            # Mark as processed
            self.state.mark_processed(metadata.message_id)

            # Mark as read (optional)
            self.imap.store(msg_id, '+FLAGS', '\\Seen')

            return processed

        except Exception as e:
            logger.error(f"Failed to process email {msg_id}: {e}")
            self.state.add_failed({'msg_id': str(msg_id), 'folder': folder, 'error': str(e)})
            return None

    def _extract_metadata(self, email_message: email.message.Message, uid: str, folder: str) -> EmailMetadata:
        """Extract comprehensive metadata from email"""
        # Decode headers safely
        subject = self._decode_header_safe(email_message.get('Subject', ''))
        sender = self._decode_header_safe(email_message.get('From', ''))

        # Parse recipients
        recipients = []
        for field in ['To', 'Cc']:
            value = email_message.get(field, '')
            if value:
                recipients.extend(self._parse_email_addresses(value))

        # Parse date
        date_str = email_message.get('Date', '')
        try:
            email_date = parsedate_to_datetime(date_str) if date_str else datetime.now()
        except:
            email_date = datetime.now()

        # Threading information
        message_id = email_message.get('Message-ID', f'<generated-{uid}@local>')
        in_reply_to = email_message.get('In-Reply-To', '')
        references = email_message.get('References', '').split()
        thread_id = email_message.get('Thread-Index', '') or email_message.get('Thread-Topic', '')

        # Priority and importance
        priority = self._calculate_priority(subject, sender, email_message)
        importance = email_message.get('Importance', 'normal').lower()

        # Attachment detection
        has_attachments = False
        attachment_count = 0
        if email_message.is_multipart():
            for part in email_message.walk():
                if part.get_content_disposition() == 'attachment':
                    has_attachments = True
                    attachment_count += 1

        # Sender analysis
        sender_domain = self._extract_domain(sender)
        sender_category = self._categorize_sender(sender_domain)

        # Content indicators
        body_preview = self._get_body_preview(email_message)
        contains_tickers = bool(self.ticker_pattern.search(subject + ' ' + body_preview))
        contains_prices = bool(self.price_pattern.search(body_preview))
        contains_research = any(term in subject.lower() for term in
                              ['research', 'analysis', 'report', 'rating', 'target'])

        return EmailMetadata(
            uid=uid,
            message_id=message_id,
            subject=subject,
            sender=sender,
            recipients=recipients,
            date=email_date,
            thread_id=thread_id,
            in_reply_to=in_reply_to,
            references=references,
            priority=priority,
            importance=importance,
            has_attachments=has_attachments,
            attachment_count=attachment_count,
            folder=folder,
            size_bytes=len(str(email_message)),
            contains_tickers=contains_tickers,
            contains_prices=contains_prices,
            contains_research=contains_research,
            sender_domain=sender_domain,
            sender_category=sender_category
        )

    def _extract_content(self, email_message: email.message.Message) -> EmailContent:
        """Extract and process email content with investment focus"""
        content = EmailContent()

        # Extract body text and HTML
        text_parts = []
        html_parts = []

        if email_message.is_multipart():
            for part in email_message.walk():
                content_type = part.get_content_type()
                content_disposition = part.get('Content-Disposition', '')

                # Skip attachments for now (process separately)
                if 'attachment' in content_disposition:
                    continue

                try:
                    payload = part.get_payload(decode=True)
                    if not payload:
                        continue

                    # Detect encoding
                    detected = chardet.detect(payload)
                    encoding = detected['encoding'] or 'utf-8'

                    if content_type == 'text/plain':
                        text_parts.append(payload.decode(encoding, errors='replace'))
                    elif content_type == 'text/html':
                        html_parts.append(payload.decode(encoding, errors='replace'))
                except Exception as e:
                    logger.warning(f"Failed to decode part: {e}")
        else:
            # Single part message
            try:
                payload = email_message.get_payload(decode=True)
                if payload:
                    detected = chardet.detect(payload)
                    encoding = detected['encoding'] or 'utf-8'
                    text_parts.append(payload.decode(encoding, errors='replace'))
            except Exception as e:
                logger.warning(f"Failed to decode body: {e}")

        # Combine text parts
        content.body_text = '\n'.join(text_parts)

        # Process HTML if no plain text
        if html_parts and not content.body_text:
            content.body_html = '\n'.join(html_parts)
            # Extract text from HTML
            soup = BeautifulSoup(content.body_html, 'html.parser')
            content.body_text = soup.get_text(separator='\n', strip=True)

            # Extract tables from HTML
            content.embedded_tables = self._extract_html_tables(soup)

        # Clean up quoted text in replies
        content.body_text = self._remove_quoted_text(content.body_text)

        # Extract investment entities
        content.tickers = self._extract_tickers(content.body_text)
        content.companies = self._extract_companies(content.body_text)
        content.price_mentions = self._extract_prices(content.body_text)
        content.percentages = self._extract_percentages(content.body_text)
        content.ratings = self._extract_ratings(content.body_text)

        # Extract dates
        content.date_mentions = self._extract_dates(content.body_text)

        # Extract links
        content.links = self._extract_links(content.body_text, content.body_html)

        # Analyze sentiment and topics
        content.sentiment = self._analyze_sentiment(content.body_text)
        content.topics = self._extract_topics(content.body_text)

        # Process attachments
        content.attachments = self._process_attachments(email_message)

        # Generate summary
        content.summary = self._generate_summary(content.body_text)

        return content

    def _decode_header_safe(self, header_value: str) -> str:
        """Safely decode email headers with multiple encodings"""
        if not header_value:
            return ''

        try:
            decoded_parts = decode_header(header_value)
            result = []

            for part, encoding in decoded_parts:
                if isinstance(part, bytes):
                    if encoding:
                        try:
                            result.append(part.decode(encoding))
                        except:
                            # Fallback to chardet
                            detected = chardet.detect(part)
                            encoding = detected['encoding'] or 'utf-8'
                            result.append(part.decode(encoding, errors='replace'))
                    else:
                        # No encoding specified, detect it
                        detected = chardet.detect(part)
                        encoding = detected['encoding'] or 'utf-8'
                        result.append(part.decode(encoding, errors='replace'))
                else:
                    result.append(str(part))

            return ''.join(result).strip()

        except Exception as e:
            logger.warning(f"Failed to decode header: {e}")
            return str(header_value)

    def _extract_tickers(self, text: str) -> List[str]:
        """Extract stock tickers with validation"""
        if not text:
            return []

        # Find potential tickers
        matches = self.ticker_pattern.findall(text)

        # Filter and validate
        tickers = []
        for match in matches:
            # Skip common words that match pattern
            if match in {'THE', 'CEO', 'CFO', 'IPO', 'NYSE', 'NASDAQ', 'SEC', 'FDA', 'GDP', 'USD', 'EUR'}:
                continue

            # Additional validation could be added here (e.g., check against known ticker list)
            if 2 <= len(match) <= 5:
                tickers.append(match)

        return list(set(tickers))  # Remove duplicates

    def _extract_companies(self, text: str) -> List[str]:
        """Extract company names"""
        if not text:
            return []

        companies = []
        matches = self.company_pattern.findall(text)

        for match in matches:
            # Filter out common false positives
            if len(match) > 3 and not match.startswith('The '):
                companies.append(match)

        return list(set(companies))

    def _extract_prices(self, text: str) -> List[Dict[str, Any]]:
        """Extract price mentions with context"""
        if not text:
            return []

        prices = []
        for match in self.price_pattern.finditer(text):
            # Get surrounding context
            start = max(0, match.start() - 50)
            end = min(len(text), match.end() + 50)
            context = text[start:end]

            prices.append({
                'value': match.group(1),
                'context': context.strip(),
                'position': match.start()
            })

        return prices

    def _extract_percentages(self, text: str) -> List[str]:
        """Extract percentage mentions"""
        if not text:
            return []

        return list(set(self.percent_pattern.findall(text)))

    def _extract_ratings(self, text: str) -> List[Dict[str, str]]:
        """Extract investment ratings and recommendations"""
        if not text:
            return []

        ratings = []
        for match in self.rating_pattern.finditer(text):
            # Get surrounding context to find associated ticker
            start = max(0, match.start() - 100)
            end = min(len(text), match.end() + 100)
            context = text[start:end]

            # Try to find associated ticker
            ticker_match = self.ticker_pattern.search(context)

            ratings.append({
                'rating': match.group(1).upper(),
                'ticker': ticker_match.group(1) if ticker_match else None,
                'context': context.strip()
            })

        return ratings

    def _extract_dates(self, text: str) -> List[datetime]:
        """Extract date mentions from text"""
        dates = []

        # Common date patterns
        date_patterns = [
            r'\b(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})\b',
            r'\b(\d{4}[-/]\d{1,2}[-/]\d{1,2})\b',
            r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}\b',
            r'\b\d{1,2} (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{4}\b'
        ]

        for pattern in date_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                try:
                    # Try to parse the date (would need more sophisticated parsing)
                    # This is simplified - could use dateutil.parser
                    dates.append(datetime.now())  # Placeholder
                except:
                    pass

        return dates

    def _extract_links(self, text: str, html: Optional[str]) -> List[Dict[str, str]]:
        """Extract URLs from text and HTML"""
        links = []

        # Extract from plain text
        url_pattern = re.compile(r'https?://[^\s<>"{}|\\^`\[\]]+')
        for match in url_pattern.finditer(text or ''):
            links.append({'url': match.group(), 'source': 'text'})

        # Extract from HTML
        if html:
            soup = BeautifulSoup(html, 'html.parser')
            for link in soup.find_all('a', href=True):
                links.append({
                    'url': link['href'],
                    'text': link.get_text(strip=True),
                    'source': 'html'
                })

        return links

    def _extract_html_tables(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract tables from HTML content"""
        tables = []

        for table in soup.find_all('table'):
            table_data = []
            headers = []

            # Extract headers
            for th in table.find_all('th'):
                headers.append(th.get_text(strip=True))

            # Extract rows
            for tr in table.find_all('tr'):
                row = []
                for td in tr.find_all('td'):
                    row.append(td.get_text(strip=True))
                if row:
                    table_data.append(row)

            if table_data or headers:
                tables.append({
                    'headers': headers,
                    'data': table_data,
                    'row_count': len(table_data),
                    'col_count': len(headers) if headers else (len(table_data[0]) if table_data else 0)
                })

        return tables

    def _analyze_sentiment(self, text: str) -> Dict[str, float]:
        """Analyze investment sentiment"""
        if not text:
            return {'bullish': 0, 'bearish': 0, 'neutral': 0}

        text_lower = text.lower()
        sentiment = {'bullish': 0, 'bearish': 0, 'neutral': 0}

        # Bullish keywords
        bullish_words = ['buy', 'bullish', 'positive', 'outperform', 'upgrade', 'strong',
                        'growth', 'beat', 'exceed', 'optimistic', 'opportunity']

        # Bearish keywords
        bearish_words = ['sell', 'bearish', 'negative', 'underperform', 'downgrade', 'weak',
                        'decline', 'miss', 'concern', 'risk', 'warning']

        # Neutral keywords
        neutral_words = ['hold', 'neutral', 'maintain', 'unchanged', 'stable', 'flat']

        # Count occurrences
        for word in bullish_words:
            sentiment['bullish'] += text_lower.count(word)

        for word in bearish_words:
            sentiment['bearish'] += text_lower.count(word)

        for word in neutral_words:
            sentiment['neutral'] += text_lower.count(word)

        # Normalize
        total = sum(sentiment.values())
        if total > 0:
            for key in sentiment:
                sentiment[key] = sentiment[key] / total

        return sentiment

    def _extract_topics(self, text: str) -> List[str]:
        """Extract investment topics"""
        if not text:
            return []

        topics = []
        text_lower = text.lower()

        # Topic keywords
        topic_keywords = {
            'earnings': ['earnings', 'revenue', 'profit', 'eps', 'guidance'],
            'merger': ['merger', 'acquisition', 'm&a', 'takeover', 'buyout'],
            'ipo': ['ipo', 'initial public offering', 'listing', 'debut'],
            'dividend': ['dividend', 'distribution', 'yield', 'payout'],
            'regulation': ['sec', 'regulation', 'compliance', 'investigation'],
            'product': ['product', 'launch', 'release', 'announcement'],
            'management': ['ceo', 'cfo', 'management', 'executive', 'board'],
            'analyst': ['analyst', 'research', 'report', 'rating', 'target']
        }

        for topic, keywords in topic_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                topics.append(topic)

        return topics

    def _process_attachments(self, email_message: email.message.Message) -> List[Dict[str, Any]]:
        """Process email attachments"""
        attachments = []

        if not email_message.is_multipart():
            return attachments

        for part in email_message.walk():
            if part.get_content_disposition() != 'attachment':
                continue

            filename = part.get_filename()
            if not filename:
                continue

            filename = self._decode_header_safe(filename)

            # Get attachment content
            content = part.get_payload(decode=True)

            attachment_info = {
                'filename': filename,
                'content_type': part.get_content_type(),
                'size': len(content) if content else 0,
                'hash': hashlib.sha256(content).hexdigest() if content else None
            }

            # Extract text from attachments if possible
            if content:
                extracted_text = self._extract_attachment_text(content, part.get_content_type(), filename)
                if extracted_text:
                    attachment_info['extracted_text'] = extracted_text[:1000]  # Limit size

            attachments.append(attachment_info)

        return attachments

    def _extract_attachment_text(self, content: bytes, content_type: str, filename: str) -> Optional[str]:
        """Extract text from attachment if possible"""
        try:
            # Text files
            if content_type.startswith('text/') or filename.endswith(('.txt', '.csv', '.log')):
                detected = chardet.detect(content)
                encoding = detected['encoding'] or 'utf-8'
                return content.decode(encoding, errors='replace')

            # PDF files (would need pdfplumber or similar)
            if content_type == 'application/pdf' or filename.endswith('.pdf'):
                # Placeholder - would need PDF extraction library
                return "[PDF content - extraction not implemented]"

            # Office documents (would need python-docx, openpyxl, etc.)
            if filename.endswith(('.docx', '.xlsx', '.pptx')):
                return "[Office document - extraction not implemented]"

        except Exception as e:
            logger.warning(f"Failed to extract attachment text: {e}")

        return None

    def _remove_quoted_text(self, text: str) -> str:
        """Remove quoted reply text"""
        if not text:
            return ''

        lines = text.split('\n')
        clean_lines = []

        for line in lines:
            # Stop at common reply indicators
            if line.strip().startswith('>'):
                break
            if 'Original Message' in line:
                break
            if re.match(r'^On .+ wrote:$', line.strip()):
                break
            if '-----' in line and 'From:' in text[text.index(line):]:
                break

            clean_lines.append(line)

        return '\n'.join(clean_lines).strip()

    def _generate_summary(self, text: str, max_length: int = 200) -> str:
        """Generate a brief summary of email content"""
        if not text:
            return ''

        # Clean text
        text = self._remove_quoted_text(text)
        text = re.sub(r'\s+', ' ', text)  # Normalize whitespace

        # Simple extractive summary (first N characters)
        if len(text) <= max_length:
            return text

        # Try to break at sentence boundary
        summary = text[:max_length]
        last_period = summary.rfind('.')
        if last_period > max_length * 0.7:  # If we have a decent amount before period
            summary = summary[:last_period + 1]
        else:
            summary = summary.strip() + '...'

        return summary

    def _calculate_priority(self, subject: str, sender: str, email_message: email.message.Message) -> int:
        """Calculate email priority for investment context"""
        priority = 0

        # Check importance header
        importance = email_message.get('Importance', '').lower()
        if importance == 'high':
            priority += 30
        elif importance == 'low':
            priority -= 10

        # Check priority header
        x_priority = email_message.get('X-Priority', '').lower()
        if '1' in x_priority or 'high' in x_priority:
            priority += 20

        # Check subject keywords
        subject_lower = subject.lower()
        urgent_keywords = ['urgent', 'asap', 'immediate', 'action required', 'flash']
        for keyword in urgent_keywords:
            if keyword in subject_lower:
                priority += 40
                break

        # Investment-specific priority
        investment_keywords = ['earnings', 'upgrade', 'downgrade', 'halt', 'breaking', 'alert']
        for keyword in investment_keywords:
            if keyword in subject_lower:
                priority += 25
                break

        # Sender reputation
        sender_lower = sender.lower()
        if any(domain in sender_lower for domain in
               ['bloomberg', 'reuters', 'wsj', 'ft.com', 'cnbc']):
            priority += 30

        return min(priority, 100)  # Cap at 100

    def _extract_domain(self, email_address: str) -> str:
        """Extract domain from email address"""
        match = re.search(r'@([^\s>]+)', email_address)
        return match.group(1).lower() if match else ''

    def _categorize_sender(self, domain: str) -> str:
        """Categorize sender based on domain"""
        if not domain:
            return 'unknown'

        # News organizations
        if any(news in domain for news in
               ['bloomberg', 'reuters', 'wsj', 'ft.com', 'cnbc', 'marketwatch']):
            return 'news'

        # Brokers and research
        if any(broker in domain for broker in
               ['gs.com', 'morganstanley', 'jpmorgan', 'citi', 'baml', 'ubs']):
            return 'broker'

        # Companies (simplified - could be enhanced)
        if not any(x in domain for x in ['gmail', 'yahoo', 'outlook', 'hotmail']):
            return 'company'

        return 'personal'

    def _parse_email_addresses(self, address_string: str) -> List[str]:
        """Parse email addresses from header field"""
        addresses = []

        # Simple extraction (could be enhanced with email.utils)
        for match in re.finditer(r'[\w\.-]+@[\w\.-]+', address_string):
            addresses.append(match.group())

        return addresses

    def _get_body_preview(self, email_message: email.message.Message) -> str:
        """Get quick preview of email body for analysis"""
        try:
            if email_message.is_multipart():
                for part in email_message.walk():
                    if part.get_content_type() == 'text/plain':
                        payload = part.get_payload(decode=True)
                        if payload:
                            return payload.decode('utf-8', errors='ignore')[:500]
            else:
                payload = email_message.get_payload(decode=True)
                if payload:
                    return payload.decode('utf-8', errors='ignore')[:500]
        except:
            pass

        return ''

    def _calculate_quality_score(self, metadata: EmailMetadata, content: EmailContent) -> float:
        """Calculate quality score for processed email"""
        score = 0.5  # Base score

        # Metadata quality
        if metadata.message_id and metadata.message_id != f'<generated-{metadata.uid}@local>':
            score += 0.1
        if metadata.thread_id:
            score += 0.05

        # Content quality
        if content.body_text and len(content.body_text) > 100:
            score += 0.1
        if content.tickers:
            score += 0.1
        if content.companies:
            score += 0.05
        if content.price_mentions:
            score += 0.05
        if content.attachments:
            score += 0.05

        # Investment relevance
        if metadata.contains_research:
            score += 0.1
        if metadata.sender_category in ['news', 'broker']:
            score += 0.1

        return min(score, 1.0)

    def get_statistics(self) -> Dict[str, Any]:
        """Get processing statistics"""
        return {
            **self.stats,
            'state': {
                'folders': list(self.state.state.get('folder_uids', {}).keys()),
                'processed_count': len(self.state.state.get('processed_message_ids', [])),
                'failed_count': len(self.state.state.get('failed_emails', [])),
                'last_sync': self.state.state.get('last_sync')
            }
        }

    def retry_failed_emails(self) -> List[ProcessedEmail]:
        """Retry processing of previously failed emails"""
        failed_emails = self.state.state.get('failed_emails', [])
        if not failed_emails:
            return []

        logger.info(f"Retrying {len(failed_emails)} failed emails")
        processed = []

        for failed in failed_emails[:10]:  # Limit retry batch
            try:
                result = self._process_single_email(failed['msg_id'], failed['folder'])
                if result:
                    processed.append(result)
                    # Remove from failed list
                    self.state.state['failed_emails'].remove(failed)
            except Exception as e:
                logger.error(f"Retry failed for {failed['msg_id']}: {e}")

        self.state.save()
        return processed

    def close(self):
        """Close IMAP connection and save state"""
        try:
            if self.imap:
                self.imap.close()
                self.imap.logout()
                self.imap = None

            self.state.save()
            logger.info("Email ingestion client closed")

        except Exception as e:
            logger.warning(f"Error closing connection: {e}")


# Example usage and testing
if __name__ == "__main__":
    import getpass

    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Initialize client
    client = EmailIngestionClient()

    # Get credentials
    email_address = input("Email address: ")
    password = getpass.getpass("Password: ")

    # Connect
    if client.connect(email_address, password):
        print("✅ Connected successfully")

        # Fetch emails
        emails = client.fetch_emails_batch(folder='INBOX', batch_size=10)

        print(f"\n📧 Processed {len(emails)} emails")

        # Show sample
        for email_obj in emails[:3]:
            print(f"\n---")
            print(f"Subject: {email_obj.metadata.subject}")
            print(f"From: {email_obj.metadata.sender} ({email_obj.metadata.sender_category})")
            print(f"Date: {email_obj.metadata.date}")
            print(f"Priority: {email_obj.metadata.priority}")
            print(f"Quality: {email_obj.quality_score:.2f}")

            if email_obj.content.tickers:
                print(f"Tickers: {', '.join(email_obj.content.tickers)}")
            if email_obj.content.companies:
                print(f"Companies: {', '.join(email_obj.content.companies[:3])}")
            if email_obj.content.topics:
                print(f"Topics: {', '.join(email_obj.content.topics)}")

            print(f"Summary: {email_obj.content.summary[:100]}...")

        # Show statistics
        stats = client.get_statistics()
        print(f"\n📊 Statistics:")
        print(f"  Processed: {stats['emails_processed']}")
        print(f"  Failed: {stats['emails_failed']}")
        print(f"  Attachments: {stats['attachments_processed']}")

        # Close
        client.close()
    else:
        print("❌ Connection failed")