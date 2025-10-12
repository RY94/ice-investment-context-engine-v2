# lightrag/test_basic.py
"""
Basic test for ICE LightRAG integration
Simple test to verify everything works
Includes model provider selection tests (OpenAI vs Ollama)
"""

import os
import sys
from unittest.mock import patch
from ice_rag import SimpleICERAG

# Add model_provider for testing
try:
    from model_provider import get_llm_provider, check_ollama_service
    MODEL_PROVIDER_AVAILABLE = True
except ImportError:
    MODEL_PROVIDER_AVAILABLE = False


def test_basic_functionality():
    """Test basic LightRAG functionality"""
    print("🧪 Testing ICE LightRAG integration...")
    
    # Initialize system
    rag = SimpleICERAG()
    
    if not rag.is_ready():
        print("❌ LightRAG not ready. Check installation and API key.")
        return False
    
    print("✅ LightRAG system initialized")
    
    # Test document processing
    sample_doc = """
    Apple Inc. (AAPL) reported strong Q4 2023 results with iPhone revenue of $43.8 billion.
    The company faces challenges in China market due to increased competition.
    Services revenue grew to $22.3 billion, showing strong recurring revenue growth.
    """
    
    print("📄 Testing document processing...")
    result = rag.add_document(sample_doc, "earnings_report")
    
    if result["status"] != "success":
        print(f"❌ Document processing failed: {result['message']}")
        return False
    
    print("✅ Document processed successfully")
    
    # Test querying
    print("❓ Testing query functionality...")
    result = rag.query("What challenges does Apple face in China?")
    
    if result["status"] != "success":
        print(f"❌ Query failed: {result['message']}")
        return False
    
    print("✅ Query successful")
    print(f"📝 Answer: {result['result'][:200]}...")
    
    return True


def test_provider_selection_openai():
    """Test default OpenAI provider selection"""
    if not MODEL_PROVIDER_AVAILABLE:
        print("⚠️  Skipping provider tests - model_provider not available")
        return True

    print("\n🧪 Testing OpenAI provider selection...")

    # Save original env vars
    original_provider = os.getenv("LLM_PROVIDER")

    try:
        # Set OpenAI as provider (or use default)
        os.environ.pop("LLM_PROVIDER", None)

        llm_func, embed_func, model_config = get_llm_provider()

        # Verify OpenAI provider selected
        assert model_config == {}, f"Expected empty config for OpenAI, got: {model_config}"
        assert llm_func is not None, "LLM function should not be None"
        assert embed_func is not None, "Embed function should not be None"

        print("✅ OpenAI provider selected correctly")
        return True

    except Exception as e:
        print(f"❌ OpenAI provider test failed: {e}")
        return False
    finally:
        # Restore env vars
        if original_provider:
            os.environ["LLM_PROVIDER"] = original_provider


def test_provider_selection_ollama_mock():
    """Test Ollama provider selection with mocked health check"""
    if not MODEL_PROVIDER_AVAILABLE:
        print("⚠️  Skipping provider tests - model_provider not available")
        return True

    print("\n🧪 Testing Ollama provider selection (mocked)...")

    # Save original env vars
    original_provider = os.getenv("LLM_PROVIDER")
    original_model = os.getenv("LLM_MODEL")

    try:
        # Mock Ollama availability
        with patch('model_provider.check_ollama_service', return_value=True), \
             patch('model_provider.check_ollama_model_available', return_value=True):

            os.environ["LLM_PROVIDER"] = "ollama"
            os.environ["LLM_MODEL"] = "qwen3:30b-32k"

            llm_func, embed_func, model_config = get_llm_provider()

            # Verify Ollama provider selected
            assert "llm_model_name" in model_config, "Model config should have llm_model_name"
            assert model_config["llm_model_name"] == "qwen3:30b-32k", f"Expected qwen3:30b-32k, got: {model_config['llm_model_name']}"
            assert "llm_model_kwargs" in model_config, "Model config should have llm_model_kwargs"

            print(f"✅ Ollama provider selected: {model_config['llm_model_name']}")
            return True

    except Exception as e:
        print(f"❌ Ollama provider test failed: {e}")
        return False
    finally:
        # Restore env vars
        os.environ.pop("LLM_PROVIDER", None)
        os.environ.pop("LLM_MODEL", None)
        if original_provider:
            os.environ["LLM_PROVIDER"] = original_provider
        if original_model:
            os.environ["LLM_MODEL"] = original_model


def test_provider_fallback():
    """Test fallback from unavailable Ollama to OpenAI"""
    if not MODEL_PROVIDER_AVAILABLE:
        print("⚠️  Skipping provider tests - model_provider not available")
        return True

    print("\n🧪 Testing Ollama → OpenAI fallback...")

    # Save original env vars
    original_provider = os.getenv("LLM_PROVIDER")

    try:
        # Mock Ollama as unavailable
        with patch('model_provider.check_ollama_service', return_value=False):
            os.environ["LLM_PROVIDER"] = "ollama"

            llm_func, embed_func, model_config = get_llm_provider()

            # Should fall back to OpenAI (empty config)
            assert model_config == {}, f"Expected OpenAI fallback (empty config), got: {model_config}"

            print("✅ Fallback to OpenAI successful")
            return True

    except Exception as e:
        print(f"❌ Fallback test failed: {e}")
        return False
    finally:
        # Restore env vars
        os.environ.pop("LLM_PROVIDER", None)
        if original_provider:
            os.environ["LLM_PROVIDER"] = original_provider


def main():
    """Main test function"""
    # Check environment
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  Warning: OPENAI_API_KEY not set")
        print("Set it with: export OPENAI_API_KEY='your-key-here'")
        return

    # Run model provider tests
    provider_tests_passed = True
    if MODEL_PROVIDER_AVAILABLE:
        print("\n" + "="*60)
        print("MODEL PROVIDER TESTS")
        print("="*60)
        provider_tests_passed = all([
            test_provider_selection_openai(),
            test_provider_selection_ollama_mock(),
            test_provider_fallback()
        ])

    # Run basic functionality test
    print("\n" + "="*60)
    print("BASIC FUNCTIONALITY TEST")
    print("="*60)
    basic_test_passed = test_basic_functionality()

    # Summary
    print("\n" + "="*60)
    if basic_test_passed and provider_tests_passed:
        print("🎉 All tests passed! LightRAG is ready for use.")
    else:
        print("❌ Some tests failed. Check the errors above.")


if __name__ == "__main__":
    main()
