# Location: /tests/test_phase_2_8_config_propagation.py
# Purpose: Verify Phase 2.8 confidence config centralization and propagation
# Why: Ensure 3 core modules (relationship_extractor, ice_query_processor, ice_graph_builder)
#      properly use centralized CONFIDENCE_DEFAULTS and CONFIDENCE_WEIGHTS
# Relevant Files: updated_architectures/implementation/config.py, src/ice_core/*.py

"""
Phase 2.8 Config Propagation Integration Tests

Tests verify:
1. Centralized config has all required keys
2. Core modules import config without errors
3. get_confidence() returns expected values
4. CONFIDENCE_WEIGHTS is properly shared
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

import pytest


class TestConfigCentralization:
    """Test the centralized config structure"""

    def test_confidence_defaults_exists(self):
        """CONFIDENCE_DEFAULTS dict should exist with required keys"""
        from updated_architectures.implementation.config import CONFIDENCE_DEFAULTS

        assert isinstance(CONFIDENCE_DEFAULTS, dict)
        assert len(CONFIDENCE_DEFAULTS) >= 40, "Should have 40+ confidence keys"

    def test_relationship_extraction_keys(self):
        """Relationship extraction keys should be present"""
        from updated_architectures.implementation.config import CONFIDENCE_DEFAULTS

        required_keys = [
            'relationship_base', 'relationship_competitive', 'relationship_supplier',
            'relationship_employment', 'relationship_portfolio', 'relationship_event_close',
            'relationship_event_distant', 'relationship_category'
        ]
        for key in required_keys:
            assert key in CONFIDENCE_DEFAULTS, f"Missing key: {key}"

    def test_query_processing_keys(self):
        """Query processing keys should be present"""
        from updated_architectures.implementation.config import CONFIDENCE_DEFAULTS

        required_keys = [
            'lightrag_base', 'query_min_threshold', 'confidence_cap',
            'confidence_floor', 'no_sources', 'single_source',
            'chunk_default', 'path_default'
        ]
        for key in required_keys:
            assert key in CONFIDENCE_DEFAULTS, f"Missing key: {key}"

    def test_graph_building_keys(self):
        """Graph building keys should be present"""
        from updated_architectures.implementation.config import CONFIDENCE_DEFAULTS

        required_keys = [
            'edge_default', 'ui_min_threshold', 'boost_financial_term',
            'boost_source_verified', 'penalty_ambiguous'
        ]
        for key in required_keys:
            assert key in CONFIDENCE_DEFAULTS, f"Missing key: {key}"

    def test_pattern_confidence_keys(self):
        """Relationship pattern confidence keys should be present"""
        from updated_architectures.implementation.config import CONFIDENCE_DEFAULTS

        required_keys = [
            'pattern_depends_on', 'pattern_supplies', 'pattern_exposed_to',
            'pattern_drives', 'pattern_impacts', 'pattern_competes_with',
            'pattern_owns', 'pattern_operates_in', 'pattern_manufactures_in'
        ]
        for key in required_keys:
            assert key in CONFIDENCE_DEFAULTS, f"Missing key: {key}"

    def test_confidence_weights_exists(self):
        """CONFIDENCE_WEIGHTS dict should exist with required keys"""
        from updated_architectures.implementation.config import CONFIDENCE_WEIGHTS

        assert isinstance(CONFIDENCE_WEIGHTS, dict)
        required_keys = [
            'source_reliability', 'relationship_clarity', 'evidence_strength',
            'base_weight', 'path_weight'
        ]
        for key in required_keys:
            assert key in CONFIDENCE_WEIGHTS, f"Missing key: {key}"

    def test_weights_sum_to_valid_values(self):
        """Weight groups should sum appropriately"""
        from updated_architectures.implementation.config import CONFIDENCE_WEIGHTS

        # Base + path weights should sum to 1.0
        base_path_sum = CONFIDENCE_WEIGHTS['base_weight'] + CONFIDENCE_WEIGHTS['path_weight']
        assert abs(base_path_sum - 1.0) < 0.01, f"base_weight + path_weight should = 1.0, got {base_path_sum}"

        # Source weights should sum to 1.0
        source_sum = (CONFIDENCE_WEIGHTS['source_reliability'] +
                      CONFIDENCE_WEIGHTS['relationship_clarity'] +
                      CONFIDENCE_WEIGHTS['evidence_strength'])
        assert abs(source_sum - 1.0) < 0.01, f"Source weights should = 1.0, got {source_sum}"


class TestAccessorFunctions:
    """Test the config accessor functions"""

    def test_get_confidence_returns_value(self):
        """get_confidence should return correct values"""
        from updated_architectures.implementation.config import get_confidence

        assert get_confidence('lightrag_base') == 0.7
        assert get_confidence('confidence_cap') == 0.95
        assert get_confidence('confidence_floor') == 0.1

    def test_get_confidence_with_default(self):
        """get_confidence should use default for unknown keys"""
        from updated_architectures.implementation.config import get_confidence

        result = get_confidence('nonexistent_key', 0.42)
        assert result == 0.42

    def test_get_confidence_fallback_to_source_default(self):
        """get_confidence should fallback to source_default when no default provided"""
        from updated_architectures.implementation.config import get_confidence, CONFIDENCE_DEFAULTS

        result = get_confidence('nonexistent_key_xyz')
        assert result == CONFIDENCE_DEFAULTS['source_default']

    def test_get_confidence_weight_returns_value(self):
        """get_confidence_weight should return correct values"""
        from updated_architectures.implementation.config import get_confidence_weight

        assert get_confidence_weight('base_weight') == 0.6
        assert get_confidence_weight('path_weight') == 0.4

    def test_get_source_confidence_returns_value(self):
        """get_source_confidence should return correct multipliers"""
        from updated_architectures.implementation.config import get_source_confidence

        assert get_source_confidence('sec_edgar') == 1.0
        assert get_source_confidence('unknown') == 0.5
        assert get_source_confidence('nonexistent') == 0.5  # Falls back to unknown


class TestModuleImports:
    """Test that core modules import config correctly"""

    def test_relationship_extractor_import(self):
        """relationship_extractor should import without errors"""
        try:
            from src.ice_core.relationship_extractor import RelationshipExtractor, Relationship
            assert RelationshipExtractor is not None
            assert Relationship is not None
        except ImportError as e:
            pytest.fail(f"Failed to import relationship_extractor: {e}")

    def test_ice_query_processor_import(self):
        """ice_query_processor should import without errors"""
        try:
            from src.ice_core.ice_query_processor import ICEQueryProcessor
            assert ICEQueryProcessor is not None
        except ImportError as e:
            pytest.fail(f"Failed to import ice_query_processor: {e}")

    def test_ice_graph_builder_import(self):
        """ice_graph_builder should import without errors"""
        try:
            from src.ice_core.ice_graph_builder import ICEGraphBuilder
            assert ICEGraphBuilder is not None
        except ImportError as e:
            pytest.fail(f"Failed to import ice_graph_builder: {e}")


class TestConfigPropagation:
    """Test that config values propagate to modules"""

    def test_graph_builder_uses_weights(self):
        """ICEGraphBuilder should use centralized CONFIDENCE_WEIGHTS"""
        from src.ice_core.ice_graph_builder import ICEGraphBuilder
        from updated_architectures.implementation.config import CONFIDENCE_WEIGHTS

        builder = ICEGraphBuilder()
        assert builder.confidence_weights == CONFIDENCE_WEIGHTS

    def test_query_processor_threshold(self):
        """ICEQueryProcessor should use centralized min_confidence_threshold"""
        from src.ice_core.ice_query_processor import ICEQueryProcessor
        from updated_architectures.implementation.config import get_confidence

        processor = ICEQueryProcessor()
        expected = get_confidence('query_min_threshold')
        assert processor.min_confidence_threshold == expected


class TestValueRanges:
    """Test that all confidence values are in valid ranges"""

    def test_all_confidence_values_in_range(self):
        """All CONFIDENCE_DEFAULTS values should be 0.0-1.0"""
        from updated_architectures.implementation.config import CONFIDENCE_DEFAULTS

        for key, value in CONFIDENCE_DEFAULTS.items():
            assert 0.0 <= value <= 1.0, f"{key}={value} out of range [0,1]"

    def test_all_weight_values_in_range(self):
        """All CONFIDENCE_WEIGHTS values should be 0.0-1.0"""
        from updated_architectures.implementation.config import CONFIDENCE_WEIGHTS

        for key, value in CONFIDENCE_WEIGHTS.items():
            assert 0.0 <= value <= 1.0, f"{key}={value} out of range [0,1]"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
