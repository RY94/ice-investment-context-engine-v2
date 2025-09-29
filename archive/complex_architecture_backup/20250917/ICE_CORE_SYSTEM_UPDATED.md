# ICE Core System Updated - Unified AI Engine Architecture

**File**: `/Capstone Project/ICE_CORE_SYSTEM_UPDATED.md`
**Purpose**: Unified LightRAG interface replacing fragmented implementations with robust, maintainable core
**Business Value**: Eliminates system fragmentation and provides reliable foundation for investment AI
**Relevant Files**: `ICE_ARCHITECTURE_UPDATED.md`, `ICE_DATA_PIPELINE_UPDATED.md`, `ice_rag_fixed.py`

---

## Executive Summary

This document defines the updated core system architecture that consolidates the fragmented LightRAG implementations into a single, robust AI engine for investment analysis:

**Problems Solved**:
- **Multiple RAG Implementations**: ice_rag.py (deprecated), ice_rag_fixed.py (current), ice_unified_rag.py (experimental)
- **Circular Dependencies**: Integration layers using lazy imports to avoid dependency cycles
- **Initialization Complexity**: Complex async setup with multiple failure points
- **Jupyter Compatibility Issues**: Event loop conflicts and async handling problems

**Key Improvements**:
- **Single Authoritative Interface**: ICEEngine replaces all fragmented implementations
- **Robust Initialization**: Simplified setup with comprehensive error handling
- **Query Intelligence**: Automated mode selection and optimization for investment queries
- **Production Readiness**: Deployment flexibility for both notebook and standalone environments

---

## Core System Architecture

### 1. Unified Engine Design

```
┌─────────────────────────────────────────────────────────────────┐
│                      ICEEngine                                  │
│                 (Unified Interface)                             │
├─────────────────────────────────────────────────────────────────┤
│  Initialization     │  Query Processing   │  Document Mgmt     │
│  • Robust setup     │  • Mode selection   │  • Batch optimize  │
│  • Error handling   │  • Optimization     │  • Knowledge graph │
│  • Health checks    │  • Result format    │  • State management│
└─────────────────────────────────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────┐
│                  LightRAG Integration                           │
│               (Single Implementation)                           │
├─────────────────────────────────────────────────────────────────┤
│  Core LightRAG      │  Storage Layer      │  Query Execution   │
│  • Native interface │  • Vector storage   │  • 6 query modes   │
│  • Pipeline status  │  • Graph storage    │  • Confidence      │
│  • Async handling   │  • Metadata store   │  • Attribution     │
└─────────────────────────────────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────┐
│                 Investment Intelligence                         │
│                  (Domain Optimization)                          │
├─────────────────────────────────────────────────────────────────┤
│  Financial Entities │  Reasoning Chains   │  Portfolio Context │
│  • Ticker mapping   │  • Multi-hop paths  │  • Risk analysis   │
│  • Company links    │  • Confidence calc  │  • Theme exposure  │
│  • Sector context   │  • Source traces    │  • Change tracking │
└─────────────────────────────────────────────────────────────────┘
```

### 2. Component Specifications

