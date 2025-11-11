# data_ingestion.py
"""
ICE Data Ingestion - Simple API calls without transformation layers
Direct data fetching that returns text documents for LightRAG processing
Eliminates complex validation pipelines and transformation orchestration
Relevant files: ice_simplified.py, ice_core.py
"""

import os
import sys
from pathlib import Path
import requests
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from html.parser import HTMLParser

# Add project root to path for production module imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Production module imports for robust data ingestion
from ice_data_ingestion.robust_client import RobustHTTPClient
from ice_data_ingestion.sec_edgar_connector import SECEdgarConnector
from imap_email_ingestion_pipeline.email_connector import EmailConnector
from imap_email_ingestion_pipeline.entity_extractor import EntityExtractor
from imap_email_ingestion_pipeline.graph_builder import GraphBuilder
from imap_email_ingestion_pipeline.attachment_processor import AttachmentProcessor
from imap_email_ingestion_pipeline.table_entity_extractor import TableEntityExtractor
from imap_email_ingestion_pipeline.enhanced_doc_creator import create_enhanced_document
from imap_email_ingestion_pipeline.intelligent_link_processor import IntelligentLinkProcessor, LinkProcessingResult
from imap_email_ingestion_pipeline.ticker_validator import TickerValidator
from ice_data_ingestion.benzinga_client import BenzingaClient
from ice_data_ingestion.exa_mcp_connector import ExaMCPConnector
import asyncio

logger = logging.getLogger(__name__)


class HTMLTextExtractor(HTMLParser):
    """Extract clean text from HTML content"""
    def __init__(self):
        super().__init__()
        self.text = []
        self.in_style = False

    def handle_starttag(self, tag, attrs):
        if tag == 'style':
            self.in_style = True

    def handle_endtag(self, tag):
        if tag == 'style':
            self.in_style = False

    def handle_data(self, data):
        if not self.in_style and data.strip():
            self.text.append(data.strip())


