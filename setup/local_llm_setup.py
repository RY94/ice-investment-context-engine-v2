# setup/local_llm_setup.py
# Complete local LLM setup and testing utilities for ICE system
# Provides installation, configuration, and benchmarking tools for local LLM backends
# RELEVANT FILES: setup/local_llm_adapter.py, CLAUDE.md, src/ice_lightrag/ice_rag.py

import subprocess
import sys
import time
import os
from typing import List, Dict, Any
from local_llm_adapter import OllamaAdapter, TextGenerationWebUIAdapter, ICEWithLocalLLM


class LocalLLMSetup:
    """Complete local LLM setup and management utilities"""
    
    def __init__(self):
        self.ollama_adapter = None
        self.webui_adapter = None
    
    def install_ollama(self) -> bool:
        """Install Ollama local LLM system"""
        print("📦 Installing Ollama...")
        
        try:
            # Download and install Ollama
            subprocess.run(
                ["curl", "-fsSL", "https://ollama.ai/install.sh"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True
            )
            
            # Download recommended model
            print("⬇️  Downloading recommended model (llama3:8b)...")
            subprocess.run(
                ["ollama", "pull", "llama3:8b"],
                check=True
            )
            
            # Start Ollama service
            print("🚀 Starting Ollama service...")
            process = subprocess.Popen(["ollama", "serve"])
            
            print(f"✅ Ollama installed and running (PID: {process.pid})")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Ollama installation failed: {e}")
            return False
        except FileNotFoundError:
            print("❌ curl not found. Please install curl first.")
            return False
    
    def install_text_generation_webui(self) -> bool:
        """Install text-generation-webui local LLM system"""
        print("📦 Setting up text-generation-webui...")
        
        try:
            # Clone repository
            subprocess.run([
                "git", "clone", 
                "https://github.com/oobabooga/text-generation-webui.git"
            ], check=True)
            
            # Change to directory
            os.chdir("text-generation-webui")
            
            # Install dependencies
            subprocess.run([
                sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
            ], check=True)
            
            # Download a model (example: DialoGPT-medium)
            subprocess.run([
                sys.executable, "download-model.py", "microsoft/DialoGPT-medium"
            ], check=True)
            
            print("✅ Text-generation-webui ready")
            print("🚀 Start with: python server.py --api --listen")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Text-generation-webui installation failed: {e}")
            return False
    
    def test_local_llm_integration(self) -> Dict[str, bool]:
        """Test ICE + Local LLM integration"""
        print("🧪 Testing ICE + Local LLM integration...")
        
        results = {
            'ollama_connection': False,
            'ice_local_integration': False
        }
        
        # Test Ollama connection
        adapter = OllamaAdapter()
        if adapter.health_check():
            print('✅ Ollama connection successful')
            results['ollama_connection'] = True
            
            # Test ICE with local LLM
            try:
                ice_local = ICEWithLocalLLM(local_llm_adapter=adapter)
                result = ice_local.query('Test query for local LLM')
                
                if result.get('source') == 'local_llm':
                    print('✅ ICE successfully using local LLM')
                    print(f'Response: {result.get("answer", "N/A")[:100]}...')
                    results['ice_local_integration'] = True
                else:
                    print('⚠️  ICE fell back to OpenAI API')
                    
            except Exception as e:
                print(f'❌ ICE integration test failed: {e}')
        else:
            print('❌ Ollama connection failed')
        
        return results
    
    def benchmark_local_vs_remote(self) -> Dict[str, Any]:
        """Benchmark Local LLM vs OpenAI performance"""
        print("⚡ Benchmarking Local LLM vs OpenAI performance...")
        
        test_queries = [
            'What are the key risks for NVDA?',
            'How does supply chain affect semiconductor stocks?',
            'What companies are exposed to China risk?'
        ]
        
        # Setup adapters
        adapter = OllamaAdapter()
        ice_local = ICEWithLocalLLM(local_llm_adapter=adapter, fallback_to_openai=False)
        
        # Import ICE for OpenAI comparison
        try:
            from src.ice_lightrag.ice_rag import ICELightRAG
            ice_openai = ICELightRAG()
        except ImportError:
            print("❌ ICELightRAG not available for comparison")
            return {}
        
        benchmark_results = []
        print('Query,Local_Time_ms,Local_Tokens,OpenAI_Time_ms,OpenAI_Tokens')
        
        for query in test_queries:
            result = {
                'query': query,
                'local_time_ms': 0,
                'local_tokens': 0,
                'openai_time_ms': 0,
                'openai_tokens': 0
            }
            
            # Local LLM timing
            if adapter.health_check():
                start = time.time()
                local_result = ice_local.query(query)
                result['local_time_ms'] = (time.time() - start) * 1000
                result['local_tokens'] = local_result.get('usage', {}).get('total_tokens', 0)
            
            # OpenAI timing
            try:
                start = time.time()
                openai_result = ice_openai.query(query)
                result['openai_time_ms'] = (time.time() - start) * 1000
                result['openai_tokens'] = openai_result.get('usage', {}).get('total_tokens', 0)
            except Exception as e:
                print(f"OpenAI query failed: {e}")
            
            benchmark_results.append(result)
            print(f"{query},{result['local_time_ms']:.0f},{result['local_tokens']},"
                  f"{result['openai_time_ms']:.0f},{result['openai_tokens']}")
        
        return {
            'results': benchmark_results,
            'summary': self._analyze_benchmark_results(benchmark_results)
        }
    
    def _analyze_benchmark_results(self, results: List[Dict]) -> Dict[str, Any]:
        """Analyze benchmark results and provide insights"""
        if not results:
            return {}
        
        local_avg_time = sum(r['local_time_ms'] for r in results) / len(results)
        openai_avg_time = sum(r['openai_time_ms'] for r in results) / len(results)
        
        local_total_tokens = sum(r['local_tokens'] for r in results)
        openai_total_tokens = sum(r['openai_tokens'] for r in results)
        
        return {
            'local_avg_time_ms': local_avg_time,
            'openai_avg_time_ms': openai_avg_time,
            'local_total_tokens': local_total_tokens,
            'openai_total_tokens': openai_total_tokens,
            'time_difference_pct': ((openai_avg_time - local_avg_time) / openai_avg_time * 100) if openai_avg_time > 0 else 0,
            'recommendation': 'local' if local_avg_time < openai_avg_time else 'openai'
        }
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive local LLM system status"""
        status = {
            'timestamp': time.time(),
            'ollama': {
                'available': False,
                'models': [],
                'health': False
            },
            'webui': {
                'available': False,
                'health': False
            }
        }
        
        # Check Ollama
        try:
            ollama_adapter = OllamaAdapter()
            status['ollama']['health'] = ollama_adapter.health_check()
            status['ollama']['available'] = True
        except Exception:
            pass
        
        # Check text-generation-webui
        try:
            webui_adapter = TextGenerationWebUIAdapter()
            status['webui']['health'] = webui_adapter.health_check()
            status['webui']['available'] = True
        except Exception:
            pass
        
        return status


def main():
    """Main CLI interface for local LLM setup"""
    import argparse
    
    parser = argparse.ArgumentParser(description='ICE Local LLM Setup Utility')
    parser.add_argument('command', choices=['ollama', 'webui', 'test', 'benchmark', 'status'],
                       help='Command to execute')
    
    args = parser.parse_args()
    setup = LocalLLMSetup()
    
    if args.command == 'ollama':
        success = setup.install_ollama()
        if success:
            setup.test_local_llm_integration()
    
    elif args.command == 'webui':
        setup.install_text_generation_webui()
    
    elif args.command == 'test':
        results = setup.test_local_llm_integration()
        print(f"\nTest Results: {results}")
    
    elif args.command == 'benchmark':
        benchmark = setup.benchmark_local_vs_remote()
        if benchmark:
            print(f"\nBenchmark Summary: {benchmark.get('summary', {})}")
    
    elif args.command == 'status':
        status = setup.get_system_status()
        print(f"\nSystem Status:")
        print(f"Ollama: {'✅' if status['ollama']['health'] else '❌'} "
              f"(Available: {status['ollama']['available']})")
        print(f"WebUI: {'✅' if status['webui']['health'] else '❌'} "
              f"(Available: {status['webui']['available']})")


if __name__ == "__main__":
    main()