#### ICEEngine (Unified Core)
```python
class ICEEngine:
    """
    Unified investment AI engine replacing all fragmented LightRAG implementations

    Consolidates:
    - ice_rag.py (deprecated)
    - ice_rag_fixed.py (current)
    - ice_unified_rag.py (experimental)

    Provides:
    - Single authoritative interface
    - Robust initialization and error handling
    - Investment-optimized query processing
    - Production deployment flexibility
    """

    def __init__(self, config: ICEEngineConfig):
        """Initialize with comprehensive configuration and error handling"""
        self.config = config
        self.lightrag = None
        self.query_optimizer = InvestmentQueryOptimizer()
        self.reasoning_engine = MultiHopReasoningEngine()
        self.confidence_calculator = ConfidenceCalculator()

        # State management
        self._initialized = False
        self._initialization_error = None
        self._deployment_mode = self._detect_deployment_mode()

        # Performance tracking
        self.metrics = EngineMetrics()
        self.health_monitor = HealthMonitor()

    async def initialize(self) -> InitializationResult:
        """
        Robust initialization with comprehensive error handling
        Replaces complex async setup patterns from previous implementations
        """
        if self._initialized:
            return InitializationResult(success=True, message="Already initialized")

        try:
            # Stage 1: Environment validation
            env_validation = await self._validate_environment()
            if not env_validation.success:
                raise ICEInitializationException(
                    message="Environment validation failed",
                    error_code="ENV_VALIDATION_FAILED",
                    context=env_validation.details,
                    recovery_suggestions=env_validation.recovery_suggestions
                )

            # Stage 2: LightRAG initialization
            lightrag_result = await self._initialize_lightrag()
            if not lightrag_result.success:
                raise ICEInitializationException(
                    message="LightRAG initialization failed",
                    error_code="LIGHTRAG_INIT_FAILED",
                    context=lightrag_result.details,
                    recovery_suggestions=["Check API keys", "Verify LightRAG installation"]
                )

            # Stage 3: Investment intelligence setup
            investment_result = await self._initialize_investment_intelligence()
            if not investment_result.success:
                raise ICEInitializationException(
                    message="Investment intelligence setup failed",
                    error_code="INVESTMENT_INIT_FAILED",
                    context=investment_result.details,
                    recovery_suggestions=["Check configuration", "Verify data sources"]
                )

            # Stage 4: Health check
            health_result = await self.health_check()
            if not health_result.is_healthy:
                logger.warning(f"Initialization completed with health issues: {health_result.issues}")

            self._initialized = True
            self.metrics.record_initialization_success()

            return InitializationResult(
                success=True,
                message="ICE Engine initialized successfully",
                health_status=health_result
            )

        except Exception as e:
            self._initialization_error = e
            self.metrics.record_initialization_failure(e)

            # Log detailed error information
            logger.error(f"ICE Engine initialization failed: {e}")

            # Re-raise as ICE exception with context
            if isinstance(e, ICEException):
                raise e
            else:
                raise ICEInitializationException(
                    message=f"Unexpected initialization error: {str(e)}",
                    error_code="UNEXPECTED_INIT_ERROR",
                    context={"error_type": type(e).__name__},
                    recovery_suggestions=["Check logs", "Verify configuration", "Restart initialization"]
                ) from e

    async def _initialize_lightrag(self) -> ComponentInitResult:
        """Initialize LightRAG with robust error handling"""
        try:
            # Import with graceful failure
            from lightrag import LightRAG, QueryParam
            from lightrag.llm.openai import gpt_4o_mini_complete, openai_embed

            # Create LightRAG instance
            self.lightrag = LightRAG(
                working_dir=str(self.config.working_dir),
                llm_model_func=gpt_4o_mini_complete,
                embedding_func=openai_embed
            )

            # Initialize storages (critical step from ice_rag_fixed.py)
            await self.lightrag.initialize_storages()

            # Initialize pipeline status with fallback handling
            await self._initialize_pipeline_status()

            return ComponentInitResult(
                success=True,
                component="LightRAG",
                message="LightRAG initialized successfully"
            )

        except ImportError as e:
            return ComponentInitResult(
                success=False,
                component="LightRAG",
                error=str(e),
                details={"missing_dependency": "lightrag"},
                recovery_suggestions=["Install LightRAG: pip install lightrag"]
            )
        except Exception as e:
            return ComponentInitResult(
                success=False,
                component="LightRAG",
                error=str(e),
                details={"initialization_stage": "storage_setup"},
                recovery_suggestions=["Check working directory permissions", "Verify API keys"]
            )

    async def _initialize_pipeline_status(self):
        """Initialize pipeline status with multiple fallback strategies"""
        try:
            # Primary import path
            from lightrag.kg.shared_storage import initialize_pipeline_status
            await initialize_pipeline_status()
            logger.info("Pipeline status initialized (primary path)")
            return

        except ImportError:
            try:
                # Fallback import path
                from lightrag.storage import initialize_pipeline_status
                await initialize_pipeline_status()
                logger.info("Pipeline status initialized (fallback path)")
                return

            except ImportError:
                logger.warning("Pipeline status initialization not available - continuing without it")
                # Continue without pipeline status - not critical for basic operation

        except Exception as e:
            logger.warning(f"Pipeline status initialization failed: {e} - continuing without it")
            # Continue without pipeline status - not critical for basic operation

    def is_ready(self) -> bool:
        """Check if engine is ready for operation"""
        return (
            self._initialized and
            self.lightrag is not None and
            self._initialization_error is None
        )

    async def health_check(self) -> EngineHealthStatus:
        """Comprehensive health check for the entire engine"""
        checks = {}

        # Core component health
        checks["lightrag"] = await self._check_lightrag_health()
        checks["storage"] = await self._check_storage_health()
        checks["query_processing"] = await self._check_query_processing_health()
        checks["investment_intelligence"] = await self._check_investment_intelligence_health()

        # Overall health assessment
        healthy_components = sum(1 for check in checks.values() if check.is_healthy)
        total_components = len(checks)
        overall_health_score = healthy_components / total_components

        is_healthy = overall_health_score >= 0.8
        issues = [f"{name}: {check.issue}" for name, check in checks.items() if not check.is_healthy]

        return EngineHealthStatus(
            is_healthy=is_healthy,
            health_score=overall_health_score,
            component_checks=checks,
            issues=issues,
            timestamp=datetime.now()
        )
```