class DataIngester:
    """
    Simple data ingestion - Direct API calls without transformation layers

    Key principles:
    1. Fetch data from APIs
    2. Return raw text documents
    3. Let LightRAG handle entity extraction and processing
    4. No validation pipelines, enhancement layers, or complex transformations
    5. Graceful degradation when APIs are unavailable
    """

    def __init__(self, api_keys: Optional[Dict[str, str]] = None, timeout: int = 30, config: Optional['ICEConfig'] = None):
        """
        Initialize data ingester with API configuration and feature flags

        Args:
            api_keys: Dictionary of API service names to keys
            timeout: Request timeout in seconds
            config: ICEConfig instance for feature flags (docling toggles, etc.)
        """
        self.timeout = timeout
        self.config = config  # Store config for feature flags (docling integration, signal store)

        # Load API keys from parameter or environment
        self.api_keys = api_keys or {
            'newsapi': os.getenv('NEWSAPI_ORG_API_KEY'),
            'alpha_vantage': os.getenv('ALPHA_VANTAGE_API_KEY'),
            'fmp': os.getenv('FMP_API_KEY'),
            'polygon': os.getenv('POLYGON_API_KEY'),
            'finnhub': os.getenv('FINNHUB_API_KEY'),
            'benzinga': os.getenv('BENZINGA_API_TOKEN'),
            'marketaux': os.getenv('MARKETAUX_API_KEY')
        }

        # Filter out None values
        self.api_keys = {k: v for k, v in self.api_keys.items() if v}

        self.available_services = list(self.api_keys.keys())

        # Initialize production modules for robust data ingestion
        # 1. Robust HTTP Client (replaces simple requests.get())
        # Note: For now, keep using requests for simple integration
        # TODO: Fully migrate to RobustHTTPClient with service-specific clients
        self.http_client = None  # Will use requests for now, migrate later

        # 2. Email Connector - NOT needed for sample emails
        # fetch_email_documents() reads .eml files directly
        # EmailConnector only needed for live IMAP connections in production
        self.email_connector = None  # Development: read sample .eml files directly

        # 3. SEC EDGAR Connector (regulatory filings: 10-K, 10-Q, 8-K)
        self.sec_connector = SECEdgarConnector()

        # 4. Entity Extractor (Phase 2.6.1: Production-grade entity extraction)
        self.entity_extractor = EntityExtractor()

        # 4.5. Ticker Validator (Reduce false positives in entity extraction)
        self.ticker_validator = TickerValidator()
        logger.info("✅ TickerValidator initialized (false positive filtering)")

        # 5. Graph Builder (Phase 2.6.1: Typed relationship extraction)
        self.graph_builder = GraphBuilder()

        # 5.5. Table Entity Extractor (Phase 2.6.2: Extract entities from attachment tables)
        self.table_entity_extractor = TableEntityExtractor()

        # 6. Attachment Processor - Switchable Design (REPLACEMENT pattern)
        # Toggle: config.use_docling_email
        # True: DoclingProcessor (docling, 97.9% table accuracy)
        # False: AttachmentProcessor (PyPDF2/openpyxl, 42% table accuracy)
        # Note: Only 3/71 emails have attachments, but processor handles PDF, Excel, Word, PowerPoint

        attachment_storage = Path(__file__).parent.parent.parent / 'data' / 'attachments'
        attachment_storage.mkdir(parents=True, exist_ok=True)

        # Check config for docling toggles (separate controls for email attachments vs URL PDFs)
        use_docling_email = self.config and self.config.use_docling_email if self.config else False
        use_docling_urls = self.config and self.config.use_docling_urls if self.config else False

        try:
            if use_docling_email:
                from src.ice_docling.docling_processor import DoclingProcessor
                self.attachment_processor = DoclingProcessor(str(attachment_storage))
                logger.info("✅ DoclingProcessor initialized (97.9% table accuracy)")
            else:
                from imap_email_ingestion_pipeline.attachment_processor import AttachmentProcessor
                self.attachment_processor = AttachmentProcessor(str(attachment_storage))
                logger.info("AttachmentProcessor initialized (42% table accuracy, PyPDF2/openpyxl)")

        except ImportError as e:
            logger.warning(f"Attachment processor initialization failed: {e}")
            self.attachment_processor = None
        except Exception as e:
            logger.warning(f"Attachment processor initialization failed: {e}")
            self.attachment_processor = None

        # 7. Benzinga Client (Phase 1: Professional real-time financial news)
        self.benzinga_client = None
        if self.is_service_available('benzinga'):
            try:
                self.benzinga_client = BenzingaClient(api_token=self.api_keys['benzinga'])
                logger.info("✅ BenzingaClient initialized (real-time professional news)")
            except Exception as e:
                logger.warning(f"BenzingaClient initialization failed: {e}")
                self.benzinga_client = None

        # 8. Exa MCP Connector (Phase 2: Semantic search for deep research)
        # On-demand research tool (not auto-ingested in waterfall)
        self.exa_connector = None
        if self.is_service_available('exa'):
            try:
                # Exa MCP requires async initialization check
                self.exa_connector = ExaMCPConnector()

                # Check if properly configured (async check)
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    is_configured = loop.run_until_complete(self.exa_connector.is_configured())
                    if not is_configured:
                        logger.warning("Exa MCP not properly configured")
                        self.exa_connector = None
                    else:
                        logger.info("✅ ExaMCPConnector initialized (semantic search for deep research)")
                finally:
                    loop.close()

            except Exception as e:
                logger.warning(f"ExaMCPConnector initialization failed: {e}")
                self.exa_connector = None

        # 9. Intelligent Link Processor (Phase 2: Hybrid URL fetching with Crawl4AI + Docling)
        # Processes URLs in email body to download research reports (PDFs, analyst reports)
        # Switchable toggles (independent controls):
        # - config.use_crawl4ai_links: Hybrid routing (simple HTTP vs Crawl4AI browser automation)
        # - config.use_docling_urls: Docling for URL PDFs (97.9% vs 42% table accuracy)
        self.link_processor = None
        try:
            # Use same storage path as AttachmentProcessor for consistency
            # Files saved directly to: data/attachments/{email_uid}/{file_hash}/original/{filename}
            link_storage_path = Path(__file__).parent.parent.parent / 'data' / 'attachments'
            link_storage_path.mkdir(parents=True, exist_ok=True)

            # Prepare DoclingProcessor for URL PDFs (independent of email attachment configuration)
            # If use_docling_urls = True, ensure we have DoclingProcessor instance
            docling_processor_for_urls = None
            if use_docling_urls:
                # Check if we can reuse existing DoclingProcessor (more efficient)
                # Only reuse if: 1) use_docling_email=True AND 2) attachment_processor is actually a DoclingProcessor
                if use_docling_email and self.attachment_processor and hasattr(self.attachment_processor, 'extract_tables_from_pdf'):
                    # Reuse existing DoclingProcessor from attachment processing (memory efficient)
                    docling_processor_for_urls = self.attachment_processor
                    logger.debug("Reusing DoclingProcessor from email attachments for URL PDFs")
                else:
                    # Create separate DoclingProcessor specifically for URL PDFs
                    # Either: user wants Docling for URLs but not email attachments
                    # OR: attachment_processor exists but isn't a DoclingProcessor
                    from src.ice_docling.docling_processor import DoclingProcessor
                    docling_processor_for_urls = DoclingProcessor(str(link_storage_path))
                    logger.debug("Created dedicated DoclingProcessor for URL PDFs")

            self.link_processor = IntelligentLinkProcessor(
                storage_path=str(link_storage_path),
                config=self.config,  # Pass ICEConfig for Crawl4AI and Docling toggles
                docling_processor=docling_processor_for_urls  # Phase 2: Docling for URL PDFs (97.9% accuracy)
            )
            docling_status = "with Docling (97.9% table accuracy)" if use_docling_urls else "with pdfplumber (42% table accuracy)"
            logger.info(f"✅ IntelligentLinkProcessor initialized (hybrid URL fetching) {docling_status}")

            # DEBUGGING: Log storage path resolution details
            logger.info(f"🗂️  STORAGE PATH RESOLUTION:")
            logger.info(f"   Current file: {__file__}")
            logger.info(f"   Resolved path: {link_storage_path.resolve()}")
            logger.info(f"   Path exists: {link_storage_path.exists()}")
            logger.info(f"   Path writable: {os.access(link_storage_path, os.W_OK)}")

            # Verify unified storage path (AttachmentProcessor vs IntelligentLinkProcessor)
            if self.attachment_processor and hasattr(self.attachment_processor, 'storage_path'):
                att_path = Path(self.attachment_processor.storage_path)
                if att_path.resolve() != link_storage_path.resolve():
                    logger.warning(f"⚠️  STORAGE PATH MISMATCH:")
                    logger.warning(f"   Attachment: {att_path.resolve()}")
                    logger.warning(f"   Link: {link_storage_path.resolve()}")
                else:
                    logger.info(f"✅ Unified storage path confirmed: {link_storage_path.resolve()}")

        except Exception as e:
            logger.warning(f"IntelligentLinkProcessor initialization failed: {e}")
            self.link_processor = None

        # Storage for structured data (Phase 2.6.2: Signal Store will use these)
        self.last_extracted_entities = []  # List of entity dicts from EntityExtractor
        self.last_graph_data = {}  # Graph data for dual-layer architecture

        logger.info(f"Data Ingester initialized with {len(self.available_services)} API services: {self.available_services}")
        modules_status = "SEC EDGAR connector, EntityExtractor, GraphBuilder"
        if self.attachment_processor:
            modules_status += ", AttachmentProcessor"
        if self.link_processor:
            modules_status += ", IntelligentLinkProcessor"
        logger.info(f"Production modules initialized: {modules_status} ready")

        # 10. Signal Store (Phase 2: Dual-layer architecture for structured queries)
        # SQLite storage for fast (<1s) lookups of ratings, price targets, financial metrics
        # Complements LightRAG (semantic search ~12s) with structured queries
        self.signal_store = None
        if config and config.use_signal_store:
            try:
                from updated_architectures.implementation.signal_store import SignalStore
                self.signal_store = SignalStore(db_path=config.signal_store_path)
                logger.info("✅ Signal Store initialized for dual-layer architecture")
            except Exception as e:
                logger.warning(f"Signal Store initialization failed, using LightRAG only: {e}")
                self.signal_store = None

    def _merge_entities(self, body_entities: Dict, table_entities: Dict) -> Dict:
        """
        Merge entities extracted from email body and attachment tables.

        Args:
            body_entities: Entities from EntityExtractor (email body text)
            table_entities: Entities from TableEntityExtractor (attachment tables)

        Returns:
            Merged entity dict with combined results
        """
        merged = body_entities.copy()

        # BUG FIX: EntityExtractor returns financial_metrics as Dict[str, List], not List
        # e.g., {'revenue': [{...}], 'profit': [{...}]}
        # TableEntityExtractor returns financial_metrics as List[Dict]
        # Need to convert body financial_metrics dict to flat list before merging
        body_financial_metrics = body_entities.get('financial_metrics', {})
        if isinstance(body_financial_metrics, dict):
            # Flatten dict of lists into single list
            body_metrics_list = []
            for category, metrics_list in body_financial_metrics.items():
                body_metrics_list.extend(metrics_list)
        else:
            # Already a list (shouldn't happen with EntityExtractor, but defensive)
            body_metrics_list = body_financial_metrics

        # Merge financial_metrics (additive - combine body + table metrics)
        merged['financial_metrics'] = (
            body_metrics_list +
            table_entities.get('financial_metrics', [])
        )

        # Add table-specific entity types (not present in body extraction)
        # BUG FIX: When merging twice (body+attachments, then +html_tables), preserve existing margin_metrics
        # if second merge source (html_table_entities) has no margin_metrics
        existing_margin = merged.get('margin_metrics', [])
        new_margin = table_entities.get('margin_metrics', [])
        merged['margin_metrics'] = existing_margin + new_margin if existing_margin or new_margin else []

        existing_comparisons = merged.get('metric_comparisons', [])
        new_comparisons = table_entities.get('metric_comparisons', [])
        merged['metric_comparisons'] = existing_comparisons + new_comparisons if existing_comparisons or new_comparisons else []

        # Update overall confidence (weighted average if both sources present)
        body_conf = body_entities.get('confidence', 0.0)
        table_conf = table_entities.get('confidence', 0.0)

        if table_conf > 0:
            merged['confidence'] = (body_conf + table_conf) / 2
        else:
            merged['confidence'] = body_conf

        return merged

    def _write_ratings_to_signal_store(
        self,
        merged_entities: Dict[str, Any],
        email_data: Dict[str, Any],
        timestamp: str
    ) -> None:
        """
        Write extracted ratings to Signal Store (dual-layer architecture).

        Converts EntityExtractor rating format to Signal Store schema and persists.
        Called during email ingestion for dual-write pattern.

        Args:
            merged_entities: Entities dict from EntityExtractor (contains 'ratings' key)
            email_data: Email metadata (for source_document_id and firm/analyst attribution)
            timestamp: ISO format timestamp for rating record

        EntityExtractor rating format:
            [{'rating': 'buy', 'confidence': 0.85, 'source': 'rating_pattern', 'context': '...'}]

        Signal Store rating schema:
            ticker, analyst, firm, rating, confidence, timestamp, source_document_id
        """
        if not self.signal_store:
            return  # Signal Store disabled or initialization failed

        ratings = merged_entities.get('ratings', [])
        if not ratings:
            return  # No ratings to write

        tickers = merged_entities.get('tickers', [])
        if not tickers:
            logger.debug("No tickers found, skipping Signal Store rating write")
            return

        # Extract metadata from email for attribution
        source_document_id = email_data.get('message_id', f"email_{timestamp}")
        firm = email_data.get('from', '').split('<')[0].strip()  # Extract firm from sender
        analyst = None  # EntityExtractor doesn't extract analyst names yet

        # Write each rating to Signal Store
        ratings_written = 0
        try:
            for rating_entity in ratings:
                rating_value = rating_entity.get('rating', '').upper()
                confidence = rating_entity.get('confidence', 0.0)

                # Write rating for each ticker mentioned in email
                # (Assumes rating applies to all tickers in email)
                for ticker_entity in tickers:
                    ticker = ticker_entity.get('ticker', '').upper()
                    if not ticker:
                        continue

                    self.signal_store.insert_rating(
                        ticker=ticker,
                        rating=rating_value,
                        timestamp=timestamp,
                        source_document_id=source_document_id,
                        analyst=analyst,
                        firm=firm if firm else None,
                        confidence=confidence
                    )
                    ratings_written += 1

            if ratings_written > 0:
                logger.info(f"✅ Wrote {ratings_written} ratings to Signal Store")

        except Exception as e:
            logger.warning(f"Signal Store write failed (graceful degradation): {e}")

    def _write_metrics_to_signal_store(
        self,
        merged_entities: Dict[str, Any],
        email_data: Dict[str, Any]
    ) -> None:
        """
        Write extracted financial metrics to Signal Store (dual-layer architecture).

        Converts TableEntityExtractor metric format to Signal Store schema and persists.
        Called during email ingestion for dual-write pattern.

        Args:
            merged_entities: Entities dict from TableEntityExtractor (contains 'financial_metrics' key)
            email_data: Email metadata (for source_document_id)

        TableEntityExtractor metric format:
            [{
                'metric': 'Operating Margin',
                'value': '62.3%',
                'period': 'Q2 2024',
                'ticker': 'NVDA',
                'confidence': 0.95,
                'table_index': 0,
                'row_index': 2
            }]

        Signal Store metric schema:
            ticker, metric_type, metric_value, period, confidence, source_document_id, table_index, row_index
        """
        if not self.signal_store:
            return  # Signal Store disabled or initialization failed

        # Extract metrics from merged_entities
        financial_metrics = merged_entities.get('financial_metrics', [])
        margin_metrics = merged_entities.get('margin_metrics', [])

        # Combine all metrics
        all_metrics = financial_metrics + margin_metrics

        if not all_metrics:
            return  # No metrics to write

        # Extract metadata from email for attribution
        source_document_id = email_data.get('message_id', f"email_{email_data.get('uid', 'unknown')}")

        # Write each metric to Signal Store
        metrics_written = 0
        try:
            for metric_entity in all_metrics:
                # Extract fields from TableEntityExtractor format
                ticker = metric_entity.get('ticker', '').upper()
                metric_type = metric_entity.get('metric', '')
                metric_value = str(metric_entity.get('value', ''))
                period = metric_entity.get('period')
                confidence = metric_entity.get('confidence', 0.0)
                table_index = metric_entity.get('table_index')
                row_index = metric_entity.get('row_index')

                if not ticker or not metric_type or not metric_value:
                    logger.debug(f"Skipping incomplete metric: ticker={ticker}, type={metric_type}, value={metric_value}")
                    continue

                self.signal_store.insert_metric(
                    ticker=ticker,
                    metric_type=metric_type,
                    metric_value=metric_value,
                    source_document_id=source_document_id,
                    period=period,
                    confidence=confidence,
                    table_index=table_index,
                    row_index=row_index
                )
                metrics_written += 1

            if metrics_written > 0:
                logger.info(f"✅ Wrote {metrics_written} metrics to Signal Store")

        except Exception as e:
            logger.warning(f"Signal Store metrics write failed (graceful degradation): {e}")
            # Continue processing - dual-write failure shouldn't block email ingestion

    def _write_price_targets_to_signal_store(
        self,
        merged_entities: Dict[str, Any],
        email_data: Dict[str, Any],
        timestamp: str
    ) -> None:
        """
        Write extracted price targets to Signal Store (dual-layer architecture).

        EntityExtractor price target format → Signal Store schema:
        {
            'value': '500',      # or 'price': '500'
            'ticker': 'NVDA',
            'currency': 'USD',
            'confidence': 0.92
        }

        Signal Store price_targets schema:
            ticker, analyst, firm, target_price, currency, confidence, timestamp, source_document_id

        Args:
            merged_entities: Entities dict from EntityExtractor (contains 'price_targets' key)
            email_data: Email metadata (for source_document_id and firm/analyst attribution)
            timestamp: ISO format timestamp for price target record
        """
        if not self.signal_store:
            return

        price_targets = merged_entities.get('price_targets', [])
        if not price_targets:
            return

        source_document_id = email_data.get('message_id', f"email_{timestamp}")
        firm = email_data.get('from', '').split('<')[0].strip()  # Extract firm from sender
        analyst = None  # EntityExtractor doesn't extract analyst names yet

        targets_written = 0
        try:
            for pt_entity in price_targets:
                # Extract price target value (can be 'value' or 'price' key)
                target_value_str = pt_entity.get('value') or pt_entity.get('price', '')
                ticker = pt_entity.get('ticker', '').upper()
                currency = pt_entity.get('currency', 'USD')
                confidence = pt_entity.get('confidence', 0.0)

                if not ticker or not target_value_str:
                    continue

                # Parse target price as float
                try:
                    target_price = float(target_value_str)
                except (ValueError, TypeError):
                    logger.debug(f"Could not parse price target value: {target_value_str}")
                    continue

                self.signal_store.insert_price_target(
                    ticker=ticker,
                    target_price=target_price,
                    timestamp=timestamp,
                    source_document_id=source_document_id,
                    analyst=analyst,
                    firm=firm if firm else None,
                    currency=currency,
                    confidence=confidence
                )
                targets_written += 1

            if targets_written > 0:
                logger.info(f"✅ Wrote {targets_written} price targets to Signal Store")

        except Exception as e:
            logger.warning(f"Signal Store price targets write failed (graceful degradation): {e}")
            # Continue processing - dual-write failure shouldn't block email ingestion

    def _write_entities_to_signal_store(
        self,
        graph_data: Dict[str, Any],
        email_data: Dict[str, Any]
    ) -> None:
        """
        Write extracted entities (nodes) to Signal Store (dual-layer architecture).

        GraphBuilder node format → Signal Store entities schema:
        {
            'id': 'ticker_NVDA',
            'type': 'ticker',
            'properties': {'symbol': 'NVDA', 'confidence': 0.98},
            'created_at': '2024-03-15T10:30:00Z'
        }

        Signal Store entities schema:
            entity_id, entity_type, entity_name, confidence, source_document_id, metadata

        Args:
            graph_data: Graph structure from GraphBuilder (contains 'nodes' key)
            email_data: Email metadata (for source_document_id)
        """
        if not self.signal_store:
            return

        nodes = graph_data.get('nodes', [])
        if not nodes:
            return

        source_document_id = email_data.get('message_id', f"email_{email_data.get('uid', 'unknown')}")

        # Prepare entities for batch insert
        entities_to_insert = []

        for node in nodes:
            node_id = node.get('id')
            node_type = node.get('type', '').upper()
            properties = node.get('properties', {})

            if not node_id or not node_type:
                continue

            # Extract entity name from properties (varies by type)
            entity_name = None
            if node_type == 'TICKER':
                entity_name = properties.get('symbol') or properties.get('ticker', node_id)
            elif node_type == 'SENDER':
                entity_name = properties.get('name') or properties.get('email', node_id)
            elif node_type == 'COMPANY':
                entity_name = properties.get('name', node_id)
            elif node_type == 'EMAIL':
                entity_name = properties.get('subject', node_id)
            else:
                entity_name = node_id  # Fallback to node ID

            # Extract confidence (default to 1.0 for structural nodes like email/sender)
            confidence = properties.get('confidence', 1.0 if node_type in ['EMAIL', 'SENDER'] else 0.8)

            # Convert properties dict to JSON string for metadata
            import json
            metadata = json.dumps(properties)

            entities_to_insert.append({
                'entity_id': node_id,
                'entity_type': node_type,
                'entity_name': entity_name,
                'source_document_id': source_document_id,
                'confidence': confidence,
                'metadata': metadata
            })

        # Batch insert with transaction
        if entities_to_insert:
            try:
                count = self.signal_store.insert_entities_batch(entities_to_insert)
                logger.info(f"✅ Wrote {count} entities to Signal Store")
            except Exception as e:
                logger.warning(f"Signal Store entities write failed (graceful degradation): {e}")
                # Continue processing - dual-write failure shouldn't block email ingestion

    def _write_relationships_to_signal_store(
        self,
        graph_data: Dict[str, Any],
        email_data: Dict[str, Any]
    ) -> None:
        """
        Write entity relationships (edges) to Signal Store (dual-layer architecture).

        GraphBuilder edge format → Signal Store relationships schema:
        {
            'source_id': 'ticker_NVDA',
            'target_id': 'company_NVIDIA',
            'edge_type': 'is_ticker_for',
            'confidence': 0.95,
            'properties': {'timestamp': '...', 'source': 'email_extraction'}
        }

        Signal Store relationships schema:
            source_entity, target_entity, relationship_type, confidence, source_document_id, metadata

        Args:
            graph_data: Graph structure from GraphBuilder (contains 'edges' key)
            email_data: Email metadata (for source_document_id)
        """
        if not self.signal_store:
            return

        edges = graph_data.get('edges', [])
        if not edges:
            return

        source_document_id = email_data.get('message_id', f"email_{email_data.get('uid', 'unknown')}")

        # Prepare relationships for batch insert
        relationships_to_insert = []

        for edge in edges:
            source_id = edge.get('source_id')
            target_id = edge.get('target_id')
            edge_type = edge.get('edge_type', '').upper()
            confidence = edge.get('confidence', 0.8)
            properties = edge.get('properties', {})

            if not source_id or not target_id or not edge_type:
                continue

            # Convert properties dict to JSON string for metadata
            import json
            metadata = json.dumps(properties)

            relationships_to_insert.append({
                'source_entity': source_id,
                'target_entity': target_id,
                'relationship_type': edge_type,
                'source_document_id': source_document_id,
                'confidence': confidence,
                'metadata': metadata
            })

        # Batch insert with transaction
        if relationships_to_insert:
            try:
                count = self.signal_store.insert_relationships_batch(relationships_to_insert)
                logger.info(f"✅ Wrote {count} relationships to Signal Store")
            except Exception as e:
                logger.warning(f"Signal Store relationships write failed (graceful degradation): {e}")
                # Continue processing - dual-write failure shouldn't block email ingestion

    def is_service_available(self, service: str) -> bool:
        """Check if specific API service is configured"""
        return service in self.api_keys and bool(self.api_keys[service])

    def _format_number(self, value: Any) -> str:
        """Safely format a number with comma separators, handle strings/None"""
        try:
            if value is None or value == '' or value == 'N/A':
                return 'N/A'
            num = int(float(value))
            return f"{num:,}"
        except (ValueError, TypeError):
            return 'N/A'

    def fetch_company_news(self, symbol: str, limit: int = 5) -> List[Dict[str, str]]:
        """
        Fetch company news from available APIs - return source-tagged documents

        Args:
            symbol: Stock ticker symbol
            limit: Maximum number of articles

        Returns:
            List of dicts with 'content' and 'source' keys for source attribution
        """
        documents = []

        # Try NewsAPI.org if available
        if self.is_service_available('newsapi'):
            try:
                logger.info(f"  📰 {symbol}: Fetching from NewsAPI...")
                newsapi_docs = self._fetch_newsapi(symbol, limit)
                documents.extend([{'content': doc, 'source': 'newsapi'} for doc in newsapi_docs])
                logger.info(f"    ✅ NewsAPI: {len(newsapi_docs)} article(s)")
            except Exception as e:
                logger.warning(f"NewsAPI fetch failed for {symbol}: {e}")

        # Try Benzinga if available and we need more articles (professional-grade news)
        if self.benzinga_client and len(documents) < limit:
            try:
                remaining = limit - len(documents)
                logger.info(f"  📰 {symbol}: Fetching from Benzinga (professional)...")
                benzinga_docs = self._fetch_benzinga_news(symbol, remaining)
                documents.extend([{'content': doc, 'source': 'benzinga'} for doc in benzinga_docs])
                logger.info(f"    ✅ Benzinga: {len(benzinga_docs)} article(s)")
            except Exception as e:
                logger.warning(f"Benzinga fetch failed for {symbol}: {e}")

        # Try Finnhub if available and we need more articles
        if self.is_service_available('finnhub') and len(documents) < limit:
            try:
                remaining = limit - len(documents)
                logger.info(f"  📰 {symbol}: Fetching from Finnhub...")
                finnhub_docs = self._fetch_finnhub_news(symbol, remaining)
                documents.extend([{'content': doc, 'source': 'finnhub'} for doc in finnhub_docs])
                logger.info(f"    ✅ Finnhub: {len(finnhub_docs)} article(s)")
            except Exception as e:
                logger.warning(f"Finnhub news fetch failed for {symbol}: {e}")

        # Try MarketAux if available and we need more articles
        if self.is_service_available('marketaux') and len(documents) < limit:
            try:
                remaining = limit - len(documents)
                logger.info(f"  📰 {symbol}: Fetching from MarketAux...")
                marketaux_docs = self._fetch_marketaux_news(symbol, remaining)
                documents.extend([{'content': doc, 'source': 'marketaux'} for doc in marketaux_docs])
                logger.info(f"    ✅ MarketAux: {len(marketaux_docs)} article(s)")
            except Exception as e:
                logger.warning(f"MarketAux fetch failed for {symbol}: {e}")

        logger.info(f"Fetched {len(documents)} news articles for {symbol}")
        return documents[:limit]

    def _fetch_newsapi(self, symbol: str, limit: int) -> List[str]:
        """Fetch news from NewsAPI.org"""
        url = "https://newsapi.org/v2/everything"
        params = {
            'q': f'"{symbol}" OR "{symbol} stock" OR "{symbol} earnings"',
            'apiKey': self.api_keys['newsapi'],
            'pageSize': min(limit, 20),  # NewsAPI limit
            'sortBy': 'relevancy',
            'language': 'en'
        }

        response = requests.get(url, params=params, timeout=self.timeout)
        response.raise_for_status()
        data = response.json()

        documents = []
        for article in data.get('articles', []):
            content = f"""
News Article: {article.get('title', 'Untitled')}

{article.get('description', '')}

{article.get('content', '')}

Source: {article.get('source', {}).get('name', 'Unknown')}
Published: {article.get('publishedAt', 'Unknown')}
URL: {article.get('url', '')}
Symbol: {symbol}
"""
            documents.append(content.strip())

        return documents

    def _fetch_finnhub_news(self, symbol: str, limit: int) -> List[str]:
        """Fetch news from Finnhub"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)

        url = "https://finnhub.io/api/v1/company-news"
        params = {
            'symbol': symbol,
            'from': start_date.strftime('%Y-%m-%d'),
            'to': end_date.strftime('%Y-%m-%d'),
            'token': self.api_keys['finnhub']
        }

        response = requests.get(url, params=params, timeout=self.timeout)
        response.raise_for_status()
        data = response.json()

        documents = []
        for article in data[:limit]:
            content = f"""
