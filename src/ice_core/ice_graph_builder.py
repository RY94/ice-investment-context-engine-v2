# ice_core/ice_graph_builder.py
"""
ICE Graph Builder - Converts LightRAG entities to NetworkX graph structures  
Extracts investment relationships from LightRAG knowledge base and builds navigable graphs
Creates graph edges compatible with existing ICE visualization and analysis systems
Relevant files: ice_lightrag/ice_rag.py, ui_mockups/ice_ui_v17.py, ice_system_manager.py
"""

import re
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set
from pathlib import Path
import networkx as nx

logger = logging.getLogger(__name__)

class ICEGraphBuilder:
    """
    Converts LightRAG document analysis into NetworkX graph structures

    This class bridges the gap between LightRAG's entity extraction and ICE's
    graph-based investment intelligence by:
    - Extracting entities and relationships from LightRAG storage
    - Converting to NetworkX-compatible edge tuples
    - Maintaining investment-focused edge types and metadata
    - Providing graph analysis methods for causal reasoning

    Edge tuple format: (source, target, edge_type, confidence, age_days, is_contrarian)
    Compatible with existing ICE graph visualization and filtering systems
    """

    # Investment-focused edge types for financial relationship mapping
    EDGE_TYPE_MAPPING = {
        # Direct business relationships
        "DEPENDS_ON": "depends_on",
        "SUPPLIES": "supplies",
        "OWNED_BY": "owned_by",
        "INVESTS_IN": "invests_in",
        "COMPETES_WITH": "competes_with",

        # Risk and exposure relationships
        "EXPOSED_TO": "exposed_to",
        "VULNERABLE_TO": "vulnerable_to",
        "HEDGED_BY": "hedged_by",
        "CORRELATED_WITH": "correlated_with",

        # Performance relationships
        "DRIVES": "drives",
        "IMPACTS": "impacts",
        "INFLUENCES": "influences",
        "LINKED_TO": "linked_to",

        # Operational relationships
        "MANUFACTURES_IN": "manufactures_in",
        "SELLS_TO": "sells_to",
        "SERVES": "serves",
        "OPERATES_IN": "operates_in",

        # External factor relationships
        "AFFECTED_BY": "affected_by",
        "PRESSURES": "pressures",
        "REGULATED_BY": "regulated_by",
        "TARGETS": "targets"
    }

    def __init__(self, lightrag_instance=None):
        """
        Initialize ICE Graph Builder

        Args:
            lightrag_instance: Optional SimpleICERAG instance for entity extraction
                              Can be injected later via set_lightrag_instance()
        """
        self._lightrag = lightrag_instance
        self.graph = nx.MultiDiGraph()
        self.edge_cache = []
        self.last_refresh = None

        # Entity extraction patterns for financial relationships
        self.entity_patterns = self._build_entity_patterns()

        # Confidence scoring weights
        self.confidence_weights = {
            "source_reliability": 0.3,
            "relationship_clarity": 0.4,
            "evidence_strength": 0.3
        }

        logger.info("ICE Graph Builder initialized")

    def set_lightrag_instance(self, lightrag_instance):
        """
        Set or update the LightRAG instance (dependency injection)

        Args:
            lightrag_instance: SimpleICERAG instance to use for operations
        """
        self._lightrag = lightrag_instance
        logger.info("LightRAG instance updated in Graph Builder")

    @property
    def lightrag(self):
        """Get the current LightRAG instance"""
        if self._lightrag is None:
            logger.warning("Graph Builder has no LightRAG instance set")
        return self._lightrag
    
    def _build_entity_patterns(self) -> Dict[str, List[str]]:
        """
        Build regex patterns for extracting investment entities and relationships
        
        Returns:
            Dict mapping entity types to extraction patterns
        """
        return {
            "tickers": [
                r'\b([A-Z]{1,5})\b(?=\s+(?:stock|shares|equity|corporation|inc|corp))',
                r'\$([A-Z]{1,5})\b',
                r'\b([A-Z]{2,5})(?:\s+(?:stock|equity|shares))'
            ],
            "companies": [
                r'\b([A-Z][a-zA-Z\s&]{2,30})\s+(?:Corporation|Corp|Inc|Company|Co\.|Ltd)',
                r'\b([A-Z][a-zA-Z\s]{2,20})\s+(?:reported|announced|expects)'
            ],
            "risks": [
                r'(?:risk|risks|vulnerability|exposure|threat)\s+(?:of|to|from)\s+([a-zA-Z\s]{2,30})',
                r'([a-zA-Z\s]{2,30})\s+(?:risk|risks|vulnerability|exposure)'
            ],
            "kpis": [
                r'(?:revenue|earnings|profit|sales|growth|margin|ROE|ROI|EBITDA)\s+([a-zA-Z\s]{2,30})',
                r'([a-zA-Z\s]{2,30})\s+(?:increased|decreased|grew|fell|improved|declined)'
            ]
        }
    
    def extract_edges_from_documents(self, document_texts: Optional[List[str]] = None) -> List[Tuple]:
        """
        Extract graph edges from LightRAG document analysis
        
        Args:
            document_texts: Optional list of specific documents to process
            
        Returns:
            List of edge tuples: (source, target, edge_type, confidence, age_days, is_contrarian)
        """
        if not self.lightrag or not self.lightrag.is_ready():
            logger.warning("LightRAG not available for entity extraction")
            return []
        
        edges = []
        
        try:
            # If specific documents provided, process those
            if document_texts:
                for doc_text in document_texts:
                    doc_edges = self._extract_edges_from_text(doc_text)
                    edges.extend(doc_edges)
            else:
                # Extract from LightRAG storage files
                edges = self._extract_edges_from_lightrag_storage()
                
            # Update cache and graph
            self.edge_cache = edges
            self.last_refresh = datetime.utcnow()
            self._rebuild_graph_from_edges(edges)
            
            logger.info(f"Extracted {len(edges)} edges from documents")
            return edges
            
        except Exception as e:
            logger.error(f"Edge extraction failed: {e}")
            return []
    
    def _extract_edges_from_lightrag_storage(self) -> List[Tuple]:
        """
        Extract edges from LightRAG storage files (entities and relationships)
        
        Returns:
            List of edge tuples extracted from storage
        """
        edges = []
        
        try:
            # Look for LightRAG storage files
            storage_path = Path(self.lightrag.working_dir) if hasattr(self.lightrag, 'working_dir') else Path("./ice_lightrag/storage")
            
            # Check for entity storage files
            entity_files = [
                storage_path / "kv_store_full_docs.json",
                storage_path / "entities.json", 
                storage_path / "relationships.json"
            ]
            
            for file_path in entity_files:
                if file_path.exists():
                    edges.extend(self._parse_lightrag_file(file_path))
                    
        except Exception as e:
            logger.error(f"Failed to extract from LightRAG storage: {e}")
            
        return edges
    
    def _parse_lightrag_file(self, file_path: Path) -> List[Tuple]:
        """
        Parse individual LightRAG storage file for entities and relationships
        
        Args:
            file_path: Path to LightRAG storage file
            
        Returns:
            List of extracted edge tuples
        """
        edges = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Different parsing strategies based on file structure
            if isinstance(data, dict):
                # Parse document-based storage
                for doc_id, doc_data in data.items():
                    if isinstance(doc_data, dict) and 'content' in doc_data:
                        doc_edges = self._extract_edges_from_text(doc_data['content'])
                        edges.extend(doc_edges)
                        
            elif isinstance(data, list):
                # Parse list-based storage
                for item in data:
                    if isinstance(item, dict):
                        if 'source' in item and 'target' in item:
                            # Direct relationship format
                            edge = self._create_edge_tuple_from_relationship(item)
                            if edge:
                                edges.append(edge)
                        elif 'content' in item:
                            # Document content format
                            doc_edges = self._extract_edges_from_text(item['content'])
                            edges.extend(doc_edges)
                            
        except Exception as e:
            logger.error(f"Failed to parse LightRAG file {file_path}: {e}")
            
        return edges
    
    def _extract_edges_from_text(self, text: str) -> List[Tuple]:
        """
        Extract investment relationships from document text using pattern matching
        
        Args:
            text: Document text content
            
        Returns:
            List of edge tuples extracted from text
        """
        edges = []
        text_lower = text.lower()
        
        # Extract entities first
        entities = self._extract_entities_from_text(text)
        
        # Look for relationship patterns between entities
        relationship_patterns = [
            # Dependency relationships
            (r'(\w+)\s+(?:depends on|relies on|requires)\s+(\w+)', "depends_on", 0.8),
            (r'(\w+)\s+(?:supplies|provides|delivers)\s+(?:to\s+)?(\w+)', "supplies", 0.75),
            
            # Risk relationships  
            (r'(\w+)\s+(?:exposed to|vulnerable to|at risk from)\s+(\w+)', "exposed_to", 0.85),
            (r'(\w+)\s+(?:risk|risks)\s+(?:from|due to|because of)\s+(\w+)', "exposed_to", 0.8),
            
            # Performance relationships
            (r'(\w+)\s+(?:drives|boosts|increases)\s+(\w+)', "drives", 0.8),
            (r'(\w+)\s+(?:impacts|affects|influences)\s+(\w+)', "impacts", 0.7),
            
            # Business relationships
            (r'(\w+)\s+(?:competes with|rival|competitor)\s+(\w+)', "competes_with", 0.75),
            (r'(\w+)\s+(?:owns|acquired|purchased)\s+(\w+)', "owns", 0.9),
            
            # Operational relationships
            (r'(\w+)\s+(?:operates in|based in|located in)\s+(\w+)', "operates_in", 0.7),
            (r'(\w+)\s+(?:manufactures in|produces in)\s+(\w+)', "manufactures_in", 0.8)
        ]
        
        for pattern, edge_type, base_confidence in relationship_patterns:
            matches = re.finditer(pattern, text_lower, re.IGNORECASE)
            
            for match in matches:
                source = match.group(1).strip().upper()
                target = match.group(2).strip().upper()
                
                # Filter out common words and ensure entities are meaningful
                if self._is_valid_entity(source) and self._is_valid_entity(target):
                    # Calculate confidence based on context
                    confidence = self._calculate_relationship_confidence(
                        source, target, edge_type, text, base_confidence
                    )
                    
                    # Estimate document age (placeholder - could be enhanced with metadata)
                    age_days = 1
                    
                    # Determine if relationship is contrarian (negative sentiment)
                    is_contrarian = self._is_contrarian_relationship(match.group(0), text)
                    
                    edge_tuple = (source, target, edge_type, confidence, age_days, is_contrarian)
                    edges.append(edge_tuple)
        
        return edges
    
    def _extract_entities_from_text(self, text: str) -> Dict[str, Set[str]]:
        """
        Extract investment entities (tickers, companies, risks, KPIs) from text
        
        Args:
            text: Document text content
            
        Returns:
            Dict mapping entity types to sets of extracted entities
        """
        entities = {
            "tickers": set(),
            "companies": set(), 
            "risks": set(),
            "kpis": set()
        }
        
        for entity_type, patterns in self.entity_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    entity = match.group(1).strip()
                    if self._is_valid_entity(entity):
                        entities[entity_type].add(entity)
        
        return entities
    
    def _is_valid_entity(self, entity: str) -> bool:
        """
        Validate if extracted text represents a meaningful investment entity
        
        Args:
            entity: Candidate entity string
            
        Returns:
            True if entity is valid for investment analysis
        """
        # Filter out common words and too-short entities
        stop_words = {
            "the", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by",
            "a", "an", "as", "is", "was", "are", "were", "be", "been", "have", "has", "had",
            "will", "would", "could", "should", "may", "might", "can", "do", "does", "did"
        }
        
        entity_clean = entity.lower().strip()
        
        # Basic validation rules
        if len(entity_clean) < 2:
            return False
        if entity_clean in stop_words:
            return False
        if entity_clean.isdigit():
            return False
        if len(entity_clean) > 50:  # Too long to be meaningful
            return False
            
        return True
    
    def _calculate_relationship_confidence(self, source: str, target: str, edge_type: str, 
                                         context: str, base_confidence: float) -> float:
        """
        Calculate confidence score for extracted relationship
        
        Args:
            source: Source entity
            target: Target entity  
            edge_type: Type of relationship
            context: Surrounding text context
            base_confidence: Base confidence from pattern matching
            
        Returns:
            Confidence score between 0 and 1
        """
        confidence = base_confidence
        
        # Boost confidence for specific financial terms
        financial_terms = ["revenue", "earnings", "profit", "growth", "margin", "risk", "exposure"]
        context_lower = context.lower()
        
        financial_term_count = sum(1 for term in financial_terms if term in context_lower)
        confidence += financial_term_count * 0.05
        
        # Boost confidence for ticker symbols (usually more reliable)
        if re.match(r'^[A-Z]{2,5}$', source) or re.match(r'^[A-Z]{2,5}$', target):
            confidence += 0.1
            
        # Penalize very long entities (less reliable)
        if len(source) > 20 or len(target) > 20:
            confidence -= 0.1
            
        # Ensure confidence stays within bounds
        return max(0.1, min(1.0, confidence))
    
    def _is_contrarian_relationship(self, relationship_text: str, context: str) -> bool:
        """
        Determine if relationship has negative/contrarian sentiment
        
        Args:
            relationship_text: Text of the specific relationship
            context: Broader context around the relationship
            
        Returns:
            True if relationship indicates negative/risk factor
        """
        negative_indicators = [
            "risk", "threat", "vulnerability", "exposure", "decline", "fall", "decrease",
            "pressure", "constraint", "bottleneck", "shortage", "disruption", "uncertainty"
        ]
        
        text_lower = (relationship_text + " " + context[-100:]).lower()
        return any(indicator in text_lower for indicator in negative_indicators)
    
    def _create_edge_tuple_from_relationship(self, relationship_data: Dict) -> Optional[Tuple]:
        """
        Create edge tuple from structured relationship data
        
        Args:
            relationship_data: Dict with relationship information
            
        Returns:
            Edge tuple or None if invalid
        """
        try:
            source = relationship_data.get('source', '').strip().upper()
            target = relationship_data.get('target', '').strip().upper()
            edge_type = relationship_data.get('type', 'linked_to').lower()
            
            if not (self._is_valid_entity(source) and self._is_valid_entity(target)):
                return None
            
            # Map to standard edge types
            edge_type = self.EDGE_TYPE_MAPPING.get(edge_type.upper(), edge_type)
            
            confidence = relationship_data.get('confidence', 0.7)
            age_days = relationship_data.get('age_days', 1)
            is_contrarian = relationship_data.get('is_contrarian', False)
            
            return (source, target, edge_type, confidence, age_days, is_contrarian)
            
        except Exception as e:
            logger.error(f"Failed to create edge tuple from relationship: {e}")
            return None
    
    def _rebuild_graph_from_edges(self, edges: List[Tuple]):
        """
        Rebuild NetworkX graph from edge tuples
        
        Args:
            edges: List of edge tuples to add to graph
        """
        self.graph.clear()
        
        for source, target, edge_type, confidence, age_days, is_contrarian in edges:
            self.graph.add_edge(
                source, target,
                label=edge_type,
                confidence=confidence,
                age_days=age_days,
                is_contrarian=is_contrarian,
                edge_type=edge_type
            )
    
    def find_causal_paths(self, entity: str, max_hops: int = 3, min_confidence: float = 0.6) -> List[Dict]:
        """
        Find causal reasoning paths from/to a specific entity
        
        Args:
            entity: Starting entity for path finding
            max_hops: Maximum number of hops in path
            min_confidence: Minimum confidence threshold for edges
            
        Returns:
            List of causal path dictionaries
        """
        if entity not in self.graph:
            return []
        
        paths = []
        
        try:
            # Find all paths within max_hops
            for target in self.graph.nodes():
                if target == entity:
                    continue
                    
                try:
                    # Find shortest path
                    if nx.has_path(self.graph, entity, target):
                        path = nx.shortest_path(self.graph, entity, target)
                        
                        if len(path) <= max_hops + 1:  # +1 because path includes start node
                            path_info = self._analyze_causal_path(path, min_confidence)
                            if path_info:
                                paths.append(path_info)
                                
                except nx.NetworkXNoPath:
                    continue
                    
        except Exception as e:
            logger.error(f"Causal path finding failed for {entity}: {e}")
            
        # Sort paths by confidence and length
        paths.sort(key=lambda x: (x['confidence'], -x['hop_count']), reverse=True)
        return paths[:10]  # Return top 10 paths
    
    def _analyze_causal_path(self, path: List[str], min_confidence: float) -> Optional[Dict]:
        """
        Analyze a causal path and extract metadata
        
        Args:
            path: List of nodes in the path
            min_confidence: Minimum confidence threshold
            
        Returns:
            Path analysis dict or None if below threshold
        """
        if len(path) < 2:
            return None
            
        hops = []
        total_confidence = 1.0
        
        for i in range(len(path) - 1):
            source, target = path[i], path[i + 1]
            
            # Get edge data
            if self.graph.has_edge(source, target):
                edge_data = self.graph[source][target]
                
                # Handle MultiDiGraph - get first edge if multiple
                if isinstance(edge_data, dict):
                    edge_info = list(edge_data.values())[0]
                else:
                    edge_info = edge_data
                
                confidence = edge_info.get('confidence', 0.5)
                edge_type = edge_info.get('edge_type', 'linked_to')
                
                if confidence < min_confidence:
                    return None  # Path doesn't meet confidence threshold
                
                hops.append({
                    "edge_type": edge_type,
                    "target": target,
                    "confidence": confidence
                })
                
                total_confidence *= confidence
            else:
                return None  # Missing edge
        
        # Calculate average confidence
        avg_confidence = total_confidence ** (1.0 / len(hops))
        
        return {
            "path_str": " → ".join([f"{path[i]} --{hops[i]['edge_type']}--> {hops[i]['target']}" 
                                   for i in range(len(hops))]),
            "hop_count": len(hops),
            "confidence": avg_confidence,
            "hops": hops,
            "entities": path
        }
    
    def get_graph_edges_for_ui(self, min_confidence: float = 0.6, max_age_days: int = 365, 
                              edge_types: Optional[List[str]] = None) -> List[Tuple]:
        """
        Get graph edges formatted for ICE UI compatibility
        
        Args:
            min_confidence: Minimum confidence filter
            max_age_days: Maximum age filter
            edge_types: Specific edge types to include
            
        Returns:
            List of edge tuples compatible with ICE UI: (source, target, edge_type, confidence, age_days, is_contrarian)
        """
        filtered_edges = []
        
        for edge in self.edge_cache:
            source, target, edge_type, confidence, age_days, is_contrarian = edge
            
            # Apply filters
            if confidence < min_confidence:
                continue
            if age_days > max_age_days:
                continue
            if edge_types and edge_type not in edge_types:
                continue
                
            filtered_edges.append(edge)
        
        return filtered_edges
    
    def refresh_edges_from_recent_documents(self):
        """
        Refresh graph edges from recently added documents
        Useful for real-time updates after new document ingestion
        """
        try:
            new_edges = self.extract_edges_from_documents()
            logger.info(f"Refreshed graph with {len(new_edges)} edges from recent documents")
            return new_edges
        except Exception as e:
            logger.error(f"Failed to refresh edges from recent documents: {e}")
            return []
    
    def get_entity_summary(self, entity: str) -> Dict[str, Any]:
        """
        Get summary of entity's relationships and position in graph
        
        Args:
            entity: Entity to summarize
            
        Returns:
            Dict with entity relationship summary
        """
        if entity not in self.graph:
            return {"status": "not_found", "message": f"Entity {entity} not in graph"}
        
        # Count relationships by type
        outgoing = {}
        incoming = {}
        
        for target in self.graph[entity]:
            for edge_data in self.graph[entity][target].values():
                edge_type = edge_data.get('edge_type', 'unknown')
                outgoing[edge_type] = outgoing.get(edge_type, 0) + 1
        
        for source in self.graph.predecessors(entity):
            for edge_data in self.graph[source][entity].values():
                edge_type = edge_data.get('edge_type', 'unknown')
                incoming[edge_type] = incoming.get(edge_type, 0) + 1
        
        return {
            "entity": entity,
            "total_connections": len(list(self.graph[entity])) + len(list(self.graph.predecessors(entity))),
            "outgoing_relationships": outgoing,
            "incoming_relationships": incoming,
            "centrality": nx.degree_centrality(self.graph).get(entity, 0)
        }