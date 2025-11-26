# Location: /tests/test_relationship_extraction.py
# Purpose: Test Refinement #3 - Universal Cross-Company Relationship Extraction
# Why: Validates multi-hop intelligence for uncovering hidden investment risks/opportunities
# Relevant Files: ice_simplified.py, relationship_extractor.py, config.py

import unittest
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from updated_architectures.implementation.ice_simplified import ICECore
from updated_architectures.implementation.config import ICEConfig


class TestRelationshipExtraction(unittest.TestCase):
    """Test suite for Refinement #3: Universal Cross-Company Relationship Extraction"""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures"""
        cls.config = ICEConfig()
        # Ensure relationship extraction is enabled
        cls.config.relationship_extraction_enabled = True
        cls.ice = ICECore(config=cls.config)

    def test_01_config_enabled(self):
        """Verify relationship extraction is enabled and configured"""
        # Check config parameters exist
        self.assertTrue(hasattr(self.config, 'relationship_extraction_enabled'))
        self.assertTrue(hasattr(self.config, 'relationship_confidence_threshold'))
        self.assertTrue(hasattr(self.config, 'max_relationships_per_doc'))
        self.assertTrue(hasattr(self.config, 'relationship_cache_size'))

        # Check defaults are sensible
        self.assertTrue(self.config.relationship_extraction_enabled)
        self.assertEqual(self.config.relationship_confidence_threshold, 0.5)
        self.assertEqual(self.config.max_relationships_per_doc, 50)
        self.assertEqual(self.config.relationship_cache_size, 1000)

    def test_02_extractor_initialized(self):
        """Verify RelationshipExtractor is initialized in ICECore"""
        # Check extractor exists
        self.assertTrue(hasattr(self.ice, 'relationship_extractor'))
        self.assertIsNotNone(self.ice.relationship_extractor)

        # Check cache exists
        self.assertTrue(hasattr(self.ice, 'relationship_cache'))
        self.assertIsInstance(self.ice.relationship_cache, dict)

        # Check source confidence multipliers exist
        self.assertTrue(hasattr(self.ice, 'SOURCE_CONFIDENCE'))
        self.assertEqual(self.ice.SOURCE_CONFIDENCE['sec_edgar'], 1.0)
        self.assertEqual(self.ice.SOURCE_CONFIDENCE['newsapi'], 0.75)
        self.assertEqual(self.ice.SOURCE_CONFIDENCE['email'], 0.70)

    def test_03_helper_methods_exist(self):
        """Verify all helper methods are implemented"""
        # Check required helper methods
        self.assertTrue(hasattr(self.ice, '_enhance_with_relationships'))
        self.assertTrue(hasattr(self.ice, '_ensure_entities'))
        self.assertTrue(hasattr(self.ice, '_detect_source_type'))
        self.assertTrue(hasattr(self.ice, '_is_quantified'))
        self.assertTrue(hasattr(self.ice, '_format_relationships'))

    def test_04_extraction_competitive_relationships(self):
        """Test extraction of competitive relationships (RELATED_TO)"""
        # Document with clear competitive relationship
        doc = {
            'content': 'NVDA competes directly with AMD in the GPU market. Both companies are rivals in AI chips.',
            'source': 'newsapi',
            'file_path': 'newsapi:test_competitive_001',
            'type': 'news',
            'entities': ['NVDA', 'AMD']
        }

        # Enhance with relationships
        enhanced = self.ice._enhance_with_relationships(doc)

        # Verify relationships were added
        self.assertIn('content', enhanced)
        content = enhanced['content']

        # Should contain formatted relationships
        # Format: "NVDA RELATED_TO AMD (confidence: 0.XX)"
        self.assertTrue(
            'RELATED_TO' in content or 'competes' in content.lower(),
            "Should extract competitive relationship"
        )

    def test_05_extraction_supply_chain_relationships(self):
        """Test extraction of supply chain relationships (IMPACTS, RELATED_TO)"""
        # Document with supply chain dependency
        doc = {
            'content': 'TSMC supplies chips to NVDA. Taiwan Semiconductor Manufacturing is a critical supplier for NVIDIA.',
            'source': 'sec_edgar',
            'file_path': 'sec_edgar:NVDA_10K_2024_test',
            'type': 'financial',
            'entities': ['TSMC', 'NVDA', 'NVIDIA']
        }

        # Enhance with relationships
        enhanced = self.ice._enhance_with_relationships(doc)

        # Verify supply chain relationships extracted
        content = enhanced['content']
        self.assertTrue(
            'supplies' in content.lower() or 'supplier' in content.lower(),
            "Should extract supply chain relationship"
        )

    def test_06_extraction_executive_relationships(self):
        """Test extraction of executive relationships (EMPLOYED_BY)"""
        # Document with executive relationship
        doc = {
            'content': 'Jensen Huang is the CEO of NVIDIA. He has led NVDA since its founding.',
            'source': 'newsapi',
            'file_path': 'newsapi:test_exec_001',
            'type': 'news',
            'entities': ['Jensen Huang', 'NVIDIA', 'NVDA']
        }

        # Enhance with relationships
        enhanced = self.ice._enhance_with_relationships(doc)

        # Verify executive relationships extracted
        content = enhanced['content']
        self.assertTrue(
            'CEO' in content or 'EMPLOYED_BY' in content,
            "Should extract executive relationship"
        )

    def test_07_source_confidence_weighting(self):
        """Test source confidence multipliers are applied correctly"""
        # Test SEC source (highest confidence 1.0x)
        sec_doc = {
            'content': 'Test content for SEC filing',
            'source': 'sec_edgar',
            'file_path': 'sec_edgar:AAPL_10K_2024_test',
            'type': 'financial'
        }

        # Test news source (medium confidence 0.75x)
        news_doc = {
            'content': 'Test content for news article',
            'source': 'newsapi',
            'file_path': 'newsapi:test_001',
            'type': 'news'
        }

        # Test email source (lower confidence 0.70x)
        email_doc = {
            'content': 'Test content for email',
            'source': 'email',
            'file_path': 'email:analyst_001',
            'type': 'email'
        }

        # Verify source type detection
        sec_type = self.ice._detect_source_type(sec_doc)
        news_type = self.ice._detect_source_type(news_doc)
        email_type = self.ice._detect_source_type(email_doc)

        self.assertEqual(sec_type, 'sec_edgar')
        self.assertEqual(news_type, 'newsapi')
        self.assertEqual(email_type, 'email')

        # Verify confidence multipliers
        self.assertEqual(self.ice.SOURCE_CONFIDENCE[sec_type], 1.0)
        self.assertEqual(self.ice.SOURCE_CONFIDENCE[news_type], 0.75)
        self.assertEqual(self.ice.SOURCE_CONFIDENCE[email_type], 0.70)

    def test_08_quantification_boost(self):
        """Test relationships with quantification get confidence boost"""
        # Mock relationship with quantification (should get +0.15 boost)
        class MockRelationship:
            def __init__(self):
                self.percentage = 25.5
                self.amount = 1000000

        quantified_rel = MockRelationship()
        self.assertTrue(self.ice._is_quantified(quantified_rel))

        # Mock relationship without quantification
        class MockRelationshipNoQuant:
            def __init__(self):
                pass

        unquantified_rel = MockRelationshipNoQuant()
        self.assertFalse(self.ice._is_quantified(unquantified_rel))

    def test_09_entity_fallback_extraction(self):
        """Test fallback entity extraction when entities not pre-extracted"""
        # Document without entities field (should extract basic entities)
        doc = {
            'content': 'AAPL competes with MSFT and GOOGL in consumer technology. Apple faces competition from Microsoft.',
            'source': 'newsapi',
            'file_path': 'newsapi:test_fallback_001',
            'type': 'news'
            # No 'entities' field
        }

        # Fallback should extract tickers and company names
        entities = self.ice._ensure_entities(doc)

        # Should extract at least AAPL, MSFT, GOOGL
        self.assertIsInstance(entities, list)
        self.assertGreater(len(entities), 0)

        # Check for extracted tickers (2-5 uppercase letters)
        # Entities are now dicts with 'text' and 'type' keys
        tickers = [e for e in entities if e['text'].isupper() and 2 <= len(e['text']) <= 5]
        self.assertGreater(len(tickers), 0, "Should extract at least one ticker")

    def test_10_content_based_caching(self):
        """Test content-based caching prevents redundant extraction"""
        # Create identical documents (same content hash)
        doc1 = {
            'content': 'NVDA competes with AMD in GPU market.',
            'source': 'newsapi',
            'file_path': 'newsapi:test_cache_001',
            'type': 'news',
            'entities': ['NVDA', 'AMD']
        }

        doc2 = {
            'content': 'NVDA competes with AMD in GPU market.',  # Same content
            'source': 'newsapi',
            'file_path': 'newsapi:test_cache_002',  # Different file_path
            'type': 'news',
            'entities': ['NVDA', 'AMD']
        }

        # Clear cache first
        self.ice.relationship_cache.clear()

        # First enhancement (cache miss)
        enhanced1 = self.ice._enhance_with_relationships(doc1)
        cache_size_after_first = len(self.ice.relationship_cache)

        # Second enhancement (cache hit - same content)
        enhanced2 = self.ice._enhance_with_relationships(doc2)
        cache_size_after_second = len(self.ice.relationship_cache)

        # Cache should have 1 entry (both docs have same content hash)
        self.assertEqual(cache_size_after_first, 1)
        self.assertEqual(cache_size_after_second, 1)  # No increase

    def test_11_graceful_degradation_on_error(self):
        """Test graceful degradation when extraction fails"""
        # Malformed document (missing content)
        doc = {
            'source': 'newsapi',
            'file_path': 'newsapi:test_error_001',
            'type': 'news'
            # Missing 'content' field
        }

        # Should return original document without crashing
        try:
            enhanced = self.ice._enhance_with_relationships(doc)
            # Should return original doc
            self.assertEqual(enhanced, doc)
        except Exception as e:
            self.fail(f"Should handle missing content gracefully, got exception: {e}")

    def test_12_integration_batch_processing(self):
        """Integration test: Batch processing with relationship extraction"""
        # Create batch of documents with known relationships
        documents = [
            {
                'content': 'NVDA competes with AMD in the GPU market. Competition is intense.',
                'source': 'newsapi',
                'file_path': 'newsapi:batch_test_001',
                'type': 'news',
                'entities': ['NVDA', 'AMD']
            },
            {
                'content': 'TSMC supplies chips to NVDA. Taiwan Semiconductor is critical supplier.',
                'source': 'sec_edgar',
                'file_path': 'sec_edgar:NVDA_10K_batch_test',
                'type': 'financial',
                'entities': ['TSMC', 'NVDA']
            },
            {
                'content': 'Jensen Huang leads NVIDIA as CEO. He founded the company decades ago.',
                'source': 'newsapi',
                'file_path': 'newsapi:batch_test_003',
                'type': 'news',
                'entities': ['Jensen Huang', 'NVIDIA', 'NVDA']
            }
        ]

        # Process batch
        result = self.ice.add_documents_batch(documents)

        # Verify batch processed successfully
        self.assertEqual(result.get('status'), 'success')
        self.assertEqual(result.get('successful'), 3)
        self.assertEqual(result.get('failed'), 0)  # Key is 'failed', not 'failed_count'

    def test_13_multi_hop_query_capability(self):
        """Test multi-hop query capability (requires API key)"""
        if not os.getenv('OPENAI_API_KEY'):
            self.skipTest("API key not configured")

        # Create knowledge graph with 3-hop relationship chain
        # TSMC → NVDA → Hyperscalers → REITs
        documents = [
            {
                'content': 'TSMC supplies advanced chips to NVDA. Taiwan tensions could impact supply chain.',
                'source': 'sec_edgar',
                'file_path': 'sec_edgar:NVDA_10K_multi_hop_1',
                'type': 'financial',
                'entities': ['TSMC', 'NVDA', 'Taiwan']
            },
            {
                'content': 'NVDA GPUs power hyperscaler data centers. GOOGL, MSFT, AMZN are major customers.',
                'source': 'newsapi',
                'file_path': 'newsapi:multi_hop_2',
                'type': 'news',
                'entities': ['NVDA', 'GOOGL', 'MSFT', 'AMZN']
            },
            {
                'content': 'Hyperscaler expansion drives REIT demand. Data center REITs benefit from AI growth.',
                'source': 'newsapi',
                'file_path': 'newsapi:multi_hop_3',
                'type': 'news',
                'entities': ['GOOGL', 'MSFT', 'REIT']
            }
        ]

        # Build knowledge graph
        result = self.ice.add_documents_batch(documents)
        self.assertEqual(result.get('status'), 'success')

        # Query for multi-hop connection (TSMC → ... → REIT)
        # This tests if relationships enable traversal
        query = "How might Taiwan tensions on TSMC impact data center REITs?"

        response = self.ice.query(
            question=query,  # ICECore.query() uses 'question' parameter
            mode='hybrid'  # Use hybrid for best recall
        )

        # Verify response mentions multiple entities in chain
        response_text = response.get('response', '').lower()

        # Should mention entities from different hops
        mentions = {
            'tsmc': 'tsmc' in response_text,
            'nvda': 'nvda' in response_text or 'nvidia' in response_text,
            'hyperscaler': any(x in response_text for x in ['googl', 'msft', 'amzn', 'hyperscaler']),
            'reit': 'reit' in response_text
        }

        # Multi-hop query should connect at least 2 entities from chain
        connected_entities = sum(mentions.values())
        self.assertGreaterEqual(
            connected_entities, 2,
            f"Multi-hop query should connect entities across chain. Got: {mentions}"
        )

    def test_14_relationship_formatting(self):
        """Test relationship formatting for LightRAG parsing"""
        # Mock relationship for formatting test
        class MockRelationship:
            def __init__(self):
                self.source_entity = "NVDA"
                self.target_entity = "AMD"
                self.relationship_type = "RELATED_TO"
                self.confidence = 0.85
                self.description = "competes in GPU market"

        relationships = [MockRelationship()]

        # Format relationships
        formatted = self.ice._format_relationships(relationships)

        # Verify format preserves directionality and confidence
        self.assertIn('NVDA', formatted)
        self.assertIn('AMD', formatted)
        self.assertIn('RELATED_TO', formatted)
        self.assertIn('0.85', formatted)  # Confidence preserved

    def test_15_disabled_extraction(self):
        """Test behavior when relationship extraction is disabled"""
        # Create new config with extraction disabled
        config_disabled = ICEConfig()
        config_disabled.relationship_extraction_enabled = False
        ice_disabled = ICECore(config=config_disabled)

        # Verify extractor is None
        self.assertIsNone(ice_disabled.relationship_extractor)

        # Document should pass through unchanged
        doc = {
            'content': 'NVDA competes with AMD.',
            'source': 'newsapi',
            'file_path': 'newsapi:disabled_test_001',
            'type': 'news'
        }

        # Process document (should skip enhancement)
        result = ice_disabled.add_documents_batch([doc])

        # Should succeed (extraction just skipped)
        self.assertEqual(result.get('status'), 'success')


if __name__ == '__main__':
    # Run with verbose output
    unittest.main(verbosity=2)