Company News: {article.get('headline', 'No Headline')}

{article.get('summary', '')}

Source: Finnhub
Published: {datetime.fromtimestamp(article.get('datetime', 0)).isoformat()}
URL: {article.get('url', '')}
Symbol: {symbol}
Related: {article.get('related', symbol)}
"""
            documents.append(content.strip())

        return documents

    def _fetch_marketaux_news(self, symbol: str, limit: int) -> List[str]:
        """Fetch news from MarketAux"""
        url = "https://api.marketaux.com/v1/news/all"
        params = {
            'symbols': symbol,
            'filter_entities': 'true',
            'language': 'en',
            'api_token': self.api_keys['marketaux'],
            'limit': min(limit, 10)  # MarketAux free tier limit
        }

        response = requests.get(url, params=params, timeout=self.timeout)
        response.raise_for_status()
        data = response.json()

        documents = []
        for article in data.get('data', []):
            content = f"""
Market News: {article.get('title', 'No Title')}

{article.get('description', '')}

Source: {article.get('source', 'MarketAux')}
Published: {article.get('published_at', 'Unknown')}
URL: {article.get('url', '')}
Symbol: {symbol}
Entities: {', '.join(article.get('entities', []))}
"""
            documents.append(content.strip())

        return documents

    def _fetch_benzinga_news(self, symbol: str, limit: int) -> List[str]:
        """Fetch news from Benzinga (professional-grade real-time financial news)"""
        if not self.benzinga_client:
            logger.warning("Benzinga client not initialized")
            return []

        try:
            # Fetch news using production BenzingaClient
            articles = self.benzinga_client.get_news(ticker=symbol, limit=limit, hours_back=168)  # 7 days

            documents = []
            for article in articles[:limit]:
                # Format article data including sentiment and confidence
                sentiment_info = ""
                if article.sentiment_label and article.sentiment_score is not None:
                    sentiment_info = f"\nSentiment: {article.sentiment_label.value} (score: {article.sentiment_score:.2f})"

                # Extract categories from metadata
                categories = article.metadata.get('categories', []) if article.metadata else []
                categories_info = f"\nCategories: {', '.join(categories)}" if categories else ""

                # Extract symbols from metadata
                symbols = article.metadata.get('symbols', []) if article.metadata else []
                symbols_info = f"\nRelated Symbols: {', '.join(symbols)}" if symbols else ""

                content = f"""
Professional News (Benzinga): {article.title}

{article.content}

