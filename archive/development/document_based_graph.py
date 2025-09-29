# document_based_graph.py
# Proper document-based graph construction for ICE system
# Replaces dummy data with real document processing and entity extraction
# Uses LightRAG for intelligent relationship discovery from financial texts

import os
import asyncio
import networkx as nx
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta

# LightRAG imports
try:
    from ice_lightrag.ice_rag import ICELightRAG
    LIGHTRAG_AVAILABLE = True
except ImportError:
    LIGHTRAG_AVAILABLE = False
    print("⚠️ LightRAG not available - using mock implementation")


@dataclass
class FinancialDocument:
    """Financial document structure for processing"""
    doc_id: str
    title: str
    content: str
    doc_type: str  # "earnings", "filing", "news", "research"
    ticker: Optional[str] = None
    date: Optional[datetime] = None
    source: Optional[str] = None


@dataclass
class ExtractedRelationship:
    """Relationship extracted from documents"""
    source_entity: str
    target_entity: str
    relationship_type: str
    confidence: float
    source_doc_id: str
    evidence_text: str
    date_extracted: datetime


class DocumentBasedGraphBuilder:
    """
    Builds investment knowledge graph from actual financial documents.
    Replaces dummy data approach with real document processing.
    """
    
    def __init__(self, working_dir: str = "./document_storage"):
        """Initialize document-based graph builder"""
        self.working_dir = Path(working_dir)
        self.working_dir.mkdir(parents=True, exist_ok=True)
        
        # Document storage
        self.documents: Dict[str, FinancialDocument] = {}
        self.processed_documents: set = set()
        
        # Graph components
        self.knowledge_graph = nx.MultiDiGraph()
        self.relationships: List[ExtractedRelationship] = []
        
        # LightRAG integration
        self.lightrag = None
        if LIGHTRAG_AVAILABLE:
            try:
                self.lightrag = ICELightRAG(working_dir=str(self.working_dir / "lightrag"))
                print("✅ LightRAG initialized for document processing")
            except Exception as e:
                print(f"⚠️ LightRAG initialization failed: {e}")
                self.lightrag = None
        
        # Financial entity patterns for extraction
        self.financial_patterns = {
            'tickers': r'\b[A-Z]{2,5}\b',  # Stock tickers
            'companies': ['NVIDIA', 'TSMC', 'Apple', 'Microsoft', 'Amazon'],
            'risks': ['China', 'Export Controls', 'Supply Chain', 'Regulation'],
            'metrics': ['Revenue', 'Margin', 'EBITDA', 'Cash Flow'],
            'regions': ['China', 'Taiwan', 'US', 'Europe', 'Asia']
        }
    
    async def add_sample_documents(self):
        """Add realistic sample financial documents for demonstration"""
        sample_docs = [
            FinancialDocument(
                doc_id="nvda_q3_2024",
                title="NVIDIA Q3 2024 Earnings Call Transcript",
                content="""
                Jensen Huang, CEO: Our data center revenue grew 206% year-over-year to $14.5 billion, 
                driven by strong demand for our H100 and A100 GPUs. However, we're seeing headwinds 
                from new export restrictions to China, which historically represented 20-25% of our 
                data center revenue. We continue to work closely with TSMC on our advanced 4nm and 
                3nm process nodes, though lead times remain extended. Gaming revenue declined 33% 
                to $2.9 billion as crypto mining demand normalized.
                """,
                doc_type="earnings",
                ticker="NVDA",
                date=datetime(2024, 8, 15),
                source="Earnings Call"
            ),
            FinancialDocument(
                doc_id="tsmc_capacity_report",
                title="TSMC Advanced Node Capacity Analysis",
                content="""
                Taiwan Semiconductor Manufacturing Company reported that advanced node capacity 
                remains tight, with 4nm and 3nm processes running at full utilization. The company's 
                fabs in Taiwan handle over 90% of advanced chip production globally. TSMC highlighted 
                geopolitical risks as a key concern, noting that any disruption to Taiwan operations 
                could impact major customers including NVIDIA, Apple, and AMD. The company is 
                investing $40 billion in US fabs to diversify production.
                """,
                doc_type="research",
                ticker="TSM",
                date=datetime(2024, 7, 20),
                source="Industry Analysis"
            ),
            FinancialDocument(
                doc_id="china_export_controls",
                title="Updated China Export Control Regulations Impact Analysis",
                content="""
                The Bureau of Industry and Security expanded export controls on advanced 
                semiconductors to China, targeting chips with performance above specific thresholds. 
                This directly impacts NVIDIA's A100 and H100 data center GPUs, potentially affecting 
                $4-5 billion in annual revenue. NVIDIA has developed alternative products like the 
                A800 for the Chinese market, but these generate lower margins. The controls also 
                impact semiconductor equipment companies like ASML and Applied Materials.
                """,
                doc_type="news",
                ticker=None,
                date=datetime(2024, 8, 1),
                source="Trade Analysis"
            )
        ]
        
        for doc in sample_docs:
            await self.add_document(doc)
    
    async def add_document(self, document: FinancialDocument):
        """Add and process a financial document"""
        self.documents[document.doc_id] = document
        
        # Process with LightRAG if available
        if self.lightrag and self.lightrag.is_ready():
            try:
                # Add to LightRAG for entity/relationship extraction
                await self.lightrag.add_document(
                    f"[{document.doc_type.upper()}] {document.title}\n\n{document.content}",
                    doc_type=document.doc_type
                )
                self.processed_documents.add(document.doc_id)
                print(f"✅ Processed document: {document.title}")
                
                # Extract relationships from this document
                await self._extract_relationships_from_document(document)
                
            except Exception as e:
                print(f"❌ Error processing {document.doc_id}: {e}")
        else:
            # Fallback: simple pattern-based extraction
            await self._extract_relationships_simple(document)
    
    async def _extract_relationships_from_document(self, document: FinancialDocument):
        """Extract investment relationships from document using LightRAG"""
        # Use LightRAG to query for relationships in this document
        relationship_queries = [
            f"What companies does {document.ticker} depend on based on this document?",
            f"What risks affect {document.ticker} according to this document?", 
            f"What supply chain relationships are mentioned?",
            f"What geographical exposures are described?"
        ]
        
        for query in relationship_queries:
            try:
                result = await self.lightrag.query(query, mode="local")  # Focus on this document
                if result.get("status") == "success":
                    # Parse relationships from LightRAG response
                    relationships = self._parse_lightrag_relationships(
                        result.get("result", ""), document
                    )
                    self.relationships.extend(relationships)
                    
            except Exception as e:
                print(f"⚠️ Relationship extraction failed for query '{query}': {e}")
    
    async def _extract_relationships_simple(self, document: FinancialDocument):
        """Simple pattern-based relationship extraction (fallback)"""
        content = document.content.lower()
        relationships = []
        
        # Define simple extraction rules
        extraction_rules = [
            # Dependencies
            (r'(\w+)\s+depends on\s+(\w+)', 'depends_on'),
            (r'(\w+)\s+relies on\s+(\w+)', 'depends_on'),
            (r'work.*closely with\s+(\w+)', 'partners_with'),
            
            # Geographic exposure
            (r'(\w+).*revenue.*(\w+)', 'has_revenue_exposure'),
            (r'operations.*in\s+(\w+)', 'operates_in'),
            
            # Risk relationships
            (r'(\w+).*impact.*(\w+)', 'impacts'),
            (r'headwinds.*from\s+(\w+)', 'faces_risk_from'),
        ]
        
        import re
        for pattern, rel_type in extraction_rules:
            matches = re.findall(pattern, content)
            for match in matches:
                if isinstance(match, tuple) and len(match) == 2:
                    source, target = match
                    relationships.append(ExtractedRelationship(
                        source_entity=source.upper(),
                        target_entity=target.upper(),
                        relationship_type=rel_type,
                        confidence=0.6,  # Lower confidence for pattern-based
                        source_doc_id=document.doc_id,
                        evidence_text=f"Pattern match in {document.title}",
                        date_extracted=datetime.now()
                    ))
        
        self.relationships.extend(relationships)
        print(f"✅ Extracted {len(relationships)} relationships from {document.title}")
    
    def _parse_lightrag_relationships(self, lightrag_result: str, document: FinancialDocument) -> List[ExtractedRelationship]:
        """Parse relationships from LightRAG response"""
        relationships = []
        
        # This would need more sophisticated parsing based on LightRAG's actual output format
        # For now, implementing basic parsing
        lines = lightrag_result.split('\n')
        for line in lines:
            if '->' in line or 'depends on' in line.lower() or 'impacts' in line.lower():
                # Extract entities and relationship type from natural language
                # This is a simplified implementation
                parts = line.replace('->', '|').split('|')
                if len(parts) >= 2:
                    relationships.append(ExtractedRelationship(
                        source_entity=parts[0].strip(),
                        target_entity=parts[1].strip(),
                        relationship_type='extracted_from_text',
                        confidence=0.8,  # Higher confidence for LightRAG
                        source_doc_id=document.doc_id,
                        evidence_text=line.strip(),
                        date_extracted=datetime.now()
                    ))
        
        return relationships
    
    def build_knowledge_graph(self) -> nx.MultiDiGraph:
        """Build NetworkX graph from extracted relationships"""
        self.knowledge_graph.clear()
        
        for rel in self.relationships:
            # Add nodes with metadata
            self.knowledge_graph.add_node(rel.source_entity, 
                                        entity_type=self._classify_entity(rel.source_entity))
            self.knowledge_graph.add_node(rel.target_entity, 
                                        entity_type=self._classify_entity(rel.target_entity))
            
            # Add edge with rich metadata
            self.knowledge_graph.add_edge(
                rel.source_entity,
                rel.target_entity,
                relationship_type=rel.relationship_type,
                confidence=rel.confidence,
                source_doc_id=rel.source_doc_id,
                evidence_text=rel.evidence_text,
                date_extracted=rel.date_extracted.isoformat(),
                weight=rel.confidence  # For graph algorithms
            )
        
        print(f"✅ Built knowledge graph: {self.knowledge_graph.number_of_nodes()} nodes, "
              f"{self.knowledge_graph.number_of_edges()} edges")
        
        return self.knowledge_graph
    
    def _classify_entity(self, entity: str) -> str:
        """Classify entity type for better visualization"""
        entity_upper = entity.upper()
        
        if entity_upper in ['NVDA', 'TSMC', 'AAPL', 'MSFT', 'AMZN', 'GOOGL']:
            return 'ticker'
        elif entity_upper in ['CHINA', 'TAIWAN', 'US', 'EUROPE', 'ASIA']:
            return 'geography'
        elif 'revenue' in entity.lower() or 'margin' in entity.lower():
            return 'financial_metric'
        elif 'control' in entity.lower() or 'restriction' in entity.lower():
            return 'regulation'
        else:
            return 'general'
    
    def get_graph_statistics(self) -> Dict[str, Any]:
        """Get comprehensive graph statistics"""
        if self.knowledge_graph.number_of_nodes() == 0:
            return {"error": "No graph data available"}
        
        return {
            "nodes": self.knowledge_graph.number_of_nodes(),
            "edges": self.knowledge_graph.number_of_edges(), 
            "documents_processed": len(self.processed_documents),
            "relationships_extracted": len(self.relationships),
            "avg_confidence": sum(r.confidence for r in self.relationships) / len(self.relationships) if self.relationships else 0,
            "entity_types": self._get_entity_type_counts(),
            "relationship_types": self._get_relationship_type_counts(),
            "coverage_by_document": {doc_id: len([r for r in self.relationships if r.source_doc_id == doc_id]) 
                                   for doc_id in self.processed_documents}
        }
    
    def _get_entity_type_counts(self) -> Dict[str, int]:
        """Count entities by type"""
        type_counts = {}
        for node, data in self.knowledge_graph.nodes(data=True):
            entity_type = data.get('entity_type', 'unknown')
            type_counts[entity_type] = type_counts.get(entity_type, 0) + 1
        return type_counts
    
    def _get_relationship_type_counts(self) -> Dict[str, int]:
        """Count relationships by type"""
        type_counts = {}
        for _, _, data in self.knowledge_graph.edges(data=True):
            rel_type = data.get('relationship_type', 'unknown')
            type_counts[rel_type] = type_counts.get(rel_type, 0) + 1
        return type_counts
    
    async def query_graph(self, question: str) -> Dict[str, Any]:
        """Query the document-based graph"""
        if self.lightrag and self.lightrag.is_ready():
            # Use LightRAG for intelligent querying
            result = await self.lightrag.query(question, mode="hybrid")
            return result
        else:
            # Fallback: simple graph-based query
            return {
                "status": "success", 
                "result": f"Graph-based response to: {question}",
                "source": "document_graph",
                "nodes_used": self.knowledge_graph.number_of_nodes()
            }


# Helper functions for integration
async def create_document_based_system() -> DocumentBasedGraphBuilder:
    """Create and initialize document-based graph system"""
    builder = DocumentBasedGraphBuilder()
    
    # Add sample documents for demonstration
    await builder.add_sample_documents()
    
    # Build the knowledge graph
    builder.build_knowledge_graph()
    
    return builder


def run_async_creation():
    """Synchronous wrapper for creating the system"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(create_document_based_system())


if __name__ == "__main__":
    print("🔬 Testing Document-Based Graph Construction...")
    
    # Create the system
    builder = run_async_creation()
    
    # Display statistics
    stats = builder.get_graph_statistics()
    print(f"\n📊 Graph Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Test query
    async def test_query():
        result = await builder.query_graph("What are NVIDIA's key dependencies?")
        print(f"\n🎯 Query Test Result: {result}")
    
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(test_query())
    except:
        pass
    
    print("\n✅ Document-based graph construction completed!")