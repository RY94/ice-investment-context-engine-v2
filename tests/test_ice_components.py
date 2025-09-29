# tests/test_ice_components.py
"""
Component-level tests for ICE integration classes
Tests individual component functionality with mock data
"""

import sys
import json
from pathlib import Path
from unittest.mock import Mock, patch

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_ice_graph_builder_with_mock_data():
    """Test ICEGraphBuilder with mock document data"""
    print("🔧 Testing ICEGraphBuilder with mock data...")
    
    try:
        from ice_core.ice_graph_builder import ICEGraphBuilder
        
        # Create with no LightRAG dependency
        builder = ICEGraphBuilder(lightrag_instance=None)
        
        # Test edge extraction from sample text
        sample_text = """
        NVIDIA depends on TSMC for chip manufacturing. TSMC operates in China and is exposed to trade risks.
        Export controls target advanced chips, which drives data center revenue concerns for NVIDIA.
        """
        
        edges = builder._extract_edges_from_text(sample_text)
        
        print(f"✅ Extracted {len(edges)} edges from sample text")
        
        # Test edge tuple format
        if edges:
            edge = edges[0]
            assert len(edge) == 6, f"Edge tuple should have 6 elements, got {len(edge)}"
            source, target, edge_type, confidence, age_days, is_contrarian = edge
            print(f"✅ Sample edge: {source} --{edge_type}--> {target} (conf: {confidence})")
        
        # Test graph building
        if edges:
            builder._rebuild_graph_from_edges(edges)
            assert len(builder.graph.nodes()) > 0, "Graph should have nodes after building"
            print(f"✅ Built graph with {len(builder.graph.nodes())} nodes, {len(builder.graph.edges())} edges")
        
        print("✅ ICEGraphBuilder component test passed")
        
    except Exception as e:
        print(f"❌ ICEGraphBuilder test failed: {e}")
        raise


def test_ice_query_processor_with_mock():
    """Test ICEQueryProcessor with mock LightRAG"""
    print("🧠 Testing ICEQueryProcessor with mock data...")
    
    try:
        from ice_core.ice_query_processor import ICEQueryProcessor
        
        # Create mock LightRAG
        mock_lightrag = Mock()
        mock_lightrag.is_ready.return_value = True
        mock_lightrag.query.return_value = {
            "status": "success",
            "result": "NVIDIA faces China trade risks due to supply chain dependencies and market exposure."
        }
        
        # Create processor with mock
        processor = ICEQueryProcessor(mock_lightrag, None)
        
        # Test entity extraction
        test_query = "What are the risks for NVDA from China trade policies?"
        entities = processor._extract_entities_from_query(test_query)
        
        print(f"✅ Extracted entities: {dict(entities)}")
        assert "NVDA" in entities.get("tickers", set()), "Should extract NVDA ticker"
        
        # Test query classification
        query_type = processor._classify_query_type(test_query, entities)
        assert query_type == "risk_analysis", f"Should classify as risk analysis, got {query_type}"
        print(f"✅ Query classified as: {query_type}")
        
        print("✅ ICEQueryProcessor component test passed")
        
    except Exception as e:
        print(f"❌ ICEQueryProcessor test failed: {e}")
        raise


def test_ice_system_manager_status():
    """Test ICESystemManager status reporting"""
    print("🎛️ Testing ICESystemManager status...")
    
    try:
        from ice_core.ice_system_manager import ICESystemManager
        
        # Create system manager
        system = ICESystemManager()
        
        # Test status reporting
        status = system.get_system_status()
        
        required_keys = ["ready", "components", "errors", "metrics"]
        for key in required_keys:
            assert key in status, f"Status should include '{key}'"
        
        print(f"✅ System ready: {status['ready']}")
        print(f"✅ Component status: {status['components']}")
        print(f"✅ Error count: {len(status['errors'])}")
        
        # Test query with unavailable system
        result = system.query_ice("test query")
        assert result["status"] == "error", "Should return error when system not ready"
        print(f"✅ Handles unavailable system gracefully: {result['message']}")
        
        print("✅ ICESystemManager component test passed")
        
    except Exception as e:
        print(f"❌ ICESystemManager test failed: {e}")
        raise


def test_mock_data_creation():
    """Create mock data files for testing"""
    print("📁 Creating mock test data...")
    
    try:
        mock_data_dir = Path(__file__).parent / "mock_data"
        mock_data_dir.mkdir(exist_ok=True)
        
        # Sample documents for testing
        sample_documents = [
            {
                "id": "doc1",
                "text": "NVIDIA reported strong Q3 2024 results with data center revenue growth of 206%. However, management flagged concerns about China export restrictions affecting future growth.",
                "type": "earnings_report",
                "company": "NVIDIA",
                "ticker": "NVDA"
            },
            {
                "id": "doc2", 
                "text": "TSMC announced capacity constraints at its advanced chip manufacturing facilities. The company manufactures critical components for NVIDIA and other semiconductor companies.",
                "type": "supply_chain_news",
                "company": "Taiwan Semiconductor",
                "ticker": "TSM"
            }
        ]
        
        # Sample graph edges
        sample_edges = [
            ("NVDA", "TSMC", "depends_on", 0.90, 1, False),
            ("TSMC", "China", "operates_in", 0.85, 2, False),
            ("China", "Export Controls", "implements", 0.80, 1, False),
            ("Export Controls", "Semiconductor Industry", "affects", 0.75, 3, True),
            ("NVDA", "Data Center Revenue", "drives", 0.88, 1, True)
        ]
        
        # Save mock data
        with open(mock_data_dir / "sample_documents.json", 'w') as f:
            json.dump(sample_documents, f, indent=2)
        
        with open(mock_data_dir / "sample_edges.json", 'w') as f:
            json.dump(sample_edges, f, indent=2)
        
        print(f"✅ Created mock data in {mock_data_dir}")
        print("✅ Mock data creation completed")
        
    except Exception as e:
        print(f"❌ Mock data creation failed: {e}")
        raise


if __name__ == "__main__":
    print("🧪 Running ICE Component Tests...")
    
    try:
        test_mock_data_creation()
        test_ice_graph_builder_with_mock_data()
        test_ice_query_processor_with_mock()
        test_ice_system_manager_status()
        
        print("\n🎉 All component tests passed!")
        
    except Exception as e:
        print(f"\n❌ Component test failed: {e}")
        sys.exit(1)