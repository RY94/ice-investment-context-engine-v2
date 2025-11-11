# Location: src/ice_lightrag/context_parser.py
# Purpose: Parse LightRAG context string into structured attribution data
# Why: Enable granular sentence-level source attribution for traceability
# Relevant Files: ice_rag_fixed.py, ice_query_processor.py

import json
import re
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class LightRAGContextParser:
    """
    Parse LightRAG context string into structured attribution data for granular traceability.

    LightRAG context format:
    -----Entities(KG)-----
    ```json
    [{"id": 1, "entity": "TENCENT", ...}]
    ```

    -----Relationships(KG)-----
    ```json
    [{"id": 1, "entity1": "TENCENT", "entity2": "Revenue", ...}]
    ```

    -----Document Chunks(DC)-----
    ```json
    [{"id": 1, "content": "[SOURCE_EMAIL:...]...", "file_path": "..."}]
    ```

    SOURCE Marker Formats (discovered via validation):
    - Email: [SOURCE_EMAIL:subject|sender:...|date:...]
    - API (enhanced): [SOURCE:FMP|SYMBOL:NVDA|DATE:2025-10-29T10:30:00.123456]
    - API (legacy): [SOURCE:FMP|SYMBOL:NVDA]  (backward compatible, date=None)
    - Entity: [TICKER:NVDA|confidence:0.95]
    """

    def __init__(self):
        """Initialize parser with regex patterns"""
        # Pattern for extracting JSON blocks from markdown sections
        self.json_block_pattern = re.compile(
            r'```json\s+(.*?)```',
            re.DOTALL
        )

        # SOURCE marker patterns (priority order)
        self.source_patterns = {
            'api': re.compile(r'\[SOURCE:(\w+)\|SYMBOL:([^\|]+)(?:\|DATE:([^\]]+))?\]'),  # DATE is optional for backward compatibility
            'email': re.compile(r'\[SOURCE_EMAIL:([^\|]+)\|sender:([^\|]+)\|date:([^\|]+?)(?:\|subject:[^\]]+)?\]'),  # Optional |subject: at end for compatibility
            'entity': re.compile(r'\[TICKER:([^\|]+)\|confidence:([\d.]+)\]'),
        }

    def parse_context(self, context_string: str) -> Dict[str, Any]:
        """
        Parse LightRAG context string into structured attribution data.

        Args:
            context_string: Raw context from LightRAG (contains entities, relationships, chunks)

        Returns:
            {
                "entities": [...],  # Parsed entities
                "relationships": [...],  # Parsed relationships
                "chunks": [  # Parsed chunks with source attribution
                    {
                        "chunk_id": 1,
                        "content": "...",
                        "file_path": "...",
                        "source_type": "email",  # or "api", "entity"
                        "source_details": {...},  # Type-specific details
                        "confidence": 0.90,
                        "date": "2025-08-15",
                        "relevance_rank": 1  # Position = relevance proxy
                    }
                ],
                "summary": {
                    "total_entities": 10,
                    "total_relationships": 15,
                    "total_chunks": 5,
                    "sources_by_type": {"email": 3, "api": 2}
                }
            }
        """
        try:
            result = {
                "entities": self._parse_entities(context_string),
                "relationships": self._parse_relationships(context_string),
                "chunks": self._parse_chunks(context_string),
            }

            # Generate summary statistics
            result["summary"] = self._generate_summary(result)

            logger.info(
                f"Parsed context: {result['summary']['total_entities']} entities, "
                f"{result['summary']['total_relationships']} relationships, "
                f"{result['summary']['total_chunks']} chunks"
            )

            return result

        except Exception as e:
            logger.error(f"Failed to parse context: {e}")
            return {
                "entities": [],
                "relationships": [],
                "chunks": [],
                "summary": {"error": str(e)}
            }

    def _parse_entities(self, context: str) -> List[Dict[str, Any]]:
        """Extract entities from Entities(KG) section"""
        match = re.search(
            r'-----Entities\(KG\)-----\s+```json\s+(.*?)```',
            context,
            re.DOTALL
        )

        if not match:
            return []

        try:
            entities = json.loads(match.group(1))
            logger.debug(f"Parsed {len(entities)} entities")
            return entities
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse entities JSON: {e}")
            return []

    def _parse_relationships(self, context: str) -> List[Dict[str, Any]]:
        """Extract relationships from Relationships(KG) section"""
        match = re.search(
            r'-----Relationships\(KG\)-----\s+```json\s+(.*?)```',
            context,
            re.DOTALL
        )

        if not match:
            return []

        try:
            relationships = json.loads(match.group(1))
            logger.debug(f"Parsed {len(relationships)} relationships")
            return relationships
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse relationships JSON: {e}")
            return []

    def _parse_chunks(self, context: str) -> List[Dict[str, Any]]:
        """
        Extract and enrich chunks from Document Chunks(DC) section.

        Each chunk is enriched with:
        - Source attribution (extracted from SOURCE markers)
        - Relevance rank (position in list, 1 = highest)
        - Confidence score (from marker or default)
        - Date information (when available)
        """
        match = re.search(
            r'-----Document Chunks\(DC\)-----\s+```json\s+(.*?)```',
            context,
            re.DOTALL
        )

        if not match:
            return []

        try:
            raw_chunks = json.loads(match.group(1))
            enriched_chunks = []

            # Process each chunk (position = relevance rank)
            for rank, chunk in enumerate(raw_chunks, start=1):
                enriched = self._enrich_chunk(chunk, rank)
                enriched_chunks.append(enriched)

            logger.debug(f"Parsed and enriched {len(enriched_chunks)} chunks")
            return enriched_chunks

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse chunks JSON: {e}")
            return []

    def _enrich_chunk(self, chunk: Dict[str, Any], relevance_rank: int) -> Dict[str, Any]:
        """
        Enrich chunk with source attribution extracted from SOURCE markers.

        Args:
            chunk: Raw chunk from LightRAG (contains content with SOURCE markers)
            relevance_rank: Position in chunk list (1 = highest relevance)

        Returns:
            Enriched chunk with source_type, source_details, confidence, date, relevance_rank
        """
        content = chunk.get('content', '')
        file_path = chunk.get('file_path', 'unknown')

        # TIER 1 + TIER 2: Try to extract source attribution from SOURCE markers
        # Priority order: API > Email > Entity
        source_info = (
            self._extract_api_source(content) or
            self._extract_email_source(content) or
            self._extract_entity_source(content)
        )

        # TIER 3: Fallback - derive source_type from file_path if no markers found
        if not source_info:
            source_info = self._derive_source_from_file_path(file_path)

        return {
            "chunk_id": chunk.get('id'),
            "content": content,
            "file_path": file_path,
            "relevance_rank": relevance_rank,  # Position-based relevance
            **source_info  # Unpack source_type, source_details, confidence, date
        }

    def _extract_api_source(self, content: str) -> Optional[Dict[str, Any]]:
        """
        Extract API source with optional date:
        - Enhanced: [SOURCE:FMP|SYMBOL:NVDA|DATE:2025-10-29T10:30:00.123456]
        - Legacy: [SOURCE:FMP|SYMBOL:NVDA]  (backward compatible)
        """
        match = self.source_patterns['api'].search(content)
        if not match:
            return None

        source_type, symbol, date_str = match.groups()  # date_str will be None if not present

        # Parse date if present (ISO 8601 format from retrieval timestamp)
        parsed_date = None
        if date_str:
            try:
                from datetime import datetime
                parsed_date = datetime.fromisoformat(date_str).isoformat()
            except (ValueError, AttributeError):
                # Invalid date format, keep as None
                pass

        return {
            "source_type": "api",
            "source_details": {
                "api": source_type.lower(),  # 'fmp', 'newsapi', 'sec_edgar'
                "symbol": symbol
            },
            "confidence": 0.85,  # Default confidence for API sources
            "date": parsed_date  # ISO 8601 timestamp or None
        }

    def _extract_email_source(self, content: str) -> Optional[Dict[str, Any]]:
        """Extract email source: [SOURCE_EMAIL:subject|sender:...|date:...]"""
        match = self.source_patterns['email'].search(content)
        if not match:
            return None

        subject, sender, date_str = match.groups()

        # Parse date if possible
        parsed_date = self._parse_email_date(date_str)

        return {
            "source_type": "email",
            "source_details": {
                "subject": subject.strip(),
                "sender": sender.strip(),
                "raw_date": date_str.strip()
            },
            "confidence": 0.90,  # Email sources typically high confidence
            "date": parsed_date
        }

    def _extract_entity_source(self, content: str) -> Optional[Dict[str, Any]]:
        """Extract entity marker: [TICKER:NVDA|confidence:0.95]"""
        match = self.source_patterns['entity'].search(content)
        if not match:
            return None

        ticker, confidence = match.groups()

        return {
            "source_type": "entity_extraction",
            "source_details": {
                "ticker": ticker,
                "extraction_method": "NER"
            },
            "confidence": float(confidence),
            "date": None
        }

    def _derive_source_from_file_path(self, file_path: str) -> Dict[str, Any]:
        """
        TIER 3 FALLBACK: Derive source_type from file_path when NO SOURCE markers found.

        file_path patterns:
        - "email:Tencent Q2 2025 Earnings.eml" → source_type="email"
        - "api:fmp:NVDA" → source_type="api" (FMP data for NVDA)
        - "sec:10-K:NVDA" → source_type="sec"
        - "unknown" or invalid → source_type="unknown"

        Args:
            file_path: File path from LightRAG storage (Tier 1 tracking)

        Returns:
            Dict with source_type, source_details, confidence, date
        """
        if not file_path or file_path == 'unknown':
            return self._default_source()

        # Parse file_path format: "source_type:details"
        if ':' not in file_path:
            return self._default_source()

        parts = file_path.split(':', 1)
        source_type_prefix = parts[0].lower()
        details = parts[1] if len(parts) > 1 else ''

        # Map file_path prefix to source_type
        if source_type_prefix == 'email':
            # Parse filename to extract subject (remove .eml extension)
            subject = details.rsplit('.eml', 1)[0] if details.endswith('.eml') else details

            return {
                "source_type": "email",
                "source_details": {
                    "subject": subject,  # Add for display compatibility with Tier 2
                    "filename": details,
                    "extraction_method": "file_path_fallback"
                },
                "confidence": 0.90,  # High confidence - verified email source (same as Tier 2)
                "date": None
            }
        elif source_type_prefix == 'api':
            # Extract API provider and symbol from details if possible
            # Format: "api:fmp:NVDA" → provider="fmp", symbol="NVDA"
            api_parts = details.split(':', 1)
            provider = api_parts[0] if api_parts else 'unknown'
            symbol = api_parts[1] if len(api_parts) > 1 else None

            return {
                "source_type": "api",
                "source_details": {
                    "provider": provider,
                    "symbol": symbol,
                    "extraction_method": "file_path_fallback"
                },
                "confidence": 0.85,  # High confidence - verified API source (same as Tier 2)
                "date": None
            }
        elif source_type_prefix == 'sec':
            return {
                "source_type": "sec",
                "source_details": {
                    "filing_type": details,
                    "extraction_method": "file_path_fallback"
                },
                "confidence": 0.90,  # High confidence - official SEC filings
                "date": None
            }
        else:
            # Unknown prefix → fallback to default
            return self._default_source()

    def _default_source(self) -> Dict[str, Any]:
        """
        Ultimate fallback when no SOURCE markers AND no valid file_path.

        This should rarely be reached now that we have Tier 3 (file_path fallback).
        """
        return {
            "source_type": "unknown",
            "source_details": {
                "extraction_method": "default_fallback"
            },
            "confidence": 0.30,  # Very low confidence for truly unknown sources
            "date": None
        }

    def _parse_email_date(self, date_str: str) -> Optional[str]:
        """
        Parse email date string to ISO format.

        Examples:
        - "Sun, 17 Aug 2025 10:59:59 +0800" -> "2025-08-17"
        - "2025-08-15T10:30:00Z" -> "2025-08-15"
        """
        date_formats = [
            "%a, %d %b %Y %H:%M:%S %z",  # RFC 2822 (email format)
            "%Y-%m-%dT%H:%M:%SZ",         # ISO 8601
            "%Y-%m-%d",                   # Simple date
        ]

        for fmt in date_formats:
            try:
                dt = datetime.strptime(date_str.strip(), fmt)
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                continue

        logger.debug(f"Could not parse date: {date_str}")
        return None

    def _generate_summary(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary statistics from parsed context"""
        chunks = result.get('chunks', [])

        # Count sources by type
        sources_by_type = {}
        for chunk in chunks:
            source_type = chunk.get('source_type', 'unknown')
            sources_by_type[source_type] = sources_by_type.get(source_type, 0) + 1

        return {
            "total_entities": len(result.get('entities', [])),
            "total_relationships": len(result.get('relationships', [])),
            "total_chunks": len(chunks),
            "sources_by_type": sources_by_type
        }

    def get_chunks_by_source_type(
        self,
        parsed_context: Dict[str, Any],
        source_type: str
    ) -> List[Dict[str, Any]]:
        """
        Filter chunks by source type.

        Args:
            parsed_context: Output from parse_context()
            source_type: 'email', 'api', 'entity_extraction', 'unknown'

        Returns:
            List of chunks matching the source type
        """
        chunks = parsed_context.get('chunks', [])
        return [c for c in chunks if c.get('source_type') == source_type]

    def get_top_n_chunks(
        self,
        parsed_context: Dict[str, Any],
        n: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get top N chunks by relevance rank.

        Args:
            parsed_context: Output from parse_context()
            n: Number of top chunks to return

        Returns:
            Top N chunks sorted by relevance_rank (1 = highest)
        """
        chunks = parsed_context.get('chunks', [])
        sorted_chunks = sorted(chunks, key=lambda c: c.get('relevance_rank', 999))
        return sorted_chunks[:n]


# Export for use in ICE modules
__all__ = ['LightRAGContextParser']