#### Query Processing (Investment-Optimized)
```python
class InvestmentQueryProcessor:
    """Investment-optimized query processing with intelligent mode selection"""

    def __init__(self, lightrag_instance, config: QueryConfig):
        self.lightrag = lightrag_instance
        self.config = config
        self.mode_selector = QueryModeSelector()
        self.result_formatter = InvestmentResultFormatter()

    async def process_query(self, query: InvestmentQuery) -> InvestmentQueryResult:
        """Process investment query with optimization and intelligence"""

        # Stage 1: Query analysis and planning
        query_plan = await self._analyze_query(query)

        # Stage 2: Mode selection optimization
        optimal_mode = await self.mode_selector.select_mode(query, query_plan)

        # Stage 3: Query execution with monitoring
        raw_result = await self._execute_query_with_monitoring(query, optimal_mode)

        # Stage 4: Investment-specific result processing
        processed_result = await self._process_investment_result(raw_result, query_plan)

        # Stage 5: Confidence calculation and source attribution
        final_result = await self._finalize_result(processed_result, query)

        return final_result

    async def _analyze_query(self, query: InvestmentQuery) -> QueryPlan:
        """Analyze query to determine optimal processing strategy"""

        # Extract investment entities
        entities = await self._extract_investment_entities(query.text)

        # Determine query type
        query_type = self._classify_query_type(query.text, entities)

        # Plan multi-hop reasoning if needed
        reasoning_plan = await self._plan_reasoning_strategy(query, entities, query_type)

        return QueryPlan(
            original_query=query,
            extracted_entities=entities,
            query_type=query_type,
            reasoning_plan=reasoning_plan,
            estimated_complexity=self._estimate_query_complexity(query, entities)
        )

    async def _execute_query_with_monitoring(self, query: InvestmentQuery, mode: QueryMode) -> RawQueryResult:
        """Execute query with performance monitoring and error handling"""

        start_time = time.time()

        try:
            # Configure query parameters for investment optimization
            query_params = QueryParam(
                mode=mode.value,
                only_need_context=False,
                response_type="investment_analysis",
                timeout=self.config.timeout
            )

            # Execute with LightRAG
            raw_response = await self.lightrag.aquery(query.text, param=query_params)

            execution_time = time.time() - start_time

            return RawQueryResult(
                response=raw_response,
                mode_used=mode,
                execution_time=execution_time,
                success=True
            )

        except Exception as e:
            execution_time = time.time() - start_time

            logger.error(f"Query execution failed: {e}")

            return RawQueryResult(
                response=None,
                mode_used=mode,
                execution_time=execution_time,
                success=False,
                error=str(e)
            )

class QueryModeSelector:
    """Intelligent selection of optimal LightRAG query mode for investment queries"""

    MODE_SELECTION_RULES = {
        QueryType.FACTUAL: {
            "single_entity": QueryMode.LOCAL,      # "What is AAPL's revenue?"
            "multiple_entities": QueryMode.HYBRID  # "Compare AAPL and GOOGL revenue"
        },
        QueryType.RELATIONSHIP: {
            "simple": QueryMode.LOCAL,             # "Who supplies AAPL?"
            "complex": QueryMode.HYBRID            # "How does China risk impact AAPL?"
        },
        QueryType.ANALYTICAL: {
            "default": QueryMode.HYBRID            # "Should I invest in AAPL?"
        },
        QueryType.MULTI_HOP: {
            "two_hop": QueryMode.GLOBAL,          # "How does AI regulation affect chip stocks?"
            "three_hop": QueryMode.HYBRID         # "What portfolio exposure via supply chain?"
        },
        QueryType.PORTFOLIO: {
            "default": QueryMode.HYBRID            # "What are my portfolio risks?"
        }
    }

    async def select_mode(self, query: InvestmentQuery, plan: QueryPlan) -> QueryMode:
        """Select optimal query mode based on investment context"""

        # Get base mode from rules
        base_mode = self._get_base_mode(plan.query_type, plan)

        # Apply investment-specific adjustments
        adjusted_mode = self._apply_investment_adjustments(base_mode, plan)

        # Consider performance and resource constraints
        final_mode = self._apply_resource_constraints(adjusted_mode, plan)

        logger.info(f"Selected query mode: {final_mode.value} for query type: {plan.query_type.value}")

        return final_mode

    def _apply_investment_adjustments(self, base_mode: QueryMode, plan: QueryPlan) -> QueryMode:
        """Apply investment-specific mode adjustments"""

        # For high-value investment queries, prefer hybrid for better accuracy
        if plan.estimated_complexity > 0.7:
            return QueryMode.HYBRID

        # For simple factual queries about known entities, local is sufficient
        if (plan.query_type == QueryType.FACTUAL and
            len(plan.extracted_entities) == 1 and
            all(e.confidence > 0.9 for e in plan.extracted_entities)):
            return QueryMode.LOCAL

        # For relationship queries with many entities, use global
        if (plan.query_type in [QueryType.RELATIONSHIP, QueryType.MULTI_HOP] and
            len(plan.extracted_entities) > 3):
            return QueryMode.GLOBAL

        return base_mode
```