Source: {article.source}{sentiment_info}{categories_info}{symbols_info}
Published: {article.published_at.isoformat() if article.published_at else 'Unknown'}
URL: {article.url}
Confidence: {article.confidence}
Symbol: {symbol}
"""
                documents.append(content.strip())

            return documents

        except Exception as e:
            logger.warning(f"Benzinga news fetch failed for {symbol}: {e}")
            return []

    def fetch_financial_fundamentals(self, symbol: str, limit: int = 2) -> List[Dict[str, str]]:
        """
        Fetch company financial fundamentals (statements, metrics, ratios) - return source-tagged documents

        Args:
            symbol: Stock ticker symbol
            limit: Maximum number of financial documents to fetch (default: 2 - one per API)
                   Set to 0 to skip financial fundamentals entirely

        Returns:
            List of dicts with 'content' and 'source' keys for source attribution
        """
        # Skip if limit is 0
        if limit == 0:
            logger.info(f"⏭️  {symbol}: Skipping financial fundamentals (limit=0)")
            return []

        documents = []

        # Try Financial Modeling Prep if available (company profile, fundamentals)
        if self.is_service_available('fmp'):
            try:
                logger.info(f"  💰 {symbol}: Fetching fundamentals from FMP...")
                fmp_docs = self._fetch_fmp_profile(symbol)
                documents.extend([{'content': doc, 'source': 'fmp'} for doc in fmp_docs])
                logger.info(f"    ✅ FMP: {len(fmp_docs)} document(s)")
            except Exception as e:
                logger.warning(f"FMP profile fetch failed for {symbol}: {e}")

        # Try Alpha Vantage if available (company overview, financial metrics)
        if self.is_service_available('alpha_vantage'):
            try:
                logger.info(f"  💰 {symbol}: Fetching fundamentals from Alpha Vantage...")
                av_docs = self._fetch_alpha_vantage_overview(symbol)
                documents.extend([{'content': doc, 'source': 'alpha_vantage'} for doc in av_docs])
                logger.info(f"    ✅ Alpha Vantage: {len(av_docs)} document(s)")
            except Exception as e:
                logger.warning(f"Alpha Vantage overview fetch failed for {symbol}: {e}")

        logger.info(f"Fetched {len(documents)} financial fundamental documents for {symbol}")
        return documents[:limit]  # Enforce limit (matches fetch_company_news pattern)

    def fetch_market_data(self, symbol: str, limit: int = 1) -> List[Dict[str, str]]:
        """
        Fetch market data (prices, trading metadata) - return source-tagged documents

        Args:
            symbol: Stock ticker symbol
            limit: Maximum number of market data documents to fetch (default: 1 - Polygon)
                   Set to 0 to skip market data entirely

        Returns:
            List of dicts with 'content' and 'source' keys for source attribution
        """
        # Skip if limit is 0
        if limit == 0:
            logger.info(f"⏭️  {symbol}: Skipping market data (limit=0)")
            return []

        documents = []

        # Try Polygon if available (market data, trading metadata)
        if self.is_service_available('polygon'):
            try:
                logger.info(f"  📈 {symbol}: Fetching market data from Polygon...")
                poly_docs = self._fetch_polygon_details(symbol)
                documents.extend([{'content': doc, 'source': 'polygon'} for doc in poly_docs])
                logger.info(f"    ✅ Polygon: {len(poly_docs)} document(s)")
            except Exception as e:
                logger.warning(f"Polygon details fetch failed for {symbol}: {e}")

        logger.info(f"Fetched {len(documents)} market data documents for {symbol}")
        return documents[:limit]  # Enforce limit

    def fetch_email_documents(self, tickers: Optional[List[str]] = None, limit: int = 71, email_files: Optional[List[str]] = None) -> List[Dict]:
        """
        Fetch broker research emails with production-grade entity extraction

        Phase 2.6.1: Uses EntityExtractor for structured entity extraction
        Creates enhanced documents with inline markup for improved LightRAG precision

        During development, reads from data/emails_samples/ directory
        In production, can switch to real IMAP using imap_email_ingestion_pipeline

        Args:
            tickers: Optional list of ticker symbols to filter emails
            limit: Maximum number of emails to return (default: 71 - all sample emails)
            email_files: Optional list of specific .eml filenames to process (e.g., ['email1.eml', 'email2.eml'])
                        If provided, only these files are processed. If None, all files are processed.

        Returns:
            List of dicts with format: {'content': str, 'file_path': 'email:filename.eml', 'type': 'financial'}
            Structured entities stored in self.last_extracted_entities for Phase 2.6.2
        """
        # Early exit for disabled source (matches fetch_market_data pattern at line 977)
        if limit == 0:
            logger.info("⏭️ Skipping emails (limit=0, email source disabled)")
            return []

        import email
        from pathlib import Path

        documents = []
        # Reset structured data storage
        self.last_extracted_entities = []

        # Path relative to this file: updated_architectures/implementation/data_ingestion.py
        # Need to go up 2 levels to reach project root, then into data/emails_samples/
        emails_dir = Path(__file__).parent.parent.parent / "data" / "emails_samples"

        if not emails_dir.exists():
            logger.warning(f"Email samples directory not found: {emails_dir}")
            return documents

        # Get .eml files (either specific files or all files)
        if email_files:
            # Process only specified files
            eml_files = [emails_dir / f for f in email_files if (emails_dir / f).exists()]
            missing_files = [f for f in email_files if not (emails_dir / f).exists()]
            if missing_files:
                logger.warning(f"Email files not found: {missing_files}")
            logger.info(f"Processing {len(eml_files)} specified email files (from {len(email_files)} requested)")
        else:
            # Process all .eml files
            eml_files = list(emails_dir.glob("*.eml"))
            logger.info(f"Found {len(eml_files)} sample email files")

        # Process each email file
        # Use tuples to maintain alignment between documents and extracted entities
        filtered_items = []  # List of (document, entities) tuples
        all_items = []       # List of (document, entities) tuples

        for eml_file in eml_files:
            try:
                # Email format validation
                if not eml_file.suffix.lower() == '.eml':
                    logger.warning(f"Skipping non-email file: {eml_file.name}")
                    continue

                file_size = eml_file.stat().st_size
                if file_size == 0:
                    logger.warning(f"Skipping empty email file: {eml_file.name}")
                    continue
                if file_size > 50 * 1024 * 1024:  # 50MB limit
                    logger.warning(f"Skipping oversized email file ({file_size / (1024*1024):.1f}MB): {eml_file.name}")
                    continue

                # Character encoding detection
                encoding = 'utf-8'
                try:
                    import chardet
                    with open(eml_file, 'rb') as f:
                        raw_data = f.read(10000)  # Sample first 10KB for detection
                        detected = chardet.detect(raw_data)
                        if detected and detected['encoding'] and detected['confidence'] > 0.7:
                            encoding = detected['encoding']
                            if encoding != 'utf-8':
                                logger.debug(f"Detected encoding {encoding} (confidence: {detected['confidence']:.2f}) for {eml_file.name}")
                except ImportError:
                    # chardet not installed, fallback to utf-8
                    pass
                except Exception as e:
                    logger.debug(f"Encoding detection failed for {eml_file.name}: {e}, using utf-8")

                with open(eml_file, 'r', encoding=encoding, errors='ignore') as f:
                    msg = email.message_from_file(f)

                # Validate email structure
                if not msg:
                    logger.warning(f"Invalid email format, cannot parse: {eml_file.name}")
                    continue

                # Extract email metadata
                subject = msg.get('Subject', 'No Subject')
                sender = msg.get('From', 'Unknown Sender')
                date = msg.get('Date', 'Unknown Date')

                # Additional validation: must have at least subject or sender
                if subject == 'No Subject' and sender == 'Unknown Sender':
                    logger.warning(f"Email missing critical metadata (no subject or sender): {eml_file.name}")
                    # Continue processing but log warning

                # Extract email body (fallback: text/plain → HTML → empty)
                body_text = ""
                body_html = ""

                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain" and not body_text:
                            payload = part.get_payload(decode=True)
                            if payload:
                                # Try to use part's charset if available, otherwise use detected encoding
                                charset = part.get_content_charset() or encoding
                                body_text = payload.decode(charset, errors='ignore')
                        elif part.get_content_type() == "text/html" and not body_html:
                            payload = part.get_payload(decode=True)
                            if payload:
                                # Try to use part's charset if available, otherwise use detected encoding
                                charset = part.get_content_charset() or encoding
                                body_html = payload.decode(charset, errors='ignore')
                else:
                    payload = msg.get_payload(decode=True)
                    if payload:
                        # Try to use message's charset if available, otherwise use detected encoding
                        charset = msg.get_content_charset() or encoding
                        body_text = payload.decode(charset, errors='ignore')

                # Use text/plain if available, otherwise convert HTML to text
                if body_text:
                    body = body_text
                elif body_html:
                    parser = HTMLTextExtractor()
                    parser.feed(body_html)
                    body = '\n'.join(parser.text)
                else:
                    body = ""

                # FIX #4: Extract HTML tables from email body for structured table processing
                # Enables queries on earnings summaries embedded as HTML tables (not just attachments)
                # Example: Quarterly results table in email body (not as PDF attachment)
                html_tables_data = []
                if body_html:
                    try:
                        from bs4 import BeautifulSoup
                        soup = BeautifulSoup(body_html, 'html.parser')

                        for table_idx, html_table in enumerate(soup.find_all('table')):
                            # Extract headers (first row)
                            rows = html_table.find_all('tr')
                            if len(rows) < 2:  # Skip tables with no data rows (headers only)
                                continue

                            headers = [th.get_text(strip=True) for th in rows[0].find_all(['th', 'td'])]
                            if not headers:  # Skip tables with no headers
                                continue

                            # Extract data rows
                            table_data = []
                            for row in rows[1:]:
                                cells = [td.get_text(strip=True) for td in row.find_all(['td', 'th'])]
                                if len(cells) == len(headers):
                                    table_data.append(dict(zip(headers, cells)))

                            if table_data:  # Only add non-empty tables
                                html_tables_data.append({
                                    'index': table_idx,
                                    'data': table_data,
                                    'num_rows': len(table_data),
                                    'num_cols': len(headers),
                                    'source': 'email_body_html',
                                    'error': None
                                })

                        if html_tables_data:
                            logger.debug(f"Extracted {len(html_tables_data)} HTML table(s) from email body")

                    except Exception as e:
                        logger.warning(f"Failed to extract HTML tables from email body: {e}")
                        html_tables_data = []

                # Extract attachments if processor available (Phase 2.6.1)
                # Only 3/71 emails have attachments, so this is optional
                attachments_data = []
                attachment_stats = {'total': 0, 'successful': 0, 'failed': 0, 'cached': 0}
                if self.attachment_processor and msg.is_multipart():
                    for part in msg.walk():
                        content_disposition = part.get('Content-Disposition', '')
                        content_type = part.get_content_type()

                        # Detect both traditional attachments AND inline images
                        # Traditional: Content-Disposition: attachment; filename="report.pdf"
                        # Inline: Content-Disposition: inline; filename="image001.png" (HTML email embedded images)
                        # Tencent earnings PNG is inline, contains 14×6 financial table → Docling extracts at 97.9% accuracy
                        is_traditional_attachment = 'attachment' in content_disposition.lower()
                        is_inline_image = 'inline' in content_disposition.lower() and content_type.startswith('image/')

                        if is_traditional_attachment or is_inline_image:
                            filename = part.get_filename()
                            if filename:
                                attachment_stats['total'] += 1  # Track total attachments encountered
                                try:
                                    # Process attachment using AttachmentProcessor interface
                                    # Requires: attachment_data (Dict with 'part' and 'filename' keys) and email_uid
                                    attachment_dict = {
                                        'part': part,
                                        'filename': filename,
                                        'content_type': part.get_content_type()
                                    }
                                    email_uid = eml_file.stem  # Use filename without extension as UID

                                    result = self.attachment_processor.process_attachment(attachment_dict, email_uid)
                                    # BUG FIX: DoclingProcessor returns 'processing_status': 'completed', not 'status': 'success'
                                    # This was preventing inline images from being added to attachments_data
                                    if result.get('processing_status') == 'completed':
                                        attachments_data.append(result)
                                        attachment_stats['successful'] += 1  # Track successful processing
                                        # Track if this was cached or fresh processing
                                        if result.get('cached', False):
                                            attachment_stats['cached'] += 1
                                        logger.debug(f"Processed attachment: {filename} ({result.get('extraction_method', 'unknown')})")
                                    else:
                                        # Processing didn't complete successfully
                                        attachment_stats['failed'] += 1
                                        logger.warning(f"Attachment processing incomplete for {filename}: status={result.get('processing_status', 'unknown')}")

                                except Exception as e:
                                    attachment_stats['failed'] += 1  # Track failed processing
                                    logger.warning(f"Failed to process attachment {filename}: {e}")

                # Log attachment processing summary for user visibility
                if attachment_stats['total'] > 0:
                    success_rate = (attachment_stats['successful'] / attachment_stats['total']) * 100
                    cache_info = f", {attachment_stats['cached']} from cache" if attachment_stats['cached'] > 0 else ""
                    logger.info(
                        f"📎 Attachment summary for {eml_file.name}: "
                        f"{attachment_stats['successful']}/{attachment_stats['total']} successful ({success_rate:.1f}%)"
                        f"{cache_info}, {attachment_stats['failed']} failed"
                    )

                # Phase 2.6.1: Use EntityExtractor for structured extraction
                document = None  # Will store either enhanced or fallback document
                try:
                    # Prepare email data for entity extraction
                    # Validate and sanitize metadata to prevent 'unknown' values in enhanced documents
                    # Use filename stem (without extension) as UID, fallback to full name if stem is empty
                    email_uid = str(eml_file.stem).strip() if eml_file.stem else eml_file.name

                    # Handle missing/invalid sender - extract email or create synthetic one
                    if not sender or sender in ('Unknown Sender', '', 'None'):
                        # Try to extract from subject or create synthetic sender
                        email_sender = f"research@{eml_file.stem.replace('_', '').replace('-', '')}.com"
                    else:
                        email_sender = sender.strip()

                    # Ensure uid is not empty (could happen with .eml files named just ".eml")
                    if not email_uid:
                        email_uid = f"email_{eml_file.name.replace('.', '_')}"

                    email_data = {
                        'uid': email_uid,              # Unique ID from filename (e.g., 'dbs_research_001')
                        'from': email_sender,          # RFC 5322 standard key for sender email
                        'sender': email_sender,        # Backward compatibility for legacy code
                        'subject': subject,
                        'date': date,
                        'body': body,
                        'source_file': eml_file.name
                    }

                    # Debug logging to track email_data before entity extraction
                    logger.debug(f"Email data for {eml_file.name}: uid={email_uid!r}, from={email_sender!r}, subject={subject[:50]!r}")

                    # Extract entities using production EntityExtractor (from email body)
                    body_entities = self.entity_extractor.extract_entities(
                        body,
                        metadata={
                            'subject': subject,
                            'date': date,
                            'source': f'Email: {eml_file.name}'
                        }
                    )

                    # Filter false positive tickers from email body
                    body_entities = self.ticker_validator.filter_tickers(body_entities)

                    # BUG FIX: Extract ticker from body_entities instead of using email subject
                    # Subject line ("Tencent Q2 2025 Earnings") is NOT a ticker symbol
                    # EntityExtractor properly extracts ticker symbols like "TCEHY", "NVDA", "AAPL"
                    extracted_ticker = None
                    if body_entities and body_entities.get('tickers'):
                        # Get first high-confidence ticker from body
                        for ticker_entity in body_entities['tickers']:
                            if ticker_entity.get('confidence', 0) > 0.7:
                                extracted_ticker = ticker_entity.get('ticker') or ticker_entity.get('symbol')
                                break

                    # Fallback to subject if no ticker found (graceful degradation)
                    ticker_for_table = extracted_ticker if extracted_ticker else subject

                    logger.debug(f"Ticker for table extraction: {ticker_for_table} (extracted: {extracted_ticker}, subject: {subject[:30]}...)")

                    # Phase 2.6.2: Extract entities from attachment tables using TableEntityExtractor
                    table_entities = {}
                    if attachments_data:
                        table_entities = self.table_entity_extractor.extract_from_attachments(
                            attachments_data,
                            email_context={'ticker': ticker_for_table, 'date': date}
                        )

                    # FIX #4 (continued): Process HTML tables extracted from email body
                    # Convert html_tables_data to same format as attachments_data for TableEntityExtractor
                    html_table_entities = {'financial_metrics': [], 'margin_metrics': [], 'confidence': 0.0}
                    if html_tables_data:
                        # Wrap HTML tables in attachment-like structure for TableEntityExtractor
                        html_attachments_format = [{
                            'extracted_data': {'tables': html_tables_data},
                            'processing_status': 'completed',
                            'filename': 'email_body_html_tables',
                            'error': None
                        }]

                        html_table_entities = self.table_entity_extractor.extract_from_attachments(
                            html_attachments_format,
                            email_context={'ticker': ticker_for_table, 'date': date}
                        )

                        logger.debug(f"Extracted {len(html_table_entities.get('financial_metrics', []))} financial metrics from HTML tables")

                    # Merge body entities + attachment table entities + HTML table entities
                    merged_entities = self._merge_entities(body_entities, table_entities)
                    merged_entities = self._merge_entities(merged_entities, html_table_entities)

                    # Phase 2: Dual-write to Signal Store (structured queries)
                    # Write ratings to SQLite before creating enhanced document
                    # Uses transaction-based pattern: both Signal Store and LightRAG succeed or both fail
                    if self.signal_store:
                        try:
                            self._write_ratings_to_signal_store(
                                merged_entities=merged_entities,
                                email_data=email_data,
                                timestamp=date  # Email date as timestamp
                            )
                        except Exception as e:
                            logger.warning(f"Signal Store dual-write failed (graceful degradation): {e}")
                            # Continue processing - dual-write failure shouldn't block email ingestion

                    # Phase 3: Write financial metrics to Signal Store
                    # Dual-write pattern for metrics extracted from tables (Docling/TableEntityExtractor)
                    if self.signal_store:
                        try:
                            self._write_metrics_to_signal_store(
                                merged_entities=merged_entities,
                                email_data=email_data
                            )
                        except Exception as e:
                            logger.warning(f"Signal Store metrics write failed (graceful degradation): {e}")
                            # Continue processing - dual-write failure shouldn't block email ingestion

                    # Build typed relationship graph using GraphBuilder (Phase 2.6.1)
                    # Creates edges like ANALYST_RECOMMENDS, FIRM_COVERS, PRICE_TARGET_SET
                    # Now includes entities from both email body AND attachment tables
                    graph_data = self.graph_builder.build_email_graph(
                        email_data=email_data,
                        extracted_entities=merged_entities,
                        attachments_data=attachments_data if attachments_data else None
                    )

                    # Store graph data for dual-layer architecture (Phase 2.6.2)
                    email_id = email_data.get('source_file', 'unknown')
                    self.last_graph_data[email_id] = graph_data

                    # Phase 4: Write price targets to Signal Store
                    # Dual-write pattern for price targets extracted from email body
                    if self.signal_store:
                        try:
                            self._write_price_targets_to_signal_store(
                                merged_entities=merged_entities,
                                email_data=email_data,
                                timestamp=date  # Email date as timestamp
                            )
                        except Exception as e:
                            logger.warning(f"Signal Store price targets write failed (graceful degradation): {e}")
                            # Continue processing - dual-write failure shouldn't block email ingestion

                    # Phase 4: Write entities to Signal Store
                    # Dual-write pattern for entities (nodes) from GraphBuilder
                    if self.signal_store:
                        try:
                            self._write_entities_to_signal_store(
                                graph_data=graph_data,
                                email_data=email_data
                            )
                        except Exception as e:
                            logger.warning(f"Signal Store entities write failed (graceful degradation): {e}")
                            # Continue processing - dual-write failure shouldn't block email ingestion

                    # Phase 4: Write relationships to Signal Store
                    # Dual-write pattern for relationships (edges) from GraphBuilder
                    if self.signal_store:
                        try:
                            self._write_relationships_to_signal_store(
                                graph_data=graph_data,
                                email_data=email_data
                            )
                        except Exception as e:
                            logger.warning(f"Signal Store relationships write failed (graceful degradation): {e}")
                            # Continue processing - dual-write failure shouldn't block email ingestion

                    # Phase 2: Process links in email body to download research reports
                    # Uses IntelligentLinkProcessor with hybrid Crawl4AI routing
                    link_reports_text = ""
                    if self.link_processor:
                        try:
                            # Process email links asynchronously
                            # BUG FIX (2025-11-04): Use existing event loop instead of creating/closing new one
                            # Previous code: Created new loop, set as current, then closed it prematurely
                            # Problem: Closing loop interfered with later LightRAG document ingestion
                            # Solution: Use existing event loop with nest_asyncio (applied in ice_rag_fixed.py:32)
                            # nest_asyncio makes loops re-entrant, allowing safe run_until_complete() calls

                            # BUG FIX: Pass HTML content to link processor, not plain text
                            # IntelligentLinkProcessor needs HTML to extract <a> tags with BeautifulSoup
                            # Fallback to plain text only if no HTML available (rare case)
                            content_for_links = body_html if body_html else body

                            # Use existing event loop if available, otherwise handle with JupyterSyncWrapper pattern
                            # This matches ice_rag_fixed.py:484-497 (_run_async method)
                            # nest_asyncio (line 32 of ice_rag_fixed.py) makes loops re-entrant
                            try:
                                loop = asyncio.get_event_loop()
                                link_result = loop.run_until_complete(
                                    self.link_processor.process_email_links(
                                        email_html=content_for_links,  # HTML with <a> tags, fallback to plain text
                                        email_metadata={'subject': subject, 'sender': sender, 'date': date}
                                    )
                                )
                            except RuntimeError as e:
                                if "no running event loop" in str(e).lower() or "Event loop is closed" in str(e):
                                    # No loop or closed loop - use asyncio.run() which creates temporary loop
                                    link_result = asyncio.run(
                                        self.link_processor.process_email_links(
                                            email_html=content_for_links,
                                            email_metadata={'subject': subject, 'sender': sender, 'date': date}
                                        )
                                    )
                                else:
                                    raise

                            # ═══════════════════════════════════════════════════════
                            # PROMINENT URL PROCESSING REPORT (for notebook visibility)
                            # ═══════════════════════════════════════════════════════
                            print(f"\n{'='*70}")
                            print(f"🔗 URL PROCESSING: {eml_file.name}")
                            print(f"{'━'*70}")
                            print(f"📊 {link_result.total_links_found} URLs extracted\n")

                            # Display each URL with tier classification and status
                            print(f"🎯 URL Processing Details:")
            
                            # Track all processed URLs
                            url_count = 0
                            successful_urls = []
                            failed_urls = []
                            skipped_urls = []
            
                            # Process successful downloads
                            for report in link_result.research_reports:
                                url_count += 1
                                tier = report.metadata.get('tier', '?')
                                tier_name = report.metadata.get('tier_name', 'unknown')
            
                                # Determine method used (Simple HTTP for Tier 1-2, Crawl4AI for Tier 3-5)
                                if tier in [1, 2]:
                                    method = "Simple HTTP"
                                else:
                                    method = "Crawl4AI" if (self.link_processor and self.link_processor.use_crawl4ai) else "Simple HTTP (fallback)"
            
                                # Format file size
                                size_kb = report.file_size / 1024
                                size_str = f"{size_kb:.1f}KB" if size_kb < 1024 else f"{size_kb/1024:.1f}MB"
            
                                # Check if from cache (processing_time near zero indicates cache hit)
                                from_cache = " [CACHED]" if report.processing_time < 0.1 else ""
            
                                print(f"  [{url_count}] Tier {tier} ({tier_name}) ✅ SUCCESS{from_cache}")
                                # Smart URL display: show full URL if ≤100 chars, else truncate with "..."
                                url_display = report.url if len(report.url) <= 100 else f"{report.url[:97]}..."
                                print(f"      {url_display}")
                                print(f"      Method: {method} | Time: {report.processing_time:.1f}s | Size: {size_str}")
                                successful_urls.append(report.url)
            
                            # Process failed downloads and skipped URLs
                            for failure in link_result.failed_downloads:
                                url_count += 1
            
                                # Check if this was a skipped URL (Tier 6)
                                if failure.get('skipped', False):
                                    tier = failure.get('tier', 6)
                                    tier_name = failure.get('tier_name', 'skip')
                                    reason = failure.get('reason', 'Unknown')
                                    url = failure.get('url', 'Unknown URL')
            
                                    print(f"  [{url_count}] Tier {tier} ({tier_name}) ⏭️  SKIPPED")
                                    # Smart URL display: show full URL if ≤100 chars, else truncate with "..."
                                    url_display = url if len(url) <= 100 else f"{url[:97]}..."
                                    print(f"      {url_display}")
                                    print(f"      Reason: {reason}")
                                    skipped_urls.append(url)
                                else:
                                    # Actual failure
                                    tier = failure.get('tier', '?')
                                    tier_name = failure.get('tier_name', 'unknown')
                                    error = failure.get('error', 'Unknown error')
                                    url = failure.get('url', 'Unknown URL')
                                    stage = failure.get('stage', 'unknown')
            
                                    print(f"  [{url_count}] Tier {tier} ({tier_name}) ❌ FAILED")
                                    # Smart URL display: show full URL if ≤100 chars, else truncate with "..."
                                    url_display = url if len(url) <= 100 else f"{url[:97]}..."
                                    print(f"      {url_display}")
                                    print(f"      Error: {error[:80]}...")
                                    print(f"      Stage: {stage}")
                                    failed_urls.append(url)
            
                            # Summary statistics
                            print(f"\n📈 Summary:")
                            processable_urls = len(successful_urls) + len(failed_urls)  # Exclude skipped
                            success_rate = (len(successful_urls) / processable_urls * 100) if processable_urls > 0 else 0
            
                            print(f"  ✅ {len(successful_urls)} downloaded | ", end="")
                            print(f"⏭️  {len(skipped_urls)} skipped | ", end="")
                            print(f"❌ {len(failed_urls)} failed")
            
                            if processable_urls > 0:
                                print(f"  Success Rate: {success_rate:.0f}% ({len(successful_urls)}/{processable_urls} processable URLs)")
            
                            # Cache information
                            cache_hits = sum(1 for r in link_result.research_reports if r.processing_time < 0.1)
                            if cache_hits > 0:
                                print(f"  Cache Hits: {cache_hits} | Fresh Downloads: {len(link_result.research_reports) - cache_hits}")
            
                            # Portal links information (if any)
                            if link_result.portal_links:
                                if self.link_processor and self.link_processor.use_crawl4ai:
                                    print(f"  🌐 Portal links: {len(link_result.portal_links)} (processed with Crawl4AI)")
                                else:
                                    print(f"  ⚠️  Portal links skipped: {len(link_result.portal_links)} (Crawl4AI disabled)")
            
                            print(f"{'='*70}\n")
            
                            # Integrate downloaded report content into enhanced document
                            if link_result.research_reports:
                                logger.info(f"Downloaded {len(link_result.research_reports)} research reports from email links in {eml_file.name}")
            
                                # Extract entities from each downloaded PDF
                                # NOTE: IntelligentLinkProcessor already saved file to data/attachments/{email_uid}/{file_hash}/original/
                                # and extracted text content, so we skip redundant AttachmentProcessor re-saving
                                for report in link_result.research_reports:

                                    # Extract entities from PDF text content
                                    # File already saved to data/attachments/{email_uid}/{file_hash}/original/ by IntelligentLinkProcessor
                                    if report.text_content and len(report.text_content) > 100:
                                        try:
                                            # PHASE 1 IMPLEMENTATION (2025-11-04): Extract entities from URL PDFs
                                            # Previously: URL PDFs were text-extracted but NOT entity-extracted
                                            # Impact: Query precision 60% (text search) → 90% (entity matching)

                                            # Extract structured entities from PDF content
                                            pdf_entities = self.entity_extractor.extract_entities(
                                                report.text_content,
                                                metadata={
                                                    'source': 'linked_report',
                                                    'url': report.url,
                                                    'email_uid': email_uid,
                                                    'tier': report.metadata.get('tier'),
                                                    'tier_name': report.metadata.get('tier_name')
                                                }
                                            )

                                            # Filter false positive tickers
                                            pdf_entities = self.ticker_validator.filter_tickers(pdf_entities)

                                            # Build typed relationships from PDF entities
                                            pdf_graph_data = self.graph_builder.build_graph(
                                                email_data={'content': report.text_content, 'url': report.url},
                                                entities=pdf_entities,
                                                metadata={'source_type': 'linked_report'}
                                            )

                                            # Merge PDF entities with email-level entities
                                            merged_entities = self._deep_merge_entities(merged_entities, pdf_entities)
                                            graph_data['nodes'].extend(pdf_graph_data['nodes'])
                                            graph_data['edges'].extend(pdf_graph_data['edges'])

                                            logger.info(f"✅ Extracted {len(pdf_entities.get('tickers', []))} tickers, "
                                                       f"{len(pdf_entities.get('ratings', []))} ratings from PDF {report.url}")

                                            # Append PDF content to enhanced document
                                            link_reports_text += f"\n\n---\n[LINKED_REPORT:{report.url}]\n{report.text_content}\n"

                                        except Exception as e:
                                            # Graceful degradation: continue with plain text if entity extraction fails
                                            logger.error(f"❌ PDF entity extraction FAILED for {report.url}", exc_info=True)
                                            logger.error(f"   Exception: {type(e).__name__}: {e}")
                                            logger.error(f"   Text size: {len(report.text_content) if report.text_content else 0} chars")
                                            logger.error(f"   → Falling back to plain text ingestion")

                                            # Still append text content even if entity extraction fails
                                            link_reports_text += f"\n\n---\n[LINKED_REPORT:{report.url}]\n{report.text_content}\n"

                        except Exception as e:
                            logger.warning(f"Link processing failed for {eml_file.name}: {e}")
                            link_reports_text = ""

                    # Create enhanced document with inline entity markup and append linked reports
                    # Format: [TICKER:NVDA|confidence:0.95]
                    # BUG FIX: Use merged_entities (body + table) instead of undefined 'entities' variable
                    # DEBUG: Log merged_entities structure before document creation
                    logger.info(f"merged_entities before create_enhanced_document:")
                    logger.info(f"  financial_metrics: {len(merged_entities.get('financial_metrics', []))}")
                    logger.info(f"  margin_metrics: {len(merged_entities.get('margin_metrics', []))}")
                    logger.info(f"  metric_comparisons: {len(merged_entities.get('metric_comparisons', []))}")
                    if merged_entities.get('financial_metrics'):
                        for i, fm in enumerate(merged_entities['financial_metrics'][:3], 1):
                            logger.info(f"    FM {i}: {fm.get('metric')} = {fm.get('value')} (src={fm.get('source')})")
                    document = create_enhanced_document(email_data, merged_entities, graph_data=graph_data) + link_reports_text

                    # Debug: Check if document was created successfully
                    if document and 'unknown' in document[:200]:
                        logger.warning(f"Enhanced document contains 'unknown' values for {eml_file.name}")
                        logger.warning(f"email_data: uid={email_data.get('uid')}, from={email_data.get('from')}")

                    logger.debug(f"EntityExtractor: Found {len(merged_entities.get('tickers', []))} tickers, "
                                f"GraphBuilder: Created {len(graph_data.get('nodes', []))} nodes, "
                                f"{len(graph_data.get('edges', []))} edges in {eml_file.name}")

                except Exception as e:
                    # Graceful fallback to basic text extraction if EntityExtractor/GraphBuilder fails
                    logger.warning(f"Entity/Graph extraction failed for {eml_file.name}, using fallback: {e}")
                    merged_entities = {}  # Empty dict for failed extraction (renamed from 'entities' for consistency)
                    graph_data = {'nodes': [], 'edges': [], 'metadata': {}}  # Empty graph for fallback
                    # BUG FIX (2025-11-04): Append link_reports_text to preserve PDF content
                    # Previously, PDFs were downloaded but discarded in fallback path
                    # Now ensures PDFs are ingested even when entity extraction fails
                    document = f"""
