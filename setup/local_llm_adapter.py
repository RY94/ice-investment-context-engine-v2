# setup/local_llm_adapter.py
# Local LLM integration adapters for ICE system
# Provides privacy-preserving local processing alternatives to OpenAI API
# RELEVANT FILES: src/ice_lightrag/ice_rag.py, CLAUDE.md, setup/local_llm_setup.py

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import requests
import json


class LocalLLMAdapter(ABC):
    """Abstract base for local LLM integrations"""
    
    @abstractmethod
    def query(self, prompt: str, **kwargs) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def health_check(self) -> bool:
        pass


class OllamaAdapter(LocalLLMAdapter):
    """Ollama local LLM adapter for privacy-preserving processing"""
    
    def __init__(self, base_url: str = "http://localhost:11434", 
                 model: str = "llama3:8b"):
        self.base_url = base_url
        self.model = model
        
    def query(self, prompt: str, **kwargs) -> Dict[str, Any]:
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": kwargs.get("temperature", 0.7),
                    "top_p": kwargs.get("top_p", 0.9),
                    "max_tokens": kwargs.get("max_tokens", 2000)
                }
            }
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=kwargs.get("timeout", 30)
            )
            response.raise_for_status()
            
            result = response.json()
            return {
                "content": result.get("response", ""),
                "model": self.model,
                "usage": {
                    "prompt_tokens": result.get("prompt_eval_count", 0),
                    "completion_tokens": result.get("eval_count", 0),
                    "total_tokens": result.get("prompt_eval_count", 0) + result.get("eval_count", 0)
                }
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "content": None,
                "model": self.model
            }
    
    def health_check(self) -> bool:
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False


class TextGenerationWebUIAdapter(LocalLLMAdapter):
    """Adapter for text-generation-webui local deployment"""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
    
    def query(self, prompt: str, **kwargs) -> Dict[str, Any]:
        payload = {
            'prompt': prompt,
            'max_new_tokens': kwargs.get('max_tokens', 2000),
            'temperature': kwargs.get('temperature', 0.7),
            'top_p': kwargs.get('top_p', 0.9),
            'do_sample': True,
            'truncation_length': kwargs.get('context_length', 4096)
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/generate",
                json=payload,
                timeout=kwargs.get("timeout", 60)
            )
            response.raise_for_status()
            
            result = response.json()
            return {
                "content": result['results'][0]['text'],
                "model": "local-model",
                "usage": {"total_tokens": len(prompt.split()) + len(result['results'][0]['text'].split())}
            }
            
        except Exception as e:
            return {"error": str(e), "content": None, "model": "local-model"}
    
    def health_check(self) -> bool:
        try:
            response = requests.get(f"{self.base_url}/api/v1/model", timeout=5)
            return response.status_code == 200
        except:
            return False


# Enhanced ICE with local LLM support
class ICEWithLocalLLM:
    """ICE integration class supporting local LLM backends"""
    
    def __init__(self, working_dir="./storage", 
                 local_llm_adapter: Optional[LocalLLMAdapter] = None,
                 fallback_to_openai: bool = True):
        # Import ICELightRAG here to avoid circular imports
        from src.ice_lightrag.ice_rag import ICELightRAG
        
        self.ice_rag = ICELightRAG(working_dir)
        self.local_llm_adapter = local_llm_adapter
        self.fallback_to_openai = fallback_to_openai
        
    def query(self, query_text: str, **kwargs) -> Dict[str, Any]:
        """Query with local LLM preference and OpenAI fallback"""
        
        # Try local LLM first if available
        if self.local_llm_adapter and self.local_llm_adapter.health_check():
            # Use local LLM for processing
            result = self._query_with_local_llm(query_text, **kwargs)
            if not result.get('error'):
                result['source'] = 'local_llm'
                return result
            elif not self.fallback_to_openai:
                return result
        
        # Fallback to OpenAI if local fails or not available
        if self.fallback_to_openai:
            result = self.ice_rag.query(query_text, **kwargs)
            result['source'] = 'openai'
            return result
        
        return {"error": "No available LLM backend", "content": None}
    
    def _query_with_local_llm(self, query_text: str, **kwargs) -> Dict[str, Any]:
        """Process query using local LLM adapter"""
        # Create a prompt for the local LLM
        prompt = f"As an investment analyst, please analyze the following query: {query_text}"
        
        # Get response from local LLM
        llm_result = self.local_llm_adapter.query(prompt, **kwargs)
        
        if llm_result.get('error'):
            return llm_result
        
        # Format result to match ICE query format
        return {
            "answer": llm_result.get('content', ''),
            "sources": ["local_llm_processing"],
            "usage": llm_result.get('usage', {}),
            "model": llm_result.get('model', 'local'),
            "confidence": 0.8  # Default confidence for local processing
        }
    
    def add_document(self, content: str, doc_type: str = "document"):
        """Add document to knowledge base"""
        return self.ice_rag.add_document(content, doc_type)


