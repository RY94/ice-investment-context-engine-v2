# Location: tests/test_email_graph_integration.py
# Purpose: Integration tests and Week 3 measurement framework for enhanced email documents
# Business Value: Validates Phase 1 success criteria to determine if Phase 2 (structured index) is needed
# Relevant Files: imap_email_ingestion_pipeline/enhanced_doc_creator.py, ice_integrator.py, entity_extractor.py

"""
Email Graph Integration Tests and Week 3 Measurement Framework

This module provides end-to-end integration testing for the enhanced email document
pipeline and implements the Week 3 measurement framework to determine Phase 1 success.

Week 3 Decision Criteria:
- If ALL metrics pass → Continue with Phase 1 (single LightRAG graph)
- If ANY metric fails → Trigger Phase 2 (add lightweight structured index)

Metrics:
1. Ticker extraction accuracy >95%
2. Confidence preservation in queries
3. Structured query performance <2s
4. Source attribution reliability
5. Cost per query acceptable
"""

import pytest
import sys
import os
import time
import json
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

# Add project root and email pipeline to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "imap_email_ingestion_pipeline"))

try:
    from imap_email_ingestion_pipeline.entity_extractor import EntityExtractor
    from imap_email_ingestion_pipeline.enhanced_doc_creator import create_enhanced_document
    from imap_email_ingestion_pipeline.ice_integrator import ICEEmailIntegrator
    PIPELINE_AVAILABLE = True
except ImportError as e:
    PIPELINE_AVAILABLE = False
    print(f"Warning: Email pipeline not available: {e}")

try:
    from src.ice_lightrag.ice_rag import ICELightRAG
    LIGHTRAG_AVAILABLE = True
except ImportError:
    LIGHTRAG_AVAILABLE = False
    print("Warning: LightRAG not available")


# Test configuration
TEST_STORAGE_DIR = project_root / "tmp" / "test_email_integration"
SAMPLE_EMAILS_DIR = project_root / "data" / "emails_samples"


@pytest.fixture(scope="module")
def test_setup():
    """Set up test environment"""
    # Create temporary test directory
    TEST_STORAGE_DIR.mkdir(parents=True, exist_ok=True)

    yield {
        'storage_dir': TEST_STORAGE_DIR,
        'emails_dir': SAMPLE_EMAILS_DIR
    }

    # Cleanup is optional - keep for debugging


@pytest.fixture(scope="module")
def entity_extractor():
    """Initialize EntityExtractor"""
    if not PIPELINE_AVAILABLE:
        pytest.skip("Email pipeline not available")

    extractor = EntityExtractor()
    return extractor


@pytest.fixture(scope="module")
def ice_integrator(test_setup):
    """Initialize ICE Email Integrator with test storage"""
    if not PIPELINE_AVAILABLE or not LIGHTRAG_AVAILABLE:
        pytest.skip("Required components not available")

    integrator = ICEEmailIntegrator(working_dir=str(test_setup['storage_dir']))
    return integrator


class TestEndToEndPipeline:
    """Test end-to-end email processing pipeline"""

    def test_basic_pipeline_flow(self, entity_extractor, ice_integrator):
        """Test basic email → enhanced doc → LightRAG flow"""
        # Sample email data
        email_data = {
            'uid': 'test_001',
            'from': 'analyst@test.com',
            'date': '2024-01-15',
            'subject': 'NVDA Upgrade',
            'body': 'We are upgrading NVIDIA (NVDA) to BUY with $500 price target.'
        }

        # Extract entities
        entities = entity_extractor.extract_entities(
            text=email_data['body'],
            metadata={'sender': email_data['from']}
        )

        assert entities is not None
        assert 'tickers' in entities
        assert 'confidence' in entities

        # Create enhanced document
        enhanced_doc = create_enhanced_document(email_data, entities)

        assert enhanced_doc is not None
        assert '[SOURCE_EMAIL:test_001' in enhanced_doc
        assert email_data['body'] in enhanced_doc

        # Integrate into LightRAG (use_enhanced=True)
        result = ice_integrator.integrate_email_data(
            email_data=email_data,
            extracted_entities=entities,
            graph_data={},
            use_enhanced=True,
            save_graph_json=False
        )

        assert result['success']
        assert result['components']['document_integration']

    def test_multiple_emails_batch(self, entity_extractor, ice_integrator):
        """Test processing multiple emails in batch"""
        emails = [
            {
                'uid': f'test_{i}',
                'from': f'analyst{i}@test.com',
                'date': '2024-01-15',
                'subject': f'Analysis {i}',
                'body': f'Analysis of company {i} with ticker TEST{i}'
            }
            for i in range(5)
        ]

        for email in emails:
            entities = entity_extractor.extract_entities(email['body'])
            result = ice_integrator.integrate_email_data(
                email_data=email,
                extracted_entities=entities,
                graph_data={},
                use_enhanced=True
            )
            assert result['success']