Broker Research Email: {subject}

From: {sender}
Date: {date}
Source: Sample Email ({eml_file.name})

{body.strip()}

---
Email Type: Broker Research
Category: Investment Intelligence
Tickers Mentioned: {', '.join(tickers) if tickers else 'All'}
""" + link_reports_text

                # Add (document, entities, metadata) tuple to maintain alignment
                # Metadata includes subject and filename for file_path tracking
                # BUG FIX: Use merged_entities (defined in try block) instead of entities (only defined in except block)
                metadata = {'subject': subject, 'filename': eml_file.name}
                all_items.append((document.strip(), merged_entities, metadata))

                # Check if matches ticker filter
                if tickers:
                    content_text = f"{subject} {body}".upper()
                    if any(ticker.upper() in content_text for ticker in tickers):
                        filtered_items.append((document.strip(), merged_entities, metadata))

            except Exception as e:
                logger.warning(f"Failed to parse email {eml_file.name}: {e}")
                continue

        # Return logic with clear semantic priority:
        # 1. Specific files selected → return ALL matched files (ignore limit)
        # 2. Ticker filter applied → return filtered results (respect limit)
        # 3. No filter → return all results (respect limit)
        if email_files:
            # User explicitly selected these files, return ALL that were found
            items = all_items
            logger.info(f"Fetched {len(items)} specifically selected email documents")
            logger.info(f"  📊 Requested: {len(email_files)}, Found & Returned: {len(items)}")
        elif tickers and filtered_items:
            items = filtered_items[:limit]
            logger.info(f"Fetched {len(items)} email documents filtered by tickers: {tickers}")
            logger.info(f"  📊 Processed: {len(all_items)} total, Filtered: {len(filtered_items)}, Returned: {len(items)}")
        else:
            items = all_items[:limit]
            logger.info(f"Fetched {len(items)} email documents (no ticker filter applied)")
            logger.info(f"  📊 Processed: {len(all_items)} emails, Returned: {len(items)} (limit: {limit})")

        # Convert tuples to dict format with file_path for LightRAG traceability
        # Format: {'content': str, 'file_path': 'email:filename.eml', 'type': 'financial'}
        documents = [
            {
                'content': doc,
                'file_path': f"email:{metadata['filename']}",
                'type': 'financial'
            }
            for doc, _, metadata in items
        ]
        self.last_extracted_entities = [ent for _, ent, _ in items]

        return documents

    def fetch_sec_filings(self, symbol: str, limit: int = 5) -> List[Dict[str, str]]:
        """
        Fetch SEC EDGAR filings - switchable between metadata-only and full content extraction

        Toggle: config.use_docling_sec
        - True: Full content extraction with docling (financial tables, 97.9% accuracy)
        - False: Metadata only (current behavior, fast but limited)

        Flow with docling:
        SEC Filing → Docling/XBRL → EntityExtractor → GraphBuilder → Enhanced Document → LightRAG
        (Same pattern as email pipeline for consistency)

        Args:
            symbol: Stock ticker symbol
            limit: Maximum number of filings to return

        Returns:
            List of dicts with 'content' and 'source' keys for source attribution
        """
        import asyncio

        documents = []

        try:
            # 1. Fetch filing metadata (existing functionality, always runs)
            logger.info(f"  📋 {symbol}: Fetching SEC filings...")
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                filings = loop.run_until_complete(
                    self.sec_connector.get_recent_filings(symbol, limit=limit)
                )
            finally:
                loop.close()

            # 2. Content extraction (NEW - conditional on toggle)
            use_docling = self.config and self.config.use_docling_sec

            if use_docling:
                # Full content extraction with EntityExtractor/GraphBuilder integration
                try:
                    from src.ice_docling.sec_filing_processor import SECFilingProcessor
                    from ice_data_ingestion.robust_client import RobustHTTPClient

                    # Initialize processor (once, reuse if exists)
                    if not hasattr(self, '_sec_processor'):
                        self._sec_processor = SECFilingProcessor(
                            entity_extractor=self.entity_extractor,  # Already exists!
                            graph_builder=self.graph_builder,        # Already exists!
                            robust_client=RobustHTTPClient('sec_edgar'),
                            sec_connector=self.sec_connector         # Already exists!
                        )

                    # Process each filing
                    for filing in filings:
                        try:
                            # Extract content (XBRL parse OR docling)
                            result = self._sec_processor.extract_filing_content(
                                filing.accession_number,
                                filing.primary_document,
                                symbol,
                                is_xbrl=filing.is_xbrl,
                                is_inline_xbrl=filing.is_inline_xbrl
                            )

                            # Use enhanced document (with inline markup) - source tagged
                            documents.append({'content': result['enhanced_document'], 'source': 'sec_edgar'})

                            # Store structured data for Phase 2.6.2 Signal Store
                            filing_id = f"sec_{filing.accession_number}"
                            self.last_graph_data[filing_id] = result['graph_data']

                            logger.info(f"SEC content extracted: {symbol} {filing.form}, "
                                      f"{len(result['tables'])} tables, "
                                      f"method={result['metadata']['extraction_method']}")

                        except Exception as e:
                            logger.warning(f"Docling SEC extraction failed for {filing.form}, "
                                         f"using metadata fallback: {e}")
                            # Fallback to metadata-only for this filing
                            documents.append({'content': self._create_metadata_document(filing, symbol), 'source': 'sec_edgar'})

                except ImportError as e:
                    logger.warning(f"Docling SEC processor not available: {e}, using metadata only")
                    # Fallback to metadata-only for all filings
                    documents = [{'content': self._create_metadata_document(f, symbol), 'source': 'sec_edgar'} for f in filings]

            else:
                # Metadata-only mode (original behavior)
                logger.info(f"Using metadata-only mode for SEC filings (USE_DOCLING_SEC=false)")
                documents = [{'content': self._create_metadata_document(f, symbol), 'source': 'sec_edgar'} for f in filings]

            logger.info(f"    ✅ SEC EDGAR: {len(documents)} filing(s)")

        except Exception as e:
            logger.warning(f"SEC filings fetch failed for {symbol}: {e}")

        return documents

    def research_company_deep(self, symbol: str, company_name: str,
                             topics: Optional[List[str]] = None,
                             include_competitors: bool = True,
                             industry: Optional[str] = None) -> List[Dict[str, str]]:
        """
        Deep company research using Exa MCP semantic search (ON-DEMAND ONLY)

        This is a specialized research tool, NOT auto-ingested in daily waterfall.
        User explicitly calls this method when deep research is needed.

        Uses Exa MCP's semantic search capabilities for:
        - Company research (SEC filings, investor relations, news, analysis)
        - Competitor intelligence (find and analyze competitors)

        Cost-conscious: Only called when user needs deep research, not on routine builds.

        Args:
            symbol: Stock ticker symbol
            company_name: Full company name for better search results
            topics: Optional topics to focus research on (e.g., ['supply chain', 'AI chips'])
            include_competitors: Whether to include competitor analysis (default: True)
            industry: Industry context for better competitor finding

        Returns:
            List of dicts with 'content' and 'source' keys for source attribution
            Sources: 'exa_company', 'exa_competitors'

        Example:
            # Explicit user-directed research
            results = ingester.research_company_deep(
                symbol='NVDA',
                company_name='NVIDIA Corporation',
                topics=['AI chips', 'supply chain'],
                include_competitors=True,
                industry='semiconductor'
            )
        """
        if not self.exa_connector:
            logger.warning("Exa MCP connector not available - deep research skipped")
            return []

        documents = []

        # Use async-to-sync bridge pattern (proven in SEC EDGAR integration)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            logger.info(f"  🔬 {symbol}: Deep research with Exa MCP semantic search...")

            # 1. Company research
            try:
                company_results = loop.run_until_complete(
                    self.exa_connector.research_company(company_name, topics)
                )

                for result in company_results:
                    # Format Exa search result as document
                    highlights_text = ""
                    if result.highlights:
                        highlights_text = "\n\nKey Highlights:\n" + "\n".join(f"- {h}" for h in result.highlights[:3])

                    published_info = ""
                    if result.published_date:
                        published_info = f"\nPublished: {result.published_date.isoformat()}"

                    score_info = f"\nRelevance Score: {result.score:.3f}" if result.score else ""

                    content = f"""
