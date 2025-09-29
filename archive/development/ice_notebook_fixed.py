# ice_notebook_fixed.py
# Fixed ICE notebook implementation - removes dummy data, implements document-based graph
# Proper RAG architecture using LightRAG for document processing and entity extraction
# Replaces static EDGE_RECORDS with dynamic document-derived relationships

import os
import sys
import asyncio
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional

# Core imports
from document_based_graph import DocumentBasedGraphBuilder, run_async_creation

# Configuration
class Config:
    """Clean configuration without dummy data dependencies"""
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    DOCUMENT_STORAGE_DIR = "./document_storage"
    LIGHTRAG_DIR = "./ice_lightrag/storage"
    DEBUG_MODE = True
    
    # RAG Engine Selection
    DEFAULT_RAG_ENGINE = "lightrag"
    ENABLE_DOCUMENT_PROCESSING = True


class ICEDocumentSystem:
    """
    Proper ICE system based on document processing instead of dummy data.
    Uses LightRAG for entity extraction and relationship discovery.
    """
    
    def __init__(self):
        """Initialize document-based ICE system"""
        self.document_builder = None
        self.knowledge_graph = None
        self.query_history = []
        self.system_ready = False
        
        print("🚀 Initializing Document-Based ICE System...")
        
        # Initialize document processor
        try:
            self.document_builder = run_async_creation()
            self.knowledge_graph = self.document_builder.knowledge_graph
            self.system_ready = True
            print("✅ Document-based system initialized successfully")
        except Exception as e:
            print(f"❌ System initialization failed: {e}")
            self.system_ready = False
    
    async def add_financial_document(self, title: str, content: str, 
                                   doc_type: str = "research", ticker: str = None):
        """Add a financial document for processing"""
        if not self.system_ready:
            return {"status": "error", "message": "System not ready"}
        
        from document_based_graph import FinancialDocument
        from datetime import datetime
        
        doc = FinancialDocument(
            doc_id=f"doc_{len(self.document_builder.documents)}",
            title=title,
            content=content,
            doc_type=doc_type,
            ticker=ticker,
            date=datetime.now()
        )
        
        await self.document_builder.add_document(doc)
        
        # Rebuild graph with new document
        self.knowledge_graph = self.document_builder.build_knowledge_graph()
        
        return {
            "status": "success",
            "message": f"Added document: {title}",
            "graph_stats": self.get_graph_statistics()
        }
    
    async def query(self, question: str, mode: str = "hybrid") -> Dict[str, Any]:
        """Query the document-based system"""
        if not self.system_ready:
            return {"status": "error", "message": "System not ready"}
        
        try:
            # Query the document-based graph
            result = await self.document_builder.query_graph(question)
            
            # Add to query history
            self.query_history.append({
                "question": question,
                "mode": mode,
                "result": result,
                "timestamp": pd.Timestamp.now()
            })
            
            return result
            
        except Exception as e:
            error_result = {
                "status": "error",
                "message": f"Query failed: {str(e)}",
                "question": question
            }
            
            self.query_history.append({
                "question": question,
                "mode": mode, 
                "result": error_result,
                "timestamp": pd.Timestamp.now()
            })
            
            return error_result
    
    def get_graph_statistics(self) -> Dict[str, Any]:
        """Get comprehensive system statistics"""
        if not self.system_ready or not self.document_builder:
            return {"error": "System not ready"}
        
        base_stats = self.document_builder.get_graph_statistics()
        
        # Add query statistics
        base_stats.update({
            "queries_executed": len(self.query_history),
            "system_ready": self.system_ready,
            "lightrag_available": self.document_builder.lightrag is not None,
        })
        
        return base_stats
    
    def get_portfolio_intelligence(self, ticker: str) -> Dict[str, Any]:
        """Get AI-driven intelligence for a specific ticker"""
        if not self.system_ready:
            return {"error": "System not ready"}
        
        # Find ticker in knowledge graph
        if ticker not in self.knowledge_graph.nodes():
            return {"error": f"Ticker {ticker} not found in knowledge graph"}
        
        # Get ticker's relationships
        relationships = []
        for source, target, data in self.knowledge_graph.edges(data=True):
            if source == ticker or target == ticker:
                relationships.append({
                    "source": source,
                    "target": target,
                    "type": data.get("relationship_type", "unknown"),
                    "confidence": data.get("confidence", 0),
                    "evidence": data.get("evidence_text", "")
                })
        
        # Get connected entities
        connected_entities = list(self.knowledge_graph.neighbors(ticker))
        
        return {
            "ticker": ticker,
            "relationships_count": len(relationships),
            "relationships": relationships[:10],  # Top 10
            "connected_entities": connected_entities,
            "entity_type": self.knowledge_graph.nodes[ticker].get("entity_type", "unknown"),
            "centrality": len(connected_entities)  # Simple centrality measure
        }
    
    def export_graph_data(self) -> Dict[str, Any]:
        """Export graph data for external analysis"""
        if not self.system_ready:
            return {"error": "System not ready"}
        
        # Export nodes
        nodes_data = []
        for node, data in self.knowledge_graph.nodes(data=True):
            nodes_data.append({
                "node": node,
                "entity_type": data.get("entity_type", "unknown")
            })
        
        # Export edges  
        edges_data = []
        for source, target, data in self.knowledge_graph.edges(data=True):
            edges_data.append({
                "source": source,
                "target": target,
                "relationship_type": data.get("relationship_type", "unknown"),
                "confidence": data.get("confidence", 0),
                "source_doc": data.get("source_doc_id", ""),
                "date_extracted": data.get("date_extracted", "")
            })
        
        return {
            "nodes": nodes_data,
            "edges": edges_data,
            "statistics": self.get_graph_statistics(),
            "documents": list(self.document_builder.documents.keys())
        }


