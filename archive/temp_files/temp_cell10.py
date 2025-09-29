# Streamlined ICE RAG System Initialization
def initialize_ice_system():
    """Streamlined initialization with smart fallback handling"""
    print("🚀 Initializing ICE Development System...")
    
    # Try unified RAG first (preferred)
    try:
        from ice_unified_rag import ICEUnifiedRAG
        
        class ICEDevelopment:
            """Enhanced development wrapper with unified RAG support"""
            
            def __init__(self):
                self.unified_rag = ICEUnifiedRAG(
                    default_engine=Config.DEFAULT_RAG_ENGINE,
                    working_dir=Config.UNIFIED_STORAGE_DIR
                )
                self.graph = ice_graph
                self.query_history = []
                self._log_initialization()
            
            def _log_initialization(self):
                """Log initialization status in batch-friendly way"""
                if should_display_widgets():
                    print("✅ ICE Development system initialized with Unified RAG")
                    print(f"📊 Available RAG engines: {list(self.unified_rag.get_available_engines().keys())}")
                    for engine, info in self.unified_rag.get_available_engines().items():
                        status = "✅" if info.available else "❌"
                        print(f"  {status} {info.name}: {info.description}")
                else:
                    # Compact batch mode logging
                    available_engines = [name for name, info in self.unified_rag.get_available_engines().items() if info.available]
                    print(f"✅ ICE system initialized (engines: {', '.join(available_engines)})")
            
            def query(self, question, mode="hybrid", **kwargs):
                """Query with unified RAG interface"""
                result = self.unified_rag.query(question, mode, **kwargs)
                self.query_history.append({
                    "question": question,
                    "mode": mode, 
                    "result": result,
                    "timestamp": time.time()
                })
                return result
            
            def get_stats(self):
                """Get comprehensive system stats"""
                return {
                    **self.unified_rag.get_stats(),
                    "graph_nodes": len(self.graph.G.nodes()),
                    "graph_edges": len(self.graph.G.edges()),
                    "query_history_count": len(self.query_history)
                }
            
            def switch_engine(self, engine_name):
                """Switch RAG engine"""
                return self.unified_rag.set_engine(engine_name)
            
            def add_document(self, text, doc_type="financial"):
                """Add document to current RAG engine"""
                return self.unified_rag.add_document(text, doc_type)
            
            def add_edges(self, edge_data):
                """Add edge data to LazyRAG (if active)"""
                return self.unified_rag.add_edges_from_data(edge_data)
        
        return ICEDevelopment()
        
    except ImportError:
        print("⚠️ Unified RAG unavailable, using fallback system")
        return _create_fallback_system()

def _create_fallback_system():
    """Create fallback system when unified RAG unavailable"""
    class ICEFallback:
        """Fallback system with individual engine support"""
        
        def __init__(self):
            self.graph = ice_graph
            self.query_history = []
            self.engines = {"lightrag": None, "lazyrag": None}
            self.current_engine = "mock"
            
            # Try individual engines
            self._try_lightrag()
            self._try_lazyrag()
            
            if not any(self.engines.values()):
                print("⚠️ No RAG engines available - using mock system")
            else:
                active = [k for k, v in self.engines.items() if v]
                self.current_engine = active[0] if active else "mock"
                print(f"✅ Fallback system ready (engines: {', '.join(active)})")
        
        def _try_lightrag(self):
            try:
                from ice_rag import ICELightRAG
                self.engines["lightrag"] = ICELightRAG(working_dir=Config.LIGHTRAG_STORAGE_DIR)
            except ImportError:
                pass
        
        def _try_lazyrag(self):
            try:
                from ice_lazyrag.lazy_rag import SimpleLazyRAG
                self.engines["lazyrag"] = SimpleLazyRAG(working_dir=Config.LAZYRAG_STORAGE_DIR)
            except ImportError:
                pass
        
        def query(self, question, mode="hybrid"):
            """Query with available engine"""
            if self.engines["lightrag"]:
                result = self.engines["lightrag"].query(question)
            elif self.engines["lazyrag"]:
                result = self.engines["lazyrag"].query(question, mode)
            else:
                result = f"Mock response: {question}\n\n[No RAG engines available]"
            
            self.query_history.append({
                "question": question,
                "result": result,
                "engine": self.current_engine,
                "timestamp": time.time()
            })
            return result
    
    return ICEFallback()

# Initialize system - make ice globally available
ice = initialize_ice_system()
print(f"✅ ICE system initialized with {type(ice).__name__}")

# Verify ice is accessible
if hasattr(ice, 'query'):
    print("📋 ICE query interface ready")
else:
    print("⚠️ ICE query interface not available")