#### Document Processing (Investment-Optimized)
```python
class InvestmentDocumentProcessor:
    """Investment-optimized document processing for LightRAG"""

    def __init__(self, lightrag_instance, config: DocumentConfig):
        self.lightrag = lightrag_instance
        self.config = config
        self.batch_optimizer = DocumentBatchOptimizer()
        self.quality_monitor = DocumentQualityMonitor()

    async def process_documents(self, documents: List[FinancialDocument]) -> DocumentProcessingResult:
        """Process financial documents with investment optimization"""

        # Stage 1: Document preparation and validation
        prepared_docs = await self._prepare_documents(documents)

        # Stage 2: Batch optimization for LightRAG
        optimized_batches = self.batch_optimizer.create_optimal_batches(prepared_docs)

        # Stage 3: Sequential batch processing with monitoring
        processing_results = []
        for batch in optimized_batches:
            batch_result = await self._process_document_batch(batch)
            processing_results.append(batch_result)

            # Monitor and adjust if needed
            await self._monitor_processing_performance(batch_result)

        # Stage 4: Aggregate results and quality assessment
        final_result = self._aggregate_processing_results(processing_results)

        return final_result

    async def _prepare_documents(self, documents: List[FinancialDocument]) -> List[PreparedDocument]:
        """Prepare documents for optimal LightRAG processing"""

        prepared = []
        for doc in documents:
            try:
                # Format content for LightRAG optimization
                formatted_content = self._format_for_lightrag(doc)

                # Add investment context markers
                enhanced_content = self._add_investment_markers(formatted_content, doc)

                # Validate content quality
                quality_result = await self.quality_monitor.validate_document(doc)

                prepared_doc = PreparedDocument(
                    original_document=doc,
                    formatted_content=enhanced_content,
                    quality_assessment=quality_result,
                    processing_priority=self._calculate_processing_priority(doc)
                )

                prepared.append(prepared_doc)

            except Exception as e:
                logger.warning(f"Failed to prepare document {doc.id}: {e}")
                # Continue with other documents

        return prepared

    def _format_for_lightrag(self, doc: FinancialDocument) -> str:
        """Format document content optimally for LightRAG entity extraction"""

        sections = []

        # Document header with structured metadata
        header = f"""[FINANCIAL_DOCUMENT]
ID: {doc.id}
Source: {doc.source.name} ({doc.source.type.value})
Quality: {doc.quality_score:.2f}
Timestamp: {doc.processing_timestamp}"""
        sections.append(header)

        # Investment context section
        if hasattr(doc, 'investment_context') and doc.investment_context:
            context_section = f"""[INVESTMENT_CONTEXT]
Sector: {doc.investment_context.get('sector', 'Unknown')}
Themes: {', '.join(doc.investment_context.get('themes', []))}
Risk Factors: {', '.join(doc.investment_context.get('risk_factors', []))}"""
            sections.append(context_section)

        # Entity pre-identification for LightRAG
        if doc.entities:
            entity_section = f"""[IDENTIFIED_ENTITIES]
Entities: {', '.join([f"{e.name} ({e.type.value})" for e in doc.entities[:10]])}"""
            sections.append(entity_section)

        # Main content
        content_section = f"""[CONTENT]
{doc.content}"""
        sections.append(content_section)

        return "\n\n".join(sections)

    async def _process_document_batch(self, batch: List[PreparedDocument]) -> BatchProcessingResult:
        """Process a batch of documents with LightRAG"""

        start_time = time.time()

        try:
            # Combine batch content for efficient LightRAG processing
            combined_content = self._combine_batch_content(batch)

            # Process with LightRAG
            await self.lightrag.ainsert(combined_content)

            processing_time = time.time() - start_time

            return BatchProcessingResult(
                batch_size=len(batch),
                processing_time=processing_time,
                success=True,
                documents_processed=[doc.original_document.id for doc in batch],
                quality_scores=[doc.quality_assessment.score for doc in batch]
            )

        except Exception as e:
            processing_time = time.time() - start_time

            logger.error(f"Batch processing failed: {e}")

            return BatchProcessingResult(
                batch_size=len(batch),
                processing_time=processing_time,
                success=False,
                error=str(e),
                documents_processed=[],
                quality_scores=[]
            )
```

