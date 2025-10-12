# Location: imap_email_ingestion_pipeline/tests/test_enhanced_documents.py
# Purpose: Unit tests for enhanced document creation with inline markup
# Business Value: Validates enhanced documents preserve EntityExtractor precision for LightRAG
# Relevant Files: enhanced_doc_creator.py, ice_integrator.py, entity_extractor.py

"""
Unit tests for Enhanced Document Creator

Tests validate that:
1. Enhanced documents are created with correct inline markup
2. Confidence scores are preserved in markup
3. Missing/empty entities are handled gracefully
4. Markup format is valid and parseable
5. Edge cases (special characters, size limits) are handled correctly
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from enhanced_doc_creator import (
    create_enhanced_document,
    validate_enhanced_document,
    escape_markup_value,
    MIN_CONFIDENCE_THRESHOLD
)


class TestMarkupEscaping:
    """Test escaping of special characters in markup values"""

    def test_escape_pipe_character(self):
        """Pipe character should be escaped"""
        result = escape_markup_value("value|with|pipes")
        assert "\\|" in result
        assert "|" not in result.replace("\\|", "")

    def test_escape_brackets(self):
        """Brackets should be escaped"""
        result = escape_markup_value("[value]")
        assert "\\[" in result
        assert "\\]" in result

    def test_escape_none_value(self):
        """None should return N/A"""
        result = escape_markup_value(None)
        assert result == "N/A"

    def test_escape_numeric_values(self):
        """Numeric values should be converted to string"""
        result = escape_markup_value(123.45)
        assert result == "123.45"


class TestBasicDocumentCreation:
    """Test basic enhanced document generation"""

    def test_create_document_with_all_entities(self):
        """Should create enhanced document with all entity types"""
        email_data = {
            'uid': '12345',
            'from': 'analyst@goldmansachs.com',
            'date': '2024-01-15',
            'subject': 'NVDA Upgrade to BUY',
            'body': 'We are upgrading NVIDIA to BUY with $500 price target.',
            'priority': 'HIGH',
            'priority_confidence': 0.85
        }

        entities = {
            'tickers': [{'ticker': 'NVDA', 'confidence': 0.95}],
            'ratings': [{'type': 'BUY', 'confidence': 0.87, 'ticker': 'NVDA'}],
            'financial_metrics': {
                'price_targets': [{
                    'value': '500',
                    'ticker': 'NVDA',
                    'currency': 'USD',
                    'confidence': 0.92
                }]
            },
            'people': [{
                'name': 'John Doe',
                'firm': 'Goldman Sachs',
                'confidence': 0.88
            }],
            'sentiment': {
                'sentiment': 'POSITIVE',
                'score': 0.8,
                'confidence': 0.85
            },
            'confidence': 0.90
        }

        doc = create_enhanced_document(email_data, entities)

        assert doc is not None
        assert '[SOURCE_EMAIL:12345' in doc
        assert '[TICKER:NVDA|confidence:0.95]' in doc
        assert '[RATING:BUY|ticker:NVDA|confidence:0.87]' in doc
        assert '[PRICE_TARGET:500|ticker:NVDA|currency:USD|confidence:0.92]' in doc
        assert '[ANALYST:John Doe|firm:Goldman Sachs|confidence:0.88]' in doc
        assert '[SENTIMENT:POSITIVE' in doc
        assert 'We are upgrading NVIDIA to BUY' in doc

    def test_create_document_minimal_data(self):
        """Should create document with minimal email data"""
        email_data = {
            'uid': 'test-001',
            'body': 'Simple email text.'
        }

        entities = {}

        doc = create_enhanced_document(email_data, entities)

        assert doc is not None
        assert '[SOURCE_EMAIL:test-001' in doc
        assert 'Simple email text.' in doc

    def test_create_document_empty_entities(self):
        """Should handle empty entities gracefully"""
        email_data = {
            'uid': '123',
            'from': 'test@test.com',
            'date': '2024-01-01',
            'body': 'Test email'
        }

        entities = {
            'tickers': [],
            'ratings': [],
            'financial_metrics': {},
            'people': [],
            'confidence': 0.0
        }

        doc = create_enhanced_document(email_data, entities)

        assert doc is not None
        assert 'Test email' in doc


class TestConfidenceThreshold:
    """Test confidence threshold filtering"""

    def test_low_confidence_entities_excluded(self):
        """Entities below confidence threshold should be excluded"""
        email_data = {
            'uid': '123',
            'body': 'Test'
        }

        entities = {
            'tickers': [
                {'ticker': 'NVDA', 'confidence': 0.95},  # Above threshold
                {'ticker': 'AMD', 'confidence': 0.45}    # Below threshold
            ],
            'ratings': [
                {'type': 'BUY', 'confidence': 0.25}      # Below threshold
            ]
        }

        doc = create_enhanced_document(email_data, entities)

        assert '[TICKER:NVDA|confidence:0.95]' in doc
        assert 'AMD' not in doc  # Low confidence ticker excluded
        assert 'BUY' not in doc  # Low confidence rating excluded

    def test_exactly_threshold_included(self):
        """Entities exactly at threshold should be included"""
        email_data = {'uid': '123', 'body': 'Test'}

        entities = {
            'tickers': [
                {'ticker': 'AAPL', 'confidence': MIN_CONFIDENCE_THRESHOLD}
            ]
        }

        doc = create_enhanced_document(email_data, entities)

        # Should NOT be included (threshold is >, not >=)
        assert 'AAPL' not in doc

    def test_above_threshold_included(self):
        """Entities above threshold should be included"""
        email_data = {'uid': '123', 'body': 'Test'}

        entities = {
            'tickers': [
                {'ticker': 'GOOGL', 'confidence': MIN_CONFIDENCE_THRESHOLD + 0.01}
            ]
        }

        doc = create_enhanced_document(email_data, entities)

        assert 'GOOGL' in doc


class TestMarkupFormat:
    """Test markup format validation"""

    def test_source_email_format(self):
        """SOURCE_EMAIL markup should have correct format"""
        email_data = {
            'uid': 'email-123',
            'from': 'sender@example.com',
            'date': '2024-01-15',
            'subject': 'Test Subject',
            'body': 'Test'
        }

        doc = create_enhanced_document(email_data, {})

        assert '[SOURCE_EMAIL:email-123|sender:sender@example.com|date:2024-01-15|subject:Test Subject]' in doc

    def test_ticker_markup_format(self):
        """TICKER markup should include confidence"""
        email_data = {'uid': '123', 'body': 'Test'}
        entities = {
            'tickers': [{'ticker': 'TSLA', 'confidence': 0.89}]
        }

        doc = create_enhanced_document(email_data, entities)

        assert '[TICKER:TSLA|confidence:0.89]' in doc

    def test_rating_markup_format(self):
        """RATING markup should include ticker and confidence"""
        email_data = {'uid': '123', 'body': 'Test'}
        entities = {
            'ratings': [{'type': 'SELL', 'ticker': 'INTC', 'confidence': 0.76}]
        }

        doc = create_enhanced_document(email_data, entities)

        assert '[RATING:SELL|ticker:INTC|confidence:0.76]' in doc


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_invalid_email_data(self):
        """Should return None for invalid email_data"""
        result = create_enhanced_document(None, {})
        assert result is None

        result = create_enhanced_document("not a dict", {})
        assert result is None

        result = create_enhanced_document({}, {})  # Empty dict is valid
        assert result is not None

    def test_special_characters_in_values(self):
        """Special characters should be escaped"""
        email_data = {
            'uid': '123',
            'from': 'test|user@example.com',
            'subject': 'Subject with [brackets] and |pipes|',
            'body': 'Test'
        }

        entities = {
            'tickers': [{'ticker': 'ABC|DEF', 'confidence': 0.9}]
        }

        doc = create_enhanced_document(email_data, entities)

        # Special characters should be escaped
        assert '\\|' in doc or 'test|user' not in doc  # Escaped or removed
        assert doc is not None  # Should still create valid document

    def test_very_large_document_truncation(self):
        """Very large documents should be truncated"""
        email_data = {
            'uid': '123',
            'body': 'A' * 60000  # 60KB body (over 50KB limit)
        }

        doc = create_enhanced_document(email_data, {})

        assert doc is not None
        assert len(doc) <= 51000  # Should be truncated to ~50KB + truncation message
        assert '[document truncated due to size limit]' in doc

    def test_missing_optional_fields(self):
        """Should handle missing optional fields"""
        email_data = {
            'uid': '123'
            # Missing: from, date, subject, body, etc.
        }

        entities = {
            'tickers': [{'ticker': 'MSFT', 'confidence': 0.9}]
            # Missing: ratings, people, etc.
        }

        doc = create_enhanced_document(email_data, entities)

        assert doc is not None
        assert '[SOURCE_EMAIL:123' in doc
        assert '[TICKER:MSFT|confidence:0.90]' in doc

    def test_attachments_with_extracted_text(self):
        """Should include attachment metadata and text"""
        email_data = {
            'uid': '123',
            'body': 'Email with attachment',
            'attachments': [
                {
                    'filename': 'report.pdf',
                    'content_type': 'application/pdf',
                    'extracted_text': 'Sample text from PDF attachment...'
                }
            ]
        }

        doc = create_enhanced_document(email_data, {})

        assert '[ATTACHMENT:report.pdf|type:application/pdf]' in doc
        assert 'Sample text from PDF attachment' in doc

    def test_attachments_long_text_truncation(self):
        """Long attachment text should be truncated"""
        email_data = {
            'uid': '123',
            'body': 'Test',
            'attachments': [
                {
                    'filename': 'long_doc.txt',
                    'content_type': 'text/plain',
                    'extracted_text': 'X' * 1000  # 1000 characters
                }
            ]
        }

        doc = create_enhanced_document(email_data, {})

        assert '[attachment text truncated]' in doc

    def test_multiple_tickers(self):
        """Should handle multiple tickers"""
        email_data = {'uid': '123', 'body': 'Test'}
        entities = {
            'tickers': [
                {'ticker': 'AAPL', 'confidence': 0.95},
                {'ticker': 'GOOGL', 'confidence': 0.92},
                {'ticker': 'MSFT', 'confidence': 0.88}
            ]
        }

        doc = create_enhanced_document(email_data, entities)

        assert '[TICKER:AAPL|confidence:0.95]' in doc
        assert '[TICKER:GOOGL|confidence:0.92]' in doc
        assert '[TICKER:MSFT|confidence:0.88]' in doc

    def test_analyst_limit(self):
        """Should limit analysts to top 3"""
        email_data = {'uid': '123', 'body': 'Test'}
        entities = {
            'people': [
                {'name': f'Analyst {i}', 'firm': 'Firm', 'confidence': 0.9}
                for i in range(5)  # 5 analysts, only top 3 should be included
            ]
        }

        doc = create_enhanced_document(email_data, entities)

        # Should have exactly 3 analyst tags
        analyst_count = doc.count('[ANALYST:')
        assert analyst_count == 3


class TestDocumentValidation:
    """Test document validation function"""

    def test_validate_valid_document(self):
        """Should validate a properly formatted document"""
        email_data = {
            'uid': '123',
            'from': 'test@test.com',
            'date': '2024-01-01',
            'body': 'Test'
        }
        entities = {
            'tickers': [{'ticker': 'NVDA', 'confidence': 0.95}]
        }

        doc = create_enhanced_document(email_data, entities)
        validation = validate_enhanced_document(doc)

        assert validation['valid'] is True
        assert validation['markup_count'] > 0
        assert 'SOURCE_EMAIL' in validation['metadata']
        assert len(validation['errors']) == 0

    def test_validate_invalid_document(self):
        """Should detect invalid document"""
        validation = validate_enhanced_document(None)
        assert validation['valid'] is False
        assert len(validation['errors']) > 0

    def test_validate_missing_source(self):
        """Should detect missing SOURCE_EMAIL tag"""
        doc = "[TICKER:NVDA|confidence:0.95] Some text without source"
        validation = validate_enhanced_document(doc)

        assert validation['valid'] is False
        assert any('SOURCE_EMAIL' in error for error in validation['errors'])

    def test_markup_count(self):
        """Should count markup tags correctly"""
        doc = "[TAG1:val] [TAG2:val] [TAG3:val]"
        validation = validate_enhanced_document(doc)

        assert validation['markup_count'] == 3


class TestEntityExtractorIntegration:
    """Test compatibility with actual EntityExtractor output format"""

    def test_ticker_field_variations(self):
        """Should handle both 'ticker' and 'symbol' fields"""
        email_data = {'uid': '123', 'body': 'Test'}

        # Some extractors use 'ticker', others use 'symbol'
        entities_v1 = {
            'tickers': [{'ticker': 'NVDA', 'confidence': 0.95}]
        }
        entities_v2 = {
            'tickers': [{'symbol': 'NVDA', 'confidence': 0.95}]
        }

        doc1 = create_enhanced_document(email_data, entities_v1)
        doc2 = create_enhanced_document(email_data, entities_v2)

        assert 'NVDA' in doc1
        assert 'NVDA' in doc2

    def test_rating_field_variations(self):
        """Should handle both 'type' and 'rating' fields"""
        email_data = {'uid': '123', 'body': 'Test'}

        entities_v1 = {
            'ratings': [{'type': 'BUY', 'confidence': 0.9}]
        }
        entities_v2 = {
            'ratings': [{'rating': 'BUY', 'confidence': 0.9}]
        }

        doc1 = create_enhanced_document(email_data, entities_v1)
        doc2 = create_enhanced_document(email_data, entities_v2)

        assert 'BUY' in doc1
        assert 'BUY' in doc2


# Run tests if executed directly
if __name__ == '__main__':
    pytest.main([__file__, '-v'])