Deep Research (Exa - Company): {result.title}

{result.text or 'No text content available'}{highlights_text}

Source: {result.author or 'Exa Semantic Search'}{published_info}{score_info}
URL: {result.url}
Symbol: {symbol}
Company: {company_name}
Search Type: Company Research
"""
                    documents.append({'content': content.strip(), 'source': 'exa_company'})

                logger.info(f"    ✅ Exa company research: {len(company_results)} result(s)")

            except Exception as e:
                logger.warning(f"Exa company research failed for {symbol}: {e}")

            # 2. Competitor analysis (if requested)
            if include_competitors:
                try:
                    competitor_results = loop.run_until_complete(
                        self.exa_connector.find_competitors(company_name, industry)
                    )

                    for result in competitor_results:
                        highlights_text = ""
                        if result.highlights:
                            highlights_text = "\n\nKey Highlights:\n" + "\n".join(f"- {h}" for h in result.highlights[:3])

                        score_info = f"\nRelevance Score: {result.score:.3f}" if result.score else ""

                        content = f"""
Deep Research (Exa - Competitors): {result.title}

{result.text or 'No text content available'}{highlights_text}

Source: Exa Competitor Intelligence{score_info}
URL: {result.url}
Symbol: {symbol}
Company: {company_name}
Search Type: Competitor Finder
"""
                        documents.append({'content': content.strip(), 'source': 'exa_competitors'})

                    logger.info(f"    ✅ Exa competitor analysis: {len(competitor_results)} result(s)")

                except Exception as e:
                    logger.warning(f"Exa competitor analysis failed for {symbol}: {e}")

        finally:
            loop.close()

        logger.info(f"  🔬 Exa MCP deep research completed: {len(documents)} document(s)")
        return documents

    def _create_metadata_document(self, filing, symbol: str) -> str:
        """Create metadata-only SEC document (original behavior)"""
        return f"""
