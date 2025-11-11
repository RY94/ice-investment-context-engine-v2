# Location: imap_email_ingestion_pipeline/enhanced_doc_creator.py
# Purpose: Create enhanced documents with inline metadata markup for LightRAG ingestion
# Business Value: Preserves high-precision EntityExtractor results while using single LightRAG graph
# Relevant Files: ice_integrator.py, entity_extractor.py, graph_builder.py, ARCHITECTURE_INTEGRATION_PLAN.md

"""
Enhanced Document Creator for ICE Email Pipeline

This module provides functionality to create enhanced documents that preserve
high-precision entity extraction results as inline markup within document text.

The enhanced documents solve the dual-graph problem by injecting custom
EntityExtractor output (tickers, ratings, price targets with confidence scores)
as structured markup before sending to LightRAG. This preserves domain expertise
while maintaining a single, queryable knowledge graph.

Example enhanced document:
    [SOURCE_EMAIL:12345|sender:analyst@gs.com|date:2024-01-15]
    [TICKER:NVDA|confidence:0.95] [RATING:BUY|confidence:0.87]
    [PRICE_TARGET:500|ticker:NVDA|currency:USD|confidence:0.92]

    Original email body text here...
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Minimum confidence threshold for including entities in markup
MIN_CONFIDENCE_THRESHOLD = 0.5


def escape_markup_value(value: Any) -> str:
    """
    Escape special characters in markup values to prevent parsing issues.

    Special characters that need escaping:
    - | (pipe): Field separator in markup
    - [ (left bracket): Start of markup tag
    - ] (right bracket): End of markup tag

    Args:
        value: Any value to be included in markup

    Returns:
        Escaped string safe for use in markup
    """
    if value is None:
        return "N/A"

    value_str = str(value)
    # Escape special characters
    value_str = value_str.replace('|', '\\|')
    value_str = value_str.replace('[', '\\[')
    value_str = value_str.replace(']', '\\]')

    return value_str


def create_enhanced_document(
    email_data: Dict[str, Any],
    entities: Dict[str, Any],
    graph_data: Optional[Dict[str, Any]] = None
) -> Optional[str]:
    """
    Create enhanced document with inline metadata markup for LightRAG.

    Takes high-precision EntityExtractor output and injects it as structured
    markup within the document text, preserving confidence scores and metadata.
    This allows a single LightRAG graph to benefit from custom domain-specific
    entity extraction without maintaining a separate graph system.

    Markup format: [TYPE:VALUE|attribute:value|attribute:value]
    Examples:
        - [TICKER:NVDA|confidence:0.95]
        - [RATING:BUY|ticker:NVDA|confidence:0.87]
        - [PRICE_TARGET:500|ticker:NVDA|currency:USD|confidence:0.92]
        - [ANALYST:John Doe|firm:Goldman Sachs|confidence:0.88]

    Args:
        email_data: Email metadata dictionary containing:
            - uid: Email unique identifier
            - from: Sender email address
            - date: Email date
            - subject: Email subject line
            - body: Email body text
            - priority: Priority level (optional)
            - attachments: List of attachment data (optional)

        entities: EntityExtractor output dictionary containing:
            - tickers: List of ticker entities with confidence scores
            - ratings: List of rating entities (BUY/SELL/HOLD)
            - financial_metrics: Dict with price_targets, revenue, etc.
            - people: List of analyst/person entities
            - companies: List of company mentions
            - sentiment: Overall sentiment analysis
            - confidence: Overall extraction confidence

        graph_data: Optional GraphBuilder output (for future use)

    Returns:
        Enhanced document string with inline markup, or None if creation fails

    Example:
        >>> email_data = {
        ...     'uid': '12345',
        ...     'from': 'analyst@gs.com',
        ...     'date': '2024-01-15',
        ...     'subject': 'NVDA Upgrade',
        ...     'body': 'We are upgrading NVDA to BUY...'
        ... }
        >>> entities = {
        ...     'tickers': [{'ticker': 'NVDA', 'confidence': 0.95}],
        ...     'ratings': [{'type': 'BUY', 'confidence': 0.87}]
        ... }
        >>> doc = create_enhanced_document(email_data, entities)
        >>> '[TICKER:NVDA|confidence:0.95]' in doc
        True
    """
    # Validate inputs
    if email_data is None or not isinstance(email_data, dict):
        logger.error("Invalid email_data: must be a dictionary")
        return None

    if not entities or not isinstance(entities, dict):
        logger.warning("No entities provided, creating basic document without markup")
        entities = {}

    try:
        # DEBUG: Function entry point
        logger.info(f"🔥 create_enhanced_document CALLED! entities keys: {list(entities.keys())}")
        logger.info(f"🔥 financial_metrics count: {len(entities.get('financial_metrics', []))}")
        logger.info(f"🔥 margin_metrics count: {len(entities.get('margin_metrics', []))}")

        doc_sections = []

        # === HEADER: Source metadata ===
        email_uid = escape_markup_value(email_data.get('uid', 'unknown'))
        sender = escape_markup_value(email_data.get('from', 'unknown'))
        date = escape_markup_value(email_data.get('date', 'unknown'))
        subject = escape_markup_value(email_data.get('subject', ''))

        # Source metadata header
        doc_sections.append(
            f"[SOURCE_EMAIL:{email_uid}|sender:{sender}|date:{date}|subject:{subject}]"
        )

        # Priority if available
        priority = email_data.get('priority')
        if priority:
            priority_confidence = email_data.get('priority_confidence', 0.0)
            if priority_confidence > MIN_CONFIDENCE_THRESHOLD:
                doc_sections.append(
                    f"[PRIORITY:{escape_markup_value(priority)}|confidence:{priority_confidence:.2f}]"
                )

        doc_sections.append("")  # Blank line after header

        # === ENTITY MARKUP: Inject high-confidence entities ===
        markup_line = []

        # Inject tickers with confidence
        tickers = entities.get('tickers', [])
        for ticker in tickers:
            if ticker.get('confidence', 0) > MIN_CONFIDENCE_THRESHOLD:
                ticker_symbol = escape_markup_value(ticker.get('ticker', ticker.get('symbol', 'UNKNOWN')))
                ticker_conf = ticker.get('confidence', 0.0)
                markup_line.append(f"[TICKER:{ticker_symbol}|confidence:{ticker_conf:.2f}]")

        # Inject ratings with metadata
        ratings = entities.get('ratings', [])
        for rating in ratings:
            if rating.get('confidence', 0) > MIN_CONFIDENCE_THRESHOLD:
                rating_type = escape_markup_value(rating.get('type', rating.get('rating', 'UNKNOWN')))
                rating_ticker = escape_markup_value(rating.get('ticker', 'N/A'))
                rating_conf = rating.get('confidence', 0.0)
                markup_line.append(
                    f"[RATING:{rating_type}|ticker:{rating_ticker}|confidence:{rating_conf:.2f}]"
                )

        # Inject price targets (direct from entities, not nested in financial_metrics)
        # BUG FIX: entities['financial_metrics'] is a list of metrics, not a dict with 'price_targets' key
        # Price targets are stored at entities['price_targets'] directly
        price_targets = entities.get('price_targets', [])
        for pt in price_targets:
            if pt.get('confidence', 0) > MIN_CONFIDENCE_THRESHOLD:
                pt_value = escape_markup_value(pt.get('value', pt.get('price', 'UNKNOWN')))
                pt_ticker = escape_markup_value(pt.get('ticker', 'N/A'))
                pt_currency = escape_markup_value(pt.get('currency', 'USD'))
                pt_conf = pt.get('confidence', 0.0)
                markup_line.append(
                    f"[PRICE_TARGET:{pt_value}|ticker:{pt_ticker}|currency:{pt_currency}|confidence:{pt_conf:.2f}]"
                )

        # Inject other financial metrics (revenue, EPS, EBITDA, etc.)
        # BUG FIX: 'financials' and 'percentages' are stored at entities level, not nested in financial_metrics
        financials = entities.get('financials', [])
        for metric in financials[:5]:  # Limit to top 5 financial metrics
            if metric.get('confidence', 0) > MIN_CONFIDENCE_THRESHOLD:
                metric_value = escape_markup_value(metric.get('value', 'UNKNOWN'))
                metric_full = escape_markup_value(metric.get('full_match', ''))[:50]  # Truncate for readability
                metric_conf = metric.get('confidence', 0.0)
                markup_line.append(
                    f"[FINANCIAL_METRIC:{metric_value}|context:{metric_full}|confidence:{metric_conf:.2f}]"
                )

        # Inject percentage metrics (margins, growth rates, etc.)
        percentages = entities.get('percentages', [])
        for pct in percentages[:5]:  # Limit to top 5 percentages
            if pct.get('confidence', 0) > MIN_CONFIDENCE_THRESHOLD:
                pct_value = escape_markup_value(pct.get('value', 'UNKNOWN'))
                pct_context = escape_markup_value(pct.get('context', ''))[:50]  # Truncate for readability
                pct_conf = pct.get('confidence', 0.0)
                markup_line.append(
                    f"[PERCENTAGE:{pct_value}|context:{pct_context}|confidence:{pct_conf:.2f}]"
                )

        # Inject analyst/people information
        people = entities.get('people', [])
        for person in people[:3]:  # Limit to top 3 analysts for readability
            if person.get('confidence', 0) > MIN_CONFIDENCE_THRESHOLD:
                person_name = escape_markup_value(person.get('name', 'UNKNOWN'))
                person_firm = escape_markup_value(person.get('firm', person.get('organization', 'Unknown')))
                person_conf = person.get('confidence', 0.0)
                markup_line.append(
                    f"[ANALYST:{person_name}|firm:{person_firm}|confidence:{person_conf:.2f}]"
                )

        # Inject company entities
        companies = entities.get('companies', [])
        for company in companies[:5]:  # Limit to top 5 companies for readability
            if company.get('confidence', 0) > MIN_CONFIDENCE_THRESHOLD:
                company_name = escape_markup_value(company.get('name', 'UNKNOWN'))
                company_ticker = escape_markup_value(company.get('ticker', 'N/A'))
                company_conf = company.get('confidence', 0.0)
                markup_line.append(
                    f"[COMPANY:{company_name}|ticker:{company_ticker}|confidence:{company_conf:.2f}]"
                )

        # Inject sentiment if high confidence
        sentiment = entities.get('sentiment', {})
        if isinstance(sentiment, dict) and sentiment.get('confidence', 0) > MIN_CONFIDENCE_THRESHOLD:
            sent_value = escape_markup_value(sentiment.get('sentiment', 'NEUTRAL'))
            sent_score = sentiment.get('score', 0.0)
            sent_conf = sentiment.get('confidence', 0.0)
            markup_line.append(
                f"[SENTIMENT:{sent_value}|score:{sent_score:.2f}|confidence:{sent_conf:.2f}]"
            )

        # === TABLE ENTITY MARKUP: Inject table-extracted entities (Phase 2.6.2) ===
        table_financial_metrics = entities.get('financial_metrics', [])
        table_margin_metrics = entities.get('margin_metrics', [])

        # DEBUG: Log table entity counts
        logger.info(f"TABLE ENTITY DEBUG: financial_metrics={len(table_financial_metrics)}, margin_metrics={len(table_margin_metrics)}")

        # Filter to only table-sourced financial metrics
        table_metrics_only = [m for m in table_financial_metrics if m.get('source') == 'table']

        if table_metrics_only or table_margin_metrics:
            table_markup = []

            # Table financial metrics
            # FIX #3: Increased limit from 10→100 to accommodate multi-column extraction
            # (e.g., Tencent table: 11 rows × 5 columns = 55 entities)
            for metric in table_metrics_only[:100]:  # Limit to avoid bloat
                if metric.get('confidence', 0) > MIN_CONFIDENCE_THRESHOLD:
                    table_markup.append(
                        f"[TABLE_METRIC:{escape_markup_value(metric.get('metric', 'UNKNOWN'))}|"
                        f"value:{escape_markup_value(metric.get('value', 'N/A'))}|"
                        f"period:{escape_markup_value(metric.get('period', 'N/A'))}|"
                        f"ticker:{escape_markup_value(metric.get('ticker', 'N/A'))}|"
                        f"confidence:{metric.get('confidence', 0.0):.2f}]"
                    )

            # Table margin metrics
            # FIX #3: Increased limit from 5→50 to accommodate multi-column extraction
            for margin in table_margin_metrics[:50]:  # Limit to avoid excessive bloat
                if margin.get('confidence', 0) > MIN_CONFIDENCE_THRESHOLD:
                    table_markup.append(
                        f"[MARGIN:{escape_markup_value(margin.get('metric', 'UNKNOWN'))}|"
                        f"value:{escape_markup_value(margin.get('value', 'N/A'))}|"
                        f"period:{escape_markup_value(margin.get('period', 'N/A'))}|"
                        f"ticker:{escape_markup_value(margin.get('ticker', 'N/A'))}|"
                        f"confidence:{margin.get('confidence', 0.0):.2f}]"
                    )

            if table_markup:
                markup_line.extend(table_markup)

        # Add entity markup line if any entities were found
        if markup_line:
            doc_sections.append(" ".join(markup_line))
            doc_sections.append("")  # Blank line after markup

        # === EMAIL CONTENT: Original email body ===
        email_body = email_data.get('body', '')
        if email_body:
            doc_sections.append("=== ORIGINAL EMAIL CONTENT ===")
            doc_sections.append("")
            doc_sections.append(email_body.strip())
            doc_sections.append("")

        # === ATTACHMENTS: Summaries with metadata ===
        attachments = email_data.get('attachments', [])
        if attachments:
            doc_sections.append("=== ATTACHMENTS ===")
            doc_sections.append("")

            for attachment in attachments:
                # Skip attachments with errors
                if attachment.get('error'):
                    continue

                filename = escape_markup_value(attachment.get('filename', 'unknown'))
                content_type = escape_markup_value(attachment.get('content_type', attachment.get('mime_type', 'unknown')))

                doc_sections.append(f"[ATTACHMENT:{filename}|type:{content_type}]")

                # Phase 2.6.2: Include FULL table content (no truncation for structured data)
                extracted_data = attachment.get('extracted_data', {})
                tables = extracted_data.get('tables', [])

                if tables:
                    # Include full table markdown (structured data from Docling)
                    for table_idx, table in enumerate(tables):
                        if table.get('error') or not table.get('markdown'):
                            continue

                        doc_sections.append(
                            f"\nTable {table_idx + 1} ({table['num_rows']} rows × {table['num_cols']} cols):"
                        )
                        doc_sections.append(table['markdown'])  # Full table, no truncation
                        doc_sections.append("")
                else:
                    # Fallback: use extracted_text with truncation (non-table attachments)
                    extracted_text = attachment.get('extracted_text', '')
                    if extracted_text:
                        # Limit attachment text to 500 characters to prevent document bloat
                        truncated_text = extracted_text[:500]
                        doc_sections.append(truncated_text)
                        if len(extracted_text) > 500:
                            doc_sections.append("... [attachment text truncated] ...")
                        doc_sections.append("")

        # === FOOTER: Investment context metadata ===
        doc_sections.append("=== INVESTMENT CONTEXT ===")
        doc_sections.append(f"Source: Email from {email_data.get('from', 'unknown sender')}")
        doc_sections.append(f"Received: {email_data.get('date', 'unknown date')}")

        overall_confidence = entities.get('confidence', 0.0)
        if overall_confidence > 0:
            doc_sections.append(f"Extraction Confidence: {overall_confidence:.2f}")

        # === FINAL DOCUMENT ASSEMBLY ===
        enhanced_doc = "\n".join(doc_sections)

        logger.info(
            f"Created enhanced document: {len(enhanced_doc)} bytes, "
            f"{len(tickers)} tickers, {len(ratings)} ratings, "
            f"confidence: {overall_confidence:.2f}"
        )

        return enhanced_doc

    except Exception as e:
        logger.error(f"Error creating enhanced document: {e}", exc_info=True)
        return None


def validate_enhanced_document(document: str) -> Dict[str, Any]:
    """
    Validate enhanced document format and extract metadata.

    Useful for testing and debugging to ensure markup is correctly formatted.

    Args:
        document: Enhanced document string to validate

    Returns:
        Validation result dictionary with:
            - valid: Boolean indicating if document is valid
            - markup_count: Number of markup tags found
            - errors: List of validation errors
            - metadata: Extracted metadata dictionary
    """
    result = {
        'valid': True,
        'markup_count': 0,
        'errors': [],
        'metadata': {}
    }

    if not document or not isinstance(document, str):
        result['valid'] = False
        result['errors'].append("Document must be a non-empty string")
        return result

    # Count markup tags (basic validation)
    import re
    markup_pattern = r'\[([A-Z_0-9]+):([^\]]+)\]'  # Support alphanumeric tag names
    matches = re.findall(markup_pattern, document)
    result['markup_count'] = len(matches)

    # Extract metadata from matches
    for tag_type, tag_value in matches:
        if tag_type not in result['metadata']:
            result['metadata'][tag_type] = []
        result['metadata'][tag_type].append(tag_value)

    # Basic validation: Check for SOURCE_EMAIL tag
    if 'SOURCE_EMAIL' not in result['metadata']:
        result['valid'] = False
        result['errors'].append("Missing SOURCE_EMAIL metadata tag")

    return result