def setup_local_llm_ice():
    """Setup ICE with local LLM integration"""
    
    # Option 1: Ollama setup
    ollama_adapter = OllamaAdapter(
        base_url="http://localhost:11434",
        model="llama3:8b"
    )
    
    # Option 2: Text-generation-webui setup  
    # webui_adapter = TextGenerationWebUIAdapter("http://localhost:5000")
    
    # Initialize ICE with local LLM
    ice_with_local = ICEWithLocalLLM(
        local_llm_adapter=ollama_adapter,
        fallback_to_openai=True
    )
    
    return ice_with_local


def test_local_llm_integration():
    """Test local LLM integration with ICE"""
    
    # Test Ollama connection
    adapter = OllamaAdapter()
    if adapter.health_check():
        print('✅ Ollama connection successful')
        
        # Test ICE with local LLM
        ice_local = ICEWithLocalLLM(local_llm_adapter=adapter)
        result = ice_local.query('What are the key risks for NVDA?')
        
        if result.get('source') == 'local_llm':
            print('✅ ICE successfully using local LLM')
            print(f'Response: {result.get("answer", "N/A")[:100]}...')
        else:
            print('⚠️  ICE fell back to OpenAI API')
    else:
        print('❌ Ollama connection failed')


def basic_usage_examples():
    """
    Basic usage examples for local LLM integration with ICE
    
    This function demonstrates the two main ways to set up and use
    local LLM integration with the ICE system.
    """
    print("=== ICE Local LLM Basic Usage Examples ===\n")
    
    # Example 1: Quick setup with defaults
    print("1. Quick setup with defaults:")
    print("   ice_with_local = setup_local_llm_ice()")
    ice_with_local = setup_local_llm_ice()
    
    # Example 2: Custom setup
    print("\n2. Custom setup:")
    print("   ollama_adapter = OllamaAdapter(model='llama3:8b')")
    print("   ice_local = ICEWithLocalLLM(local_llm_adapter=ollama_adapter, fallback_to_openai=True)")
    
    ollama_adapter = OllamaAdapter(model="llama3:8b")
    ice_local = ICEWithLocalLLM(
        local_llm_adapter=ollama_adapter,
        fallback_to_openai=True
    )
    
    # Example 3: Query with local LLM preference
    print("\n3. Query with local LLM preference:")
    print("   result = ice_local.query('What are NVDA's key risks?')")
    print("   print(f'Processed with: {result.get(\"source\")}')")
    
    # Actually run a test query if Ollama is available
    if ollama_adapter.health_check():
        print("\n   Running live example...")
        result = ice_local.query("What are NVDA's key risks?")
        print(f"   ✅ Processed with: {result.get('source', 'unknown')}")
        print(f"   Response preview: {str(result.get('answer', ''))[:100]}...")
    else:
        print("\n   ⚠️  Ollama not available - example would fallback to OpenAI")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "examples":
        # Run usage examples
        basic_usage_examples()
    else:
        # Run basic integration test
        test_local_llm_integration()