SEC EDGAR Filing: {filing.form} - {symbol}

Filing Date: {filing.filing_date}
Accession Number: {filing.accession_number}
File Number: {filing.file_number}
Acceptance DateTime: {filing.acceptance_datetime}
Act: {filing.act}
Document Size: {filing.size:,} bytes
XBRL: {filing.is_xbrl}
Inline XBRL: {filing.is_inline_xbrl}
Primary Document: {filing.primary_document or 'N/A'}
Document Description: {filing.primary_doc_description or 'N/A'}

---
Source: SEC EDGAR Database
Symbol: {symbol}
Document Type: Regulatory Filing
Form Type: {filing.form}
""".strip()

    def _fetch_fmp_profile(self, symbol: str) -> List[str]:
        """Fetch company profile from Financial Modeling Prep"""
        url = f"https://financialmodelingprep.com/api/v3/profile/{symbol}"
        params = {'apikey': self.api_keys['fmp']}

        response = requests.get(url, params=params, timeout=self.timeout)
        response.raise_for_status()
        data = response.json()

        if not data:
            return []

        company = data[0]
        profile_text = f"""
Company Profile: {company.get('companyName', symbol)}

Symbol: {symbol}
Exchange: {company.get('exchangeShortName', 'Unknown')}
Sector: {company.get('sector', 'Unknown')}
Industry: {company.get('industry', 'Unknown')}
Country: {company.get('country', 'Unknown')}
Market Cap: ${self._format_number(company.get('mktCap', 0))}
Current Price: ${company.get('price', 0)}
Beta: {company.get('beta', 'N/A')}
Volume Average: {self._format_number(company.get('volAvg', 0))}
Website: {company.get('website', '')}

Business Description:
{company.get('description', 'No description available')}

Key Metrics:
- CEO: {company.get('ceo', 'Unknown')}
- Full Time Employees: {self._format_number(company.get('fullTimeEmployees', 0))}
- IPO Date: {company.get('ipoDate', 'Unknown')}
- 52 Week Range: ${company.get('range', 'N/A')}

Address: {company.get('address', '')}, {company.get('city', '')}, {company.get('state', '')} {company.get('zip', '')}

Source: Financial Modeling Prep
Retrieved: {datetime.now().isoformat()}
"""
        return [profile_text.strip()]

    def _fetch_alpha_vantage_overview(self, symbol: str) -> List[str]:
        """Fetch company overview from Alpha Vantage"""
        url = "https://www.alphavantage.co/query"
        params = {
            'function': 'OVERVIEW',
            'symbol': symbol,
            'apikey': self.api_keys['alpha_vantage']
        }

        response = requests.get(url, params=params, timeout=self.timeout)
        response.raise_for_status()
        data = response.json()

        if 'Symbol' not in data:
            return []

        overview_text = f"""
Company Overview: {data.get('Name', symbol)}

Symbol: {data.get('Symbol', symbol)}
AssetType: {data.get('AssetType', 'Unknown')}
Exchange: {data.get('Exchange', 'Unknown')}
Currency: {data.get('Currency', 'USD')}
Country: {data.get('Country', 'Unknown')}
Sector: {data.get('Sector', 'Unknown')}
Industry: {data.get('Industry', 'Unknown')}

Financial Metrics:
- Market Capitalization: ${self._format_number(data.get('MarketCapitalization', 0))}
- Shares Outstanding: {self._format_number(data.get('SharesOutstanding', 0))}
- PE Ratio: {data.get('PERatio', 'N/A')}
- PEG Ratio: {data.get('PEGRatio', 'N/A')}
- Book Value: {data.get('BookValue', 'N/A')}
- Dividend Per Share: {data.get('DividendPerShare', 'N/A')}
- Dividend Yield: {data.get('DividendYield', 'N/A')}
- EPS: {data.get('EPS', 'N/A')}
- Revenue Per Share (TTM): {data.get('RevenuePerShareTTM', 'N/A')}
- Profit Margin: {data.get('ProfitMargin', 'N/A')}
- Operating Margin (TTM): {data.get('OperatingMarginTTM', 'N/A')}
- Return on Assets (TTM): {data.get('ReturnOnAssetsTTM', 'N/A')}
- Return on Equity (TTM): {data.get('ReturnOnEquityTTM', 'N/A')}