def create_ice_system() -> ICEDocumentSystem:
    """Create the proper document-based ICE system"""
    return ICEDocumentSystem()


# Notebook integration functions
def display_system_status(ice_system: ICEDocumentSystem):
    """Display system status for notebook"""
    print("=" * 60)
    print("🎯 ICE Document-Based System Status")
    print("=" * 60)
    
    stats = ice_system.get_graph_statistics()
    
    print(f"📊 System Ready: {'✅' if ice_system.system_ready else '❌'}")
    print(f"📄 Documents Processed: {stats.get('documents_processed', 0)}")
    print(f"🕸️ Knowledge Graph: {stats.get('nodes', 0)} entities, {stats.get('edges', 0)} relationships")
    print(f"🎯 Queries Executed: {stats.get('queries_executed', 0)}")
    print(f"🧠 LightRAG Available: {'✅' if stats.get('lightrag_available', False) else '❌'}")
    
    if stats.get('entity_types'):
        print(f"\n📋 Entity Types:")
        for entity_type, count in stats['entity_types'].items():
            print(f"  • {entity_type}: {count}")
    
    if stats.get('relationship_types'):
        print(f"\n🔗 Relationship Types:")
        for rel_type, count in stats['relationship_types'].items():
            print(f"  • {rel_type}: {count}")


async def demo_document_processing():
    """Demonstrate document-based processing"""
    print("\n🔬 Document Processing Demo")
    print("-" * 40)
    
    ice_system = create_ice_system()
    
    if not ice_system.system_ready:
        print("❌ System not ready for demo")
        return
    
    # Add a new document
    sample_doc = """
    Apple reported strong iPhone sales in China despite economic headwinds. 
    The company's supply chain remains heavily dependent on Foxconn facilities in Taiwan.
    Tim Cook highlighted concerns about potential trade restrictions affecting semiconductor suppliers.
    Services revenue grew 8% driven by App Store sales in emerging markets.
    """
    
    result = await ice_system.add_financial_document(
        title="Apple Q4 China Performance Update",
        content=sample_doc,
        doc_type="earnings",
        ticker="AAPL"
    )
    
    print(f"Document processing result: {result['status']}")
    
    # Query the system
    query_result = await ice_system.query("What are Apple's key dependencies mentioned in recent documents?")
    print(f"\nQuery result: {query_result}")
    
    # Display updated statistics
    display_system_status(ice_system)


if __name__ == "__main__":
    print("🚀 ICE Document-Based System - Fixed Implementation")
    print("This replaces dummy data with proper document processing")
    
    # Create system
    ice_system = create_ice_system()
    
    # Display status
    display_system_status(ice_system)
    
    # Run demo
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(demo_document_processing())
    except Exception as e:
        print(f"Demo failed: {e}")
    
    print("\n✅ Fixed implementation completed!")
    print("📚 Use ice_system.query() for intelligent investment queries")
    print("📄 Use ice_system.add_financial_document() to add new documents")
    print("📊 Use ice_system.get_portfolio_intelligence(ticker) for ticker analysis")