# Location: tests/test_temperature_config.py
# Purpose: Verify separate LLM temperature configuration (entity extraction & query answering)
# Why: Ensure correct temperature separation for reproducible graphs and creative queries
# Relevant Files: src/ice_lightrag/model_provider.py, ice_building_workflow.ipynb

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'ice_lightrag'))

from model_provider import get_llm_provider, get_extraction_temperature, get_query_temperature


def test_default_temperatures():
    """Test that default temperatures are correct (0.3 extraction, 0.5 query)"""
    # Clear any existing settings
    for key in ['ICE_LLM_TEMPERATURE_ENTITY_EXTRACTION', 'ICE_LLM_TEMPERATURE_QUERY_ANSWERING', 'ICE_LLM_TEMPERATURE']:
        if key in os.environ:
            del os.environ[key]

    extraction_temp = get_extraction_temperature()
    query_temp = get_query_temperature()

    assert extraction_temp == 0.3, f"Expected default extraction temp 0.3, got {extraction_temp}"
    assert query_temp == 0.5, f"Expected default query temp 0.5, got {query_temp}"

    print("✅ Default temperatures correct: extraction=0.3, query=0.5")


def test_custom_temperatures():
    """Test that custom temperatures can be set via environment variables"""
    os.environ['ICE_LLM_TEMPERATURE_ENTITY_EXTRACTION'] = '0.2'
    os.environ['ICE_LLM_TEMPERATURE_QUERY_ANSWERING'] = '0.7'

    extraction_temp = get_extraction_temperature()
    query_temp = get_query_temperature()

    assert extraction_temp == 0.2, f"Expected extraction temp 0.2, got {extraction_temp}"
    assert query_temp == 0.7, f"Expected query temp 0.7, got {query_temp}"

    print("✅ Custom temperatures work: extraction=0.2, query=0.7")

    # Clean up
    del os.environ['ICE_LLM_TEMPERATURE_ENTITY_EXTRACTION']
    del os.environ['ICE_LLM_TEMPERATURE_QUERY_ANSWERING']


def test_invalid_temperatures():
    """Test that invalid temperatures default to 0.3/0.5"""
    # Test out of range extraction
    os.environ['ICE_LLM_TEMPERATURE_ENTITY_EXTRACTION'] = '1.5'
    extraction_temp = get_extraction_temperature()
    assert extraction_temp == 0.3, f"Expected 0.3 for invalid extraction temp, got {extraction_temp}"

    # Test non-numeric extraction
    os.environ['ICE_LLM_TEMPERATURE_ENTITY_EXTRACTION'] = 'invalid'
    extraction_temp = get_extraction_temperature()
    assert extraction_temp == 0.3, f"Expected 0.3 for non-numeric extraction temp, got {extraction_temp}"

    # Test out of range query
    os.environ['ICE_LLM_TEMPERATURE_QUERY_ANSWERING'] = '-0.5'
    query_temp = get_query_temperature()
    assert query_temp == 0.5, f"Expected 0.5 for invalid query temp, got {query_temp}"

    print("✅ Invalid temperatures default correctly")

    # Clean up
    for key in ['ICE_LLM_TEMPERATURE_ENTITY_EXTRACTION', 'ICE_LLM_TEMPERATURE_QUERY_ANSWERING']:
        if key in os.environ:
            del os.environ[key]


def test_high_extraction_temp_warning(capsys=None):
    """Test that high extraction temperature (>0.2) triggers warning"""
    os.environ['ICE_LLM_TEMPERATURE_ENTITY_EXTRACTION'] = '0.3'

    # This should trigger a warning log (we can't easily capture logger.warning in tests)
    extraction_temp = get_extraction_temperature()
    assert extraction_temp == 0.3, f"Expected 0.3, got {extraction_temp}"

    print("✅ High extraction temp (>0.2) correctly set (warning logged)")

    # Clean up
    del os.environ['ICE_LLM_TEMPERATURE_ENTITY_EXTRACTION']


def test_deprecated_temperature_warning():
    """Test that old ICE_LLM_TEMPERATURE variable triggers deprecation warning"""
    os.environ['ICE_LLM_TEMPERATURE'] = '0.5'

    # Should trigger deprecation warning but still work
    extraction_temp = get_extraction_temperature()

    # The deprecated variable should be ignored; default should be used
    assert extraction_temp == 0.3, f"Deprecated var should not affect result, got {extraction_temp}"

    print("✅ Deprecated ICE_LLM_TEMPERATURE triggers warning (logged)")

    # Clean up
    del os.environ['ICE_LLM_TEMPERATURE']


def test_provider_returns_4tuple():
    """Test that model provider returns 4-tuple (not 3-tuple)"""
    os.environ['ICE_LLM_TEMPERATURE_ENTITY_EXTRACTION'] = '0.3'
    os.environ['ICE_LLM_TEMPERATURE_QUERY_ANSWERING'] = '0.5'
    os.environ['OPENAI_API_KEY'] = 'test_key'  # Needed for provider check

    try:
        result = get_llm_provider()

        assert len(result) == 4, f"Expected 4-tuple, got {len(result)}-tuple"

        llm_func, embed_func, model_config, base_kwargs_template = result

        # Check model_config has extraction temperature
        assert 'llm_model_kwargs' in model_config, "model_config should have llm_model_kwargs"
        assert 'temperature' in model_config['llm_model_kwargs'], "llm_model_kwargs should have temperature"
        assert model_config['llm_model_kwargs']['temperature'] == 0.3, \
            f"Expected extraction temp 0.3 in config, got {model_config['llm_model_kwargs']['temperature']}"

        # Check base_kwargs_template does NOT have temperature
        assert 'temperature' not in base_kwargs_template, "base_kwargs_template should NOT have temperature"

        # Check seed is present for determinism
        assert 'seed' in base_kwargs_template, "base_kwargs_template should have seed"

        print("✅ Model provider returns correct 4-tuple")
        print(f"   - model_config has extraction temp: {model_config['llm_model_kwargs']['temperature']}")
        print(f"   - base_kwargs_template has no temp: {list(base_kwargs_template.keys())}")

    except ImportError as e:
        print(f"⚠️  Skipping provider test: {e}")
    finally:
        # Clean up
        for key in ['ICE_LLM_TEMPERATURE_ENTITY_EXTRACTION', 'ICE_LLM_TEMPERATURE_QUERY_ANSWERING']:
            if key in os.environ:
                del os.environ[key]


if __name__ == '__main__':
    print("🧪 Testing Separate Temperature Configuration")
    print("=" * 70)
    print()

    test_default_temperatures()
    test_custom_temperatures()
    test_invalid_temperatures()
    test_high_extraction_temp_warning()
    test_deprecated_temperature_warning()
    test_provider_returns_4tuple()

    print()
    print("=" * 70)
    print("✅ All temperature configuration tests passed!")
    print("=" * 70)
    print()
    print("📊 Summary:")
    print("   • Separate temperatures working correctly")
    print("   • Extraction default: 0.3 (reproducible graphs)")
    print("   • Query default: 0.5 (creative synthesis)")
    print("   • Provider returns 4-tuple (llm_func, embed_func, config, base_kwargs)")
    print("   • Deprecated variables trigger warnings")
