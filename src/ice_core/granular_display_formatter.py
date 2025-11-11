# Location: src/ice_core/granular_display_formatter.py
# Purpose: Comprehensive display formatter for granular traceability system
# Why: Present all attribution data (sentences, sources, paths, dates) in user-friendly format
# Relevant Files: ice_query_processor.py, sentence_attributor.py, graph_path_attributor.py

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class GranularDisplayFormatter:
    """
    Comprehensive display formatter for ICE granular traceability system.

    Integrates:
    - Sentence-level attribution (from SentenceAttributor)
    - Graph path attribution (from GraphPathAttributor)
    - Source details (from LightRAGContextParser)
    - Confidence scores, dates, relevance rankings

    Output Format:
    ┌─────────────────────────────────────────────────────────────┐
    │ ✅ ANSWER                                                    │
    ├─────────────────────────────────────────────────────────────┤
    │ [1] Tencent's Q2 2025 operating margin was 34%.            │
    │     📧 Email (0.90) | Similarity: 0.87 | 2025-08-15        │
    │                                                             │
    │ [2] This represents a 2% increase from Q1 2025.            │
    │     📊 API/FMP (0.85) | Similarity: 0.82 | 2025-08-14      │
    └─────────────────────────────────────────────────────────────┘

    ┌─────────────────────────────────────────────────────────────┐
    │ 📚 SOURCES (3 sources, 100% coverage)                       │
    ├─────────────────────────────────────────────────────────────┤
    │ #1 📧 Email: Tencent Q2 2025 Earnings                       │
    │    Confidence: 0.90 | Date: 2025-08-15                      │
    │    Sender: Jia Jun (AGT Partners)                           │
    │                                                             │
    │ #2 📊 API: FMP (TENCENT)                                    │
    │    Confidence: 0.85 | Date: 2025-08-14                      │
    └─────────────────────────────────────────────────────────────┘

    ┌─────────────────────────────────────────────────────────────┐
    │ 🔗 REASONING PATHS (if multi-hop query)                     │
    ├─────────────────────────────────────────────────────────────┤
    │ Path: NVIDIA → TSMC → Taiwan (Confidence: 0.85)            │
    │                                                             │
    │ Hop 1: NVIDIA --DEPENDS_ON--> TSMC                          │
    │   📧 Email (0.90) | 2025-08-15 | 2 supporting chunks        │
    │                                                             │
    │ Hop 2: TSMC --LOCATED_IN--> Taiwan                          │
    │   📊 API/FMP (0.85) | 2025-08-12 | 1 supporting chunk       │
    └─────────────────────────────────────────────────────────────┘
    """

    def __init__(self):
        """Initialize granular display formatter"""
        # Source type to emoji mapping
        self.source_icons = {
            'email': '📧',
            'api': '📊',
            'sec_edgar': '📄',
            'entity_extraction': '🏷️',
            'knowledge_graph': '🕸️',
            'document_context': '📝',
            'unknown': '❓'
        }

    def format_granular_response(
        self,
        answer: str,
        attributed_sentences: List[Dict[str, Any]],
        parsed_context: Dict[str, Any],
        attributed_paths: Optional[List[Dict[str, Any]]] = None,
        show_answer_sentences: bool = True,
        show_sources: bool = True,
        show_paths: bool = True,
        show_statistics: bool = True
    ) -> str:
        """
        Format complete granular response with all attribution data.

        Args:
            answer: Generated answer text
            attributed_sentences: Output from SentenceAttributor.attribute_sentences()
            parsed_context: Output from LightRAGContextParser.parse_context()
            attributed_paths: Output from GraphPathAttributor.attribute_paths() (optional)
            show_answer_sentences: Show sentence-level attribution
            show_sources: Show source details card
            show_paths: Show reasoning paths card (if available)
            show_statistics: Show attribution statistics

        Returns:
            Formatted display string with all attribution cards
        """
        sections = []

        # Section 1: Answer with sentence-level attribution
        if show_answer_sentences and attributed_sentences:
            sections.append(self._format_answer_section(attributed_sentences))

        # Section 2: Source details
        if show_sources:
            chunks = parsed_context.get('chunks', [])
            sections.append(self._format_sources_section(chunks, attributed_sentences))

        # Section 3: Reasoning paths (if multi-hop query)
        if show_paths and attributed_paths:
            sections.append(self._format_paths_section(attributed_paths))

        # Section 4: Attribution statistics
        if show_statistics and attributed_sentences:
            sections.append(self._format_statistics_section(attributed_sentences))

        return "\n\n".join(sections)

    def _format_answer_section(
        self,
        attributed_sentences: List[Dict[str, Any]]
    ) -> str:
        """
        Format answer section with sentence-level attribution.

        Returns:
        ┌─────────────────────────────────────────────────────────────┐
        │ ✅ ANSWER                                                    │
        ├─────────────────────────────────────────────────────────────┤
        │ [1] Sentence text...                                        │
        │     📧 Email (0.90) | Similarity: 0.87 | 2025-08-15        │
        └─────────────────────────────────────────────────────────────┘
        """
        lines = []
        width = 65

        # Header
        lines.append("┌" + "─" * (width - 2) + "┐")
        lines.append("│ ✅ ANSWER" + " " * (width - 11) + "│")
        lines.append("├" + "─" * (width - 2) + "┤")

        # Each sentence with attribution
        for sent_attr in attributed_sentences:
            sent_num = sent_attr['sentence_number']
            sentence = sent_attr['sentence']
            has_attribution = sent_attr['has_attribution']
            attributed_chunks = sent_attr.get('attributed_chunks', [])

            # Sentence line
            sent_line = f"│ [{sent_num}] {sentence}"
            # Pad to width
            sent_line += " " * max(0, width - len(sent_line) - 1) + "│"
            lines.append(sent_line)

            # Attribution line (show top source)
            if has_attribution and attributed_chunks:
                top_chunk = attributed_chunks[0]
                source_type = top_chunk.get('source_type', 'unknown')
                icon = self.source_icons.get(source_type, '❓')
                confidence = top_chunk.get('confidence', 'N/A')
                similarity = top_chunk.get('similarity_score', 'N/A')
                date = top_chunk.get('date', 'N/A')

                # Format attribution line
                attr_line = f"│     {icon} {source_type.title()} ({confidence})"
                if similarity != 'N/A':
                    attr_line += f" | Similarity: {similarity}"
                if date != 'N/A':
                    attr_line += f" | {date}"

                # Pad to width
                attr_line += " " * max(0, width - len(attr_line) - 1) + "│"
                lines.append(attr_line)

                # Show additional sources if multiple
                if len(attributed_chunks) > 1:
                    extra_line = f"│     + {len(attributed_chunks) - 1} more source(s)"
                    extra_line += " " * max(0, width - len(extra_line) - 1) + "│"
                    lines.append(extra_line)
            else:
                # No attribution
                no_attr_line = "│     ⚠️  No source attribution"
                no_attr_line += " " * max(0, width - len(no_attr_line) - 1) + "│"
                lines.append(no_attr_line)

            # Blank line between sentences (except last)
            if sent_num < len(attributed_sentences):
                blank_line = "│" + " " * (width - 2) + "│"
                lines.append(blank_line)

        # Footer
        lines.append("└" + "─" * (width - 2) + "┘")

        return "\n".join(lines)

    def _format_sources_section(
        self,
        chunks: List[Dict[str, Any]],
        attributed_sentences: List[Dict[str, Any]]
    ) -> str:
        """
        Format sources section with all source details.

        Returns:
        ┌─────────────────────────────────────────────────────────────┐
        │ 📚 SOURCES (3 sources, 100% coverage)                       │
        ├─────────────────────────────────────────────────────────────┤
        │ #1 📧 Email: Subject...                                     │
        │    Confidence: 0.90 | Date: 2025-08-15                      │
        └─────────────────────────────────────────────────────────────┘
        """
        lines = []
        width = 65

        # Calculate coverage
        total_sentences = len(attributed_sentences)
        attributed_count = sum(1 for s in attributed_sentences if s['has_attribution'])
        coverage = (attributed_count / total_sentences * 100) if total_sentences > 0 else 0

        # Header
        lines.append("┌" + "─" * (width - 2) + "┐")
        header_text = f"│ 📚 SOURCES ({len(chunks)} sources, {coverage:.0f}% coverage)"
        header_text += " " * max(0, width - len(header_text) - 1) + "│"
        lines.append(header_text)
        lines.append("├" + "─" * (width - 2) + "┤")

        # Each source (show top 5)
        for idx, chunk in enumerate(chunks[:5], 1):
            source_type = chunk.get('source_type', 'unknown')
            icon = self.source_icons.get(source_type, '❓')
            confidence = chunk.get('confidence', 'N/A')
            date = chunk.get('date', 'N/A')
            relevance_rank = chunk.get('relevance_rank', idx)
            source_details = chunk.get('source_details', {})

            # Source title line
            if source_type == 'email':
                subject = source_details.get('subject', 'Unknown')
                title_line = f"│ #{relevance_rank} {icon} Email: {subject[:35]}"
            elif source_type == 'api':
                api_name = source_details.get('api', 'Unknown').upper()
                symbol = source_details.get('symbol', '')
                title_line = f"│ #{relevance_rank} {icon} API: {api_name}"
                if symbol:
                    title_line += f" ({symbol})"
            else:
                title_line = f"│ #{relevance_rank} {icon} {source_type.title()}"

            title_line += " " * max(0, width - len(title_line) - 1) + "│"
            lines.append(title_line)

            # Details line
            details_line = f"│    Confidence: {confidence} | Date: {date}"
            details_line += " " * max(0, width - len(details_line) - 1) + "│"
            lines.append(details_line)

            # Type-specific additional details
            if source_type == 'email' and source_details.get('sender'):
                sender_line = f"│    Sender: {source_details['sender'][:40]}"
                sender_line += " " * max(0, width - len(sender_line) - 1) + "│"
                lines.append(sender_line)

            # Blank line between sources (except last)
            if idx < min(len(chunks), 5):
                blank_line = "│" + " " * (width - 2) + "│"
                lines.append(blank_line)

        # Show "... more sources" if truncated
        if len(chunks) > 5:
            more_line = f"│ ... and {len(chunks) - 5} more sources"
            more_line += " " * max(0, width - len(more_line) - 1) + "│"
            lines.append(more_line)

        # Footer
        lines.append("└" + "─" * (width - 2) + "┘")

        return "\n".join(lines)

    def _format_paths_section(
        self,
        attributed_paths: List[Dict[str, Any]]
    ) -> str:
        """
        Format reasoning paths section with per-hop attribution.

        Returns:
        ┌─────────────────────────────────────────────────────────────┐
        │ 🔗 REASONING PATHS (1 path)                                 │
        ├─────────────────────────────────────────────────────────────┤
        │ Path: NVIDIA → TSMC → Taiwan (Confidence: 0.85)            │
        │                                                             │
        │ Hop 1: NVIDIA --DEPENDS_ON--> TSMC                          │
        │   📧 Email (0.90) | 2 supporting chunks                     │
        └─────────────────────────────────────────────────────────────┘
        """
        lines = []
        width = 65

        # Header
        lines.append("┌" + "─" * (width - 2) + "┐")
        header_text = f"│ 🔗 REASONING PATHS ({len(attributed_paths)} path(s))"
        header_text += " " * max(0, width - len(header_text) - 1) + "│"
        lines.append(header_text)
        lines.append("├" + "─" * (width - 2) + "┤")

        # Each path (show top 2)
        for path_idx, path in enumerate(attributed_paths[:2]):
            path_desc = path.get('path_description', 'Unknown')
            overall_conf = path.get('overall_confidence', 'N/A')
            hops = path.get('hops', [])

            # Path header
            path_line = f"│ Path: {path_desc[:35]}"
            if overall_conf != 'N/A':
                path_line += f" (Conf: {overall_conf})"
            path_line += " " * max(0, width - len(path_line) - 1) + "│"
            lines.append(path_line)

            # Blank line
            blank_line = "│" + " " * (width - 2) + "│"
            lines.append(blank_line)

            # Each hop
            for hop in hops:
                hop_num = hop.get('hop_number', '?')
                relationship = hop.get('relationship', 'Unknown')
                sources = hop.get('sources', [])
                confidence = hop.get('confidence', 'N/A')
                num_chunks = hop.get('num_supporting_chunks', 0)

                # Hop line
                hop_line = f"│ Hop {hop_num}: {relationship[:45]}"
                hop_line += " " * max(0, width - len(hop_line) - 1) + "│"
                lines.append(hop_line)

                # Sources line
                if sources:
                    source_icons_str = " ".join([
                        self.source_icons.get(s, '❓')
                        for s in sources[:3]
                    ])
                    sources_str = ", ".join([s.title() for s in sources[:2]])
                    sources_line = f"│   {source_icons_str} {sources_str} ({confidence})"
                    sources_line += f" | {num_chunks} chunk(s)"
                    sources_line += " " * max(0, width - len(sources_line) - 1) + "│"
                    lines.append(sources_line)

                # Blank line between hops
                if hop_num < len(hops):
                    blank_line = "│" + " " * (width - 2) + "│"
                    lines.append(blank_line)

            # Blank line between paths
            if path_idx < min(len(attributed_paths), 2) - 1:
                blank_line = "│" + " " * (width - 2) + "│"
                lines.append(blank_line)

        # Show "... more paths" if truncated
        if len(attributed_paths) > 2:
            more_line = f"│ ... and {len(attributed_paths) - 2} more path(s)"
            more_line += " " * max(0, width - len(more_line) - 1) + "│"
            lines.append(more_line)

        # Footer
        lines.append("└" + "─" * (width - 2) + "┘")

        return "\n".join(lines)

    def _format_statistics_section(
        self,
        attributed_sentences: List[Dict[str, Any]]
    ) -> str:
        """
        Format attribution statistics section.

        Returns:
        ┌─────────────────────────────────────────────────────────────┐
        │ 📊 ATTRIBUTION STATISTICS                                   │
        ├─────────────────────────────────────────────────────────────┤
        │ Coverage: 100% (5/5 sentences attributed)                   │
        │ Average Confidence: 0.85                                    │
        │ Sources: Email (3), API (2)                                 │
        └─────────────────────────────────────────────────────────────┘
        """
        lines = []
        width = 65

        # Calculate statistics
        total = len(attributed_sentences)
        attributed = sum(1 for s in attributed_sentences if s['has_attribution'])
        coverage = (attributed / total * 100) if total > 0 else 0

        # Average confidence (for attributed sentences only)
        confidences = [
            s['attribution_confidence']
            for s in attributed_sentences
            if s['has_attribution']
        ]
        avg_conf = sum(confidences) / len(confidences) if confidences else 0

        # Count sources by type
        sources_by_type = {}
        for sent in attributed_sentences:
            for chunk in sent.get('attributed_chunks', []):
                source_type = chunk.get('source_type', 'unknown')
                sources_by_type[source_type] = sources_by_type.get(source_type, 0) + 1

        # Header
        lines.append("┌" + "─" * (width - 2) + "┐")
        header_text = "│ 📊 ATTRIBUTION STATISTICS"
        header_text += " " * max(0, width - len(header_text) - 1) + "│"
        lines.append(header_text)
        lines.append("├" + "─" * (width - 2) + "┤")

        # Coverage
        coverage_line = f"│ Coverage: {coverage:.0f}% ({attributed}/{total} sentences attributed)"
        coverage_line += " " * max(0, width - len(coverage_line) - 1) + "│"
        lines.append(coverage_line)

        # Average confidence
        conf_line = f"│ Average Confidence: {avg_conf:.2f}"
        conf_line += " " * max(0, width - len(conf_line) - 1) + "│"
        lines.append(conf_line)

        # Sources by type
        if sources_by_type:
            sources_str = ", ".join([
                f"{k.title()} ({v})"
                for k, v in sorted(sources_by_type.items(), key=lambda x: -x[1])
            ])
            sources_line = f"│ Sources: {sources_str[:50]}"
            sources_line += " " * max(0, width - len(sources_line) - 1) + "│"
            lines.append(sources_line)

        # Footer
        lines.append("└" + "─" * (width - 2) + "┘")

        return "\n".join(lines)

    def format_compact_response(
        self,
        answer: str,
        attributed_sentences: List[Dict[str, Any]],
        show_sources: bool = True
    ) -> str:
        """
        Format compact response (answer + top sources only, no boxes).

        For situations where full granular display is too verbose.

        Returns:
        **Answer:**
        [1] Sentence 1... (📧 Email, 0.90)
        [2] Sentence 2... (📊 API, 0.85)

        **Top Sources:**
        - Email: Tencent Q2 2025 Earnings (0.90, 2025-08-15)
        - API: FMP/TENCENT (0.85, 2025-08-14)
        """
        lines = []

        # Answer section
        lines.append("**Answer:**")
        for sent_attr in attributed_sentences:
            sent_num = sent_attr['sentence_number']
            sentence = sent_attr['sentence']
            attributed_chunks = sent_attr.get('attributed_chunks', [])

            sent_line = f"[{sent_num}] {sentence}"

            # Add top source inline
            if attributed_chunks:
                top_chunk = attributed_chunks[0]
                source_type = top_chunk.get('source_type', 'unknown')
                icon = self.source_icons.get(source_type, '❓')
                confidence = top_chunk.get('confidence', 'N/A')
                sent_line += f" ({icon} {source_type.title()}, {confidence})"

            lines.append(sent_line)

        # Top sources section
        if show_sources and attributed_sentences:
            lines.append("")
            lines.append("**Top Sources:**")

            # Collect unique sources
            seen_sources = set()
            for sent_attr in attributed_sentences:
                for chunk in sent_attr.get('attributed_chunks', [])[:1]:  # Top 1 per sentence
                    chunk_id = chunk.get('chunk_id')
                    if chunk_id not in seen_sources:
                        seen_sources.add(chunk_id)

                        source_type = chunk.get('source_type', 'unknown')
                        icon = self.source_icons.get(source_type, '❓')
                        confidence = chunk.get('confidence', 'N/A')
                        date = chunk.get('date', 'N/A')
                        source_details = chunk.get('source_details', {})

                        if source_type == 'email':
                            subject = source_details.get('subject', 'Unknown')
                            source_line = f"- {icon} Email: {subject} ({confidence}, {date})"
                        elif source_type == 'api':
                            api_name = source_details.get('api', 'Unknown').upper()
                            symbol = source_details.get('symbol', '')
                            source_line = f"- {icon} API: {api_name}/{symbol} ({confidence}, {date})"
                        else:
                            source_line = f"- {icon} {source_type.title()} ({confidence}, {date})"

                        lines.append(source_line)

        return "\n".join(lines)


# Export for use in ICE modules
__all__ = ['GranularDisplayFormatter']
