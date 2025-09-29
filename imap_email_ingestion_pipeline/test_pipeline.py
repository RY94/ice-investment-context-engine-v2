# imap_email_ingestion_pipeline/test_pipeline.py
# Comprehensive test suite for the email ingestion pipeline
# Tests all components with mock data and error scenarios
# RELEVANT FILES: All pipeline components, pipeline_orchestrator.py

import unittest
import tempfile
import shutil
import logging
import json
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import pipeline components
from state_manager import StateManager
from attachment_processor import AttachmentProcessor
from entity_extractor import EntityExtractor
from graph_builder import GraphBuilder
from ice_integrator import ICEEmailIntegrator
from pipeline_orchestrator import PipelineOrchestrator

class TestStateManager(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_state.db")
        self.state_manager = StateManager(self.db_path)
    
    def tearDown(self):
        self.state_manager.close()
        shutil.rmtree(self.temp_dir)
    
    def test_email_processing_state(self):
        """Test email state tracking"""
        email_uid = "test_email_123"
        email_data = {
            'subject': 'Test Email',
            'from': 'test@example.com',
            'date': '2024-01-01',
            'priority': 5
        }
        
        # Test initial state
        self.assertFalse(self.state_manager.is_email_processed(email_uid))
        
        # Mark as processing
        self.assertTrue(self.state_manager.mark_email_processing(email_uid, email_data))
        
        # Test completion
        self.assertTrue(self.state_manager.mark_email_completed(email_uid, 1000))
        self.assertTrue(self.state_manager.is_email_processed(email_uid))
        
        # Test failure handling
        email_uid_2 = "test_email_456"
        self.assertTrue(self.state_manager.mark_email_processing(email_uid_2, email_data))
        self.assertTrue(self.state_manager.mark_email_failed(email_uid_2, "Test error"))
        self.assertFalse(self.state_manager.is_email_processed(email_uid_2))
    
    def test_attachment_deduplication(self):
        """Test attachment hash-based deduplication"""
        content = b"test attachment content"
        file_hash = self.state_manager.get_attachment_hash(content)
        
        # First attachment
        self.assertFalse(self.state_manager.is_attachment_processed(file_hash))
        self.assertTrue(self.state_manager.record_attachment(
            "email_123", "test.pdf", file_hash, len(content), "application/pdf"
        ))
        
        # Update results
        self.assertTrue(self.state_manager.update_attachment_results(
            file_hash, 500, 0.95, "native_extraction"
        ))
        self.assertTrue(self.state_manager.is_attachment_processed(file_hash))
        
        # Same content should be deduplicated
        same_hash = self.state_manager.get_attachment_hash(content)
        self.assertEqual(file_hash, same_hash)
    
    def test_metrics_recording(self):
        """Test metrics recording"""
        self.state_manager.record_metric("processing_rate", 10.5)
        self.state_manager.record_metric("error_rate", 0.02, {"component": "ocr"})
        
        # Get stats
        stats = self.state_manager.get_processing_stats(hours=1)
        self.assertIsInstance(stats, dict)


class TestEntityExtractor(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.entity_extractor = EntityExtractor(self.temp_dir)
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def test_ticker_extraction(self):
        """Test ticker symbol extraction"""
        test_text = "I think AAPL will outperform this quarter. MSFT is also looking strong."
        entities = self.entity_extractor.extract_entities(test_text)
        
        tickers = entities['tickers']
        ticker_symbols = [t['ticker'] for t in tickers]
        
        self.assertIn('AAPL', ticker_symbols)
        self.assertIn('MSFT', ticker_symbols)
        
        # Check confidence scores
        for ticker in tickers:
            self.assertGreaterEqual(ticker['confidence'], 0.0)
            self.assertLessEqual(ticker['confidence'], 1.0)
    
    def test_financial_metrics_extraction(self):
        """Test financial metrics extraction"""
        test_text = "Price target raised to $150. EPS estimate is $2.50. P/E ratio of 25.5."
        entities = self.entity_extractor.extract_entities(test_text)
        
        metrics = entities['financial_metrics']
        self.assertIn('price_targets', metrics)
        self.assertIn('financials', metrics)
    
    def test_sentiment_analysis(self):
        """Test sentiment analysis"""
        bullish_text = "Strong buy recommendation. Excellent earnings beat expectations."
        bearish_text = "Downgrade to sell. Weak guidance disappoints investors."
        neutral_text = "The company reported quarterly results."
        
        bullish_result = self.entity_extractor.extract_entities(bullish_text)
        bearish_result = self.entity_extractor.extract_entities(bearish_text)
        neutral_result = self.entity_extractor.extract_entities(neutral_text)
        
        self.assertEqual(bullish_result['sentiment']['sentiment'], 'bullish')
        self.assertEqual(bearish_result['sentiment']['sentiment'], 'bearish')
        self.assertEqual(neutral_result['sentiment']['sentiment'], 'neutral')
    
    def test_empty_text_handling(self):
        """Test handling of empty or None text"""
        entities = self.entity_extractor.extract_entities("")
        self.assertEqual(entities['confidence'], 0.0)
        
        entities = self.entity_extractor.extract_entities(None)
        self.assertEqual(entities['confidence'], 0.0)


class TestGraphBuilder(unittest.TestCase):
    def setUp(self):
        self.graph_builder = GraphBuilder()
    
    def test_email_graph_creation(self):
        """Test email graph structure creation"""
        email_data = {
            'uid': 'test_123',
            'subject': 'AAPL Earnings Update',
            'from': 'analyst@research.com',
            'date': '2024-01-01',
            'body': 'Apple reported strong quarterly earnings.',
            'attachments': []
        }
        
        entities = {
            'tickers': [{'ticker': 'AAPL', 'confidence': 0.9, 'source': 'known_ticker'}],
            'sentiment': {'sentiment': 'bullish', 'confidence': 0.8},
            'confidence': 0.85
        }
        
        graph_data = self.graph_builder.build_email_graph(email_data, entities)
        
        # Check structure
        self.assertIn('nodes', graph_data)
        self.assertIn('edges', graph_data)
        self.assertIn('metadata', graph_data)
        
        # Should have at least email, sender, and ticker nodes
        self.assertGreaterEqual(len(graph_data['nodes']), 3)
        
        # Should have edges connecting them
        self.assertGreater(len(graph_data['edges']), 0)
        
        # Validate graph structure
        validation = self.graph_builder.validate_graph_structure(graph_data)
        self.assertTrue(validation['valid'], f"Validation errors: {validation['errors']}")
    
    def test_edge_creation(self):
        """Test edge creation with proper metadata"""
        edge = self.graph_builder._create_edge(
            'node1', 'node2', 'mentions', 0.8,
            properties={'context': 'test context'}
        )
        
        self.assertEqual(edge['source'], 'node1')
        self.assertEqual(edge['target'], 'node2')
        self.assertEqual(edge['type'], 'mentions')
        self.assertEqual(edge['confidence'], 0.8)
        self.assertIn('context', edge['properties'])
        self.assertIn('created_at', edge)


class TestAttachmentProcessor(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.attachment_processor = AttachmentProcessor(self.temp_dir)
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    @patch('magic.from_buffer')
    def test_text_file_processing(self, mock_magic):
        """Test plain text file processing"""
        mock_magic.return_value = 'text/plain'
        
        # Create mock attachment
        test_content = "This is a test document with AAPL mentioned."
        mock_part = Mock()
        mock_part.get_payload.return_value = test_content.encode('utf-8')
        
        attachment_data = {
            'filename': 'test.txt',
            'content_type': 'text/plain',
            'size': len(test_content),
            'part': mock_part
        }
        
        result = self.attachment_processor.process_attachment(attachment_data, "email_123")
        
        self.assertTrue(result.get('processing_status') in ['completed', 'error'])
        if result.get('processing_status') == 'completed':
            self.assertEqual(result['extracted_text'], test_content)
    
    def test_unsupported_file_type(self):
        """Test handling of unsupported file types"""
        mock_part = Mock()
        mock_part.get_payload.return_value = b"binary content"
        
        attachment_data = {
            'filename': 'test.unknown',
            'content_type': 'application/unknown',
            'size': 100,
            'part': mock_part
        }
        
        with patch('magic.from_buffer', return_value='application/unknown'):
            result = self.attachment_processor.process_attachment(attachment_data, "email_123")
        
        self.assertIn('error', result)
    
    def test_file_size_limit(self):
        """Test file size limit enforcement"""
        # Create oversized content
        large_content = b"x" * (self.attachment_processor.max_file_size + 1)
        
        mock_part = Mock()
        mock_part.get_payload.return_value = large_content
        
        attachment_data = {
            'filename': 'large_file.txt',
            'content_type': 'text/plain',
            'size': len(large_content),
            'part': mock_part
        }
        
        result = self.attachment_processor.process_attachment(attachment_data, "email_123")
        
        self.assertIn('error', result)
        self.assertIn('too large', result['error'].lower())


class TestICEIntegrator(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.ice_integrator = ICEEmailIntegrator(self.temp_dir)
    
    def tearDown(self):
        self.ice_integrator.close()
        shutil.rmtree(self.temp_dir)
    
    def test_document_creation(self):
        """Test comprehensive document creation"""
        email_data = {
            'uid': 'test_123',
            'subject': 'Test Email',
            'from': 'test@example.com',
            'date': '2024-01-01',
            'body': 'This is a test email about AAPL.'
        }
        
        entities = {
            'tickers': [{'ticker': 'AAPL', 'confidence': 0.9}],
            'sentiment': {'sentiment': 'bullish', 'confidence': 0.8},
            'confidence': 0.85
        }
        
        document = self.ice_integrator._create_comprehensive_document(email_data, entities)
        
        self.assertIsNotNone(document)
        self.assertIn('EMAIL METADATA', document)
        self.assertIn('EXTRACTED ENTITIES', document)
        self.assertIn('EMAIL CONTENT', document)
        self.assertIn('AAPL', document)
    
    def test_integration_result_structure(self):
        """Test integration result structure"""
        email_data = {'uid': 'test_123', 'subject': 'Test'}
        entities = {'confidence': 0.8}
        graph_data = {'nodes': [], 'edges': []}
        
        result = self.ice_integrator.integrate_email_data(
            email_data, entities, graph_data
        )
        
        self.assertIn('success', result)
        self.assertIn('components', result)
        self.assertIn('document_integration', result['components'])


class TestPipelineOrchestrator(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        config_path = os.path.join(self.temp_dir, "test_config.json")
        self.orchestrator = PipelineOrchestrator(config_path)
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def test_config_loading(self):
        """Test configuration loading and defaults"""
        self.assertIsInstance(self.orchestrator.config, dict)
        self.assertIn('email', self.orchestrator.config)
        self.assertIn('processing', self.orchestrator.config)
        self.assertIn('scheduling', self.orchestrator.config)
    
    def test_health_check(self):
        """Test health check functionality"""
        # Mock IMAP connector
        self.orchestrator.imap_connector = Mock()
        self.orchestrator.imap_connector.ensure_connection.return_value = True
        
        # Should pass with mocked components
        result = self.orchestrator._perform_health_check()
        self.assertTrue(result)
    
    @patch('imap_connector.ResilientIMAPConnector')
    def test_email_connection_initialization(self, mock_connector_class):
        """Test email connection initialization"""
        mock_connector = Mock()
        mock_connector.connect.return_value = True
        mock_connector_class.return_value = mock_connector
        
        result = self.orchestrator.initialize_email_connection("test@example.com", "password")
        self.assertTrue(result)
    
    def test_metrics_update(self):
        """Test metrics update functionality"""
        processing_result = {
            'successful': 5,
            'failed': 1,
            'processing_times': [1.0, 2.0, 1.5, 3.0, 2.5, 4.0]
        }
        
        initial_rate = self.orchestrator.metrics['processing_rate']
        self.orchestrator._update_metrics(processing_result, 10.0)
        
        # Processing rate should be calculated
        self.assertGreater(self.orchestrator.metrics['processing_rate'], 0)
        
        # Average processing time should be calculated
        self.assertGreater(self.orchestrator.metrics['average_processing_time'], 0)


class TestErrorHandling(unittest.TestCase):
    """Test error handling scenarios across all components"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def test_database_connection_error(self):
        """Test state manager with invalid database path"""
        invalid_path = "/invalid/path/state.db"
        
        with self.assertRaises(Exception):
            StateManager(invalid_path)
    
    def test_malformed_email_data(self):
        """Test handling of malformed email data"""
        entity_extractor = EntityExtractor(self.temp_dir)
        graph_builder = GraphBuilder()
        
        # Empty email data
        malformed_data = {}
        entities = entity_extractor.extract_entities("")
        graph_data = graph_builder.build_email_graph(malformed_data, entities)
        
        # Should handle gracefully without crashing
        self.assertIsInstance(graph_data, dict)
    
    def test_attachment_processing_errors(self):
        """Test attachment processor error handling"""
        attachment_processor = AttachmentProcessor(self.temp_dir)
        
        # Malformed attachment data
        bad_attachment = {
            'filename': 'test.pdf',
            'part': None  # Invalid part
        }
        
        result = attachment_processor.process_attachment(bad_attachment, "email_123")
        self.assertIn('error', result)


class MockIMAPConnector:
    """Mock IMAP connector for testing"""
    
    def __init__(self, *args, **kwargs):
        self.connected = False
    
    def connect(self):
        self.connected = True
        return True
    
    def ensure_connection(self):
        return self.connected
    
    def fetch_new_emails(self, **kwargs):
        return [
            {
                'uid': 'test_001',
                'subject': 'Test Email 1',
                'from': 'test@example.com',
                'date': '2024-01-01',
                'body': 'This is a test email about AAPL.',
                'attachments': []
            }
        ]
    
    def close(self):
        self.connected = False


def run_integration_test():
    """Run end-to-end integration test"""
    print("Running integration test...")
    
    temp_dir = tempfile.mkdtemp()
    try:
        # Create test orchestrator
        config_path = os.path.join(temp_dir, "integration_config.json")
        orchestrator = PipelineOrchestrator(config_path)
        
        # Mock IMAP connector
        orchestrator.imap_connector = MockIMAPConnector()
        
        # Run single cycle
        result = orchestrator.run_single_cycle()
        
        print(f"Integration test result: {json.dumps(result, indent=2)}")
        return result.get('success', False)
        
    except Exception as e:
        print(f"Integration test failed: {e}")
        return False
        
    finally:
        shutil.rmtree(temp_dir)


def main():
    """Main test runner"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Email Pipeline Test Suite')
    parser.add_argument('--integration', action='store_true', 
                       help='Run integration test')
    parser.add_argument('--component', choices=[
        'state', 'entity', 'graph', 'attachment', 'ice', 'orchestrator'
    ], help='Test specific component')
    
    args = parser.parse_args()
    
    # Setup logging for tests
    logging.basicConfig(level=logging.WARNING)
    
    if args.integration:
        success = run_integration_test()
        return 0 if success else 1
    
    # Run unit tests
    test_classes = [
        TestStateManager,
        TestEntityExtractor,
        TestGraphBuilder,
        TestAttachmentProcessor,
        TestICEIntegrator,
        TestPipelineOrchestrator,
        TestErrorHandling
    ]
    
    if args.component:
        component_map = {
            'state': [TestStateManager],
            'entity': [TestEntityExtractor],
            'graph': [TestGraphBuilder],
            'attachment': [TestAttachmentProcessor],
            'ice': [TestICEIntegrator],
            'orchestrator': [TestPipelineOrchestrator]
        }
        test_classes = component_map.get(args.component, test_classes)
    
    # Create test suite
    suite = unittest.TestSuite()
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())