#### Multi-Hop Reasoning Engine
```python
class MultiHopReasoningEngine:
    """Investment-specific multi-hop reasoning with confidence tracking"""

    def __init__(self, config: ReasoningConfig):
        self.config = config
        self.confidence_calculator = ConfidenceCalculator()
        self.reasoning_validator = ReasoningValidator()

    async def generate_reasoning_chain(self, query: InvestmentQuery, raw_result: str) -> ReasoningChain:
        """Generate multi-hop reasoning chain for investment analysis"""

        # Stage 1: Parse reasoning steps from LightRAG result
        reasoning_steps = await self._parse_reasoning_steps(raw_result)

        # Stage 2: Enhance with investment-specific logic
        enhanced_steps = await self._enhance_reasoning_steps(reasoning_steps, query)

        # Stage 3: Calculate confidence for each step
        confidence_scores = await self._calculate_step_confidence(enhanced_steps)

        # Stage 4: Validate reasoning chain
        validation_result = await self.reasoning_validator.validate_chain(enhanced_steps)

        # Stage 5: Format for presentation
        formatted_chain = self._format_reasoning_chain(enhanced_steps, confidence_scores)

        return ReasoningChain(
            query=query,
            steps=enhanced_steps,
            confidence_scores=confidence_scores,
            overall_confidence=np.mean(confidence_scores),
            validation_result=validation_result,
            formatted_chain=formatted_chain
        )

    async def _enhance_reasoning_steps(self, steps: List[ReasoningStep], query: InvestmentQuery) -> List[EnhancedReasoningStep]:
        """Enhance reasoning steps with investment-specific context"""

        enhanced = []
        for step in steps:
            try:
                # Add investment context
                investment_context = await self._get_investment_context(step)

                # Add risk analysis
                risk_factors = await self._identify_risk_factors(step)

                # Add temporal context
                temporal_context = await self._get_temporal_context(step)

                enhanced_step = EnhancedReasoningStep(
                    original_step=step,
                    investment_context=investment_context,
                    risk_factors=risk_factors,
                    temporal_context=temporal_context,
                    confidence_factors=self._analyze_confidence_factors(step)
                )

                enhanced.append(enhanced_step)

            except Exception as e:
                logger.warning(f"Failed to enhance reasoning step: {e}")
                # Use original step if enhancement fails
                enhanced.append(step)

        return enhanced
```

