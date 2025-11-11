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

# Import citation formatter for user-facing traceability display
from src.ice_core.citation_formatter import CitationFormatter

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

    def _query_with_fallback(self, question: str, mode: str) -> Dict[str, Any]:
        """
        Execute LightRAG query with automatic mode fallback for robustness

        Week 4 Integration: Implements mix → hybrid → local cascade for advanced modes

        Args:
            question: User's investment question
            mode: Requested LightRAG query mode

        Returns:
            Query result dict from first successful mode
        """
        # Define fallback chains for advanced modes
        fallback_chain = {
            'mix': ['mix', 'hybrid', 'local'],
            'hybrid': ['hybrid', 'local']
        }
        # Use fallback chain if available, otherwise try only requested mode
        modes_to_try = fallback_chain.get(mode, [mode])

        last_error = None
        for attempt_mode in modes_to_try:
            try:
                logger.info(f"Attempting query with mode: {attempt_mode}")
                result = self.lightrag.query(question, attempt_mode)

                if result.get("status") == "success":
                    if attempt_mode != mode:
                        logger.warning(f"Fallback successful: {mode} → {attempt_mode}")
                    return result

            except Exception as e:
                logger.warning(f"Mode {attempt_mode} failed: {e}")
                last_error = e
                continue

        # All modes failed
        return {
            "status": "error",
            "message": f"All query modes failed. Last error: {str(last_error)}",
            "attempted_modes": modes_to_try
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

            # Step 2: Execute LightRAG semantic search with fallback (Week 4 enhancement)
            rag_result = self._query_with_fallback(question, mode)

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

            # Step 5: Apply Contextual Traceability System (Week 7 enhancement)
            # Classify temporal intent
            temporal_intent = self._classify_temporal_intent(question)

            # Enrich source metadata with quality badges, links, temporal context
            # Use rich parsed_context if available (chunk-level attribution), fallback to simple sources
            sources = enhanced_response.get("sources", [])
            parsed_context = enhanced_response.get("parsed_context")

            if parsed_context and parsed_context.get('chunks'):
                # Use sophisticated chunk-level attribution from context_parser
                enriched_metadata = self._enrich_chunks_metadata(parsed_context.get('chunks'), temporal_intent)
            else:
                # Fallback to simple source enrichment for backward compatibility
                enriched_metadata = self._enrich_source_metadata(sources, temporal_intent)

            # Calculate adaptive confidence (scenario-specific formulas)
            reliability = self._calculate_adaptive_confidence(sources, graph_context)

            # Detect conflicts when sources disagree (variance > 10%)
            conflicts = self._detect_conflicts(enriched_metadata['enriched_sources'])

            # Format user-facing citations from enriched sources (Week 7.5 enhancement)
            # Surfaces ICE's backend traceability in readable formats
            citation_display = CitationFormatter.format_citations(
                answer=enhanced_response["formatted_response"],
                enriched_sources=enriched_metadata["enriched_sources"],
                style="inline",  # Default to inline, can be made configurable
                max_inline=3  # Show top 3 sources, truncate rest
            )

            return {
                "status": "success",
                "result": enhanced_response["formatted_response"],
                "answer": enhanced_response["formatted_response"],  # Alias for adaptive display
                "entities": entities,
                "query_type": query_type,
                "graph_context": graph_context,
                "sources": sources,
                "confidence": enhanced_response["confidence"],

                # NEW: Contextual Traceability fields (backward compatible - optional)
                "query_classification": {
                    "business_type": query_type,
                    "temporal_intent": temporal_intent
                },
                "reliability": reliability,
                "source_metadata": enriched_metadata,
                "conflicts": conflicts,
                "citation_display": citation_display  # NEW: User-facing citation string
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

    def _classify_temporal_intent(self, question: str) -> str:
        """
        Classify query temporal intent using keyword heuristics

        Purpose: Determines what type of temporal context is relevant for a query.
        This drives adaptive display of freshness metrics and temporal attribution.

        Why: Freshness matters for "current headwinds" but NOT for "Q2 2025 margin".
        Different query types require different temporal contextualization.

        Args:
            question: User's question text

        Returns:
            Temporal classification: 'historical' | 'current' | 'trend' | 'forward' | 'unknown'

        Examples:
            "What was Tencent's Q2 2025 operating margin?" -> 'historical'
            "What are the current headwinds for NVDA?" -> 'current'
            "How has AAPL revenue been trending?" -> 'trend'
            "What is TSMC's target price?" -> 'forward'
        """
        q_lower = question.lower()

        # Historical queries: Past facts, quarterly results, reported financials
        # Patterns: Q2 2025, fiscal 2024, FY2023, was/were, reported, previous, last quarter
        # Note: Using lowercase patterns since q_lower is already lowercased
        historical_patterns = [
            r'q\d+\s+\d{4}',           # q2 2025, q4 2024 (lowercase after .lower())
            r'fy\s*\d{4}',             # fy2024, fy 2023
            r'fiscal\s+\d{4}',         # fiscal 2024
            r'\d{4}\s+fiscal',         # 2024 fiscal
            r'year\s+\d{4}'            # year 2024
        ]
        historical_keywords = [
            'was', 'were', 'reported', 'announced', 'previous', 'past',
            'last quarter', 'last year', 'historical', 'earned', 'posted'
        ]

        # Check historical patterns first (more specific)
        if any(re.search(pattern, q_lower) for pattern in historical_patterns):
            return 'historical'
        if any(keyword in q_lower for keyword in historical_keywords):
            return 'historical'

        # Current queries: Real-time status, present situation, latest info
        # Keywords: current, now, today, latest, present, currently
        current_keywords = [
            'current', 'now', 'today', 'latest', 'present', 'currently',
            'right now', 'at present', 'this moment', 'as of now'
        ]
        if any(keyword in q_lower for keyword in current_keywords):
            return 'current'

        # Trend queries: Changes over time, patterns, trajectories
        # Keywords: trend, trending, over time, changing, evolution
        trend_keywords = [
            'trend', 'trending', 'over time', 'changing', 'evolution',
            'trajectory', 'pattern', 'historically', 'progression',
            'how has', 'been growing', 'been declining'
        ]
        if any(keyword in q_lower for keyword in trend_keywords):
            return 'trend'

        # Forward-looking queries: Predictions, targets, forecasts
        # Keywords: target, outlook, forecast, will, expect, guidance, future
        forward_keywords = [
            'target', 'outlook', 'forecast', 'will be', 'expected',
            'guidance', 'future', 'predict', 'projection', 'ahead',
            'going forward', 'next quarter', 'next year', 'upcoming'
        ]
        if any(keyword in q_lower for keyword in forward_keywords):
            return 'forward'

        # Default: Cannot determine temporal intent
        # This is safe - we simply won't display temporal context
        logger.debug(f"Could not classify temporal intent for query: {question}")
        return 'unknown'

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
            "sources": rag_result.get("sources", []),  # Use real sources from LightRAG
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
            "parsed_context": rag_result.get("parsed_context"),  # Pass through rich context for chunk-level attribution
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

    def _calculate_adaptive_confidence(self, sources: List[Dict], graph_context: Dict = None) -> Dict[str, Any]:
        """
        Calculate confidence using scenario-specific formulas

        Purpose: Different reasoning scenarios require different confidence semantics.
        Simple averaging misleads when sources conflict or multi-hop reasoning is used.

        Why: User critique identified that "overall confidence" is misleading.
        Confidence must adapt to: single fact vs multi-fact vs multi-hop vs conflicting sources.

        Args:
            sources: List of source dicts with 'source', 'confidence', optional 'value' for numerical data
            graph_context: Optional graph context with 'causal_paths' for multi-hop reasoning

        Returns:
            Dict with:
                - confidence: Float (final confidence score)
                - confidence_type: Str (weighted_average | variance_penalized | path_integrity | single_source)
                - explanation: Str (human-readable explanation)
                - breakdown: Dict (per-source confidence scores)

        Examples:
            Single authoritative source (SEC filing) -> 'single_source', 0.98
            Multiple agreeing sources -> 'weighted_average', 0.92
            Multiple conflicting sources -> 'variance_penalized', 0.67
            Multi-hop reasoning -> 'path_integrity', 0.66 (multiplicative)
        """
        # Edge case: No sources
        if not sources:
            return {
                'confidence': 0.0,
                'confidence_type': 'no_sources',
                'explanation': 'No sources available',
                'breakdown': {}
            }

        # Scenario 1: Single source (most common for factual queries)
        if len(sources) == 1:
            source_conf = sources[0].get('confidence', 0.7)
            source_name = sources[0].get('source', 'unknown')
            return {
                'confidence': source_conf,
                'confidence_type': 'single_source',
                'explanation': f'Single authoritative source: {source_name}',
                'breakdown': {source_name: source_conf}
            }

        # Scenario 2: Multi-hop reasoning (check graph_context for causal paths)
        if graph_context and graph_context.get('causal_paths'):
            return self._apply_path_integrity(sources, graph_context)

        # Scenario 3: Check if sources have conflicting numerical values
        has_variance, variance_data = self._has_variance(sources)
        if has_variance:
            return self._apply_variance_penalty(sources, variance_data)

        # Scenario 4: Multiple agreeing sources (default weighted average)
        return self._apply_weighted_average(sources)

    def _has_variance(self, sources: List[Dict]) -> Tuple[bool, Dict]:
        """
        Check if sources contain conflicting numerical values

        Returns:
            Tuple of (has_variance: bool, variance_data: dict)
            variance_data contains: values, mean, std, coef_var
        """
        # Extract numerical values from sources (if present)
        values = []
        for source in sources:
            if 'value' in source and isinstance(source['value'], (int, float)):
                values.append(float(source['value']))

        # Need at least 2 values to compute variance
        if len(values) < 2:
            return False, {}

        import statistics
        mean = statistics.mean(values)
        std = statistics.stdev(values) if len(values) > 1 else 0
        coef_var = (std / mean) if mean != 0 else 0

        # Flag variance if coefficient of variation > 0.1 (10% disagreement)
        has_variance = coef_var > 0.1

        return has_variance, {
            'values': values,
            'mean': mean,
            'std': std,
            'coef_var': coef_var
        }

    def _apply_variance_penalty(self, sources: List[Dict], variance_data: Dict) -> Dict[str, Any]:
        """
        Apply variance penalty when sources disagree on numerical values

        Formula: base_confidence * (1 - coef_var)
        Example: 3 sources with coef_var=0.15 -> 0.90 * 0.85 = 0.765
        """
        base_conf = self._apply_weighted_average(sources)['confidence']
        coef_var = variance_data['coef_var']
        penalized_conf = base_conf * (1 - coef_var)

        return {
            'confidence': max(0.5, penalized_conf),  # Floor at 0.5
            'confidence_type': 'variance_penalized',
            'explanation': f'Sources disagree ({coef_var:.1%} variance), confidence penalized',
            'breakdown': {s['source']: s.get('confidence', 0.7) for s in sources}
        }

    def _apply_path_integrity(self, sources: List[Dict], graph_context: Dict) -> Dict[str, Any]:
        """
        Calculate path integrity confidence for multi-hop reasoning

        Formula: Multiplicative confidence across reasoning hops
        Example: 3-hop path with [0.85, 0.90, 0.87] -> 0.85 * 0.90 * 0.87 = 0.666
        """
        causal_paths = graph_context.get('causal_paths', [])
        if not causal_paths:
            return self._apply_weighted_average(sources)

        # Get top path confidence
        top_path = causal_paths[0]
        path_conf = top_path.get('confidence', 0.7)
        num_hops = len(top_path.get('path', []))

        return {
            'confidence': path_conf,
            'confidence_type': 'path_integrity',
            'explanation': f'{num_hops}-hop reasoning chain, multiplicative confidence',
            'breakdown': {s['source']: s.get('confidence', 0.7) for s in sources}
        }

    def _apply_weighted_average(self, sources: List[Dict]) -> Dict[str, Any]:
        """
        Calculate weighted average confidence for agreeing sources

        Source quality weights (based on ICE design principles):
        - SEC filings: 0.5 (primary, regulatory)
        - FMP API: 0.3 (secondary, aggregated)
        - News/Email: 0.2 (tertiary, qualitative)

        Formula: sum(weight_i * confidence_i) / sum(weights_i)
        """
        # Configuration: Source quality weights
        source_weights = {
            'sec': 0.5,
            'sec_edgar': 0.5,
            'fmp': 0.3,
            'api': 0.3,
            'email': 0.2,
            'news': 0.2,
            'newsapi': 0.2,
            'unknown': 0.1
        }

        weighted_sum = 0.0
        total_weight = 0.0
        breakdown = {}

        for source in sources:
            source_name = source.get('source', 'unknown').lower()
            confidence = source.get('confidence', 0.7)

            # Match source name to weight (fuzzy matching)
            weight = source_weights.get(source_name, 0.1)
            for key in source_weights:
                if key in source_name:
                    weight = source_weights[key]
                    break

            weighted_sum += weight * confidence
            total_weight += weight
            breakdown[source_name] = confidence

        final_conf = weighted_sum / total_weight if total_weight > 0 else 0.7

        return {
            'confidence': final_conf,
            'confidence_type': 'weighted_average',
            'explanation': f'Weighted average across {len(sources)} agreeing sources',
            'breakdown': breakdown
        }

    def _enrich_source_metadata(self, sources: List[Dict], temporal_intent: str) -> Dict[str, Any]:
        """
        Enrich source metadata with quality badges, links, and temporal context

        Purpose: Transform raw SOURCE markers into actionable, informative metadata.
        Adds visual quality indicators, clickable links, and temporal context when relevant.

        Why: Users need to quickly assess source credibility and access original materials.
        Temporal context shown ONLY when query type requires it (user's key feedback).

        Args:
            sources: List of source dicts from LightRAG extraction
            temporal_intent: Query temporal classification (historical/current/trend/forward/unknown)

        Returns:
            Dict with:
                - enriched_sources: List of sources with quality badges, links, timestamps
                - temporal_context: Dict (only if temporal_intent != 'unknown')
                    - most_recent: Source with latest timestamp
                    - oldest: Source with earliest timestamp
                    - age_range: "2 days - 3 months" human-readable range

        Example enriched source:
            {
                'source': 'sec_edgar',
                'confidence': 0.98,
                'quality_badge': '🟢 Primary',
                'link': 'https://www.sec.gov/cgi-bin/browse-edgar?...',
                'timestamp': '2024-03-15',
                'age': '2 days ago'
            }
        """
        enriched = []

        for source in sources:
            source_name = source.get('source', 'unknown').lower()
            confidence = source.get('confidence', 0.7)

            # Add quality badge based on ICE source hierarchy
            quality_badge = self._get_quality_badge(source_name)

            # Attempt to extract/construct clickable link
            link = self._extract_or_construct_link(source)

            # Extract temporal information (timestamp, age)
            temporal_info = self._extract_temporal_info(source)

            enriched_source = {
                'source': source_name,
                'confidence': confidence,
                'quality_badge': quality_badge,
                'link': link if link else None,
                **temporal_info  # Adds 'timestamp', 'age' if present
            }

            # Preserve any additional fields from original source
            for key, value in source.items():
                if key not in enriched_source:
                    enriched_source[key] = value

            enriched.append(enriched_source)

        # Build temporal context ONLY if query requires it
        temporal_context = None
        if temporal_intent in ['current', 'trend'] and enriched:
            temporal_context = self._build_temporal_context(enriched)

        return {
            'enriched_sources': enriched,
            'temporal_context': temporal_context
        }

    def _enrich_chunks_metadata(self, chunks: List[Dict], temporal_intent: str) -> Dict[str, Any]:
        """
        Enrich chunks from context_parser with quality badges and links

        Purpose: Leverage sophisticated chunk-level attribution from LightRAGContextParser.
        Chunks already have source_type, confidence, date, relevance_rank from 3-tier fallback.
        This method adds visual quality indicators and clickable links.

        Why: Eliminates redundant SOURCE marker parsing by using pre-parsed rich chunks.
        Gains chunk-level attribution, relevance ranking, and 3-tier fallback automatically.

        Args:
            chunks: Pre-parsed chunks from LightRAGContextParser.parse_context()
                Each chunk has: chunk_id, content, file_path, source_type, source_details,
                confidence, date, relevance_rank
            temporal_intent: Query temporal classification (historical/current/trend/forward/unknown)

        Returns:
            Dict with:
                - enriched_sources: List of enriched chunks with quality badges, links
                - temporal_context: Dict (only if temporal_intent != 'unknown')

        Example enriched chunk:
            {
                'chunk_id': 1,
                'content': '...',
                'file_path': '...',
                'source_type': 'email',
                'source_details': {'subject': '...', 'sender': '...'},
                'confidence': 0.90,
                'date': '2025-08-15',
                'relevance_rank': 1,
                'quality_badge': '🔴 Tertiary',  # Added by this method
                'link': 'mailto:...',  # Added by this method
                'age': '2 days ago'  # Added by temporal extraction
            }
        """
        enriched = []

        for chunk in chunks:
            # Extract source info (already parsed by context_parser)
            source_type = chunk.get('source_type', 'unknown')
            confidence = chunk.get('confidence', 0.7)

            # Add quality badge based on ICE source hierarchy
            quality_badge = self._get_quality_badge(source_type)

            # Attempt to construct clickable link from source_details
            source_details = chunk.get('source_details', {})
            link = self._construct_link_from_details(source_type, source_details)

            # Extract temporal information if available
            date = chunk.get('date')
            temporal_info = {}
            if date:
                temporal_info = {
                    'timestamp': date,
                    'age': self._calculate_age(date)
                }

            # Build enriched chunk (preserve all original fields + add new ones)
            enriched_chunk = {
                **chunk,  # Keep all existing chunk data
                'quality_badge': quality_badge,
                'link': link if link else None,
                **temporal_info  # Adds 'timestamp', 'age' if date present
            }

            enriched.append(enriched_chunk)

        # Build temporal context ONLY if query requires it
        temporal_context = None
        if temporal_intent in ['current', 'trend'] and enriched:
            temporal_context = self._build_temporal_context(enriched)

        return {
            'enriched_sources': enriched,
            'temporal_context': temporal_context
        }

    def _construct_link_from_details(self, source_type: str, source_details: Dict) -> Optional[str]:
        """
        Construct clickable link from source_details

        Args:
            source_type: 'email', 'api', 'sec', 'entity_extraction', 'unknown'
            source_details: Type-specific details from context_parser

        Returns:
            Clickable link string or None
        """
        if source_type == 'email':
            sender = source_details.get('sender')
            subject = source_details.get('subject')
            if sender and subject:
                return f"mailto:{sender}?subject=Re: {subject[:50]}"

        elif source_type == 'api':
            # Try to construct link based on API provider
            api_provider = source_details.get('api', '').lower()
            symbol = source_details.get('symbol')

            if api_provider == 'fmp' and symbol:
                return f"https://financialmodelingprep.com/financial-summary/{symbol}"
            elif api_provider == 'newsapi' and symbol:
                return f"https://newsapi.org/search?q={symbol}"

        elif source_type == 'sec':
            filing_type = source_details.get('filing_type', '')
            # Could extract ticker from filing_type if format is "10-K:NVDA"
            if ':' in filing_type:
                parts = filing_type.split(':', 1)
                ticker = parts[1] if len(parts) > 1 else None
                if ticker:
                    return f"https://www.sec.gov/cgi-bin/browse-edgar?company={ticker}&action=getcompany"

        return None

    def _calculate_age(self, date_str: str) -> str:
        """
        Calculate human-readable age from date string

        Args:
            date_str: ISO format date string '2025-08-15'

        Returns:
            Human-readable age like '2 days ago', '3 months ago'
        """
        from datetime import datetime, timedelta

        try:
            date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            now = datetime.now(date.tzinfo) if date.tzinfo else datetime.now()
            delta = now - date

            if delta.days < 1:
                hours = delta.seconds // 3600
                return f"{hours} hours ago" if hours > 1 else "less than 1 hour ago"
            elif delta.days == 1:
                return "1 day ago"
            elif delta.days < 7:
                return f"{delta.days} days ago"
            elif delta.days < 30:
                weeks = delta.days // 7
                return f"{weeks} week{'s' if weeks > 1 else ''} ago"
            elif delta.days < 365:
                months = delta.days // 30
                return f"{months} month{'s' if months > 1 else ''} ago"
            else:
                years = delta.days // 365
                return f"{years} year{'s' if years > 1 else ''} ago"

        except (ValueError, AttributeError):
            return "unknown age"

    def _get_quality_badge(self, source_name: str) -> str:
        """
        Get visual quality badge for source based on ICE hierarchy

        Quality tiers (from ICE design principles):
        🟢 Primary: SEC filings (regulatory, audited)
        🟡 Secondary: FMP API, aggregated financials
        🔴 Tertiary: News, email (qualitative, opinions)
        ⚪ Unknown: Unclassified sources

        Args:
            source_name: Source identifier (lowercase)

        Returns:
            Quality badge string (emoji + label)
        """
        if any(key in source_name for key in ['sec', 'edgar', '10-k', '10-q']):
            return '🟢 Primary'
        elif any(key in source_name for key in ['fmp', 'api', 'financial']):
            return '🟡 Secondary'
        elif any(key in source_name for key in ['email', 'news', 'article']):
            return '🔴 Tertiary'
        else:
            return '⚪ Unknown'

    def _extract_or_construct_link(self, source: Dict) -> Optional[str]:
        """
        Extract existing link or construct one from source metadata

        Strategy:
        1. Check for explicit 'url' or 'link' field
        2. Check for 'file_path' to construct file:// link
        3. Construct SEC EDGAR link if source has CIK/filing info
        4. Return None if no link can be determined

        Args:
            source: Source dict with metadata

        Returns:
            Clickable URL string or None
        """
        # Direct link fields
        if 'url' in source and source['url']:
            return source['url']
        if 'link' in source and source['link']:
            return source['link']

        # File path to file:// URL
        if 'file_path' in source and source['file_path']:
            file_path = source['file_path']
            return f"file://{file_path}"

        # Construct SEC EDGAR link if we have CIK + filing metadata
        if 'cik' in source or 'ticker' in source:
            return self._construct_sec_link(source)

        return None

    def _construct_sec_link(self, source: Dict) -> Optional[str]:
        """
        Construct SEC EDGAR browser link from source metadata

        Pattern: https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0000320193&type=10-K&dateb=&owner=exclude&count=40

        Args:
            source: Source dict with CIK or ticker

        Returns:
            SEC EDGAR URL or None
        """
        cik = source.get('cik')
        ticker = source.get('ticker', source.get('symbol'))
        filing_type = source.get('filing_type', '10-K')

        if cik:
            # Pad CIK to 10 digits
            cik_padded = str(cik).zfill(10)
            return f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik_padded}&type={filing_type}"
        elif ticker:
            # SEC also accepts ticker symbols
            return f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={ticker}&type={filing_type}"

        return None

    def _extract_temporal_info(self, source: Dict) -> Dict[str, str]:
        """
        Extract timestamp and calculate human-readable age

        Looks for: 'timestamp', 'date', 'published_at', 'created_at' fields
        Calculates age: "2 days ago", "3 months ago", "1 year ago"

        Args:
            source: Source dict

        Returns:
            Dict with 'timestamp' (ISO format) and 'age' (human-readable)
        """
        from datetime import datetime

        # Try to find timestamp field
        timestamp = None
        for field in ['timestamp', 'date', 'published_at', 'created_at']:
            if field in source and source[field]:
                timestamp = source[field]
                break

        if not timestamp:
            return {}

        # Parse timestamp (handle various formats)
        try:
            if isinstance(timestamp, str):
                # Try ISO format first
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            elif isinstance(timestamp, datetime):
                dt = timestamp
            else:
                return {}

            # Calculate age
            now = datetime.now(dt.tzinfo) if dt.tzinfo else datetime.now()
            age_delta = now - dt

            # Human-readable age
            if age_delta.days == 0:
                age = "today"
            elif age_delta.days == 1:
                age = "1 day ago"
            elif age_delta.days < 30:
                age = f"{age_delta.days} days ago"
            elif age_delta.days < 365:
                months = age_delta.days // 30
                age = f"{months} month{'s' if months > 1 else ''} ago"
            else:
                years = age_delta.days // 365
                age = f"{years} year{'s' if years > 1 else ''} ago"

            return {
                'timestamp': dt.isoformat(),
                'age': age
            }

        except Exception as e:
            logger.debug(f"Failed to parse timestamp {timestamp}: {e}")
            return {}

    def _build_temporal_context(self, enriched_sources: List[Dict]) -> Dict[str, Any]:
        """
        Build temporal context summary for current/trend queries

        Shows: Most recent source, oldest source, age range
        Only called when temporal_intent in ['current', 'trend']

        Args:
            enriched_sources: List of enriched source dicts with timestamps

        Returns:
            Dict with most_recent, oldest, age_range
        """
        from datetime import datetime

        sources_with_time = [s for s in enriched_sources if 'timestamp' in s]

        if not sources_with_time:
            return {
                'most_recent': None,
                'oldest': None,
                'age_range': 'Timestamps not available'
            }

        # Sort by timestamp
        try:
            sorted_sources = sorted(
                sources_with_time,
                key=lambda s: datetime.fromisoformat(s['timestamp']),
                reverse=True
            )

            most_recent = sorted_sources[0]
            oldest = sorted_sources[-1]

            age_range = f"{most_recent['age']} - {oldest['age']}"

            return {
                'most_recent': {
                    'source': most_recent['source'],
                    'age': most_recent['age']
                },
                'oldest': {
                    'source': oldest['source'],
                    'age': oldest['age']
                },
                'age_range': age_range
            }

        except Exception as e:
            logger.debug(f"Failed to build temporal context: {e}")
            return {
                'most_recent': None,
                'oldest': None,
                'age_range': 'Timestamps not available'
            }

    def _detect_conflicts(self, enriched_sources: List[Dict]) -> Optional[Dict[str, Any]]:
        """
        Detect conflicts when sources disagree on numerical values

        Purpose: Surface disagreements transparently instead of hiding them in averages.
        Users need to see when sources conflict to assess answer reliability.

        Why: User emphasized that conflicting sources should be flagged, not hidden.
        Variance >10% indicates material disagreement requiring user awareness.

        Args:
            enriched_sources: List of enriched source dicts (from _enrich_source_metadata)

        Returns:
            Dict with conflict details if variance >10%, None otherwise:
                - detected: bool (always True if returned)
                - values: List of conflicting values
                - sources: List of source names
                - variance: Coefficient of variation (%)
                - explanation: Human-readable description

        Example conflict:
            {
                'detected': True,
                'values': [100, 120, 95],
                'sources': ['sec', 'api', 'email'],
                'variance': 0.122,
                'explanation': '3 sources disagree (12.2% variance): values range from 95 to 120'
            }
        """
        # Extract sources with numerical values
        sources_with_values = []
        for source in enriched_sources:
            if 'value' in source and isinstance(source['value'], (int, float)):
                sources_with_values.append({
                    'source': source.get('source', 'unknown'),
                    'value': float(source['value']),
                    'confidence': source.get('confidence', 0.7)
                })

        # Need at least 2 values to detect conflict
        if len(sources_with_values) < 2:
            return None

        # Calculate variance
        values = [s['value'] for s in sources_with_values]
        source_names = [s['source'] for s in sources_with_values]

        import statistics
        mean = statistics.mean(values)
        std = statistics.stdev(values) if len(values) > 1 else 0
        coef_var = (std / mean) if mean != 0 else 0

        # Flag conflict if coefficient of variation > 0.1 (10% threshold)
        if coef_var <= 0.1:
            return None

        # Build conflict explanation
        min_val = min(values)
        max_val = max(values)

        explanation = (
            f"{len(values)} sources disagree ({coef_var:.1%} variance): "
            f"values range from {min_val:.2f} to {max_val:.2f}"
        )

        return {
            'detected': True,
            'values': values,
            'sources': source_names,
            'variance': coef_var,
            'explanation': explanation,
            'mean': mean,
            'std': std
        }

    def format_adaptive_display(self, enriched_result: Dict[str, Any]) -> str:
        """
        Format adaptive traceability display based on query context

        Purpose: Main user-facing formatter that orchestrates context-adaptive information disclosure.
        Different queries show different cards - no fixed "Level 1/2/3" structure.

        Why: User feedback showed fixed levels mislead. Information must adapt to query type.
        Always show: Answer + Reliability + Sources
        Conditionally show: Temporal context (current/trend), Conflicts (if detected), Reasoning path (multi-hop)

        Args:
            enriched_result: Dict with all traceability data:
                - answer: Str (AI-generated answer)
                - query_classification: Dict (business_type, temporal_intent)
                - reliability: Dict (confidence, type, explanation, breakdown)
                - source_metadata: Dict (enriched_sources, temporal_context)
                - conflicts: Dict or None (conflict details if detected)
                - graph_context: Dict or None (causal_paths for multi-hop)

        Returns:
            Formatted display string with adaptive cards

        Example output (current query with conflict):
            ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            ✅ ANSWER
            ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            NVDA faces supply chain risks from TSMC's China exposure...

            ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            🎯 RELIABILITY
            ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            Confidence: 85% (weighted_average)
            Explanation: Weighted average across 3 agreeing sources
            Breakdown: SEC (98%), FMP (90%), Email (75%)

            ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            📚 SOURCES
            ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            1. 🟢 Primary: sec_edgar (98% confidence)
               Link: https://www.sec.gov/...
               Age: 2 days ago

            2. 🟡 Secondary: fmp (90% confidence)
               Link: https://financialmodelingprep.com/...
               Age: 1 day ago

            3. 🔴 Tertiary: email (75% confidence)
               Age: today

            ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            ⏰ TEMPORAL CONTEXT
            ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            Most Recent: fmp (1 day ago)
            Oldest: sec_edgar (2 days ago)
            Age Range: today - 2 days ago

            ⚠️  CONFLICTS DETECTED
            ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            3 sources disagree (12.2% variance): values range from 95.00 to 120.00
            Sources: sec (100), api (120), email (95)
        """
        # Build adaptive card list
        cards = []

        # ALWAYS SHOW: Answer card
        answer_card = self._format_answer_card(enriched_result.get('answer', 'No answer available'))
        cards.append(answer_card)

        # ALWAYS SHOW: Reliability card
        reliability_data = enriched_result.get('reliability')
        if reliability_data:
            reliability_card = self._format_reliability_card(reliability_data)
            cards.append(reliability_card)

        # ALWAYS SHOW: Sources card
        source_metadata = enriched_result.get('source_metadata', {})
        enriched_sources = source_metadata.get('enriched_sources', [])
        if enriched_sources:
            source_card = self._format_source_card(enriched_sources)
            cards.append(source_card)

        # CONDITIONAL: Temporal context (only for current/trend queries)
        temporal_context = source_metadata.get('temporal_context')
        if temporal_context:
            temporal_card = self._format_temporal_card(temporal_context)
            cards.append(temporal_card)

        # CONDITIONAL: Conflicts (only if detected)
        conflicts = enriched_result.get('conflicts')
        if conflicts and conflicts.get('detected'):
            conflict_card = self._format_conflict_card(conflicts)
            cards.append(conflict_card)

        # CONDITIONAL: Reasoning path (only for multi-hop queries)
        graph_context = enriched_result.get('graph_context')
        if graph_context and graph_context.get('causal_paths'):
            reasoning_card = self._format_reasoning_card(graph_context)
            cards.append(reasoning_card)

        # Join all cards with spacing
        return '\n\n'.join(cards)

    def _format_answer_card(self, answer: str) -> str:
        """Format answer card (always shown)"""
        separator = "━" * 50
        return f"""{separator}
✅ ANSWER
{separator}
{answer}"""

    def _format_reliability_card(self, reliability: Dict[str, Any]) -> str:
        """
        Format reliability card with confidence score and explanation

        Shows:
        - Overall confidence percentage
        - Confidence type (weighted_average | variance_penalized | path_integrity | single_source)
        - Human-readable explanation
        - Per-source confidence breakdown
        """
        separator = "━" * 50
        confidence = reliability.get('confidence', 0) * 100
        conf_type = reliability.get('confidence_type', 'unknown')
        explanation = reliability.get('explanation', 'No explanation available')
        breakdown = reliability.get('breakdown', {})

        # Build breakdown text
        breakdown_lines = []
        for source, conf in breakdown.items():
            breakdown_lines.append(f"  • {source}: {conf*100:.0f}%")

        breakdown_text = "\n".join(breakdown_lines) if breakdown_lines else "  • No breakdown available"

        return f"""{separator}
🎯 RELIABILITY
{separator}
Confidence: {confidence:.0f}% ({conf_type})
Explanation: {explanation}

Breakdown:
{breakdown_text}"""

    def _format_source_card(self, enriched_sources: List[Dict]) -> str:
        """
        Format sources card with quality badges, links, and metadata

        Shows for each source:
        - Quality badge (🟢 Primary | 🟡 Secondary | 🔴 Tertiary)
        - Source name
        - Confidence percentage
        - Clickable link (if available)
        - Age (if available)
        """
        separator = "━" * 50
        source_lines = []

        for i, source in enumerate(enriched_sources, 1):
            source_name = source.get('source', 'unknown')
            quality_badge = source.get('quality_badge', '⚪ Unknown')
            confidence = source.get('confidence', 0) * 100
            link = source.get('link')
            age = source.get('age')

            # Build source entry
            source_entry = f"{i}. {quality_badge}: {source_name} ({confidence:.0f}% confidence)"

            # Add link if available
            if link:
                source_entry += f"\n   Link: {link}"

            # Add age if available
            if age:
                source_entry += f"\n   Age: {age}"

            source_lines.append(source_entry)

        sources_text = "\n\n".join(source_lines) if source_lines else "No sources available"

        return f"""{separator}
📚 SOURCES
{separator}
{sources_text}"""

    def _format_temporal_card(self, temporal_context: Dict[str, Any]) -> str:
        """
        Format temporal context card (only for current/trend queries)

        Shows:
        - Most recent source and age
        - Oldest source and age
        - Age range across all sources
        """
        separator = "━" * 50
        most_recent = temporal_context.get('most_recent')
        oldest = temporal_context.get('oldest')
        age_range = temporal_context.get('age_range', 'Unknown')

        if not most_recent or not oldest:
            return f"""{separator}
⏰ TEMPORAL CONTEXT
{separator}
{age_range}"""

        return f"""{separator}
⏰ TEMPORAL CONTEXT
{separator}
Most Recent: {most_recent['source']} ({most_recent['age']})
Oldest: {oldest['source']} ({oldest['age']})
Age Range: {age_range}"""

    def _format_conflict_card(self, conflicts: Dict[str, Any]) -> str:
        """
        Format conflict warning card (only when variance > 10%)

        Shows:
        - Warning indicator
        - Explanation of disagreement
        - Source-by-source value breakdown
        """
        separator = "━" * 50
        explanation = conflicts.get('explanation', 'Sources disagree on values')
        values = conflicts.get('values', [])
        sources = conflicts.get('sources', [])

        # Build source-value pairs
        value_pairs = []
        for source, value in zip(sources, values):
            value_pairs.append(f"  • {source}: {value:.2f}")

        values_text = "\n".join(value_pairs) if value_pairs else "  • No values available"

        return f"""⚠️  CONFLICTS DETECTED
{separator}
{explanation}

Values by Source:
{values_text}"""

    def _format_reasoning_card(self, graph_context: Dict[str, Any]) -> str:
        """
        Format reasoning path card (only for multi-hop queries)

        Shows:
        - Number of reasoning hops
        - Path confidence (multiplicative across hops)
        - Step-by-step reasoning chain
        """
        separator = "━" * 50
        causal_paths = graph_context.get('causal_paths', [])

        if not causal_paths:
            return ""

        top_path = causal_paths[0]
        path_conf = top_path.get('confidence', 0) * 100
        path_steps = top_path.get('path', [])
        num_hops = len(path_steps)

        # Build reasoning chain
        chain_text = " → ".join(path_steps) if path_steps else "No path available"

        return f"""{separator}
🔗 REASONING PATH
{separator}
Hops: {num_hops}
Path Confidence: {path_conf:.0f}%
Chain: {chain_text}"""