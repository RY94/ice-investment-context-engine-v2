# setup/development_workflows.py
# Advanced development workflow utilities and patterns for ICE system
# Provides rapid prototyping, hot-reload, and debugging tools for power users
# RELEVANT FILES: CLAUDE.md, src/ice_lightrag/ice_rag.py, setup/architecture_patterns.py

import importlib
import sys
import subprocess
import time
import functools
import cProfile
import pstats
import json
from typing import Any, Dict


class DevelopmentWorkflows:
    """Advanced development utilities for ICE power users"""
    
    def __init__(self):
        self.project_root = "/Users/royyeo/Library/CloudStorage/OneDrive-NationalUniversityofSingapore/Capstone Project"
    
    def create_ui_iteration(self, version: int = None) -> str:
        """Create new UI iteration for rapid prototyping"""
        if version is None:
            version = self._get_next_ui_version()
        
        source_file = f"UI/ice_ui_v17.py"
        target_file = f"UI/ice_ui_v{version}.py"
        
        try:
            subprocess.run(["cp", source_file, target_file], check=True)
            print(f"✅ Created new UI iteration: {target_file}")
            print(f"🚀 Test with: streamlit run {target_file} --server.port {8500 + version}")
            return target_file
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to create UI iteration: {e}")
            return ""
    
    def _get_next_ui_version(self) -> int:
        """Get the next available UI version number"""
        import glob
        existing_files = glob.glob("UI/ice_ui_v*.py")
        versions = []
        for file in existing_files:
            try:
                version = int(file.split('_v')[-1].split('.py')[0])
                versions.append(version)
            except ValueError:
                continue
        return max(versions, default=17) + 1
    
    def hot_reload_module(self, module_name: str) -> bool:
        """Hot-reload a Python module during development"""
        try:
            if module_name in sys.modules:
                importlib.reload(sys.modules[module_name])
                print(f"🔄 Reloaded {module_name}")
                return True
            else:
                print(f"❌ Module {module_name} not found in sys.modules")
                return False
        except Exception as e:
            print(f"❌ Failed to reload {module_name}: {e}")
            return False
    
    def validate_ui_import(self, ui_file: str) -> bool:
        """Validate that a UI file can be imported successfully"""
        try:
            module_path = ui_file.replace("/", ".").replace(".py", "")
            exec(f"from {module_path} import *")
            print(f"✅ Import successful for {ui_file}")
            return True
        except Exception as e:
            print(f"❌ Import failed for {ui_file}: {e}")
            return False


class ICEDebugger:
    """Advanced debugging utilities for ICE system"""
    
    def __init__(self, ice_rag=None):
        self.ice_rag = ice_rag
    
    def enable_lightrag_debug_mode(self, working_dir="./src/ice_lightrag/storage"):
        """Enable debug mode for LightRAG with query introspection"""
        try:
            from src.ice_lightrag.ice_rag import ICELightRAG
            self.ice_rag = ICELightRAG(working_dir=working_dir, debug=True)
            print("🐛 LightRAG debug mode enabled")
            return self.ice_rag
        except ImportError as e:
            print(f"❌ Failed to import ICELightRAG: {e}")
            return None
    
    def query_with_trace(self, query: str, mode="hybrid", **kwargs) -> Dict[str, Any]:
        """Execute query with full execution trace"""
        if not self.ice_rag:
            print("❌ ICE RAG not initialized. Call enable_lightrag_debug_mode() first.")
            return {}
        
        try:
            result = self.ice_rag.query(query, mode=mode, trace=True, **kwargs)
            
            # Print execution analysis
            print(f"🔍 Query Analysis:")
            print(f"  Query: {query}")
            print(f"  Mode: {mode}")
            
            if result.get('execution_trace'):
                print(f"  Execution trace:")
                print(json.dumps(result['execution_trace'], indent=2))
            
            if result.get('token_count'):
                print(f"  Token usage: {result['token_count']}")
            
            if result.get('execution_time_ms'):
                print(f"  Query latency: {result['execution_time_ms']}ms")
            
            return result
            
        except Exception as e:
            print(f"❌ Query execution failed: {e}")
            return {"error": str(e)}
    
    def inspect_knowledge_graph(self) -> Dict[str, Any]:
        """Examine graph structure and health"""
        if not self.ice_rag:
            print("❌ ICE RAG not initialized")
            return {}
        
        try:
            stats = self.ice_rag.get_graph_statistics()
            
            print(f"📊 Graph Stats:")
            print(f"  • Entities: {stats.get('entity_count', 'N/A')}")
            print(f"  • Relationships: {stats.get('relationship_count', 'N/A')}")
            print(f"  • Orphaned entities: {stats.get('orphaned_entities', 'N/A')}")
            print(f"  • Average degree: {stats.get('avg_degree', 0):.2f}")
            print(f"  • Graph density: {stats.get('density', 0):.4f}")
            
            # Health analysis
            entity_count = stats.get('entity_count', 0)
            orphaned = stats.get('orphaned_entities', 0)
            density = stats.get('density', 0)
            
            if entity_count > 0 and orphaned > entity_count * 0.1:
                print("⚠️  High orphaned entity rate - consider relationship cleanup")
            
            if density < 0.001:
                print("⚠️  Very sparse graph - may impact query performance")
            
            return stats
            
        except Exception as e:
            print(f"❌ Failed to get graph statistics: {e}")
            return {"error": str(e)}


def profile_function(func):
    """Decorator for profiling individual functions"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        pr = cProfile.Profile()
        pr.enable()
        start_time = time.time()
        
        result = func(*args, **kwargs)
        
        end_time = time.time()
        pr.disable()
        
        # Print timing info
        execution_time = (end_time - start_time) * 1000
        print(f"⏱️  {func.__name__} executed in {execution_time:.2f}ms")
        
        # Print top 10 function calls
        stats = pstats.Stats(pr)
        stats.sort_stats('cumulative').print_stats(10)
        
        return result
    return wrapper


def main():
    """Interactive development workflow utility"""
    import argparse
    
    parser = argparse.ArgumentParser(description='ICE Development Workflow Utilities')
    parser.add_argument('command', choices=['new-ui', 'reload', 'debug', 'profile'],
                       help='Development command to execute')
    parser.add_argument('--module', help='Module name for reload command')
    parser.add_argument('--query', help='Query for debug command')
    parser.add_argument('--version', type=int, help='UI version number')
    
    args = parser.parse_args()
    
    workflows = DevelopmentWorkflows()
    
    if args.command == 'new-ui':
        workflows.create_ui_iteration(args.version)
    
    elif args.command == 'reload':
        if args.module:
            workflows.hot_reload_module(args.module)
        else:
            print("❌ --module required for reload command")
    
    elif args.command == 'debug':
        debugger = ICEDebugger()
        debugger.enable_lightrag_debug_mode()
        
        if args.query:
            debugger.query_with_trace(args.query)
        
        debugger.inspect_knowledge_graph()
    
    elif args.command == 'profile':
        print("🔍 Profile mode - use @profile_function decorator in your code")


if __name__ == "__main__":
    main()