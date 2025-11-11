# Location: src/ice_core/citation_formatter.py
# Purpose: Format enriched source metadata into user-friendly citations
# Why: Bridge gap between backend traceability and user-facing display for trust
# Relevant Files: ice_query_processor.py, context_parser.py, granular_display_formatter.py

from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class CitationFormatter:
    """
    Format enriched source metadata into user-friendly citation displays.

    Surfaces ICE's comprehensive backend traceability (SOURCE markers, confidence,
    timestamps, quality badges) in readable formats for end users.

    Design Principles:
    - Reuses enriched_sources from ICEQueryProcessor (no re-parsing)
    - Supports 3 citation styles: inline, footnote, structured
    - Handles edge cases gracefully (missing fields, no sources)
    - Backward compatible (additive field only)

    Citation Styles:

    **Inline** (default, concise):
    "Tencent Q2 margin: 31% [Email: Goldman, 90% | API: FMP, 85%]"

    **Footnote** (detailed, academic):
    "Tencent Q2 margin: 31%[1][2]

    [1] Goldman Sachs Email, Aug 17 2025, Confidence: 90%, Quality: 🔴 Tertiary
        mailto:goldman@gs.com?subject=Re: Tencent Q2 2025 Earnings
    [2] FMP API, Oct 29 2025, Confidence: 85%, Quality: 🟡 Secondary
        https://financialmodelingprep.com/financial-summary/TENCENT"

    **Structured** (API-friendly, JSON):
    {"answer": "...", "citations": [{"source": "email", "label": "Goldman", ...}]}
    """

    @staticmethod
    def format_citations(
        answer: str,
        enriched_sources: List[Dict[str, Any]],
        style: str = "inline",
        max_inline: int = 3
    ) -> str:
        """
        Format enriched sources into user-friendly citations.

        Args:
            answer: Generated answer text
            enriched_sources: List from enriched_metadata['enriched_sources']
                Expected fields: source_type, confidence, date, quality_badge, link
            style: Citation style - 'inline' | 'footnote' | 'structured'
            max_inline: Max sources to show inline before truncating (inline style only)

        Returns:
            Formatted citation string (or JSON for structured style)
        """
        if not enriched_sources:
            logger.debug("No enriched sources provided for citation formatting")
            if style == "structured":
                return {"answer": answer, "citations": []}
            return answer  # No citations to add

        try:
            # Route to appropriate formatter based on style
            if style == "inline":
                return CitationFormatter._format_inline(answer, enriched_sources, max_inline)
            elif style == "footnote":
                return CitationFormatter._format_footnote(answer, enriched_sources)
            elif style == "structured":
                return CitationFormatter._format_structured(answer, enriched_sources)
            else:
                logger.warning(f"Unknown citation style '{style}', defaulting to inline")
                return CitationFormatter._format_inline(answer, enriched_sources, max_inline)

        except Exception as e:
            logger.error(f"Citation formatting failed: {e}")
            # Graceful degradation: return answer without citations
            return answer if style != "structured" else {"answer": answer, "citations": []}

    @staticmethod
    def _format_inline(answer: str, sources: List[Dict], max_inline: int) -> str:
        """
        Format inline citations: [Email: Goldman, 90% | API: FMP, 85%]

        Truncates if more than max_inline sources with "...and N more" indicator.
        """
        # Truncate sources if exceeds max_inline
        display_sources, truncated_count = CitationFormatter._truncate_sources(sources, max_inline)

        # Build citation labels
        citation_parts = []
        for source in display_sources:
            label = CitationFormatter._format_source_label(source)
            citation_parts.append(label)

        # Add truncation indicator if needed
        if truncated_count > 0:
            citation_parts.append(f"...and {truncated_count} more")

        # Assemble final inline citation
        citation_text = " | ".join(citation_parts)
        return f"{answer} [{citation_text}]"

    @staticmethod
    def _format_footnote(answer: str, sources: List[Dict]) -> str:
        """
        Format footnote-style citations with numbered references.

        Example:
        "Answer text[1][2]

        [1] Email: Goldman Sachs, Aug 17 2025, Confidence: 90%, Quality: 🔴 Tertiary
            mailto:goldman@gs.com
        [2] API: FMP, Oct 29 2025, Confidence: 85%, Quality: 🟡 Secondary
            https://fmp.com/TENCENT"
        """
        # Build answer with footnote markers [1][2]...
        footnote_markers = "".join([f"[{i+1}]" for i in range(len(sources))])
        answer_with_markers = f"{answer}{footnote_markers}"

        # Build footnote details
        footnotes = []
        for idx, source in enumerate(sources, start=1):
            source_type = source.get('source_type', 'unknown').replace('_', ' ').title()
            label = source.get('label', 'Unknown')
            date = source.get('date', 'N/A')
            confidence = source.get('confidence', 0.0)
            quality_badge = source.get('quality_badge', '')
            link = source.get('link', '')

            # Format footnote entry
            footnote = f"[{idx}] {source_type}: {label}, {date}, Confidence: {confidence:.0%}"
            if quality_badge:
                footnote += f", Quality: {quality_badge}"
            if link:
                footnote += f"\n    {link}"

            footnotes.append(footnote)

        # Combine answer with footnotes
        return f"{answer_with_markers}\n\n" + "\n".join(footnotes)

    @staticmethod
    def _format_structured(answer: str, sources: List[Dict]) -> Dict[str, Any]:
        """
        Format as structured JSON for API consumption.

        Returns:
            {
                "answer": "...",
                "citations": [
                    {
                        "source": "email",
                        "label": "Goldman Sachs",
                        "date": "2025-08-17",
                        "confidence": 0.90,
                        "quality_badge": "🔴 Tertiary",
                        "link": "mailto:..."
                    }
                ]
            }
        """
        citations = []
        for source in sources:
            citation = {
                "source": source.get('source_type', 'unknown'),
                "label": source.get('label', 'Unknown'),
                "date": source.get('date', 'N/A'),
                "confidence": source.get('confidence', 0.0),
                "quality_badge": source.get('quality_badge', ''),
                "link": source.get('link', '')
            }
            citations.append(citation)

        return {
            "answer": answer,
            "citations": citations
        }

    @staticmethod
    def _truncate_sources(sources: List[Dict], max_count: int) -> tuple[List[Dict], int]:
        """
        Smart truncation of sources for inline display.

        Args:
            sources: Full list of enriched sources
            max_count: Maximum sources to display

        Returns:
            (display_sources, truncated_count)
        """
        if len(sources) <= max_count:
            return sources, 0

        display_sources = sources[:max_count]
        truncated_count = len(sources) - max_count
        return display_sources, truncated_count

    @staticmethod
    def _format_source_label(source: Dict) -> str:
        """
        Format single source label for inline display.

        Example: "Email: Goldman, 90%" or "API: FMP, 85%"
        """
        source_type = source.get('source_type', 'unknown').replace('_', ' ').title()
        label = source.get('label', 'Unknown')
        confidence = source.get('confidence', 0.0)

        # Format: "Type: Label, Confidence%"
        return f"{source_type}: {label}, {confidence:.0%}"


# Export for ICE modules
__all__ = ['CitationFormatter']