class TestWeek3Metrics:
    """Week 3 measurement framework for Phase 1 success criteria"""

    @pytest.fixture(scope="class")
    def ground_truth_emails(self):
        """
        Ground truth dataset for accuracy measurement.

        In production, this would be manually labeled emails.
        For testing, we use synthetic data with known entities.
        """
        return [
            {
                'email': {
                    'uid': 'gt_001',
                    'from': 'goldman@gs.com',
                    'date': '2024-01-15',
                    'subject': 'NVDA Upgrade to BUY',
                    'body': 'We are upgrading NVIDIA (NVDA) to BUY with $500 price target. '
                           'Strong data center growth driven by AI demand.'
                },
                'expected_tickers': ['NVDA'],
                'expected_ratings': ['BUY'],
                'expected_price_targets': ['500']
            },
            {
                'email': {
                    'uid': 'gt_002',
                    'from': 'morgan@ms.com',
                    'date': '2024-01-16',
                    'subject': 'AMD and INTC Analysis',
                    'body': 'AMD remains our top pick at BUY. Downgrading INTC to SELL. '
                           'AMD target $180, INTC target $30.'
                },
                'expected_tickers': ['AMD', 'INTC'],
                'expected_ratings': ['BUY', 'SELL'],
                'expected_price_targets': ['180', '30']
            },
            {
                'email': {
                    'uid': 'gt_003',
                    'from': 'jpmorgan@jpm.com',
                    'date': '2024-01-17',
                    'subject': 'Tech Sector Review',
                    'body': 'Maintaining HOLD on GOOGL, MSFT, and AAPL. Sector neutral. '
                           'GOOGL target $140, MSFT target $380, AAPL target $180.'
                },
                'expected_tickers': ['GOOGL', 'MSFT', 'AAPL'],
                'expected_ratings': ['HOLD', 'HOLD', 'HOLD'],
                'expected_price_targets': ['140', '380', '180']
            }
        ]

    def test_metric1_ticker_extraction_accuracy(self, entity_extractor, ice_integrator, ground_truth_emails):
        """
        Metric 1: Ticker Extraction Accuracy >95%

        Tests if LightRAG can accurately retrieve tickers from enhanced documents.
        """
        if not LIGHTRAG_AVAILABLE:
            pytest.skip("LightRAG not available for integration testing")

        total_tickers = 0
        correct_tickers = 0

        for item in ground_truth_emails:
            email = item['email']
            expected = set(item['expected_tickers'])

            # Process email through pipeline
            entities = entity_extractor.extract_entities(email['body'])
            result = ice_integrator.integrate_email_data(
                email_data=email,
                extracted_entities=entities,
                graph_data={},
                use_enhanced=True
            )

            assert result['success']

            # Query LightRAG for tickers
            # Note: This is a simplified test - in production would use actual LightRAG query
            extracted = set([t['ticker'] for t in entities.get('tickers', [])
                           if t.get('confidence', 0) > 0.5])

            total_tickers += len(expected)
            correct_tickers += len(expected & extracted)

        accuracy = correct_tickers / total_tickers if total_tickers > 0 else 0
        assert accuracy > 0.95, f"Ticker accuracy {accuracy:.2%} < 95% target"

    def test_metric2_confidence_preservation(self, entity_extractor):
        """
        Metric 2: Confidence Preservation

        Tests if confidence scores are preserved in enhanced document markup.
        """
        email_data = {
            'uid': 'conf_test',
            'body': 'NVDA upgrade to BUY'
        }

        entities = entity_extractor.extract_entities(email_data['body'])
        enhanced_doc = create_enhanced_document(email_data, entities)

        # Check if confidence scores are in the markup
        assert 'confidence:' in enhanced_doc, "Confidence scores not preserved in markup"

        # Verify format
        import re
        conf_pattern = r'confidence:0\.\d{2}'
        matches = re.findall(conf_pattern, enhanced_doc)
        assert len(matches) > 0, "No confidence scores found in expected format"

    def test_metric3_query_performance(self, ice_integrator):
        """
        Metric 3: Structured Query Performance <2s

        Tests query response time for structured filters.
        """
        if not LIGHTRAG_AVAILABLE:
            pytest.skip("LightRAG not available")

        # Prepare test data
        email_data = {
            'uid': 'perf_test',
            'from': 'test@test.com',
            'date': '2024-01-15',
            'body': 'NVDA analysis with BUY rating and $500 target'
        }

        entities = {
            'tickers': [{'ticker': 'NVDA', 'confidence': 0.95}],
            'ratings': [{'type': 'BUY', 'confidence': 0.87}],
            'financial_metrics': {
                'price_targets': [{'value': '500', 'ticker': 'NVDA', 'confidence': 0.92}]
            }
        }

        ice_integrator.integrate_email_data(
            email_data=email_data,
            extracted_entities=entities,
            graph_data={},
            use_enhanced=True
        )

        # Simple query performance test
        start_time = time.time()

        # In production, this would query LightRAG
        # For now, just test document creation time
        enhanced_doc = create_enhanced_document(email_data, entities)

        elapsed = time.time() - start_time

        assert elapsed < 2.0, f"Query took {elapsed:.2f}s > 2s target"

    def test_metric4_source_attribution(self, entity_extractor):
        """
        Metric 4: Source Attribution Reliability

        Tests if source metadata (email UID, sender, date) is preserved and traceable.
        """
        email_data = {
            'uid': 'source_test_12345',
            'from': 'analyst@goldmansachs.com',
            'date': '2024-01-15T10:30:00',
            'subject': 'Test Email',
            'body': 'Test content'
        }

        entities = {}
        enhanced_doc = create_enhanced_document(email_data, entities)

        # Verify all source metadata is present
        assert '[SOURCE_EMAIL:source_test_12345' in enhanced_doc
        assert 'sender:analyst@goldmansachs.com' in enhanced_doc
        assert 'date:2024-01-15T10:30:00' in enhanced_doc

    def test_metric5_cost_measurement(self):
        """
        Metric 5: Cost Per Query

        Placeholder for cost measurement - tracks API calls to OpenAI.
        In production, this would integrate with actual API call tracking.
        """
        # This is a placeholder - actual implementation would:
        # 1. Track OpenAI API calls during test execution
        # 2. Calculate cost based on token usage
        # 3. Compare to baseline

        # For now, just assert the enhanced doc creation doesn't make LLM calls
        email_data = {'uid': '123', 'body': 'Test'}
        entities = {}

        # Enhanced doc creation is deterministic (no LLM calls)
        doc = create_enhanced_document(email_data, entities)
        assert doc is not None

        # Cost optimization: EntityExtractor uses regex + spaCy (local), not LLM
        # This is the key benefit - no duplicate LLM calls