---

## Deployment and Configuration

### 1. Environment Detection and Adaptation

#### Deployment Mode Detection
```python
class DeploymentModeDetector:
    """Detect and adapt to different deployment environments"""

    @staticmethod
    def detect_deployment_mode() -> DeploymentMode:
        """Detect current deployment environment"""

        # Check for Jupyter environment
        if DeploymentModeDetector._is_jupyter_environment():
            return DeploymentMode.JUPYTER

        # Check for production environment
        if DeploymentModeDetector._is_production_environment():
            return DeploymentMode.PRODUCTION

        # Check for development environment
        if DeploymentModeDetector._is_development_environment():
            return DeploymentMode.DEVELOPMENT

        return DeploymentMode.STANDALONE

    @staticmethod
    def _is_jupyter_environment() -> bool:
        """Detect if running in Jupyter notebook"""
        try:
            # Check for IPython kernel
            __IPYTHON__

            # Check for notebook environment
            import IPython
            return IPython.get_ipython() is not None

        except NameError:
            return False

    @staticmethod
    def configure_for_deployment(mode: DeploymentMode) -> DeploymentConfig:
        """Configure engine for specific deployment mode"""

        configs = {
            DeploymentMode.JUPYTER: DeploymentConfig(
                async_handling="nest_asyncio",
                event_loop_policy="jupyter_compatible",
                logging_level="INFO",
                memory_optimization=True,
                batch_size=5  # Smaller batches for interactive use
            ),
            DeploymentMode.PRODUCTION: DeploymentConfig(
                async_handling="native",
                event_loop_policy="default",
                logging_level="WARNING",
                memory_optimization=True,
                batch_size=20  # Larger batches for throughput
            ),
            DeploymentMode.DEVELOPMENT: DeploymentConfig(
                async_handling="native",
                event_loop_policy="default",
                logging_level="DEBUG",
                memory_optimization=False,
                batch_size=10  # Balanced for testing
            )
        }

        return configs.get(mode, configs[DeploymentMode.STANDALONE])
```

### 2. Configuration Management

#### Comprehensive Configuration
```yaml
# ice_engine_config.yaml
engine:
  core:
    working_dir: "./ice_storage"
    timeout: 30
    max_retries: 3

  lightrag:
    llm_model: "gpt-4o-mini"
    embedding_model: "text-embedding-ada-002"
    chunk_size: 1200
    chunk_overlap: 200

  query_processing:
    default_mode: "hybrid"
    confidence_threshold: 0.7
    max_hops: 3
    timeout: 30

  document_processing:
    batch_size: 10
    max_parallel_batches: 3
    quality_threshold: 0.8

  investment_optimization:
    entity_types:
      - TICKER
      - COMPANY
      - PERSON
      - METRIC
      - RISK

    relationship_types:
      - depends_on
      - exposed_to
      - drives
      - competes_with

    confidence_weights:
      entity_confidence: 0.3
      relationship_confidence: 0.3
      source_credibility: 0.2
      temporal_freshness: 0.2

deployment:
  mode: "auto_detect"  # auto_detect, jupyter, production, development

  jupyter:
    async_handling: "nest_asyncio"
    memory_optimization: true
    interactive_logging: true

  production:
    health_monitoring: true
    performance_logging: true
    error_reporting: true

monitoring:
  health_check_interval: 60
  performance_metrics: true
  error_tracking: true

logging:
  level: "INFO"
  format: "structured"
  output: "console"
```

### 3. Error Handling and Recovery

