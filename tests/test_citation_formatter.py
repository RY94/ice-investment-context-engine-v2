# Location: tests/test_citation_formatter.py
# Purpose: Unit tests for CitationFormatter citation display functionality
# Why: Verify all citation styles work correctly with various input scenarios
# Relevant Files: src/ice_core/citation_formatter.py, ice_query_processor.py

import pytest
from src.ice_core.citation_formatter import CitationFormatter


class TestCitationFormatter:
    """Test CitationFormatter citation display functionality"""

    def setup_method(self):
        """Setup test data"""
        # Sample enriched source with all fields
        self.sample_source = {
            'source_type': 'email',
            'label': 'Goldman Sachs',
            'date': '2025-08-17',
            'confidence': 0.90,
            'quality_badge': '🔴 Tertiary',
            'link': 'mailto:goldman@gs.com?subject=Re: Tencent Q2 2025 Earnings'
        }

        # Sample answer for testing
        self.answer = "Tencent Q2 margin: 31%"

    def test_inline_single_source(self):
        """Test inline citation with single source"""
        sources = [self.sample_source]
        result = CitationFormatter.format_citations(self.answer, sources, style="inline")

        assert "[Email: Goldman Sachs, 90%]" in result
        assert self.answer in result

    def test_inline_three_sources(self):
        """Test inline citation with exactly 3 sources (no truncation)"""
        sources = [
            self.sample_source,
            {'source_type': 'api', 'label': 'FMP', 'date': '2025-10-29', 'confidence': 0.85,
             'quality_badge': '🟡 Secondary', 'link': 'https://fmp.com/TENCENT'},
            {'source_type': 'entity_extraction', 'label': 'NER', 'date': 'N/A', 'confidence': 0.75,
             'quality_badge': '', 'link': ''}
        ]
        result = CitationFormatter.format_citations(self.answer, sources, style="inline", max_inline=3)

        # Should show all 3 sources with pipes
        assert "[Email: Goldman Sachs, 90% | Api: FMP, 85% | Entity Extraction: NER, 75%]" in result
        assert "...and" not in result  # No truncation

    def test_inline_truncation(self):
        """Test inline citation truncation with >3 sources"""
        sources = [self.sample_source] * 10  # 10 identical sources
        result = CitationFormatter.format_citations(self.answer, sources, style="inline", max_inline=3)

        # Should truncate to 3 sources + indicator
        assert "...and 7 more" in result
        assert result.count("|") == 3  # 3 pipes = 4 items (3 sources + "...and 7 more")

    def test_footnote_style(self):
        """Test footnote-style citation formatting"""
        sources = [
            self.sample_source,
            {'source_type': 'api', 'label': 'FMP', 'date': '2025-10-29', 'confidence': 0.85,
             'quality_badge': '🟡 Secondary', 'link': 'https://fmp.com/TENCENT'}
        ]
        result = CitationFormatter.format_citations(self.answer, sources, style="footnote")

        # Check footnote markers in answer
        assert "[1][2]" in result
        assert self.answer in result

        # Check footnote entries
        assert "[1] Email: Goldman Sachs, 2025-08-17, Confidence: 90%" in result
        assert "Quality: 🔴 Tertiary" in result
        assert "mailto:goldman@gs.com" in result

        assert "[2] Api: FMP, 2025-10-29, Confidence: 85%" in result
        assert "Quality: 🟡 Secondary" in result
        assert "https://fmp.com/TENCENT" in result

    def test_structured_json_style(self):
        """Test structured JSON citation formatting"""
        sources = [self.sample_source]
        result = CitationFormatter.format_citations(self.answer, sources, style="structured")

        # Result should be dict
        assert isinstance(result, dict)
        assert result["answer"] == self.answer
        assert len(result["citations"]) == 1

        citation = result["citations"][0]
        assert citation["source"] == "email"
        assert citation["label"] == "Goldman Sachs"
        assert citation["date"] == "2025-08-17"
        assert citation["confidence"] == 0.90
        assert citation["quality_badge"] == "🔴 Tertiary"
        assert citation["link"] == "mailto:goldman@gs.com?subject=Re: Tencent Q2 2025 Earnings"

    def test_no_sources_inline(self):
        """Test inline citation with no sources (edge case)"""
        result = CitationFormatter.format_citations(self.answer, [], style="inline")
        # Should return answer unchanged (graceful degradation)
        assert result == self.answer
        assert "[" not in result

    def test_no_sources_structured(self):
        """Test structured citation with no sources (edge case)"""
        result = CitationFormatter.format_citations(self.answer, [], style="structured")
        assert isinstance(result, dict)
        assert result["answer"] == self.answer
        assert result["citations"] == []

    def test_missing_fields(self):
        """Test citation with missing optional fields (robustness)"""
        incomplete_source = {
            'source_type': 'email',
            'label': 'Goldman',
            # Missing: date, confidence, quality_badge, link
        }
        result = CitationFormatter.format_citations(self.answer, [incomplete_source], style="inline")

        # Should handle gracefully with defaults
        assert "Email: Goldman, 0%" in result  # Default confidence 0.0

    def test_unknown_style_fallback(self):
        """Test unknown citation style falls back to inline"""
        sources = [self.sample_source]
        result = CitationFormatter.format_citations(self.answer, sources, style="INVALID_STYLE")

        # Should fallback to inline style
        assert "[Email: Goldman Sachs, 90%]" in result
        assert self.answer in result

    def test_source_label_formatting(self):
        """Test _format_source_label helper"""
        label = CitationFormatter._format_source_label(self.sample_source)
        assert label == "Email: Goldman Sachs, 90%"

        # Test with entity_extraction type (underscore replacement)
        entity_source = {'source_type': 'entity_extraction', 'label': 'NER', 'confidence': 0.75}
        label = CitationFormatter._format_source_label(entity_source)
        assert label == "Entity Extraction: NER, 75%"

    def test_truncate_sources_helper(self):
        """Test _truncate_sources helper"""
        sources = [self.sample_source] * 5

        # No truncation needed
        display, truncated = CitationFormatter._truncate_sources(sources, max_count=10)
        assert len(display) == 5
        assert truncated == 0

        # Truncation needed
        display, truncated = CitationFormatter._truncate_sources(sources, max_count=2)
        assert len(display) == 2
        assert truncated == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
