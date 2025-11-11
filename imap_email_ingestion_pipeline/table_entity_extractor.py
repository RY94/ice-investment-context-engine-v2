# Location: imap_email_ingestion_pipeline/table_entity_extractor.py
# Purpose: Extract financial entities from Docling-processed table data
# Why: Enable portfolio-level analytics by converting table content to structured entities for knowledge graph
# Relevant Files: entity_extractor.py, graph_builder.py, data_ingestion.py, docling_processor.py

import re
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime


class TableEntityExtractor:
    """
    Extract structured financial entities from attachment table data.

    Processes Docling table output (structured DataFrames) to identify:
    - Financial metrics (revenue, profit, EPS)
    - Margin metrics (gross margin, operating margin)
    - Metric comparisons (YoY/QoQ changes)

    Designed to work with DoclingProcessor output format:
    table['data'] = [{'col1': val1, 'col2': val2}, ...]  # List of row dicts
    """

    def __init__(self, min_confidence: float = 0.5):
        """
        Initialize table entity extractor.

        Args:
            min_confidence: Minimum confidence threshold for entity extraction
        """
        self.logger = logging.getLogger(__name__)
        self.min_confidence = min_confidence

        # Financial metric patterns (case-insensitive)
        self.metric_patterns = {
            'revenue': r'revenue|sales|turnover',
            'profit': r'profit|income|earnings|ebit|ebitda',
            'margin': r'margin|profitability',
            'eps': r'eps|earnings per share',
            'assets': r'assets|liabilities',
            'cash': r'cash|liquidity'
        }

        # Value format patterns (with optional +/- signs to preserve direction)
        self.value_patterns = {
            'billions': r'[+-]?\s*[\d,.]+\s*[bB](?:illion)?',  # +184.5B, -50.2B, 184.5 billion
            'millions': r'[+-]?\s*[\d,.]+\s*[mM](?:illion)?',  # +60.1M, -12.3M, 60.1M
            'percentage': r'[+-]?\s*[\d,.]+\s*%',              # +6%, -6%, 51%, 14.5%
            'ppt': r'[+-]?\s*[\d,.]+\s*ppt',                   # +1.2ppt, -1.0ppt (percentage points)
            'currency': r'[$¥€£]\s*[+-]?\s*[\d,.]+',           # $+184.5, $-50.2, ¥60.1
            'plain_number': r'[+-]?\s*[\d,.]+'                 # +123, -456, 789
        }

    def extract_from_attachments(
        self,
        attachments_data: List[Dict[str, Any]],
        email_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Extract entities from all attachment tables.

        Args:
            attachments_data: List of processed attachments from DoclingProcessor
            email_context: Email metadata (ticker, date) for entity enrichment

        Returns:
            Dict with entity lists:
            {
                'financial_metrics': [...],
                'margin_metrics': [...],
                'metric_comparisons': [...],
                'confidence': float
            }
        """
        all_entities = {
            'financial_metrics': [],
            'margin_metrics': [],
            'metric_comparisons': [],
            'confidence': 0.0
        }

        # DEBUG: Log what we received
        self.logger.debug(f"extract_from_attachments called with {len(attachments_data) if attachments_data else 0} attachments")

        if not attachments_data:
            self.logger.debug("No attachments_data provided, returning empty entities")
            return all_entities

        total_confidence = 0.0
        table_count = 0

        for idx, attachment in enumerate(attachments_data):
            # DEBUG: Log attachment structure
            self.logger.debug(f"  Attachment {idx}: status={attachment.get('processing_status')}, error={attachment.get('error')}")
            self.logger.debug(f"  Attachment {idx} keys: {list(attachment.keys())}")

            # Skip failed attachments
            if attachment.get('error') or attachment.get('processing_status') != 'completed':
                self.logger.debug(f"  Skipping attachment {idx}: failed or incomplete")
                continue

            # Extract tables from attachment
            extracted_data = attachment.get('extracted_data', {})
            self.logger.debug(f"  extracted_data keys: {list(extracted_data.keys()) if extracted_data else 'None'}")

            tables = extracted_data.get('tables', [])
            self.logger.debug(f"  Found {len(tables)} tables")

            for table_index, table in enumerate(tables):
                # Skip tables with errors
                if table.get('error'):
                    continue

                # Extract entities from this table
                table_entities = self._extract_from_table(
                    table,
                    table_index,
                    email_context
                )

                # Merge entities
                all_entities['financial_metrics'].extend(table_entities.get('financial_metrics', []))
                all_entities['margin_metrics'].extend(table_entities.get('margin_metrics', []))
                all_entities['metric_comparisons'].extend(table_entities.get('metric_comparisons', []))

                total_confidence += table_entities.get('confidence', 0.0)
                table_count += 1

        # Calculate average confidence
        if table_count > 0:
            all_entities['confidence'] = total_confidence / table_count

        self.logger.info(
            f"Extracted {len(all_entities['financial_metrics'])} financial metrics, "
            f"{len(all_entities['margin_metrics'])} margin metrics from {table_count} tables"
        )

        return all_entities

    def _extract_from_table(
        self,
        table: Dict[str, Any],
        table_index: int,
        email_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Extract entities from a single table.

        Args:
            table: Docling table dict with 'data', 'num_rows', 'num_cols'
            table_index: Index of table in attachment
            email_context: Email metadata for entity enrichment

        Returns:
            Dict with extracted entities for this table
        """
        entities = {
            'financial_metrics': [],
            'margin_metrics': [],
            'metric_comparisons': [],
            'confidence': 0.0
        }

        # Get table data (list of row dicts)
        table_data = table.get('data', [])
        if not table_data:
            return entities

        # Detect column types (which column has metric names, which has values)
        column_map = self._detect_column_types(table_data)
        if not column_map:
            self.logger.debug(f"Could not detect column structure in table {table_index}")
            return entities

        # Extract entities from each row AND each value column
        # FIX #1: Multi-column extraction (not just first column)
        # Enables queries like "What was Q2 2024 margin?" (needs historical columns)
        # and "What's the YoY growth?" (needs comparison columns)
        confidences = []
        for row_index, row in enumerate(table_data):
            # DEBUG: Track metric name for row-level logging
            metric_name = row.get(column_map.get('metric_col', ''), '')

            # Loop through ALL value columns (e.g., 2Q2025, 2Q2024, YoY, 1Q2025, QoQ)
            for value_col in column_map.get('value_cols', []):
                # Create single-column map for this specific value column
                single_col_map = {
                    'metric_col': column_map['metric_col'],
                    'value_cols': [value_col]  # Extract one column at a time
                }

                # Parse financial metric from row for THIS value column
                metric_entity = self._parse_financial_metric(
                    row,
                    single_col_map,  # Use single-column map
                    table_index,
                    row_index,
                    email_context
                )

                if metric_entity:
                    # Classify metric type
                    metric_name_lower = metric_entity['metric'].lower()

                    if 'margin' in metric_name_lower:
                        entities['margin_metrics'].append(metric_entity)
                        # DEBUG: Log margin metric extraction
                        self.logger.debug(
                            f"✅ Margin metric extracted: row={row_index}, "
                            f"metric={metric_entity['metric']}, value={metric_entity['value']}, "
                            f"period={metric_entity['period']}, confidence={metric_entity['confidence']:.2f}"
                        )
                    else:
                        entities['financial_metrics'].append(metric_entity)

                    confidences.append(metric_entity.get('confidence', 0.0))
                else:
                    # DEBUG: Log failed extraction for margin-related rows
                    if metric_name and 'margin' in metric_name.lower():
                        raw_value = row.get(value_col, '')
                        self.logger.debug(
                            f"❌ Margin metric extraction FAILED: row={row_index}, "
                            f"metric={metric_name}, column={value_col}, raw_value={raw_value}"
                        )

        # Calculate table confidence
        if confidences:
            entities['confidence'] = sum(confidences) / len(confidences)

        return entities

    def _detect_column_types(self, table_data: List[Dict[str, str]]) -> Optional[Dict[str, Any]]:
        """
        Detect which columns contain metric names vs values.

        Strategy (FIXED 2025-10-28):
        - Use STRUCTURE-based detection instead of pattern matching
        - Metric column: Contains TEXT (not just numbers)
        - Value columns: Contain NUMBERS with optional currency/percentage symbols
        - More robust: Works for ANY company's table format (BABA, NVDA, TSLA, etc.)

        Args:
            table_data: List of row dicts from Docling

        Returns:
            Dict mapping column roles: {'metric_col': 'Metric', 'value_cols': ['Q2 2025', 'Q2 2024'], ...}
        """
        if not table_data:
            return None

        # Get column names from first row
        columns = list(table_data[0].keys())

        # Analyze each column
        metric_col = None
        value_cols = []

        for col in columns:
            # Count how many rows in this column are:
            # - text (not just numbers)
            # - numbers (with/without currency symbols)
            text_count = 0
            number_count = 0

            # Check up to 10 rows for better coverage
            sample_rows = table_data[:min(10, len(table_data))]

            for row in sample_rows:
                cell_value = str(row.get(col, '')).strip()
                if not cell_value:
                    continue

                # Check if this cell is purely numeric (value column indicator)
                # Matches: "123", "123.45", "123,456", "$123", "123%", "123B", etc.
                if re.match(r'^[+-]?\s*[$¥€£]?\s*[\d,.]+\s*[%BMKbmk]?$', cell_value):
                    number_count += 1
                else:
                    # Contains text beyond just numbers/currency/symbols
                    text_count += 1

            # Column classification:
            # - If majority text → metric column
            # - If majority numbers → value column
            if text_count > number_count and text_count > 0:
                # This column has more text than numbers → metric column
                # NOTE: Use 'is None' check instead of 'not' to handle empty string column names
                if metric_col is None:  # Take first text column as metric column
                    metric_col = col
                    self.logger.debug(f"Detected metric column: '{col}' (text_count={text_count}, number_count={number_count})")
            elif number_count > 0:
                # This column has numbers → value column
                value_cols.append(col)
                self.logger.debug(f"Detected value column: '{col}' (number_count={number_count}, text_count={text_count})")

        # NOTE: Use 'is None' check instead of 'not' to handle empty string column names
        if metric_col is None or not value_cols:
            self.logger.debug(f"Column detection failed: metric_col={metric_col}, value_cols={value_cols}")
            return None

        self.logger.debug(f"✅ Column detection successful: metric_col='{metric_col}', value_cols={value_cols}")
        return {
            'metric_col': metric_col,
            'value_cols': value_cols
        }

    def _parse_financial_metric(
        self,
        row: Dict[str, str],
        column_map: Dict[str, Any],
        table_index: int,
        row_index: int,
        email_context: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Parse a financial metric from a table row.

        Args:
            row: Single row dict from table
            column_map: Column type mapping from _detect_column_types
            table_index: Index of table in attachment
            row_index: Index of row in table
            email_context: Email metadata

        Returns:
            Entity dict or None if parsing fails
        """
        metric_col = column_map.get('metric_col')
        value_cols = column_map.get('value_cols', [])

        # Get metric name
        metric_name = str(row.get(metric_col, '')).strip()
        if not metric_name:
            return None

        # Get value from first value column
        if not value_cols:
            return None

        value_col = value_cols[0]  # Use first value column as primary
        raw_value = str(row.get(value_col, '')).strip()

        # Parse value and detect format
        parsed_value, value_format = self._parse_value(raw_value)
        if not parsed_value:
            return None

        # Calculate confidence based on metric clarity and value format
        confidence = self._calculate_confidence(metric_name, parsed_value, value_format)

        if confidence < self.min_confidence:
            return None

        # Extract period from column name (e.g., "Q2 2025")
        period = self._extract_period(value_col)

        # Build entity
        entity = {
            'metric': metric_name,
            'value': parsed_value,
            'period': period,
            'ticker': email_context.get('ticker', 'N/A'),
            'source': 'table',
            'table_index': table_index,
            'row_index': row_index,
            'confidence': confidence,
            'raw_value': raw_value,
            'value_format': value_format
        }

        return entity

    def _parse_value(self, raw_value: str) -> tuple[Optional[str], Optional[str]]:
        """
        Parse numeric value from raw cell text.

        Returns:
            (parsed_value, format) or (None, None) if parsing fails
        """
        # Try each value pattern
        for format_name, pattern in self.value_patterns.items():
            match = re.search(pattern, raw_value)
            if match:
                return (match.group(0).strip(), format_name)

        return (None, None)

    def _extract_period(self, column_name: str) -> str:
        """
        Extract time period or comparison dimension from column name.

        FIX #2: Enhanced to detect comparison columns (YoY, QoQ, MoM)
        Enables queries like "What's the YoY growth?" and "Did revenue increase QoQ?"

        Examples:
            "Q2 2025" → "Q2 2025"
            "2024" → "2024"
            "YoY" → "YoY"
            "QoQ" → "QoQ"
            "FY2024" → "FY2024"
        """
        # NEW: Check for comparison columns first (highest priority)
        if re.search(r'YoY|Y-o-Y|Year.?over.?Year', column_name, re.I):
            return 'YoY'
        if re.search(r'QoQ|Q-o-Q|Quarter.?over.?Quarter', column_name, re.I):
            return 'QoQ'
        if re.search(r'MoM|M-o-M|Month.?over.?Month', column_name, re.I):
            return 'MoM'

        # Look for quarter patterns (Q1, Q2, Q3, Q4 or 1Q, 2Q, 3Q, 4Q)
        # Handles both "Q2 2025" and "2Q2024" formats
        quarter_match = re.search(r'(?:\d[Qq]|[Qq]\d)\s*\d{4}', column_name)
        if quarter_match:
            return quarter_match.group(0)

        # NEW: Look for fiscal year patterns (FY2024, FY 2024)
        fy_match = re.search(r'FY\s*\d{4}', column_name, re.I)
        if fy_match:
            return fy_match.group(0)

        # Look for year patterns (4-digit year)
        year_match = re.search(r'\d{4}', column_name)
        if year_match:
            return year_match.group(0)

        return 'Unknown'

    def _calculate_confidence(
        self,
        metric_name: str,
        parsed_value: str,
        value_format: str
    ) -> float:
        """
        Calculate confidence score for extracted metric.

        High confidence (0.95): Clear metric name + expected value format
        Medium confidence (0.7): Ambiguous metric or unusual format
        Low confidence (0.5): Unclear metric or plain number
        """
        confidence = 0.5  # Base confidence

        # Boost for recognized metric patterns
        metric_lower = metric_name.lower()
        for pattern_name, pattern in self.metric_patterns.items():
            if re.search(pattern, metric_lower):
                confidence += 0.2
                break

        # Boost for expected value formats
        if value_format in ['billions', 'millions', 'percentage', 'ppt', 'plain_number']:
            confidence += 0.2
        elif value_format == 'currency':
            confidence += 0.15

        # Boost for completeness
        if parsed_value and len(parsed_value) > 0:
            confidence += 0.05

        return min(0.95, confidence)  # Cap at 0.95
