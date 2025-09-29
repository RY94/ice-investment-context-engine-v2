# Component Specifications for ICE Quality-First Architecture
## Detailed Technical Specifications for LightRAG + LazyGraph + LLM Orchestra

**Document Version**: 1.0  
**Date**: September 2025  
**Purpose**: Comprehensive technical specifications for each system component  

---

## Table of Contents

1. [LivingMemoryRAG Component](#livingmemoryrag-component)
2. [HypothesisLazyGraph Component](#hypothesislazygraph-component)
3. [LocalLLMOrchestra Component](#localllmorchestra-component)
4. [Integration Layer Components](#integration-layer-components)
5. [Data Processing Pipeline](#data-processing-pipeline)
6. [Quality Assurance Systems](#quality-assurance-systems)

---

## LivingMemoryRAG Component

### Overview
The LivingMemoryRAG extends traditional RAG with three types of memory that mirror human cognition: episodic (recent interactions), semantic (concepts and relationships), and procedural (analysis patterns).

### Core Architecture

```python
class LivingMemoryRAG:
    """
    Advanced RAG system with cognitive memory types
    Integrates with existing ICE LightRAG infrastructure
    """
    
    def __init__(self, working_dir: str, config: Dict):
        # Initialize base LightRAG
        self.lightrag = LightRAG(working_dir=working_dir, **config)
        
        # Initialize memory subsystems
        self.episodic_memory = EpisodicMemoryManager()
        self.semantic_memory = SemanticMemoryManager()
        self.procedural_memory = ProceduralMemoryManager()
        
        # Initialize temporal decay system
        self.temporal_decay = TemporalDecayEngine()
        
        # Initialize confidence scoring
        self.confidence_scorer = ConfidenceScorer()
        
        # Initialize cross-document synthesizer
        self.synthesizer = CrossDocumentSynthesizer()
        
    async def absorb_document(self, document: Document) -> DocumentAbsorptionResult:
        """
        Processes document through all memory systems
        
        Args:
            document: Document with content, metadata, source info
            
        Returns:
            DocumentAbsorptionResult with entities, relationships, confidence scores
        """
        absorption_start = time.time()
        
        try:
            # Phase 1: Entity extraction using fast local LLM
            entities = await self._extract_entities(document)
            
            # Phase 2: Relationship inference using reasoning LLM  
            relationships = await self._infer_relationships(entities, document)
            
            # Phase 3: Confidence scoring across all findings
            confidence_scores = await self._score_confidence(
                entities, 
                relationships, 
                document
            )
            
            # Phase 4: Temporal decay application
            temporal_weights = self.temporal_decay.calculate_weights(
                document.timestamp,
                document.source_reliability
            )
            
            # Phase 5: Integration with existing memory
            integration_result = await self._integrate_with_memory(
                entities,
                relationships, 
                confidence_scores,
                temporal_weights
            )
            
            # Phase 6: Update procedural memory with successful patterns
            await self._update_procedural_memory(
                document.type,
                entities,
                relationships,
                integration_result.success_metrics
            )
            
            return DocumentAbsorptionResult(
                entities=entities,
                relationships=relationships,
                confidence_scores=confidence_scores,
                integration_result=integration_result,
                processing_time=time.time() - absorption_start,
                memory_updates=integration_result.memory_changes
            )
            
        except Exception as e:
            return DocumentAbsorptionResult(
                success=False,
                error=str(e),
                processing_time=time.time() - absorption_start
            )
    
    async def _extract_entities(self, document: Document) -> List[Entity]:
        """
        Extract entities using pattern-recognition LLM
        """
        extraction_prompt = self._build_entity_extraction_prompt(document)
        
        # Use fast LLM (Mistral 7B) for entity extraction
        llm_result = await self.llm_orchestra.route_task(
            task_type="entity_extraction",
            content=extraction_prompt,
            requirements={"speed_priority": "high"}
        )
        
        # Parse LLM result into structured entities
        entities = self._parse_entities_from_llm_output(
            llm_result.content,
            document
        )
        
        # Cross-reference with existing semantic memory
        enhanced_entities = await self._enhance_entities_with_memory(entities)
        
        return enhanced_entities
    
    async def _infer_relationships(self, entities: List[Entity], document: Document) -> List[Relationship]:
        """
        Infer relationships using deep reasoning LLM
        """
        relationship_prompt = self._build_relationship_prompt(entities, document)
        
        # Use reasoning LLM (Yi 34B or Llama 70B) for relationship inference
        llm_result = await self.llm_orchestra.route_task(
            task_type="relationship_inference",
            content=relationship_prompt,
            requirements={
                "quality_priority": "high",
                "context_size": len(relationship_prompt.split())
            }
        )
        
        # Parse relationships with confidence scoring
        relationships = self._parse_relationships_from_llm_output(
            llm_result.content,
            entities,
            document
        )
        
        # Validate relationships against existing knowledge
        validated_relationships = await self._validate_relationships(relationships)
        
        return validated_relationships
    
    async def get_contextual_memory(self, query: Query) -> ContextualMemory:
        """
        Retrieves relevant memory based on query context
        Combines all three memory types for comprehensive understanding
        """
        memory_retrieval_start = time.time()
        
        # Analyze query for memory retrieval strategy
        query_analysis = await self._analyze_query_for_memory(query)
        
        # Retrieve from episodic memory (recent similar queries)
        episodic_results = await self.episodic_memory.recall_similar_queries(
            query,
            similarity_threshold=0.7,
            max_results=10,
            time_decay_factor=query_analysis.time_sensitivity
        )
        
        # Retrieve from semantic memory (related concepts)
        semantic_results = await self.semantic_memory.get_related_concepts(
            query,
            depth=query_analysis.concept_depth,
            breadth=query_analysis.concept_breadth
        )
        
        # Retrieve from procedural memory (analysis patterns)
        procedural_results = await self.procedural_memory.get_analysis_patterns(
            query_type=query_analysis.query_type,
            domain=query_analysis.domain,
            complexity=query_analysis.complexity
        )
        
        # Synthesize all memory types into coherent context
        synthesized_memory = await self.synthesizer.synthesize_memory_context(
            episodic=episodic_results,
            semantic=semantic_results,
            procedural=procedural_results,
            query=query
        )
        
        return ContextualMemory(
            episodic=episodic_results,
            semantic=semantic_results, 
            procedural=procedural_results,
            synthesized=synthesized_memory,
            retrieval_time=time.time() - memory_retrieval_start,
            confidence=synthesized_memory.overall_confidence
        )
```

### Memory Subsystem Specifications

```python
class EpisodicMemoryManager:
    """
    Manages recent interactions and their outcomes
    """
    
    def __init__(self):
        self.recent_queries = CircularBuffer(max_size=1000)
        self.query_embeddings = {}
        self.outcome_tracker = QueryOutcomeTracker()
        
    async def store_query_episode(self, query: Query, result: QueryResult):
        """
        Stores query-result episode with contextual metadata
        """
        episode = QueryEpisode(
            query=query,
            result=result,
            timestamp=datetime.now(),
            context_hash=self._compute_context_hash(query),
            success_metrics=result.quality_metrics,
            user_feedback=result.user_feedback
        )
        
        # Store in circular buffer
        self.recent_queries.append(episode)
        
        # Generate and store embedding for similarity search
        query_embedding = await self.embedding_model.encode(query.text)
        self.query_embeddings[episode.id] = query_embedding
        
        # Update outcome patterns
        await self.outcome_tracker.update_patterns(episode)
    
    async def recall_similar_queries(self, query: Query, **kwargs) -> List[QueryEpisode]:
        """
        Recalls similar past queries with their outcomes
        """
        query_embedding = await self.embedding_model.encode(query.text)
        
        # Find semantically similar queries
        similar_episodes = []
        for episode_id, stored_embedding in self.query_embeddings.items():
            similarity = cosine_similarity(query_embedding, stored_embedding)
            
            if similarity >= kwargs.get("similarity_threshold", 0.7):
                episode = self.recent_queries.get_by_id(episode_id)
                similar_episodes.append((episode, similarity))
        
        # Sort by relevance and apply temporal decay
        similar_episodes.sort(key=lambda x: (
            x[1] * self._calculate_temporal_relevance(x[0], kwargs.get("time_decay_factor", 0.1))
        ), reverse=True)
        
        return [episode for episode, _ in similar_episodes[:kwargs.get("max_results", 10)]]


class SemanticMemoryManager:
    """
    Manages conceptual knowledge and relationships
    """
    
    def __init__(self):
        self.concept_graph = ConceptGraph()
        self.relationship_index = RelationshipIndex()
        self.domain_knowledge = DomainKnowledgeBase()
        
    async def store_concept(self, concept: Concept, relationships: List[Relationship]):
        """
        Stores concept with its relationships in semantic memory
        """
        # Add concept to graph
        concept_node = await self.concept_graph.add_concept(concept)
        
        # Add relationships
        for relationship in relationships:
            await self.concept_graph.add_relationship(
                source=concept_node,
                target=relationship.target,
                relationship_type=relationship.type,
                weight=relationship.confidence,
                metadata=relationship.metadata
            )
            
            # Index relationship for fast lookup
            await self.relationship_index.index_relationship(relationship)
        
        # Update domain knowledge
        await self.domain_knowledge.integrate_concept(concept, relationships)
    
    async def get_related_concepts(self, query: Query, **kwargs) -> List[Concept]:
        """
        Retrieves concepts related to query with specified depth/breadth
        """
        # Extract key concepts from query
        query_concepts = await self._extract_query_concepts(query)
        
        # Explore concept graph with specified parameters
        related_concepts = []
        
        for concept in query_concepts:
            # BFS/DFS exploration based on requirements
            exploration_results = await self.concept_graph.explore_from_concept(
                start_concept=concept,
                max_depth=kwargs.get("depth", 3),
                max_breadth=kwargs.get("breadth", 10),
                relationship_filters=kwargs.get("relationship_filters", [])
            )
            
            related_concepts.extend(exploration_results)
        
        # Deduplicate and rank by relevance
        unique_concepts = self._deduplicate_concepts(related_concepts)
        ranked_concepts = await self._rank_concepts_by_relevance(
            unique_concepts,
            query
        )
        
        return ranked_concepts


class ProceduralMemoryManager:
    """
    Manages learned analysis patterns and procedures
    """
    
    def __init__(self):
        self.analysis_patterns = AnalysisPatternDatabase()
        self.successful_procedures = SuccessfulProcedureTracker()
        self.pattern_learner = PatternLearningEngine()
        
    async def learn_pattern(self, analysis_context: AnalysisContext, outcome: AnalysisOutcome):
        """
        Learns successful analysis patterns from outcomes
        """
        # Extract pattern from successful analysis
        if outcome.quality_score >= 8.0:  # High quality threshold
            pattern = await self.pattern_learner.extract_pattern(
                context=analysis_context,
                process=outcome.analysis_process,
                result=outcome.result
            )
            
            # Store pattern for future use
            await self.analysis_patterns.store_pattern(pattern)
            
            # Update success tracking
            await self.successful_procedures.update_success_rate(
                pattern_type=pattern.type,
                context_type=analysis_context.type,
                success=True
            )
    
    async def get_analysis_patterns(self, **kwargs) -> List[AnalysisPattern]:
        """
        Retrieves applicable analysis patterns for given context
        """
        # Find patterns matching the context
        matching_patterns = await self.analysis_patterns.find_patterns(
            query_type=kwargs.get("query_type"),
            domain=kwargs.get("domain"), 
            complexity=kwargs.get("complexity")
        )
        
        # Filter by success rate
        high_success_patterns = [
            pattern for pattern in matching_patterns
            if pattern.success_rate >= 0.8
        ]
        
        # Rank by relevance and success rate
        ranked_patterns = sorted(
            high_success_patterns,
            key=lambda p: (p.relevance_score * p.success_rate),
            reverse=True
        )
        
        return ranked_patterns[:10]  # Return top 10 patterns
```

### Temporal Decay Engine

```python
class TemporalDecayEngine:
    """
    Applies time-based decay to information relevance
    """
    
    def __init__(self):
        self.decay_functions = {
            "linear": self._linear_decay,
            "exponential": self._exponential_decay,
            "logarithmic": self._logarithmic_decay,
            "stepped": self._stepped_decay
        }
        
        self.domain_decay_rates = {
            "breaking_news": 0.1,      # Fast decay
            "earnings_data": 0.05,     # Medium decay
            "fundamental_data": 0.01,  # Slow decay
            "regulatory_data": 0.001   # Very slow decay
        }
    
    def calculate_weights(self, timestamp: datetime, source_reliability: float, 
                         domain: str = "general") -> TemporalWeights:
        """
        Calculates temporal weights for information based on age and domain
        """
        current_time = datetime.now()
        age_days = (current_time - timestamp).days
        age_hours = (current_time - timestamp).total_seconds() / 3600
        
        # Get domain-specific decay rate
        decay_rate = self.domain_decay_rates.get(domain, 0.02)
        
        # Calculate base temporal weight
        temporal_weight = self._exponential_decay(age_days, decay_rate)
        
        # Adjust for source reliability
        reliability_adjusted = temporal_weight * (0.5 + 0.5 * source_reliability)
        
        # Apply recency boost for very recent information
        if age_hours < 24:  # Last 24 hours
            recency_boost = 1.2 - (age_hours / 120)  # Max 20% boost
            reliability_adjusted *= recency_boost
        
        return TemporalWeights(
            base_weight=temporal_weight,
            reliability_adjusted=reliability_adjusted,
            age_days=age_days,
            decay_rate=decay_rate,
            recency_boost=recency_boost if age_hours < 24 else 1.0
        )
    
    def _exponential_decay(self, age_days: float, decay_rate: float) -> float:
        """
        Exponential decay function: weight = e^(-decay_rate * age)
        """
        return math.exp(-decay_rate * age_days)
    
    def _linear_decay(self, age_days: float, decay_rate: float) -> float:
        """
        Linear decay function: weight = max(0, 1 - decay_rate * age)
        """
        return max(0, 1 - decay_rate * age_days)
```

---

## HypothesisLazyGraph Component

### Overview
The HypothesisLazyGraph extends traditional graph traversal with intelligent hypothesis generation and directed exploration, only expanding paths that lead to meaningful insights.

### Core Architecture

```python
class HypothesisLazyGraph:
    """
    Intelligent graph exploration driven by hypothesis generation
    Only expands promising paths to avoid combinatorial explosion
    """
    
    def __init__(self, knowledge_base: KnowledgeBase):
        self.knowledge_base = knowledge_base
        self.hypothesis_generator = HypothesisGenerator()
        self.path_explorer = LazyPathExplorer()
        self.relevance_scorer = RelevanceScorer()
        self.expansion_controller = ExpansionController()
        
    async def explore_query(self, query: InvestmentQuery) -> ExplorationResult:
        """
        Main exploration method that generates hypotheses and explores systematically
        """
        exploration_start = time.time()
        
        try:
            # Stage 1: Generate multiple hypotheses
            hypotheses = await self.hypothesis_generator.generate_hypotheses(
                query=query,
                context=query.context,
                num_hypotheses=5,
                diversity_threshold=0.7
            )
            
            # Stage 2: Parallel hypothesis exploration
            exploration_tasks = []
            for hypothesis in hypotheses:
                task = self._explore_single_hypothesis(
                    hypothesis=hypothesis,
                    query=query,
                    max_depth=3,
                    confidence_threshold=0.6
                )
                exploration_tasks.append(task)
            
            # Execute explorations in parallel
            hypothesis_results = await asyncio.gather(*exploration_tasks)
            
            # Stage 3: Synthesize findings across all hypotheses
            synthesis = await self._synthesize_hypothesis_results(
                hypotheses=hypotheses,
                results=hypothesis_results,
                query=query
            )
            
            return ExplorationResult(
                query=query,
                hypotheses=hypotheses,
                exploration_results=hypothesis_results,
                synthesis=synthesis,
                total_paths_explored=sum(r.paths_explored for r in hypothesis_results),
                exploration_time=time.time() - exploration_start,
                confidence_score=synthesis.overall_confidence
            )
            
        except Exception as e:
            return ExplorationResult(
                success=False,
                error=str(e),
                exploration_time=time.time() - exploration_start
            )
    
    async def _explore_single_hypothesis(self, hypothesis: Hypothesis, query: InvestmentQuery,
                                       max_depth: int, confidence_threshold: float) -> HypothesisResult:
        """
        Explores a single hypothesis through directed graph expansion
        """
        # Initialize exploration context
        exploration_context = ExplorationContext(
            hypothesis=hypothesis,
            query=query,
            max_depth=max_depth,
            confidence_threshold=confidence_threshold,
            visited_nodes=set(),
            exploration_path=[]
        )
        
        # Start exploration from hypothesis root entities
        root_entities = self._extract_root_entities(hypothesis)
        
        evidence_paths = []
        for root_entity in root_entities:
            # Lazy expansion from each root
            paths = await self._lazy_expand_from_entity(
                entity=root_entity,
                context=exploration_context
            )
            evidence_paths.extend(paths)
        
        # Score and rank evidence paths
        scored_paths = await self._score_evidence_paths(evidence_paths, hypothesis)
        
        return HypothesisResult(
            hypothesis=hypothesis,
            evidence_paths=scored_paths,
            paths_explored=len(evidence_paths),
            strongest_evidence=scored_paths[0] if scored_paths else None,
            overall_support=self._calculate_hypothesis_support(scored_paths),
            confidence=self._calculate_hypothesis_confidence(scored_paths)
        )
    
    async def _lazy_expand_from_entity(self, entity: Entity, 
                                      context: ExplorationContext) -> List[EvidencePath]:
        """
        Performs lazy expansion from entity, only following promising paths
        """
        current_depth = 0
        evidence_paths = []
        
        # Initialize frontier with starting entity
        frontier = [(entity, [], 1.0)]  # (entity, path, confidence)
        
        while frontier and current_depth < context.max_depth:
            next_frontier = []
            
            for current_entity, current_path, path_confidence in frontier:
                if current_entity.id in context.visited_nodes:
                    continue
                    
                # Mark as visited
                context.visited_nodes.add(current_entity.id)
                
                # Get potential next steps
                neighbors = await self.knowledge_base.get_neighbors(current_entity)
                
                for neighbor, relationship in neighbors:
                    # Score relevance to hypothesis
                    relevance = await self.relevance_scorer.score_relevance(
                        entity=neighbor,
                        relationship=relationship,
                        hypothesis=context.hypothesis,
                        current_path=current_path
                    )
                    
                    # Only continue if relevance exceeds threshold
                    if relevance.score >= context.confidence_threshold:
                        new_path = current_path + [(relationship, neighbor)]
                        new_confidence = path_confidence * relevance.score
                        
                        # Add to next frontier
                        next_frontier.append((neighbor, new_path, new_confidence))
                        
                        # If this completes an evidence path, store it
                        if self._is_complete_evidence_path(new_path, context.hypothesis):
                            evidence_path = EvidencePath(
                                start_entity=entity,
                                end_entity=neighbor,
                                path=new_path,
                                confidence=new_confidence,
                                depth=len(new_path),
                                hypothesis_support=relevance.hypothesis_support
                            )
                            evidence_paths.append(evidence_path)
            
            frontier = next_frontier
            current_depth += 1
        
        return evidence_paths
```

### Hypothesis Generation Engine

```python
class HypothesisGenerator:
    """
    Generates investment hypotheses for systematic exploration
    """
    
    def __init__(self):
        self.llm_orchestra = None  # Injected dependency
        self.hypothesis_templates = self._load_hypothesis_templates()
        self.domain_patterns = self._load_domain_patterns()
        
    async def generate_hypotheses(self, query: InvestmentQuery, **kwargs) -> List[Hypothesis]:
        """
        Generates diverse hypotheses for investment query
        """
        # Analyze query to determine hypothesis types needed
        query_analysis = await self._analyze_query_for_hypotheses(query)
        
        # Generate hypotheses using multiple strategies
        generated_hypotheses = []
        
        # Strategy 1: Template-based generation
        template_hypotheses = await self._generate_from_templates(
            query, query_analysis
        )
        generated_hypotheses.extend(template_hypotheses)
        
        # Strategy 2: LLM-based creative generation
        creative_hypotheses = await self._generate_creative_hypotheses(
            query, query_analysis, kwargs.get("num_hypotheses", 5)
        )
        generated_hypotheses.extend(creative_hypotheses)
        
        # Strategy 3: Pattern-based generation from historical data
        pattern_hypotheses = await self._generate_from_patterns(
            query, query_analysis
        )
        generated_hypotheses.extend(pattern_hypotheses)
        
        # Ensure diversity and quality
        diverse_hypotheses = self._ensure_hypothesis_diversity(
            generated_hypotheses,
            target_count=kwargs.get("num_hypotheses", 5),
            diversity_threshold=kwargs.get("diversity_threshold", 0.7)
        )
        
        return diverse_hypotheses
    
    async def _generate_creative_hypotheses(self, query: InvestmentQuery, 
                                          analysis: QueryAnalysis, num_hypotheses: int) -> List[Hypothesis]:
        """
        Uses LLM to generate creative, non-template hypotheses
        """
        hypothesis_prompt = f"""
        As an expert investment analyst, generate {num_hypotheses} diverse hypotheses to investigate for this query:
        
        Query: {query.text}
        Context: {query.context}
        
        For the company/asset: {analysis.primary_entity}
        Domain: {analysis.domain}
        Query Type: {analysis.query_type}
        
        Generate hypotheses that cover different dimensions:
        1. Company-specific factors
        2. Industry/sector dynamics
        3. Macroeconomic influences
        4. Supply chain/operational risks
        5. Regulatory/policy impacts
        
        For each hypothesis, provide:
        - Clear hypothesis statement
        - Key entities to investigate
        - Expected evidence types
        - Testability criteria
        
        Format as JSON array of hypothesis objects.
        """
        
        # Route to reasoning LLM for creative hypothesis generation
        llm_result = await self.llm_orchestra.route_task(
            task_type="hypothesis_generation",
            content=hypothesis_prompt,
            requirements={
                "quality_priority": "high",
                "creativity": "high"
            }
        )
        
        # Parse LLM output into structured hypotheses
        hypotheses = self._parse_hypotheses_from_llm(llm_result.content, query)
        
        return hypotheses
    
    def _load_hypothesis_templates(self) -> Dict[str, HypothesisTemplate]:
        """
        Loads pre-defined hypothesis templates for different query types
        """
        return {
            "price_movement": HypothesisTemplate(
                name="Price Movement Analysis",
                patterns=[
                    "Company-specific news or events",
                    "Sector rotation or industry trends", 
                    "Supply chain disruptions",
                    "Macroeconomic factors",
                    "Technical trading patterns",
                    "Institutional investor actions"
                ],
                entities_to_investigate=["company", "competitors", "suppliers", "customers"],
                evidence_types=["news", "filings", "price_data", "volume_data"]
            ),
            
            "investment_thesis": HypothesisTemplate(
                name="Investment Thesis Development",
                patterns=[
                    "Competitive positioning and moats",
                    "Growth drivers and catalysts",
                    "Financial strength and efficiency",
                    "Management quality and strategy",
                    "Market opportunity and TAM",
                    "Risk factors and mitigation"
                ],
                entities_to_investigate=["company", "management", "competitors", "market"],
                evidence_types=["financials", "strategy_docs", "analyst_reports", "management_commentary"]
            ),
            
            "risk_assessment": HypothesisTemplate(
                name="Risk Assessment",
                patterns=[
                    "Operational risks and dependencies",
                    "Financial risks and leverage",
                    "Regulatory and compliance risks",
                    "Market and competitive risks",
                    "Technological and disruption risks",
                    "ESG and reputational risks"
                ],
                entities_to_investigate=["company", "regulators", "competitors", "technology_trends"],
                evidence_types=["risk_disclosures", "regulatory_filings", "news", "industry_reports"]
            )
        }


class LazyPathExplorer:
    """
    Efficiently explores graph paths without exhaustive traversal
    """
    
    def __init__(self):
        self.path_cache = {}
        self.pruning_strategies = PruningStrategies()
        self.expansion_heuristics = ExpansionHeuristics()
        
    async def explore_path(self, start_entity: Entity, target_criteria: TargetCriteria,
                          max_depth: int) -> List[ExplorationPath]:
        """
        Explores paths from start entity using lazy expansion
        """
        # Check cache first
        cache_key = self._generate_cache_key(start_entity, target_criteria, max_depth)
        if cache_key in self.path_cache:
            return self.path_cache[cache_key]
        
        # Initialize exploration
        exploration_state = ExplorationState(
            frontier=[(start_entity, [], 1.0)],  # (entity, path, confidence)
            visited=set(),
            completed_paths=[],
            depth=0
        )
        
        while exploration_state.frontier and exploration_state.depth < max_depth:
            # Expand most promising paths first
            exploration_state.frontier.sort(key=lambda x: x[2], reverse=True)
            
            next_frontier = []
            for entity, path, confidence in exploration_state.frontier:
                if entity.id in exploration_state.visited:
                    continue
                
                # Expand from current entity
                expanded_paths = await self._expand_from_entity(
                    entity, path, confidence, target_criteria
                )
                
                for expanded_path in expanded_paths:
                    if self._meets_target_criteria(expanded_path, target_criteria):
                        exploration_state.completed_paths.append(expanded_path)
                    else:
                        # Continue exploration if promising
                        if self._should_continue_expansion(expanded_path, target_criteria):
                            next_frontier.append((
                                expanded_path.end_entity,
                                expanded_path.path,
                                expanded_path.confidence
                            ))
                
                exploration_state.visited.add(entity.id)
            
            exploration_state.frontier = next_frontier
            exploration_state.depth += 1
        
        # Cache results
        self.path_cache[cache_key] = exploration_state.completed_paths
        
        return exploration_state.completed_paths
```

### Relevance Scoring System

```python
class RelevanceScorer:
    """
    Scores relevance of entities and relationships to hypotheses
    """
    
    def __init__(self):
        self.scoring_models = {
            "semantic_similarity": SemanticSimilarityScorer(),
            "domain_relevance": DomainRelevanceScorer(), 
            "causal_strength": CausalStrengthScorer(),
            "temporal_relevance": TemporalRelevanceScorer()
        }
        
    async def score_relevance(self, entity: Entity, relationship: Relationship,
                             hypothesis: Hypothesis, current_path: List) -> RelevanceScore:
        """
        Comprehensive relevance scoring for graph expansion decisions
        """
        # Score across multiple dimensions
        scores = {}
        
        # Semantic similarity to hypothesis concepts
        scores["semantic"] = await self.scoring_models["semantic_similarity"].score(
            entity, hypothesis.core_concepts
        )
        
        # Domain relevance (financial, industry-specific)
        scores["domain"] = await self.scoring_models["domain_relevance"].score(
            entity, relationship, hypothesis.domain
        )
        
        # Causal strength (how strongly does this entity relate to hypothesis)
        scores["causal"] = await self.scoring_models["causal_strength"].score(
            relationship, hypothesis.causal_structure
        )
        
        # Temporal relevance (is this current/recent information)
        scores["temporal"] = await self.scoring_models["temporal_relevance"].score(
            entity, relationship, hypothesis.time_horizon
        )
        
        # Path coherence (does this fit the current exploration path)
        scores["coherence"] = self._score_path_coherence(
            entity, relationship, current_path
        )
        
        # Calculate weighted composite score
        weights = {
            "semantic": 0.25,
            "domain": 0.30,
            "causal": 0.25,
            "temporal": 0.10,
            "coherence": 0.10
        }
        
        composite_score = sum(
            scores[dimension] * weights[dimension]
            for dimension in weights.keys()
        )
        
        return RelevanceScore(
            composite_score=composite_score,
            dimension_scores=scores,
            hypothesis_support=self._calculate_hypothesis_support(scores),
            confidence=self._calculate_confidence(scores),
            reasoning=self._generate_scoring_reasoning(scores, entity, relationship)
        )


class ExpansionController:
    """
    Controls graph expansion to prevent combinatorial explosion
    """
    
    def __init__(self):
        self.expansion_budget = ExpansionBudget()
        self.pruning_engine = PruningEngine()
        self.priority_queue = PriorityQueue()
        
    async def should_expand(self, expansion_request: ExpansionRequest) -> ExpansionDecision:
        """
        Decides whether to continue expanding from current node
        """
        # Check expansion budget
        if not self.expansion_budget.can_afford(expansion_request):
            return ExpansionDecision(
                should_expand=False,
                reason="Expansion budget exceeded",
                alternative_action="prioritize_existing_paths"
            )
        
        # Check if expansion is promising
        promise_score = await self._evaluate_expansion_promise(expansion_request)
        
        if promise_score < expansion_request.min_promise_threshold:
            return ExpansionDecision(
                should_expand=False,
                reason=f"Promise score {promise_score} below threshold",
                alternative_action="prune_path"
            )
        
        # Check for redundant exploration
        if await self._is_redundant_expansion(expansion_request):
            return ExpansionDecision(
                should_expand=False,
                reason="Similar path already explored",
                alternative_action="merge_with_existing"
            )
        
        return ExpansionDecision(
            should_expand=True,
            promise_score=promise_score,
            allocated_budget=self.expansion_budget.allocate(expansion_request)
        )
```

---

## LocalLLMOrchestra Component

### Overview
The LocalLLMOrchestra manages multiple specialized LLM models, routing tasks to optimal models based on task requirements and current system state.

### Core Architecture

```python
class LocalLLMOrchestra:
    """
    Orchestrates multiple local LLM models for optimal task performance
    Handles model routing, loading, unloading, and performance optimization
    """
    
    def __init__(self, config: OrchestraConfig):
        self.config = config
        self.model_manager = ModelManager(config)
        self.task_router = TaskRouter(config)
        self.performance_monitor = PerformanceMonitor()
        self.load_balancer = LoadBalancer()
        
        # Initialize Ollama client
        self.ollama_client = ollama.AsyncClient()
        
        # Model registry
        self.model_registry = ModelRegistry(config.hardware_profile)
        
        # Task execution queue
        self.execution_queue = TaskExecutionQueue()
        
    async def route_task(self, task_type: str, content: str, 
                        requirements: Optional[TaskRequirements] = None) -> TaskResult:
        """
        Main entry point for task execution
        Routes task to optimal model and manages execution
        """
        execution_start = time.time()
        
        try:
            # Analyze task to determine optimal model
            task_analysis = await self.task_router.analyze_task(
                task_type=task_type,
                content=content,
                requirements=requirements or TaskRequirements()
            )
            
            # Select optimal model
            model_selection = await self.task_router.select_model(task_analysis)
            
            # Ensure model is loaded and ready
            model_instance = await self.model_manager.ensure_model_ready(
                model_selection.model_name
            )
            
            # Execute task
            execution_result = await self._execute_task_on_model(
                model_instance=model_instance,
                task_analysis=task_analysis,
                content=content
            )
            
            # Monitor performance
            performance_metrics = PerformanceMetrics(
                model_used=model_selection.model_name,
                task_type=task_type,
                execution_time=time.time() - execution_start,
                content_length=len(content),
                quality_score=execution_result.quality_score,
                memory_usage=execution_result.memory_usage
            )
            
            await self.performance_monitor.record_metrics(performance_metrics)
            
            return TaskResult(
                content=execution_result.content,
                model_used=model_selection.model_name,
                quality_score=execution_result.quality_score,
                execution_time=performance_metrics.execution_time,
                metadata=execution_result.metadata,
                performance_metrics=performance_metrics
            )
            
        except Exception as e:
            return TaskResult(
                success=False,
                error=str(e),
                execution_time=time.time() - execution_start
            )
    
    async def _execute_task_on_model(self, model_instance: ModelInstance,
                                   task_analysis: TaskAnalysis, content: str) -> ExecutionResult:
        """
        Executes task on specific model with optimal parameters
        """
        # Build model-specific prompt
        prompt = await self._build_prompt_for_model(
            model_instance=model_instance,
            task_analysis=task_analysis,
            content=content
        )
        
        # Get optimal generation parameters
        generation_params = self._get_generation_parameters(
            model_instance=model_instance,
            task_analysis=task_analysis
        )
        
        # Execute on model
        start_memory = self._get_memory_usage()
        
        response = await self.ollama_client.generate(
            model=model_instance.name,
            prompt=prompt.text,
            options=generation_params,
            stream=False
        )
        
        end_memory = self._get_memory_usage()
        
        # Process and validate response
        processed_result = await self._process_model_response(
            response=response,
            task_analysis=task_analysis,
            model_instance=model_instance
        )
        
        return ExecutionResult(
            content=processed_result.content,
            quality_score=processed_result.quality_score,
            metadata=processed_result.metadata,
            memory_usage=end_memory - start_memory,
            raw_response=response
        )


class ModelManager:
    """
    Manages model lifecycle: loading, unloading, optimization
    """
    
    def __init__(self, config: OrchestraConfig):
        self.config = config
        self.loaded_models = {}
        self.model_queue = deque()  # LRU queue
        self.memory_tracker = MemoryTracker()
        self.loading_locks = {}  # Prevent concurrent loading of same model
        
    async def ensure_model_ready(self, model_name: str) -> ModelInstance:
        """
        Ensures specified model is loaded and ready for inference
        """
        # Check if already loaded
        if model_name in self.loaded_models:
            # Move to front of LRU queue
            self._update_lru_queue(model_name)
            return self.loaded_models[model_name]
        
        # Prevent concurrent loading
        if model_name in self.loading_locks:
            await self.loading_locks[model_name].wait()
            return self.loaded_models[model_name]
        
        # Create loading lock
        self.loading_locks[model_name] = asyncio.Event()
        
        try:
            # Check memory requirements
            model_spec = self.config.get_model_spec(model_name)
            required_memory = model_spec.memory_requirement
            
            # Free memory if needed
            await self._ensure_memory_available(required_memory)
            
            # Load model
            model_instance = await self._load_model(model_name, model_spec)
            
            # Register loaded model
            self.loaded_models[model_name] = model_instance
            self.model_queue.appendleft(model_name)
            
            # Update memory tracking
            self.memory_tracker.add_allocation(model_name, required_memory)
            
            # Release loading lock
            self.loading_locks[model_name].set()
            del self.loading_locks[model_name]
            
            return model_instance
            
        except Exception as e:
            # Release lock on error
            if model_name in self.loading_locks:
                self.loading_locks[model_name].set()
                del self.loading_locks[model_name]
            raise e
    
    async def _ensure_memory_available(self, required_memory: int):
        """
        Ensures sufficient memory is available, unloading models if necessary
        """
        available_memory = self.memory_tracker.get_available_memory()
        
        if available_memory >= required_memory:
            return
        
        memory_to_free = required_memory - available_memory
        freed_memory = 0
        
        # Unload least recently used models
        while freed_memory < memory_to_free and len(self.model_queue) > 1:
            lru_model = self.model_queue.pop()  # Remove from end (LRU)
            
            if lru_model in self.loaded_models:
                model_memory = self.config.get_model_spec(lru_model).memory_requirement
                
                await self._unload_model(lru_model)
                
                del self.loaded_models[lru_model]
                self.memory_tracker.remove_allocation(lru_model)
                
                freed_memory += model_memory
                
                logger.info(f"Unloaded {lru_model} to free {model_memory}GB memory")
        
        if freed_memory < memory_to_free:
            raise MemoryError(f"Could not free sufficient memory: need {memory_to_free}GB, freed {freed_memory}GB")
    
    async def _load_model(self, model_name: str, model_spec: ModelSpec) -> ModelInstance:
        """
        Loads model with optimal configuration
        """
        loading_start = time.time()
        
        # Prepare model for loading (pull if not available)
        await self._ensure_model_available(model_name)
        
        # Configure model parameters
        model_config = self._build_model_config(model_spec)
        
        # Create model instance
        model_instance = ModelInstance(
            name=model_name,
            spec=model_spec,
            config=model_config,
            loaded_at=datetime.now(),
            loading_time=time.time() - loading_start
        )
        
        logger.info(f"Loaded {model_name} in {model_instance.loading_time:.2f} seconds")
        
        return model_instance


class TaskRouter:
    """
    Intelligent routing of tasks to optimal models
    """
    
    def __init__(self, config: OrchestraConfig):
        self.config = config
        self.routing_rules = RoutingRules()
        self.performance_history = PerformanceHistory()
        self.model_capabilities = ModelCapabilities()
        
    async def analyze_task(self, task_type: str, content: str, 
                          requirements: TaskRequirements) -> TaskAnalysis:
        """
        Analyzes task to determine optimal model characteristics
        """
        analysis = TaskAnalysis(
            task_type=task_type,
            content_length=len(content),
            estimated_complexity=self._estimate_complexity(content, task_type),
            domain=self._detect_domain(content),
            required_capabilities=self._determine_required_capabilities(task_type),
            quality_priority=requirements.quality_priority,
            speed_priority=requirements.speed_priority,
            context_size_needed=self._estimate_context_size(content),
            expected_output_length=self._estimate_output_length(task_type, content)
        )
        
        return analysis
    
    async def select_model(self, task_analysis: TaskAnalysis) -> ModelSelection:
        """
        Selects optimal model for task based on analysis
        """
        # Get candidate models for this task type
        candidates = self.routing_rules.get_candidates(task_analysis.task_type)
        
        # Filter by capability requirements
        capable_models = [
            model for model in candidates
            if self.model_capabilities.can_handle(model, task_analysis.required_capabilities)
        ]
        
        # Score each capable model
        scored_models = []
        for model in capable_models:
            score = await self._score_model_for_task(model, task_analysis)
            scored_models.append((model, score))
        
        # Sort by score and select best
        scored_models.sort(key=lambda x: x[1].total_score, reverse=True)
        
        if not scored_models:
            raise ValueError(f"No capable models found for task type: {task_analysis.task_type}")
        
        best_model, best_score = scored_models[0]
        
        return ModelSelection(
            model_name=best_model,
            selection_score=best_score,
            alternatives=scored_models[1:3],  # Keep top 3 alternatives
            selection_reasoning=best_score.reasoning
        )
    
    async def _score_model_for_task(self, model: str, task_analysis: TaskAnalysis) -> ModelScore:
        """
        Scores how well a model fits the task requirements
        """
        model_spec = self.config.get_model_spec(model)
        
        scores = {}
        
        # Quality score based on model capability
        scores["quality"] = self._score_quality_capability(model_spec, task_analysis)
        
        # Speed score based on model size and task complexity
        scores["speed"] = self._score_speed_capability(model_spec, task_analysis)
        
        # Memory efficiency score
        scores["memory"] = self._score_memory_efficiency(model_spec, task_analysis)
        
        # Context handling score
        scores["context"] = self._score_context_handling(model_spec, task_analysis)
        
        # Historical performance score
        scores["history"] = await self._score_historical_performance(model, task_analysis)
        
        # Current system load score
        scores["load"] = self._score_current_load(model)
        
        # Calculate weighted total score
        weights = self._get_scoring_weights(task_analysis)
        total_score = sum(scores[category] * weights[category] for category in weights)
        
        return ModelScore(
            total_score=total_score,
            component_scores=scores,
            weights_used=weights,
            reasoning=self._generate_selection_reasoning(scores, model_spec, task_analysis)
        )


class PerformanceMonitor:
    """
    Monitors and optimizes model performance
    """
    
    def __init__(self):
        self.metrics_database = MetricsDatabase()
        self.performance_analyzer = PerformanceAnalyzer()
        self.optimization_engine = OptimizationEngine()
        
    async def record_metrics(self, metrics: PerformanceMetrics):
        """
        Records performance metrics for analysis
        """
        await self.metrics_database.store_metrics(metrics)
        
        # Trigger optimization if needed
        if await self._should_optimize(metrics):
            await self._trigger_optimization(metrics)
    
    async def _should_optimize(self, metrics: PerformanceMetrics) -> bool:
        """
        Determines if optimization should be triggered
        """
        # Check if performance is below expectations
        expected_performance = await self._get_expected_performance(
            metrics.model_used,
            metrics.task_type
        )
        
        performance_ratio = metrics.execution_time / expected_performance.execution_time
        
        # Trigger optimization if significantly slower than expected
        return performance_ratio > 1.5
    
    async def generate_performance_report(self) -> PerformanceReport:
        """
        Generates comprehensive performance analysis
        """
        recent_metrics = await self.metrics_database.get_recent_metrics(hours=24)
        
        analysis = await self.performance_analyzer.analyze_metrics(recent_metrics)
        
        return PerformanceReport(
            summary=analysis.summary,
            model_performance=analysis.per_model_performance,
            task_type_performance=analysis.per_task_performance,
            bottlenecks=analysis.identified_bottlenecks,
            recommendations=analysis.optimization_recommendations,
            generated_at=datetime.now()
        )
```

---

## Integration Layer Components

### Data Source Integration

```python
class DataSourceIntegrator:
    """
    Integrates multiple data sources into unified knowledge representation
    """
    
    def __init__(self):
        self.source_managers = {
            "mcp_financial": MCPFinancialManager(),
            "mcp_yahoo": MCPYahooManager(), 
            "news_apis": NewsAPIManager(),
            "sec_edgar": SECEdgarManager(),
            "user_documents": UserDocumentManager()
        }
        
        self.data_harmonizer = DataHarmonizer()
        self.conflict_resolver = ConflictResolver()
        self.quality_validator = DataQualityValidator()
        
    async def integrate_all_sources(self, query_context: QueryContext) -> IntegratedDataSet:
        """
        Integrates data from all relevant sources for query context
        """
        integration_tasks = []
        
        # Determine relevant sources for query
        relevant_sources = self._determine_relevant_sources(query_context)
        
        # Fetch from each relevant source in parallel
        for source_name in relevant_sources:
            source_manager = self.source_managers[source_name]
            task = source_manager.fetch_data(query_context)
            integration_tasks.append((source_name, task))
        
        # Execute all fetches in parallel
        source_results = {}
        for source_name, task in integration_tasks:
            try:
                result = await task
                source_results[source_name] = result
            except Exception as e:
                logger.warning(f"Failed to fetch from {source_name}: {e}")
                source_results[source_name] = None
        
        # Harmonize data formats
        harmonized_data = await self.data_harmonizer.harmonize_sources(source_results)
        
        # Resolve conflicts between sources
        resolved_data = await self.conflict_resolver.resolve_conflicts(harmonized_data)
        
        # Validate data quality
        validated_data = await self.quality_validator.validate_and_score(resolved_data)
        
        return IntegratedDataSet(
            harmonized_data=validated_data,
            source_contributions=source_results,
            integration_metadata=self._generate_integration_metadata(source_results),
            quality_scores=validated_data.quality_scores
        )


class QueryOrchestrator:
    """
    Orchestrates the complete query processing pipeline
    """
    
    def __init__(self):
        self.living_memory = LivingMemoryRAG()
        self.lazy_graph = HypothesisLazyGraph()
        self.llm_orchestra = LocalLLMOrchestra()
        self.data_integrator = DataSourceIntegrator()
        self.quality_assurance = QualityAssurance()
        
    async def process_investment_query(self, query: InvestmentQuery) -> InvestmentAnalysis:
        """
        Main query processing pipeline integrating all components
        """
        pipeline_start = time.time()
        
        try:
            # Stage 1: Query Understanding and Context Building
            query_context = await self._build_query_context(query)
            
            # Stage 2: Data Integration from Multiple Sources
            integrated_data = await self.data_integrator.integrate_all_sources(query_context)
            
            # Stage 3: Memory Retrieval and Context Enhancement
            memory_context = await self.living_memory.get_contextual_memory(query)
            
            # Stage 4: Hypothesis Generation and Graph Exploration
            exploration_result = await self.lazy_graph.explore_query(query)
            
            # Stage 5: Evidence Synthesis and Analysis
            synthesis_result = await self._synthesize_all_evidence(
                integrated_data=integrated_data,
                memory_context=memory_context,
                exploration_result=exploration_result,
                query=query
            )
            
            # Stage 6: Quality Assurance and Validation
            validated_analysis = await self.quality_assurance.validate_analysis(
                analysis=synthesis_result,
                query=query
            )
            
            # Stage 7: Final Report Generation
            final_report = await self._generate_final_report(
                validated_analysis=validated_analysis,
                query=query,
                processing_metadata={
                    "pipeline_time": time.time() - pipeline_start,
                    "data_sources_used": list(integrated_data.source_contributions.keys()),
                    "hypotheses_explored": len(exploration_result.hypotheses),
                    "evidence_pieces": len(synthesis_result.evidence_pieces)
                }
            )
            
            return InvestmentAnalysis(
                query=query,
                analysis=final_report,
                evidence_chain=synthesis_result.evidence_chain,
                confidence_metrics=validated_analysis.confidence_metrics,
                processing_metadata=final_report.processing_metadata
            )
            
        except Exception as e:
            return InvestmentAnalysis(
                success=False,
                error=str(e),
                processing_time=time.time() - pipeline_start
            )
```

---

## Data Processing Pipeline

### Multi-Stage Processing Architecture

```python
class DataProcessingPipeline:
    """
    Multi-stage pipeline for processing financial data through the system
    """
    
    def __init__(self):
        self.stages = [
            IngestionStage(),
            NormalizationStage(), 
            EnrichmentStage(),
            ValidationStage(),
            IndexingStage(),
            MemoryIntegrationStage()
        ]
        
    async def process_document(self, document: Document) -> ProcessingResult:
        """
        Processes document through all pipeline stages
        """
        current_data = document
        stage_results = []
        
        for stage in self.stages:
            try:
                stage_result = await stage.process(current_data)
                stage_results.append(stage_result)
                current_data = stage_result.output_data
                
                if not stage_result.success:
                    break
                    
            except Exception as e:
                stage_results.append(StageResult(
                    stage_name=stage.__class__.__name__,
                    success=False,
                    error=str(e)
                ))
                break
        
        return ProcessingResult(
            final_data=current_data,
            stage_results=stage_results,
            overall_success=all(r.success for r in stage_results)
        )


class IngestionStage:
    """
    First stage: Raw data ingestion and format detection
    """
    
    async def process(self, document: Document) -> StageResult:
        """
        Ingests raw document and detects format/type
        """
        # Detect document type and format
        document_type = self._detect_document_type(document)
        
        # Extract raw content based on type
        if document_type == "pdf":
            content = await self._extract_pdf_content(document)
        elif document_type == "html":
            content = await self._extract_html_content(document)
        elif document_type == "json":
            content = await self._extract_json_content(document)
        else:
            content = document.content
        
        # Basic cleaning and preprocessing
        cleaned_content = self._clean_content(content)
        
        return StageResult(
            stage_name="Ingestion",
            success=True,
            output_data=Document(
                content=cleaned_content,
                type=document_type,
                metadata={**document.metadata, "processed_at": datetime.now()}
            )
        )


class EnrichmentStage:
    """
    Enriches data with additional context and metadata
    """
    
    async def process(self, document: Document) -> StageResult:
        """
        Enriches document with contextual information
        """
        enrichment_tasks = [
            self._add_temporal_context(document),
            self._add_market_context(document),
            self._add_entity_context(document),
            self._add_sentiment_analysis(document)
        ]
        
        enrichment_results = await asyncio.gather(*enrichment_tasks, return_exceptions=True)
        
        # Combine enrichments
        enriched_metadata = document.metadata.copy()
        for result in enrichment_results:
            if not isinstance(result, Exception):
                enriched_metadata.update(result)
        
        return StageResult(
            stage_name="Enrichment",
            success=True,
            output_data=Document(
                content=document.content,
                type=document.type,
                metadata=enriched_metadata
            )
        )
```

---

## Quality Assurance Systems

### Multi-Layer Quality Framework

```python
class QualityAssurance:
    """
    Comprehensive quality assurance system for investment analysis
    """
    
    def __init__(self):
        self.quality_gates = [
            DepthGate(),
            AccuracyGate(), 
            CoherenceGate(),
            CompletenessGate(),
            RelevanceGate()
        ]
        
        self.enhancement_engine = AnalysisEnhancementEngine()
        self.quality_scorer = AnalysisQualityScorer()
        
    async def validate_analysis(self, analysis: AnalysisResult, query: InvestmentQuery) -> ValidatedAnalysis:
        """
        Validates analysis through multiple quality gates
        """
        validation_results = []
        current_analysis = analysis
        
        for gate in self.quality_gates:
            gate_result = await gate.validate(current_analysis, query)
            validation_results.append(gate_result)
            
            if not gate_result.passed:
                # Attempt to enhance analysis to pass gate
                enhanced_analysis = await self.enhancement_engine.enhance_for_gate(
                    analysis=current_analysis,
                    failed_gate=gate,
                    query=query
                )
                
                if enhanced_analysis:
                    current_analysis = enhanced_analysis
                    
                    # Re-validate with enhanced analysis
                    revalidation = await gate.validate(current_analysis, query)
                    validation_results[-1] = revalidation
        
        # Calculate overall quality score
        quality_score = await self.quality_scorer.score_analysis(current_analysis)
        
        return ValidatedAnalysis(
            analysis=current_analysis,
            validation_results=validation_results,
            quality_score=quality_score,
            passed_all_gates=all(r.passed for r in validation_results)
        )


class DepthGate:
    """
    Ensures analysis has sufficient depth
    """
    
    async def validate(self, analysis: AnalysisResult, query: InvestmentQuery) -> GateResult:
        """
        Validates analysis depth requirements
        """
        depth_metrics = {
            "reasoning_chain_length": len(analysis.reasoning_chain),
            "evidence_layers": analysis.evidence_depth,
            "hypothesis_exploration": len(analysis.hypotheses_explored),
            "source_diversity": len(analysis.unique_sources)
        }
        
        # Minimum requirements based on query complexity
        if query.complexity == "high":
            requirements = {
                "reasoning_chain_length": 5,
                "evidence_layers": 3,
                "hypothesis_exploration": 4,
                "source_diversity": 4
            }
        elif query.complexity == "medium":
            requirements = {
                "reasoning_chain_length": 3,
                "evidence_layers": 2, 
                "hypothesis_exploration": 3,
                "source_diversity": 3
            }
        else:  # low complexity
            requirements = {
                "reasoning_chain_length": 2,
                "evidence_layers": 1,
                "hypothesis_exploration": 2,
                "source_diversity": 2
            }
        
        # Check if all requirements are met
        failures = []
        for metric, required_value in requirements.items():
            actual_value = depth_metrics[metric]
            if actual_value < required_value:
                failures.append(f"{metric}: {actual_value} < {required_value}")
        
        return GateResult(
            gate_name="Depth",
            passed=len(failures) == 0,
            score=self._calculate_depth_score(depth_metrics, requirements),
            failures=failures,
            enhancement_suggestions=self._generate_depth_suggestions(failures)
        )


class AccuracyGate:
    """
    Validates factual accuracy of analysis
    """
    
    async def validate(self, analysis: AnalysisResult, query: InvestmentQuery) -> GateResult:
        """
        Validates factual accuracy through cross-referencing
        """
        fact_checks = []
        
        # Extract factual claims from analysis
        factual_claims = self._extract_factual_claims(analysis)
        
        # Cross-reference each claim
        for claim in factual_claims:
            verification = await self._verify_claim(claim)
            fact_checks.append(verification)
        
        # Calculate accuracy score
        verified_claims = [fc for fc in fact_checks if fc.verified]
        accuracy_score = len(verified_claims) / len(fact_checks) if fact_checks else 1.0
        
        # Determine if gate passes
        passes = accuracy_score >= 0.85  # 85% accuracy threshold
        
        return GateResult(
            gate_name="Accuracy",
            passed=passes,
            score=accuracy_score,
            failures=[fc.claim for fc in fact_checks if not fc.verified],
            verification_details=fact_checks
        )
```

---

## Conclusion

These detailed component specifications provide a comprehensive technical foundation for implementing the quality-first ICE architecture. Each component is designed to work synergistically with others while maintaining clear interfaces and responsibilities.

**Key Implementation Points:**
1. **Modular Design**: Each component can be developed and tested independently
2. **Async Architecture**: Full support for concurrent operations
3. **Quality Gates**: Multiple validation layers ensure high-quality outputs
4. **Extensibility**: Easy to add new data sources, models, or analysis techniques
5. **Monitoring**: Comprehensive performance and quality tracking

**Next Steps**: Use these specifications as blueprints for implementation, following the detailed interfaces and method signatures provided.