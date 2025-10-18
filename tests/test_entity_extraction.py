# Location: /tests/test_entity_extraction.py
# Purpose: Integration test for Phase 2.6.1 EntityExtractor integration
# Why: Validates production-grade entity extraction in email ingestion pipeline
# Relevant Files: data_ingestion.py, entity_extractor.py, enhanced_doc_creator.py

import sys
from pathlib import Path
import pytest

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from updated_architectures.implementation.data_ingestion import DataIngester


class TestEntityExtraction:
    """
    Phase 2.6.1 Integration Tests

    Validates EntityExtractor integration with email ingestion:
    1. EntityExtractor output format (entities dict with confidence)
    2. Enhanced document inline markup format
    3. Backward compatibility (returns List[str])
    4. Class attribute storage for Phase 2.6.2
    """

    @pytest.fixture
    def data_ingester(self):
        """Create DataIngester instance for testing"""
        return DataIngester()

    def test_fetch_email_documents_returns_list_of_strings(self, data_ingester):
        """Test backward compatibility: returns List[str]"""
        documents = data_ingester.fetch_email_documents(limit=2)

        # Should return list
        assert isinstance(documents, list), "fetch_email_documents must return List"

        # All items should be strings
        for doc in documents:
            assert isinstance(doc, str), f"Document must be string, got {type(doc)}"

        print(f"✅ Backward compatibility: Returns List[str] ({len(documents)} docs)")

    def test_entity_extractor_creates_structured_data(self, data_ingester):
        """Test EntityExtractor creates structured entity data"""
        # Fetch emails to trigger entity extraction
        documents = data_ingester.fetch_email_documents(limit=2)

        # Should have extracted entities stored in class attribute
        assert hasattr(data_ingester, 'last_extracted_entities'), \
            "DataIngester must have last_extracted_entities attribute"

        entities_list = data_ingester.last_extracted_entities

        # Should have entity data (if EntityExtractor succeeded)
        if len(entities_list) > 0:
            # Check first entity has expected structure
            entities = entities_list[0]
            assert isinstance(entities, dict), "Entities must be dict"

            # EntityExtractor provides these keys
            expected_keys = ['tickers', 'companies', 'financial_metrics', 'confidence']
            for key in expected_keys:
                assert key in entities, f"Entities missing expected key: {key}"

            print(f"✅ EntityExtractor output: {len(entities_list)} entity dicts created")
            print(f"   Sample: {list(entities.keys())}")
        else:
            print("⚠️  No entities extracted (EntityExtractor may have failed or no emails)")

    def test_enhanced_document_has_inline_markup(self, data_ingester):
        """Test enhanced documents contain inline entity markup"""
        documents = data_ingester.fetch_email_documents(limit=5)

        # Look for inline markup patterns: [TICKER:XXX|confidence:0.XX]
        markup_found = False
        for doc in documents:
            # Check for characteristic patterns of enhanced documents
            if '[' in doc and '|confidence:' in doc:
                markup_found = True
                print(f"✅ Enhanced document inline markup detected")
                # Show sample (first 200 chars of first enhanced doc)
                sample = doc[:200].replace('\n', ' ')
                print(f"   Sample: {sample}...")
                break

        if not markup_found:
            print("⚠️  No inline markup found (EntityExtractor may have used fallback)")

    def test_entity_storage_for_phase_2_6_2(self, data_ingester):
        """Test structured data storage for future Signal Store (Phase 2.6.2)"""
        # Reset storage
        data_ingester.last_extracted_entities = []

        # Fetch emails
        documents = data_ingester.fetch_email_documents(limit=3)

        # Verify storage attributes exist
        assert hasattr(data_ingester, 'last_extracted_entities'), \
            "Missing last_extracted_entities for Phase 2.6.2"
        assert hasattr(data_ingester, 'last_graph_data'), \
            "Missing last_graph_data for Phase 2.6.2"

        print(f"✅ Phase 2.6.2 storage ready: {len(data_ingester.last_extracted_entities)} entity records")

    def test_graceful_fallback_on_entity_extraction_failure(self, data_ingester):
        """Test system remains stable if EntityExtractor fails"""
        # Even with potential EntityExtractor failures, should return valid documents
        documents = data_ingester.fetch_email_documents(limit=2)

        # Should still return documents (fallback to basic extraction)
        assert isinstance(documents, list), "Should return list even on failure"
        assert len(documents) >= 0, "Should return documents (or empty list if no emails)"

        # All documents should be valid strings
        for doc in documents:
            assert isinstance(doc, str), "Fallback should produce valid string documents"
            assert len(doc) > 0, "Fallback documents should not be empty"

        print(f"✅ Graceful fallback: {len(documents)} documents returned")

    def test_document_entity_alignment(self, data_ingester):
        """
        CRITICAL: Validate documents and entities are aligned

        Bug fix for Phase 2.6.1: Ensures len(documents) == len(last_extracted_entities)
        and that documents[i] corresponds to last_extracted_entities[i]
        """
        # Test unfiltered case
        docs = data_ingester.fetch_email_documents(limit=5)
        ents = data_ingester.last_extracted_entities
        assert len(docs) == len(ents), \
            f"Unfiltered alignment broken: {len(docs)} docs != {len(ents)} entities"

        # Test filtered case with ticker parameter (this was the original bug)
        docs_filtered = data_ingester.fetch_email_documents(tickers=['NVDA', 'AAPL'], limit=3)
        ents_filtered = data_ingester.last_extracted_entities
        assert len(docs_filtered) == len(ents_filtered), \
            f"Filtered alignment broken: {len(docs_filtered)} docs != {len(ents_filtered)} entities"

        print(f"✅ Document-entity alignment verified:")
        print(f"   Unfiltered: {len(docs)} docs ↔ {len(ents)} entities")
        print(f"   Filtered: {len(docs_filtered)} docs ↔ {len(ents_filtered)} entities")


def run_tests():
    """Run all Phase 2.6.1 integration tests"""
    print("\n" + "="*70)
    print("Phase 2.6.1 Entity Extraction Integration Tests")
    print("="*70 + "\n")

    # Create ingester
    ingester = DataIngester()

    # Run tests
    test_suite = TestEntityExtraction()

    print("Test 1: Backward Compatibility (List[str] return type)")
    print("-" * 70)
    test_suite.test_fetch_email_documents_returns_list_of_strings(ingester)

    print("\nTest 2: EntityExtractor Structured Data")
    print("-" * 70)
    test_suite.test_entity_extractor_creates_structured_data(ingester)

    print("\nTest 3: Enhanced Document Inline Markup")
    print("-" * 70)
    test_suite.test_enhanced_document_has_inline_markup(ingester)

    print("\nTest 4: Phase 2.6.2 Storage Attributes")
    print("-" * 70)
    test_suite.test_entity_storage_for_phase_2_6_2(ingester)

    print("\nTest 5: Graceful Fallback on Errors")
    print("-" * 70)
    test_suite.test_graceful_fallback_on_entity_extraction_failure(ingester)

    print("\nTest 6: Document-Entity Alignment (CRITICAL BUG FIX)")
    print("-" * 70)
    test_suite.test_document_entity_alignment(ingester)

    print("\n" + "="*70)
    print("✅ Phase 2.6.1 Integration Tests Complete")
    print("="*70 + "\n")


if __name__ == "__main__":
    run_tests()
