# ice_core/ice_query_processor.py
"""
ICE Query Processor - Hybrid Graph-RAG query processing for investment intelligence
Combines LightRAG semantic search with graph-based structural context for enhanced responses
Provides multi-hop reasoning chains and source attribution for investment decision making
Relevant files: ice_lightrag/ice_rag.py, ice_graph_builder.py, ice_system_manager.py
"""

import re
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set
import networkx as nx

logger = logging.getLogger(__name__)

class ICEQueryProcessor:
    """
    Hybrid Graph-RAG query processor for enhanced investment intelligence
    
    This class combines:
    - LightRAG semantic document search and retrieval  
    - Graph-based structural context and relationship analysis
    - Multi-hop reasoning chains for complex investment questions
    - Source attribution and confidence scoring for transparency
    
    Query processing pipeline:
    1. Entity extraction from user question
    2. LightRAG semantic search for relevant documents
    3. Graph context expansion around extracted entities  
    4. Combined context synthesis for enhanced response
    5. Source attribution and confidence assessment
    """
    
    def __init__(self, lightrag_instance=None, graph_builder=None):
        """
        Initialize ICE Query Processor
        
        Args:
            lightrag_instance: SimpleICERAG instance for document search
            graph_builder: ICEGraphBuilder instance for graph context
        """
        self.lightrag = lightrag_instance
        self.graph_builder = graph_builder
        
        # Query processing configuration
        self.max_context_documents = 10
        self.max_graph_hops = 3
        self.min_confidence_threshold = 0.6
        
        # Entity extraction patterns for investment queries
        self.query_patterns = self._build_query_patterns()
        
        # Response formatting templates
        self.response_templates = self._build_response_templates()
        
        logger.info("ICE Query Processor initialized")
    
    def _build_query_patterns(self) -> Dict[str, List[str]]:
        """
        Build patterns for extracting entities and intent from user queries
        
        Returns:
            Dict mapping query types to extraction patterns
        """
        return {
            "ticker_queries": [
                r'\b([A-Z]{1,5})\b(?:\s+(?:stock|shares|equity|price|performance))?',
                r'(?:shares of|stock in|equity in|invest in)\s+([A-Z]{1,5})\b',
                r'\$([A-Z]{1,5})\b'
            ],
            "company_queries": [
                r'\b([A-Z][a-zA-Z\s&]{2,30})\s+(?:Corporation|Corp|Inc|Company|Co\.|Ltd)',
                r'(?:company|firm|business)\s+([A-Z][a-zA-Z\s]{2,25})'
            ],
            "risk_queries": [
                r'(?:risk|risks|threats|vulnerabilities|exposures?)\s+(?:to|for|of|from)\s+([a-zA-Z\s]{2,30})',
                r'what.*(?:risk|threat|vulnerability)\s+(?:does|is|are)\s+([a-zA-Z\s]{2,30})',
                r'([a-zA-Z\s]{2,30})\s+(?:at risk|vulnerable|exposed|threatened)'
            ],
            "performance_queries": [
                r'(?:performance|earnings|revenue|growth|profitability)\s+(?:of|for)\s+([a-zA-Z\s]{2,30})',
                r'how\s+(?:is|are|did|does)\s+([a-zA-Z\s]{2,30})\s+(?:performing|doing|growing)'
            ],
            "relationship_queries": [
                r'(?:relationship|connection|link|dependency|correlation)\s+between\s+([a-zA-Z\s]{2,30})\s+and\s+([a-zA-Z\s]{2,30})',
                r'how\s+(?:does|do|is|are)\s+([a-zA-Z\s]{2,30})\s+(?:related to|connected to|linked to|depend on)\s+([a-zA-Z\s]{2,30})',
                r'([a-zA-Z\s]{2,30})\s+(?:impact|affect|influence|drive)\s+([a-zA-Z\s]{2,30})'
            ]
        }
    
    def _build_response_templates(self) -> Dict[str, str]:
        """
        Build response templates for different query types
        
        Returns:
            Dict mapping query types to response templates
        """
        return {
            "default": """## 💡 ICE Analysis

{main_response}

### 🧠 Key Insights
{key_insights}

### 🔗 Relationship Context  
{graph_context}

### 📚 Sources
{sources}""",
            
            "risk_analysis": """## ⚠️ Risk Analysis

{main_response}

### 🎯 Risk Factors
{risk_factors}

### 🔗 Risk Pathways
{risk_pathways}

### 📊 Confidence Assessment
{confidence_info}

### 📚 Sources
{sources}""",
            
            "performance_analysis": """## 📈 Performance Analysis  

{main_response}

### 🎯 Key Performance Drivers
{performance_drivers}

### 📊 Performance Context
{performance_context}

### 🔗 Related Factors
{related_factors}

### 📚 Sources
{sources}"""
        }
    
    def process_enhanced_query(self, question: str, mode: str = "hybrid") -> Dict[str, Any]:
        """
        Process user query with enhanced Graph-RAG capabilities
        
        Args:
            question: User's investment question
            mode: LightRAG query mode ("hybrid", "local", "global", "naive")
            
        Returns:
            Dict with enhanced query results including graph context
        """
        if not self.lightrag or not self.lightrag.is_ready():
            return {
                "status": "error",
                "message": "LightRAG not available for query processing"
            }
        
        try:
            # Step 1: Extract entities and classify query intent
            entities = self._extract_entities_from_query(question)
            query_type = self._classify_query_type(question, entities)
            
            # Step 2: Execute LightRAG semantic search
            rag_result = self.lightrag.query(question, mode)
            
            if rag_result["status"] != "success":
                return rag_result
            
            # Step 3: Get graph-based context if graph builder available
            graph_context = {}
            if self.graph_builder:
                graph_context = self._get_graph_context(entities, question)
            
            # Step 4: Combine contexts for enhanced response
            enhanced_response = self._synthesize_enhanced_response(
                question, rag_result, graph_context, entities, query_type
            )
            
            return {
                "status": "success",
                "result": enhanced_response["formatted_response"],
                "entities": entities,
                "query_type": query_type,
                "graph_context": graph_context,
                "sources": enhanced_response["sources"],
                "confidence": enhanced_response["confidence"]
            }
            
        except Exception as e:
            logger.error(f"Enhanced query processing failed: {e}")
            return {
                "status": "error",
                "message": f"Query processing failed: {str(e)}"
            }
    
    def _extract_entities_from_query(self, question: str) -> Dict[str, Set[str]]:
        """
        Extract investment entities from user question
        
        Args:
            question: User's question text
            
        Returns:
            Dict mapping entity types to sets of extracted entities
        """
        entities = {
            "tickers": set(),
            "companies": set(),
            "risks": set(),
            "general": set()
        }
        
        # Extract tickers (most reliable)
        ticker_patterns = self.query_patterns.get("ticker_queries", [])
        for pattern in ticker_patterns:
            matches = re.finditer(pattern, question, re.IGNORECASE)
            for match in matches:
                ticker = match.group(1).upper().strip()
                if self._is_valid_ticker(ticker):
                    entities["tickers"].add(ticker)
        
        # Extract company names
        company_patterns = self.query_patterns.get("company_queries", [])
        for pattern in company_patterns:
            matches = re.finditer(pattern, question, re.IGNORECASE)
            for match in matches:
                company = match.group(1).strip()
                if len(company) > 2:
                    entities["companies"].add(company)
        
        # Extract general investment entities (broader catch)
        general_entities = re.findall(r'\b[A-Z][A-Za-z]{2,15}\b', question)
        for entity in general_entities:
            if entity not in {"What", "Why", "How", "When", "Where", "The", "And", "But"}:
                entities["general"].add(entity)
        
        logger.info(f"Extracted entities from query: {dict(entities)}")
        return entities
    
    def _classify_query_type(self, question: str, entities: Dict[str, Set[str]]) -> str:
        """
        Classify the type of investment query for appropriate response formatting
        
        Args:
            question: User's question text
            entities: Extracted entities
            
        Returns:
            Query type classification
        """
        question_lower = question.lower()
        
        # Risk analysis queries
        risk_keywords = ["risk", "risks", "threat", "threats", "vulnerability", "vulnerable", 
                        "exposure", "exposed", "danger", "downside"]
        if any(keyword in question_lower for keyword in risk_keywords):
            return "risk_analysis"
        
        # Performance analysis queries  
        performance_keywords = ["performance", "earnings", "revenue", "growth", "profit",
                               "returns", "gains", "performing", "doing"]
        if any(keyword in question_lower for keyword in performance_keywords):
            return "performance_analysis"
        
        # Relationship queries
        relationship_keywords = ["relationship", "connection", "related", "connected", "link",
                                "impact", "affect", "influence", "depend", "correlation"]
        if any(keyword in question_lower for keyword in relationship_keywords):
            return "relationship_analysis"
        
        # Default to general analysis
        return "default"
    
    def _is_valid_ticker(self, ticker: str) -> bool:
        """
        Validate if extracted text represents a valid ticker symbol
        
        Args:
            ticker: Candidate ticker symbol
            
        Returns:
            True if appears to be valid ticker
        """
        # Basic ticker validation rules
        if not ticker or len(ticker) < 1 or len(ticker) > 5:
            return False
        if not ticker.isalpha():
            return False
        if ticker in {"THE", "AND", "BUT", "FOR", "ARE", "HAS", "WAS", "CAN", "ALL"}:
            return False
            
        return True
    
    def _get_graph_context(self, entities: Dict[str, Set[str]], question: str) -> Dict[str, Any]:
        """
        Get graph-based context for extracted entities
        
        Args:
            entities: Extracted entities from query
            question: Original user question
            
        Returns:
            Dict with graph context information
        """
        if not self.graph_builder:
            return {}
        
        graph_context = {
            "causal_paths": [],
            "entity_relationships": {},
            "relevant_subgraph": None
        }
        
        try:
            # Focus on tickers first (most reliable entities)
            primary_entities = list(entities["tickers"])
            if not primary_entities:
                # Fallback to companies or general entities
                primary_entities = list(entities["companies"])[:2]
            if not primary_entities:
                primary_entities = list(entities["general"])[:2]
            
            # Get causal paths for primary entities
            for entity in primary_entities[:3]:  # Limit to 3 entities for performance
                entity_paths = self.graph_builder.find_causal_paths(
                    entity, 
                    max_hops=self.max_graph_hops,
                    min_confidence=self.min_confidence_threshold
                )
                
                if entity_paths:
                    graph_context["causal_paths"].extend(entity_paths[:5])  # Top 5 paths per entity
                
                # Get entity relationship summary
                entity_summary = self.graph_builder.get_entity_summary(entity)
                if entity_summary.get("status") != "not_found":
                    graph_context["entity_relationships"][entity] = entity_summary
            
            # Build relevant subgraph if entities found
            if primary_entities and self.graph_builder.graph:
                try:
                    # Create subgraph centered on primary entities
                    subgraph_nodes = set()
                    for entity in primary_entities:
                        if entity in self.graph_builder.graph:
                            # Add ego graph nodes (entity + immediate neighbors)
                            ego_nodes = set(nx.ego_graph(self.graph_builder.graph, entity, radius=2).nodes())
                            subgraph_nodes.update(ego_nodes)
                    
                    if subgraph_nodes:
                        subgraph = self.graph_builder.graph.subgraph(subgraph_nodes)
                        graph_context["relevant_subgraph"] = {
                            "node_count": len(subgraph.nodes()),
                            "edge_count": len(subgraph.edges()),
                            "entities": list(subgraph_nodes)[:10]  # Sample of nodes
                        }
                        
                except Exception as e:
                    logger.warning(f"Failed to build relevant subgraph: {e}")
            
        except Exception as e:
            logger.error(f"Graph context extraction failed: {e}")
        
        return graph_context
    
    def _synthesize_enhanced_response(self, question: str, rag_result: Dict, 
                                    graph_context: Dict, entities: Dict, 
                                    query_type: str) -> Dict[str, Any]:
        """
        Synthesize enhanced response combining LightRAG and graph context
        
        Args:
            question: Original user question
            rag_result: LightRAG query result
            graph_context: Graph-based context information
            entities: Extracted entities
            query_type: Classified query type
            
        Returns:
            Dict with synthesized enhanced response
        """
        # Base response from LightRAG
        main_response = rag_result.get("result", "No specific information found.")
        
        # Enhanced sections based on available context
        sections = {
            "main_response": main_response,
            "key_insights": self._extract_key_insights(main_response, entities),
            "graph_context": self._format_graph_context(graph_context),
            "sources": "LightRAG document analysis",
            "confidence": self._calculate_response_confidence(rag_result, graph_context)
        }
        
        # Query-type specific enhancements
        if query_type == "risk_analysis":
            sections.update({
                "risk_factors": self._extract_risk_factors(main_response, graph_context),
                "risk_pathways": self._format_risk_pathways(graph_context.get("causal_paths", [])),
                "confidence_info": f"Analysis confidence: {sections['confidence']:.1%}"
            })
        elif query_type == "performance_analysis":
            sections.update({
                "performance_drivers": self._extract_performance_drivers(main_response, graph_context),
                "performance_context": self._format_performance_context(graph_context),
                "related_factors": self._extract_related_factors(graph_context)
            })
        
        # Format using appropriate template
        template = self.response_templates.get(query_type, self.response_templates["default"])
        formatted_response = template.format(**sections)
        
        return {
            "formatted_response": formatted_response,
            "sources": sections["sources"],
            "confidence": sections["confidence"]
        }
    
    def _extract_key_insights(self, main_response: str, entities: Dict) -> str:
        """
        Extract key insights from the main response
        
        Args:
            main_response: Main LightRAG response text
            entities: Extracted entities
            
        Returns:
            Formatted key insights text
        """
        # Look for sentences with key financial terms
        sentences = main_response.split('.')
        insight_keywords = ["revenue", "earnings", "growth", "risk", "margin", "profit", 
                           "decline", "increase", "exposure", "dependency"]
        
        key_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 20:  # Meaningful length
                if any(keyword in sentence.lower() for keyword in insight_keywords):
                    key_sentences.append(f"• {sentence}")
        
        return "\n".join(key_sentences[:3]) if key_sentences else "• Analysis based on available financial data"
    
    def _format_graph_context(self, graph_context: Dict) -> str:
        """
        Format graph context information for display
        
        Args:
            graph_context: Graph context data
            
        Returns:
            Formatted graph context text
        """
        if not graph_context:
            return "No graph relationships available"
        
        context_parts = []
        
        # Format causal paths
        causal_paths = graph_context.get("causal_paths", [])
        if causal_paths:
            context_parts.append("**Key Relationships:**")
            for path in causal_paths[:3]:
                confidence_pct = path.get("confidence", 0) * 100
                context_parts.append(f"• {path.get('path_str', 'Unknown')} (confidence: {confidence_pct:.0f}%)")
        
        # Format entity relationships
        entity_relationships = graph_context.get("entity_relationships", {})
        if entity_relationships:
            context_parts.append("\n**Entity Connections:**")
            for entity, summary in list(entity_relationships.items())[:2]:
                total_connections = summary.get("total_connections", 0)
                context_parts.append(f"• {entity}: {total_connections} total relationships")
        
        return "\n".join(context_parts) if context_parts else "Graph analysis in progress"
    
    def _extract_risk_factors(self, main_response: str, graph_context: Dict) -> str:
        """
        Extract risk factors from response and graph context
        
        Args:
            main_response: Main response text
            graph_context: Graph context data
            
        Returns:
            Formatted risk factors text
        """
        risk_keywords = ["risk", "threat", "vulnerability", "exposure", "uncertainty", "volatility"]
        sentences = main_response.split('.')
        
        risk_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if any(keyword in sentence.lower() for keyword in risk_keywords):
                risk_sentences.append(f"• {sentence}")
        
        # Add graph-based risk paths
        causal_paths = graph_context.get("causal_paths", [])
        risk_paths = [path for path in causal_paths if any(risk_word in path.get("path_str", "").lower() 
                                                          for risk_word in risk_keywords)]
        
        if risk_paths:
            risk_sentences.append("\n**Risk Pathways from Graph:**")
            for path in risk_paths[:2]:
                risk_sentences.append(f"• {path.get('path_str', 'Unknown')}")
        
        return "\n".join(risk_sentences[:5]) if risk_sentences else "Risk analysis based on available data"
    
    def _format_risk_pathways(self, causal_paths: List[Dict]) -> str:
        """
        Format causal paths as risk pathways
        
        Args:
            causal_paths: List of causal path dictionaries
            
        Returns:
            Formatted risk pathways text
        """
        if not causal_paths:
            return "No specific risk pathways identified"
        
        pathways = []
        for i, path in enumerate(causal_paths[:3], 1):
            path_str = path.get("path_str", "Unknown pathway")
            confidence = path.get("confidence", 0) * 100
            pathways.append(f"{i}. {path_str} (confidence: {confidence:.0f}%)")
        
        return "\n".join(pathways)
    
    def _extract_performance_drivers(self, main_response: str, graph_context: Dict) -> str:
        """
        Extract performance drivers from response and graph context
        
        Args:
            main_response: Main response text
            graph_context: Graph context data
            
        Returns:
            Formatted performance drivers text
        """
        performance_keywords = ["revenue", "earnings", "growth", "margin", "profit", "performance"]
        sentences = main_response.split('.')
        
        driver_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if any(keyword in sentence.lower() for keyword in performance_keywords):
                driver_sentences.append(f"• {sentence}")
        
        return "\n".join(driver_sentences[:4]) if driver_sentences else "Performance drivers based on available data"
    
    def _format_performance_context(self, graph_context: Dict) -> str:
        """
        Format performance context from graph relationships
        
        Args:
            graph_context: Graph context data
            
        Returns:
            Formatted performance context text
        """
        causal_paths = graph_context.get("causal_paths", [])
        
        if not causal_paths:
            return "Performance context based on document analysis"
        
        # Look for performance-related paths
        performance_paths = [path for path in causal_paths 
                           if "drives" in path.get("path_str", "").lower() or 
                              "revenue" in path.get("path_str", "").lower()]
        
        if performance_paths:
            context = "**Performance Relationships:**\n"
            for path in performance_paths[:2]:
                context += f"• {path.get('path_str', 'Unknown')}\n"
            return context
        
        return "Performance context derived from relationship analysis"
    
    def _extract_related_factors(self, graph_context: Dict) -> str:
        """
        Extract related factors from graph context
        
        Args:
            graph_context: Graph context data
            
        Returns:
            Formatted related factors text
        """
        entity_relationships = graph_context.get("entity_relationships", {})
        
        if not entity_relationships:
            return "Related factors identified through document analysis"
        
        factors = []
        for entity, summary in list(entity_relationships.items())[:2]:
            outgoing = summary.get("outgoing_relationships", {})
            if outgoing:
                top_relationships = sorted(outgoing.items(), key=lambda x: x[1], reverse=True)[:2]
                for rel_type, count in top_relationships:
                    factors.append(f"• {entity} has {count} '{rel_type}' relationships")
        
        return "\n".join(factors) if factors else "Related factors analysis in progress"
    
    def _calculate_response_confidence(self, rag_result: Dict, graph_context: Dict) -> float:
        """
        Calculate overall confidence score for the enhanced response
        
        Args:
            rag_result: LightRAG result data
            graph_context: Graph context data
            
        Returns:
            Confidence score between 0 and 1
        """
        base_confidence = 0.7  # Base confidence for LightRAG responses
        
        # Boost confidence if graph context available
        if graph_context:
            causal_paths = graph_context.get("causal_paths", [])
            if causal_paths:
                # Average confidence of top causal paths
                path_confidences = [path.get("confidence", 0) for path in causal_paths[:3]]
                avg_path_confidence = sum(path_confidences) / len(path_confidences) if path_confidences else 0
                base_confidence = 0.6 * base_confidence + 0.4 * avg_path_confidence
            
            # Boost for entity relationships
            if graph_context.get("entity_relationships"):
                base_confidence += 0.05
        
        return min(0.95, base_confidence)  # Cap at 95%