#### Engine-Level Error Management
```python
class ICEEngineErrorHandler:
    """Comprehensive error handling for the entire ICE engine"""

    def __init__(self, config: ErrorHandlingConfig):
        self.config = config
        self.error_metrics = ErrorMetrics()
        self.recovery_strategies = self._initialize_recovery_strategies()

    async def handle_engine_error(self, error: Exception, context: EngineContext) -> ErrorHandlingResult:
        """Handle errors at the engine level with comprehensive recovery"""

        # Classify error type and severity
        error_classification = self._classify_engine_error(error, context)

        # Select recovery strategy
        recovery_strategy = self._select_recovery_strategy(error_classification)

        # Execute recovery
        recovery_result = await self._execute_recovery(recovery_strategy, context)

        # Update metrics and logging
        self.error_metrics.record_error(error_classification, recovery_result)

        return ErrorHandlingResult(
            error_classification=error_classification,
            recovery_strategy=recovery_strategy,
            recovery_success=recovery_result.success,
            recommendations=self._generate_recommendations(error_classification, context)
        )

    def _classify_engine_error(self, error: Exception, context: EngineContext) -> ErrorClassification:
        """Classify errors for appropriate handling"""

        if isinstance(error, ICEInitializationException):
            return ErrorClassification(
                type=ErrorType.INITIALIZATION,
                severity=ErrorSeverity.HIGH,
                component="engine_initialization",
                recoverable=True
            )
        elif isinstance(error, ICEQueryException):
            return ErrorClassification(
                type=ErrorType.QUERY_PROCESSING,
                severity=ErrorSeverity.MEDIUM,
                component="query_engine",
                recoverable=True
            )
        elif isinstance(error, ICEDataException):
            return ErrorClassification(
                type=ErrorType.DATA_PROCESSING,
                severity=ErrorSeverity.MEDIUM,
                component="document_processor",
                recoverable=True
            )
        else:
            return ErrorClassification(
                type=ErrorType.UNKNOWN,
                severity=ErrorSeverity.HIGH,
                component="unknown",
                recoverable=False
            )
```

---

## Performance Optimization

### 1. Query Performance Optimization

#### Performance Targets and Monitoring
```python
class PerformanceOptimizer:
    """Optimize engine performance for investment workloads"""

    PERFORMANCE_TARGETS = {
        "query_response_time": 5.0,  # seconds
        "document_processing_rate": 10,  # documents per second
        "memory_usage": 0.8,  # fraction of available memory
        "cpu_usage": 0.7  # fraction of available CPU
    }

    def __init__(self, engine_instance):
        self.engine = engine_instance
        self.metrics_collector = MetricsCollector()
        self.optimization_history = []

    async def optimize_performance(self):
        """Continuously optimize engine performance"""

        while self.engine.is_running():
            try:
                # Collect current metrics
                current_metrics = await self.metrics_collector.collect_metrics()

                # Identify optimization opportunities
                optimizations = self._identify_optimizations(current_metrics)

                # Apply optimizations
                for optimization in optimizations:
                    await self._apply_optimization(optimization)

                # Monitor results
                await self._monitor_optimization_results()

            except Exception as e:
                logger.error(f"Performance optimization error: {e}")

            await asyncio.sleep(60)  # Optimize every minute

    def _identify_optimizations(self, metrics: PerformanceMetrics) -> List[OptimizationAction]:
        """Identify performance optimization opportunities"""

        optimizations = []

        # Query response time optimization
        if metrics.avg_query_time > self.PERFORMANCE_TARGETS["query_response_time"]:
            optimizations.append(OptimizationAction(
                type="reduce_query_time",
                priority="high",
                action="optimize_query_mode_selection"
            ))

        # Memory usage optimization
        if metrics.memory_usage > self.PERFORMANCE_TARGETS["memory_usage"]:
            optimizations.append(OptimizationAction(
                type="reduce_memory_usage",
                priority="high",
                action="optimize_batch_size"
            ))

        # Document processing optimization
        if metrics.doc_processing_rate < self.PERFORMANCE_TARGETS["document_processing_rate"]:
            optimizations.append(OptimizationAction(
                type="increase_processing_rate",
                priority="medium",
                action="optimize_parallel_processing"
            ))

        return optimizations
```

### 2. Memory and Resource Management