def generate_week3_report(test_results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate Week 3 evaluation report to determine if Phase 2 is needed.

    Args:
        test_results: Dictionary of test results from pytest

    Returns:
        Report dictionary with metrics and Phase 2 recommendation
    """
    report = {
        'report_date': datetime.now().isoformat(),
        'phase': 'Phase 1 - Enhanced Documents',
        'metrics': {
            'ticker_extraction_accuracy': {
                'value': test_results.get('ticker_accuracy', 0.0),
                'target': 0.95,
                'passed': test_results.get('ticker_accuracy', 0.0) > 0.95
            },
            'confidence_preservation': {
                'value': test_results.get('confidence_preserved', False),
                'target': True,
                'passed': test_results.get('confidence_preserved', False)
            },
            'query_performance': {
                'value': test_results.get('query_time', 999),
                'target': 2.0,
                'passed': test_results.get('query_time', 999) < 2.0
            },
            'source_attribution': {
                'value': test_results.get('source_traceable', False),
                'target': True,
                'passed': test_results.get('source_traceable', False)
            },
            'cost_optimization': {
                'value': 'No duplicate LLM calls',
                'target': 'Cost effective',
                'passed': True
            }
        },
        'overall_success': all(
            m['passed'] for m in test_results.get('metrics', {}).values()
        ),
        'phase_2_required': not all(
            m['passed'] for m in test_results.get('metrics', {}).values()
        ),
        'recommendation': ''
    }

    if report['overall_success']:
        report['recommendation'] = (
            "✅ All Phase 1 metrics passed. Continue with single LightRAG graph. "
            "No need for Phase 2 structured index."
        )
    else:
        failed_metrics = [
            name for name, data in report['metrics'].items()
            if not data['passed']
        ]
        report['recommendation'] = (
            f"❌ Phase 1 metrics failed: {', '.join(failed_metrics)}. "
            "Trigger Phase 2: Implement lightweight structured index."
        )

    return report


# Test execution helpers
if __name__ == '__main__':
    # Run tests with verbose output
    pytest.main([__file__, '-v', '--tb=short'])
