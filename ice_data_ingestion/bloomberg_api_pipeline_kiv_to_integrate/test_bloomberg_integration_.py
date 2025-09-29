# test_bloomberg_integration.py
# Test script for Bloomberg Terminal API integration with ICE Investment Context Engine  
# Validates Bloomberg connection, data fetching, and ICE system compatibility
# RELEVANT FILES: ice_data_ingestion/bloomberg_connector.py, ice_data_ingestion/bloomberg_ice_integration.py, simple_demo.py, test_api_key.py

import sys
import os
sys.path.append('ice_data_ingestion')

from bloomberg_connector import BloombergConnector, test_bloomberg_connection
from bloomberg_ice_integration import BloombergICEIntegrator, example_bloomberg_ice_integration

def main():
    """
    Comprehensive test of Bloomberg API integration with ICE system.
    """
    print("🔬 Testing Bloomberg Terminal API Integration with ICE")
    print("=" * 60)
    
    # Test 1: Basic Bloomberg connection
    print("\n1️⃣  Testing Bloomberg API Connection...")
    if not test_bloomberg_connection():
        print("❌ Bloomberg connection failed. Please ensure:")
        print("   • Bloomberg Terminal is running and logged in")
        print("   • blpapi Python package is installed")
        print("   • Bloomberg API service is available on localhost:8194")
        return False
    
    # Test 2: ICE Integration Layer  
    print("\n2️⃣  Testing ICE Integration Layer...")
    try:
        ice_data = example_bloomberg_ice_integration()
        if ice_data:
            print("✅ ICE integration successful")
            
            # Validate ICE data structure
            required_keys = ['portfolio_metrics', 'knowledge_graph_edges', 'lightrag_documents', 'risk_exposures']
            missing_keys = [key for key in required_keys if key not in ice_data]
            
            if missing_keys:
                print(f"⚠️  Missing ICE data keys: {missing_keys}")
            else:
                print("✅ ICE data structure validated")
        else:
            print("❌ ICE integration failed")
            return False
            
    except Exception as e:
        print(f"❌ ICE integration error: {e}")
        return False
    
    # Test 3: Sample Data Quality
    print("\n3️⃣  Validating Data Quality...")
    
    # Check portfolio metrics
    portfolio_count = len(ice_data.get('portfolio_metrics', {}))
    edge_count = len(ice_data.get('knowledge_graph_edges', []))
    doc_count = len(ice_data.get('lightrag_documents', []))
    
    print(f"   📈 Portfolio holdings analyzed: {portfolio_count}")
    print(f"   🕸️  Knowledge graph edges: {edge_count}")
    print(f"   📄 LightRAG documents: {doc_count}")
    
    if portfolio_count > 0 and edge_count > 0 and doc_count > 0:
        print("✅ Data quality validation passed")
    else:
        print("⚠️  Low data quality - check Bloomberg data availability")
    
    # Test 4: ICE Compatibility
    print("\n4️⃣  Testing ICE System Compatibility...")
    
    # Check edge format
    if ice_data.get('knowledge_graph_edges'):
        sample_edge = ice_data['knowledge_graph_edges'][0]
        required_edge_fields = ['source', 'target', 'edge_type', 'weight', 'confidence']
        edge_valid = all(field in sample_edge for field in required_edge_fields)
        
        if edge_valid:
            print("✅ Knowledge graph edge format validated")
        else:
            print("❌ Invalid knowledge graph edge format")
    
    # Check document format
    if ice_data.get('lightrag_documents'):
        sample_doc = ice_data['lightrag_documents'][0]  
        required_doc_fields = ['doc_id', 'content', 'title', 'source']
        doc_valid = all(field in sample_doc for field in required_doc_fields)
        
        if doc_valid:
            print("✅ LightRAG document format validated")
        else:
            print("❌ Invalid LightRAG document format")
    
    print("\n🎉 Bloomberg API integration test completed successfully!")
    print("\nNext steps:")
    print("• Add Bloomberg connector to your ICE UI (ice_ui_v17.py)")
    print("• Configure Bloomberg data refresh schedules")
    print("• Set up portfolio monitoring with Bloomberg feeds")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)