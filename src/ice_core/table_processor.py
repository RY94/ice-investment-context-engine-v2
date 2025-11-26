# Location: src/ice_core/table_processor.py
# Purpose: Process extracted tables into dual-layer storage (Signal Store + LightRAG)
# Why: Bridge structured table data to queryable insights (quantitative SQL queries + semantic relationships)
# Relevant Files: signal_store.py, sec_filing_processor.py, data_ingestion.py

from typing import Dict, Any, List, Optional
import hashlib
import re
import logging


class TableProcessor:
    """
    Processes Docling-extracted tables into dual-layer storage.

    Storage Strategy:
    - Signal Store: Structured cells for fast quantitative queries (<100ms)
    - LightRAG: Semantic summaries for relationship discovery

    Features:
    - Table classification (financial vs insider vs general)
    - Value normalization (currency, percentages, accounting formats)
    - 100% source attribution (SHA256-based table IDs)
    - Graceful error handling (Tier 2: degraded mode)
    """

    # Constants for value normalization
    MAX_TABLE_CELLS = 10000  # Memory protection limit

    def __init__(self, signal_store):
        """
        Initialize TableProcessor with Signal Store connection.

        Args:
            signal_store: SignalStore instance for structured data storage
        """
        self.signal_store = signal_store
        self.logger = logging.getLogger(__name__)

    def process_table(self, table_data: Dict[str, Any], source_doc: str) -> Dict[str, Any]:
        """
        Process single table into dual storage.

        Args:
            table_data: Dict with keys: headers, rows, confidence, page, table_index
            source_doc: Source document path (for attribution)

        Returns:
            {
                'table_id': str,
                'graph_summary': str,
                'cells_stored': int,
                'table_type': str,
                'success': bool
            }

        Error Handling: Tier 2 (degraded mode - logs error, returns failure dict)
        """
        try:
            # 1. Early validation: Reject empty headers/rows (Fix #5)
            headers = table_data.get('headers', [])
            rows = table_data.get('rows', [])

            if not headers or not rows:
                self.logger.warning(f"Rejecting malformed table from {source_doc}: empty headers or rows")
                return {
                    'table_id': None,
                    'graph_summary': '',
                    'cells_stored': 0,
                    'table_type': 'invalid',
                    'success': False,
                    'error': 'Empty headers or rows'
                }

            # 2. Generate deterministic table ID (for 100% source attribution)
            table_id = self._generate_table_id(
                source_doc,
                table_data.get('page'),
                table_data.get('table_index', 0)
            )

            # 3. Classify table type (financial vs insider vs general)
            table_type = self._classify_table_type(headers, rows)

            # 4. Memory protection: Check table size (Fix #4: Modify table_data in-place)
            total_cells = len(headers) * len(rows)

            if total_cells > self.MAX_TABLE_CELLS and len(headers) > 0:
                max_rows = self.MAX_TABLE_CELLS // len(headers)
                self.logger.warning(
                    f"Table {table_id} too large ({total_cells} cells), "
                    f"truncating to {self.MAX_TABLE_CELLS} (keeping first {max_rows} rows)"
                )
                table_data['rows'] = table_data['rows'][:max_rows]
                rows = table_data['rows']  # Update local reference

            # 4. Store in Signal Store (structured)
            cells_stored = self._store_in_signal_store(
                table_id, table_data, source_doc, table_type
            )

            # 5. Create semantic summary for LightRAG
            graph_summary = self._create_graph_summary(
                table_id, table_data, table_type
            )

            return {
                'table_id': table_id,
                'graph_summary': graph_summary,
                'cells_stored': cells_stored,
                'table_type': table_type,
                'success': True
            }

        except Exception as e:
            # Tier 2: Individual table processing fails, log and continue
            self.logger.error(f"Failed to process table from {source_doc}: {e}")
            return {
                'table_id': None,
                'graph_summary': '',
                'cells_stored': 0,
                'table_type': 'unknown',
                'success': False,
                'error': str(e)
            }

    def _generate_table_id(self, source_doc: str, page: Optional[int],
                          table_index: int) -> str:
        """
        Generate deterministic SHA256 table ID for source attribution.

        Args:
            source_doc: Source document path
            page: Page number (can be None)
            table_index: Table index on page

        Returns:
            16-character hex string (first 16 chars of SHA256)
        """
        # Create reproducible content string
        page_str = str(page) if page is not None else "unknown"
        content = f"{source_doc}|page_{page_str}|index_{table_index}"

        # Generate SHA256 hash (truncate to 16 chars for readability)
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def _classify_table_type(self, headers: List[str], rows: List[List[str]]) -> str:
        """
        Classify table type using heuristics.

        Classification Logic:
        1. Check for insider transaction keywords → 'insider_transactions'
        2. Check for financial keywords + high numeric ratio → 'financial_statement'
        3. High numeric ratio (>60%) → 'peer_comparison'
        4. Default → 'general'

        Args:
            headers: List of column headers
            rows: List of row data

        Returns:
            One of: 'financial_statement', 'insider_transactions',
                   'peer_comparison', 'general'
        """
        if not headers or not rows:
            return 'general'

        # Normalize headers to lowercase for matching
        header_text = ' '.join(headers).lower()

        # Insider transaction detection
        insider_keywords = {
            'insider', 'director', 'officer', 'shares', 'transaction',
            'beneficial owner', 'form 4', 'ownership'
        }
        has_insider = any(kw in header_text for kw in insider_keywords)
        if has_insider:
            return 'insider_transactions'

        # Financial statement detection
        financial_keywords = {
            'revenue', 'eps', 'margin', 'profit', 'cash', 'debt',
            'assets', 'ebitda', 'operating income', 'net income',
            'earnings', 'sales'
        }
        has_financial = any(kw in header_text for kw in financial_keywords)

        # Calculate numeric ratio (financial tables are mostly numeric)
        total_cells = sum(len(row) for row in rows)
        if total_cells == 0:
            return 'general'

        numeric_cells = sum(
            1 for row in rows
            for cell in row
            if self._is_numeric(cell)
        )
        numeric_ratio = numeric_cells / total_cells

        # Classification decision
        if has_financial and numeric_ratio > 0.5:
            return 'financial_statement'
        elif numeric_ratio > 0.6:
            return 'peer_comparison'
        else:
            return 'general'

    def _is_numeric(self, value: str) -> bool:
        """
        Check if cell contains numeric data (including formatted numbers).

        Handles: numbers, currency ($100), percentages (12.5%), accounting (25.3)

        Args:
            value: Cell value string

        Returns:
            True if numeric, False otherwise
        """
        if not value or not isinstance(value, str):
            return False

        # Remove common financial formatting
        cleaned = re.sub(r'[$£€¥,%()BMK]', '', value.strip())

        # Try to convert to float
        try:
            float(cleaned)
            return True
        except ValueError:
            return False

    def _escape_markdown(self, text: str) -> str:
        """
        Escape markdown special characters to prevent injection (Fix #3).

        Handles: pipes (|), brackets ([]), to prevent table structure corruption.

        Args:
            text: Raw cell value

        Returns:
            Escaped string safe for markdown tables
        """
        if not text:
            return ''
        return str(text).replace('|', '\\|').replace('[', '\\[').replace(']', '\\]')

    def normalize_value(self, cell_value: str) -> Optional[float]:
        """
        Normalize financial values to float for SQL queries.

        Handles:
        - Currency symbols: $, £, €, ¥
        - Multipliers: B (billion), M (million), K (thousand)
        - Percentages: 12.5% → 0.125
        - Accounting negatives: (25.3) → -25.3
        - N/A values: Return None

        Args:
            cell_value: Raw cell value string

        Returns:
            Normalized float or None if not numeric

        Examples:
            "$100.5M" → 100500000.0
            "(25.3)" → -25.3
            "12.5%" → 0.125
            "N/A" → None
        """
        if not cell_value or not isinstance(cell_value, str):
            return None

        try:
            cleaned = cell_value.strip().upper()

            # Handle N/A, dashes, empty strings
            if cleaned in ['N/A', 'NA', '-', '—', '', 'NULL', 'NONE']:
                return None

            # Fix #2: Handle accounting negatives FIRST (before percentages)
            # This allows "(12.5%)" to work correctly: extract 12.5% → then handle %
            is_negative = cleaned.startswith('(') and cleaned.endswith(')')
            if is_negative:
                cleaned = cleaned[1:-1]

            # Handle percentages (now works with negative percentages like "(12.5%)")
            if '%' in cleaned:
                cleaned = cleaned.replace('%', '').replace(',', '')
                value = float(cleaned) / 100.0
                return -value if is_negative else value

            # Handle multipliers: B, M, K
            multiplier = 1.0
            if cleaned.endswith('B'):
                multiplier = 1_000_000_000
                cleaned = cleaned[:-1]
            elif cleaned.endswith('M'):
                multiplier = 1_000_000
                cleaned = cleaned[:-1]
            elif cleaned.endswith('K'):
                multiplier = 1_000
                cleaned = cleaned[:-1]

            # Remove currency symbols, commas, spaces
            cleaned = re.sub(r'[$£€¥,\s]', '', cleaned)

            # Convert to float
            value = float(cleaned) * multiplier
            return -value if is_negative else value

        except (ValueError, AttributeError) as e:
            self.logger.debug(f"Failed to normalize value '{cell_value}': {e}")
            return None

    def _store_in_signal_store(self, table_id: str, table_data: Dict[str, Any],
                               source_doc: str, table_type: str) -> int:
        """
        Store table in Signal Store (structured storage) with atomic transaction (Fix #1).

        Uses atomic wrapper to ensure ACID guarantees:
        Either both metadata AND cells are inserted, or neither is (prevents orphaned metadata).

        Args:
            table_id: Unique table identifier
            table_data: Table dict with headers, rows, confidence, page
            source_doc: Source document path
            table_type: Classification result

        Returns:
            Number of cells successfully stored
        """
        headers = table_data.get('headers', [])
        rows = table_data.get('rows', [])

        # Prepare cells for atomic insertion
        cells = []
        for row_idx, row in enumerate(rows):
            # Handle rows with inconsistent column counts (defensive)
            for col_idx in range(min(len(row), len(headers))):
                cell_value = row[col_idx] if col_idx < len(row) else ''
                cell_id = f"{table_id}_{row_idx}_{col_idx}"

                # Determine cell type
                cell_type = 'numeric' if self._is_numeric(cell_value) else 'text'

                # Normalize if numeric
                normalized = self.normalize_value(cell_value) if cell_type == 'numeric' else None

                cells.append({
                    'cell_id': cell_id,
                    'table_id': table_id,
                    'row_index': row_idx,
                    'col_index': col_idx,
                    'cell_value': str(cell_value),
                    'cell_type': cell_type,
                    'normalized_value': normalized,
                    'column_header': headers[col_idx] if col_idx < len(headers) else None,
                    'row_label': row[0] if len(row) > 0 else None,  # First column as row label
                    'confidence': table_data.get('confidence', 0.8)
                })

        # Atomic insert: metadata + cells in single transaction (Fix #1)
        result = self.signal_store.insert_table_with_cells_atomic(
            table_id=table_id,
            source_document=source_doc,
            source_page=table_data.get('page'),
            table_type=table_type,
            extraction_confidence=table_data.get('confidence', 0.8),
            row_count=len(rows),
            col_count=len(headers),
            cells=cells
        )

        if not result['success']:
            self.logger.warning(
                f"Atomic table insert failed for {table_id}: {result.get('error')}"
            )
            return 0

        return result['cells_stored']

    def _create_graph_summary(self, table_id: str, table_data: Dict[str, Any],
                              table_type: str) -> str:
        """
        Create semantic summary for LightRAG ingestion.

        Format: Markdown table with first 3 rows + reference to Signal Store

        Args:
            table_id: Unique table identifier
            table_data: Table dict with headers, rows, confidence, page
            table_type: Classification result

        Returns:
            Markdown-formatted summary string
        """
        headers = table_data.get('headers', [])
        rows = table_data.get('rows', [])

        if not headers or not rows:
            return ""

        # Build markdown summary
        summary = f"\n\n### Table: {table_type.replace('_', ' ').title()}\n"
        summary += f"**Source**: Page {table_data.get('page', 'unknown')} | "
        summary += f"Confidence: {table_data.get('confidence', 0.8):.2f} | "
        summary += f"Table ID: `{table_id}` (full data in Signal Store)\n\n"

        # Add header row (Fix #3: Escape markdown special characters)
        summary += "| " + " | ".join(self._escape_markdown(h) for h in headers) + " |\n"
        summary += "|" + "|".join(["---"] * len(headers)) + "|\n"

        # Add first 3 rows (representative sample for graph context)
        for row in rows[:3]:
            # Pad row if shorter than headers
            padded_row = row + [''] * (len(headers) - len(row))
            summary += "| " + " | ".join(self._escape_markdown(cell) for cell in padded_row[:len(headers)]) + " |\n"

        if len(rows) > 3:
            summary += f"\n*({len(rows) - 3} additional rows available in Signal Store - query table_id: `{table_id}`)*\n"

        # Add semantic insights for financial tables
        if table_type == 'financial_statement' and len(rows) > 0:
            summary += f"\n**Quantitative Analysis**: This table contains {len(rows)} data points "
            summary += f"across {len(headers)} metrics. Use Signal Store queries with table_id `{table_id}` "
            summary += f"for SQL-based filtering (e.g., revenue > $1B, P/E < 15).\n"

        return summary

    def process_tables_batch(self, tables: List[Dict[str, Any]],
                             source_doc: str) -> Dict[str, Any]:
        """
        Process multiple tables in batch (optimized for performance).

        Args:
            tables: List of table dicts from Docling
            source_doc: Source document path

        Returns:
            {
                'total_tables': int,
                'successful': int,
                'failed': int,
                'graph_summaries': List[str],
                'table_ids': List[str]
            }
        """
        results = {
            'total_tables': len(tables),
            'successful': 0,
            'failed': 0,
            'graph_summaries': [],
            'table_ids': []
        }

        for table_data in tables:
            result = self.process_table(table_data, source_doc)

            if result['success']:
                results['successful'] += 1
                results['graph_summaries'].append(result['graph_summary'])
                results['table_ids'].append(result['table_id'])
            else:
                results['failed'] += 1

        self.logger.info(
            f"Batch processed {results['total_tables']} tables from {source_doc}: "
            f"{results['successful']} successful, {results['failed']} failed"
        )

        return results