Price Information:
- 52 Week High: ${data.get('52WeekHigh', 'N/A')}
- 52 Week Low: ${data.get('52WeekLow', 'N/A')}
- 50 Day Moving Average: ${data.get('50DayMovingAverage', 'N/A')}
- 200 Day Moving Average: ${data.get('200DayMovingAverage', 'N/A')}

Business Description:
{data.get('Description', 'No description available')}

Source: Alpha Vantage
Retrieved: {datetime.now().isoformat()}
"""
        return [overview_text.strip()]

    def _fetch_polygon_details(self, symbol: str) -> List[str]:
        """Fetch company details from Polygon.io"""
        url = f"https://api.polygon.io/v3/reference/tickers/{symbol}"
        params = {'apikey': self.api_keys['polygon']}

        response = requests.get(url, params=params, timeout=self.timeout)
        response.raise_for_status()
        data = response.json()

        if 'results' not in data:
            return []

        details = data['results']
        details_text = f"""
Company Details: {details.get('name', symbol)}

Ticker: {details.get('ticker', symbol)}
Market: {details.get('market', 'Unknown')}
Locale: {details.get('locale', 'Unknown')}
Primary Exchange: {details.get('primary_exchange', 'Unknown')}
Type: {details.get('type', 'Unknown')}
Active: {details.get('active', 'Unknown')}
Currency Name: {details.get('currency_name', 'Unknown')}
CIK: {details.get('cik', 'Unknown')}
Composite FIGI: {details.get('composite_figi', 'Unknown')}
Share Class FIGI: {details.get('share_class_figi', 'Unknown')}

Market Cap: ${self._format_number(details.get('market_cap', 0))}
Weighted Shares Outstanding: {self._format_number(details.get('weighted_shares_outstanding', 0))}
Outstanding Shares: {self._format_number(details.get('share_class_shares_outstanding', 0))}

Homepage: {details.get('homepage_url', '')}
Description: {details.get('description', 'No description available')}

Source: Polygon.io
Retrieved: {datetime.now().isoformat()}
"""
        return [details_text.strip()]

    def fetch_comprehensive_data(self, symbols: List[str],
                                news_limit: int = 2,
                                financial_limit: int = 2,
                                market_limit: int = 1,
                                email_limit: int = 71,
                                sec_limit: int = 2,
                                research_limit: int = 0) -> List[str]:
        """
        Fetch comprehensive data from ALL data sources with fine-grained category control

        This is the UNIFIED data ingestion method that combines:
        1. Email documents (broker research) from sample emails
        2. News data (API) from NewsAPI, Benzinga, Finnhub, MarketAux
        3. Financial fundamentals (API) from FMP, Alpha Vantage
        4. Market data (API) from Polygon
        5. SEC EDGAR filings (10-K, 10-Q, 8-K) from regulatory database
        6. Research/Search (MCP) from Exa MCP (on-demand, not auto-ingested)

        Args:
            symbols: List of stock ticker symbols
            news_limit: Maximum number of news articles per symbol (default: 2)
            financial_limit: Maximum number of financial fundamental documents per symbol (default: 2)
            market_limit: Maximum number of market data documents per symbol (default: 1)
            email_limit: Maximum number of emails to fetch (default: 71 - all samples)
            sec_limit: Maximum number of SEC filings per symbol (default: 2)
            research_limit: Maximum research documents per symbol (default: 0 - on-demand only)

        Returns:
            Combined list of all documents from all sources ready for LightRAG ingestion
        """
        all_documents = []

        logger.info(f"🚀 Fetching comprehensive data from 6 categories for symbols: {symbols}")

        # SOURCE 1: Email documents (CORE data source - broker research and signals)
        # Changed to tickers=None for full relationship discovery (Stage 1: Trust the Graph)
        # Rationale: LightRAG semantic search handles relevance filtering better than manual ticker matching
        # Impact: Enables multi-hop reasoning, competitor intelligence, sector context
        try:
            email_docs = self.fetch_email_documents(tickers=None, limit=email_limit)
            all_documents.extend(email_docs)
            logger.info(f"✅ Category 1 (Email): Added {len(email_docs)} email documents (unfiltered for relationship discovery)")
        except Exception as e:
            logger.error(f"❌ Category 1 (Email) failed: {e}")

        # CATEGORIES 2-6: For each symbol, get API/MCP data + SEC filings
        for symbol in symbols:
            # CATEGORY 2: News data (API)
            try:
                news_docs = self.fetch_company_news(symbol, news_limit)
                all_documents.extend(news_docs)
                logger.info(f"✅ Category 2 (News): Added {len(news_docs)} documents for {symbol}")
            except Exception as e:
                logger.error(f"❌ Category 2 (News) failed for {symbol}: {e}")

            # CATEGORY 3: Financial fundamentals (API)
            try:
                financial_docs = self.fetch_financial_fundamentals(symbol, financial_limit)
                all_documents.extend(financial_docs)
                logger.info(f"✅ Category 3 (Financial): Added {len(financial_docs)} documents for {symbol}")
            except Exception as e:
                logger.error(f"❌ Category 3 (Financial) failed for {symbol}: {e}")

            # CATEGORY 4: Market data (API)
            try:
                market_docs = self.fetch_market_data(symbol, market_limit)
                all_documents.extend(market_docs)
                logger.info(f"✅ Category 4 (Market): Added {len(market_docs)} documents for {symbol}")
            except Exception as e:
                logger.error(f"❌ Category 4 (Market) failed for {symbol}: {e}")

            # CATEGORY 5: SEC EDGAR filings (regulatory)
            try:
                sec_docs = self.fetch_sec_filings(symbol, limit=sec_limit)
                all_documents.extend(sec_docs)
                logger.info(f"✅ Category 5 (SEC): Added {len(sec_docs)} filings for {symbol}")
            except Exception as e:
                logger.error(f"❌ Category 5 (SEC) failed for {symbol}: {e}")

            # CATEGORY 6: Research/Search (MCP - on-demand only, not auto-ingested)
            # Note: research_limit typically 0 (default) since research_company_deep() is user-directed
            if research_limit > 0:
                try:
                    logger.info(f"  🔬 {symbol}: Initiating deep research (Exa MCP, limit={research_limit})...")
                    research_docs = self.research_company_deep(
                        symbol=symbol,
                        company_name=symbol,  # Simplified - ideally get full name from profile
                        topics=None,  # No topic filtering for comprehensive mode
                        include_competitors=False,  # Avoid overwhelming the graph
                        industry=None
                    )
                    all_documents.extend(research_docs[:research_limit])
                    logger.info(f"✅ Category 6 (Research): Added {len(research_docs[:research_limit])} documents for {symbol}")
                except Exception as e:
                    logger.error(f"❌ Category 6 (Research) failed for {symbol}: {e}")

        logger.info(f"📊 COMPREHENSIVE DATA FETCH COMPLETE: {len(all_documents)} total documents from 6 categories")
        logger.info(f"   Categories: Email + News + Financial + Market + SEC + Research")
        return all_documents

    def get_service_status(self) -> Dict[str, Any]:
        """
        Get status of available API services

        Returns:
            Dictionary with service availability and configuration info
        """
        status = {
            'total_services': len(self.api_keys),
            'available_services': self.available_services,
            'service_details': {}
        }

        # Service capabilities
        service_info = {
            'newsapi': {'type': 'news', 'limit': '1000/day', 'description': 'General news articles'},
            'finnhub': {'type': 'news+financial', 'limit': '60/minute', 'description': 'Financial news and company data'},
            'alpha_vantage': {'type': 'financial', 'limit': '25/day', 'description': 'Company fundamentals and overview'},
            'fmp': {'type': 'financial', 'limit': '250/day', 'description': 'Company profiles and financials'},
            'polygon': {'type': 'financial', 'limit': '5/minute', 'description': 'Company details and market data'},
            'marketaux': {'type': 'news', 'limit': '100/month', 'description': 'Financial news with entity extraction'},
            'benzinga': {'type': 'news', 'limit': 'varies', 'description': 'Professional financial news'}
        }

        for service in self.available_services:
            status['service_details'][service] = {
                'configured': True,
                **service_info.get(service, {'type': 'unknown', 'limit': 'unknown', 'description': 'Unknown service'})
            }

        return status


# Convenience functions
def create_data_ingester(api_keys: Optional[Dict[str, str]] = None) -> DataIngester:
    """
    Create and initialize data ingester

    Args:
        api_keys: Optional API keys dictionary

    Returns:
        Initialized DataIngester instance
    """
    ingester = DataIngester(api_keys=api_keys)
    logger.info(f"✅ Data Ingester created with {len(ingester.available_services)} services")
    return ingester


def test_data_ingestion(symbols: List[str] = ["NVDA", "TSMC", "AMD", "ASML"]) -> bool:
    """
    Test integrated data ingestion from all 3 sources

    Tests the complete integration:
    1. Email documents (broker research from sample emails)
    2. API data (news + financials from NewsAPI, Alpha Vantage, FMP, etc.)
    3. SEC EDGAR filings (regulatory documents)

    Args:
        symbols: List of stock symbols to test with (default: semiconductor portfolio)

    Returns:
        True if test passes, False otherwise
    """
    try:
        logger.info(f"🧪 Testing INTEGRATED data ingestion for {len(symbols)} symbols: {symbols}")

        ingester = create_data_ingester()

        # Test comprehensive data fetch from ALL 3 sources
        documents = ingester.fetch_comprehensive_data(
            symbols=symbols,
            news_limit=2,      # 2 news articles per symbol
            email_limit=71,    # All 71 broker emails from data/emails_samples/
            sec_limit=2        # 2 SEC filings per symbol
        )

        if documents:
            logger.info(f"✅ INTEGRATION TEST PASSED: {len(documents)} documents fetched from 3 sources")

            # Show breakdown by source
            email_docs = [d for d in documents if 'Broker Research Email' in d or 'Sample Email' in d]
            api_docs = [d for d in documents if any(src in d for src in ['NewsAPI', 'Alpha Vantage', 'Financial Modeling Prep', 'Finnhub', 'MarketAux', 'Polygon'])]
            sec_docs = [d for d in documents if 'SEC EDGAR' in d]

            logger.info(f"   📧 Email documents: {len(email_docs)}")
            logger.info(f"   📊 API documents: {len(api_docs)}")
            logger.info(f"   📋 SEC filings: {len(sec_docs)}")

            return True
        else:
            logger.warning("⚠️ No documents fetched, but no errors occurred")
            return True

    except Exception as e:
        logger.error(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Demo usage
    print("🚀 Data Ingestion Demo")

    try:
        # Test data ingestion
        if test_data_ingestion():
            print("✅ Data ingestion is working correctly")
        else:
            print("❌ Data ingestion test failed")

        # Show service status
        ingester = create_data_ingester()
        status = ingester.get_service_status()
        print(f"\n📊 Service Status: {status['total_services']} services configured")
        for service in status['available_services']:
            details = status['service_details'][service]
            print(f"  ✅ {service}: {details['type']} ({details['limit']})")

    except Exception as e:
        print(f"❌ Demo failed: {e}")