#### Intelligent Resource Management
```python
class ResourceManager:
    """Manage memory and computational resources efficiently"""

    def __init__(self, config: ResourceConfig):
        self.config = config
        self.memory_monitor = MemoryMonitor()
        self.cpu_monitor = CPUMonitor()

    async def manage_resources(self, engine_instance):
        """Actively manage resources during operation"""

        while engine_instance.is_running():
            try:
                # Monitor resource usage
                memory_usage = await self.memory_monitor.get_usage()
                cpu_usage = await self.cpu_monitor.get_usage()

                # Apply resource management strategies
                if memory_usage > self.config.memory_threshold:
                    await self._manage_memory_usage(engine_instance)

                if cpu_usage > self.config.cpu_threshold:
                    await self._manage_cpu_usage(engine_instance)

            except Exception as e:
                logger.error(f"Resource management error: {e}")

            await asyncio.sleep(30)  # Check every 30 seconds

    async def _manage_memory_usage(self, engine_instance):
        """Manage memory usage when threshold exceeded"""

        # Reduce batch sizes
        current_batch_size = engine_instance.get_batch_size()
        new_batch_size = max(1, int(current_batch_size * 0.7))
        engine_instance.set_batch_size(new_batch_size)

        # Clear caches
        engine_instance.clear_caches()

        # Force garbage collection
        import gc
        gc.collect()

        logger.info(f"Memory optimization: reduced batch size to {new_batch_size}")
```

---

## Testing and Validation

### 1. Engine Testing Framework

#### Comprehensive Testing Suite
```python
class ICEEngineTestSuite:
    """Comprehensive testing suite for ICE Engine validation"""

    def __init__(self, test_config: TestConfig):
        self.config = test_config
        self.test_results = TestResults()

    async def run_comprehensive_tests(self) -> TestSuiteResult:
        """Run complete test suite for engine validation"""

        test_categories = [
            ("initialization", self._test_initialization),
            ("query_processing", self._test_query_processing),
            ("document_processing", self._test_document_processing),
            ("error_handling", self._test_error_handling),
            ("performance", self._test_performance),
            ("investment_features", self._test_investment_features)
        ]

        results = {}
        for category, test_function in test_categories:
            try:
                category_result = await test_function()
                results[category] = category_result
                logger.info(f"Test category '{category}': {category_result.status}")

            except Exception as e:
                results[category] = TestCategoryResult(
                    status="FAILED",
                    error=str(e)
                )
                logger.error(f"Test category '{category}' failed: {e}")

        return TestSuiteResult(
            overall_status=self._calculate_overall_status(results),
            category_results=results,
            recommendations=self._generate_test_recommendations(results)
        )

    async def _test_query_processing(self) -> TestCategoryResult:
        """Test query processing functionality"""

        test_queries = [
            InvestmentQuery(text="What is AAPL's current stock price?", query_type=QueryType.FACTUAL),
            InvestmentQuery(text="How does China risk impact NVDA?", query_type=QueryType.MULTI_HOP),
            InvestmentQuery(text="Should I invest in tech stocks?", query_type=QueryType.ANALYTICAL)
        ]

        test_results = []
        for query in test_queries:
            try:
                result = await self.engine.process_query(query)
                test_results.append(QueryTestResult(
                    query=query,
                    success=result.success,
                    response_time=result.execution_time,
                    confidence=result.confidence
                ))
            except Exception as e:
                test_results.append(QueryTestResult(
                    query=query,
                    success=False,
                    error=str(e)
                ))

        success_rate = sum(1 for r in test_results if r.success) / len(test_results)

        return TestCategoryResult(
            status="PASSED" if success_rate >= 0.8 else "FAILED",
            success_rate=success_rate,
            individual_results=test_results
        )
```

---

## Success Metrics and KPIs

### Technical Performance Metrics
- **Initialization Success Rate**: >99% successful initialization across all deployment modes
- **Query Response Time**: <5 seconds for 95% of investment queries
- **System Reliability**: >99% uptime with graceful error handling
- **Memory Efficiency**: <2GB memory usage for typical investment workloads

### Investment Intelligence Metrics
- **Query Accuracy**: >85% factual accuracy for investment queries
- **Reasoning Quality**: >80% confidence in multi-hop reasoning chains
- **Entity Recognition**: >90% accuracy for financial entities (tickers, companies, metrics)
- **Source Attribution**: 100% traceability for all investment claims

### Business Value Metrics
- **Code Consolidation**: Eliminate 3 fragmented implementations → 1 unified engine
- **Maintenance Reduction**: 50% reduction in debugging time due to unified interface
- **Development Velocity**: 3x faster feature development with clear interfaces
- **Production Readiness**: Support for both interactive and production deployment

---

**Document Status**: Updated Core System Design
**Implementation Priority**: Phase 1 - Engine Consolidation
**Next Steps**: Implement ICEEngine and replace fragmented implementations