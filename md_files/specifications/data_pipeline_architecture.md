# ICE Data Pipeline Architecture
## Technical Architecture Specification for Investment Context Engine

**Document Type**: Technical Architecture Specification  
**Author**: Senior AI Engineering Team  
**Project**: Investment Context Engine (ICE) Data Pipeline  
**Version**: 1.0  
**Date**: August 2025  

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Component Specifications](#2-component-specifications)
3. [Data Flow Design](#3-data-flow-design)
4. [Integration Patterns](#4-integration-patterns)
5. [Scalability & Performance](#5-scalability--performance)
6. [Security Architecture](#6-security-architecture)
7. [Implementation Guidelines](#7-implementation-guidelines)

---

## 1. Architecture Overview

### 1.1 System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                    ICE DATA PIPELINE ARCHITECTURE                   │
│                        (Layer-by-Layer View)                        │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│  Layer 1: EXTERNAL DATA SOURCE INTEGRATION                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌─────────┐  │
│  │   News APIs   │ │ Financial APIs│ │ Regulatory    │ │Internal │  │
│  │               │ │               │ │ Sources       │ │Sources  │  │
│  │ • NewsAPI     │ │ • yfinance    │ │ • SEC EDGAR   │ │• Email  │  │
│  │ • Benzinga    │ │ • Alpha Vantage│ │ • XBRL Data   │ │• Docs   │  │
│  │ • Reuters     │ │ • FMP         │ │ • Form 4      │ │• Notes  │  │
│  └───────────────┘ └───────────────┘ └───────────────┘ └─────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────┐
│  Layer 2: DATA INGESTION & CONNECTION MANAGEMENT                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │        Connection Pool Manager (ice_connection_manager.py)      │ │
│  │  • API Rate Limiting      • Connection Pooling                 │ │
│  │  • Auth Management        • Health Monitoring                  │ │
│  │  • Retry Logic            • Circuit Breakers                   │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  ┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌─────────┐  │
│  │ News Connector│ │Financial      │ │Regulatory     │ │Internal │  │
│  │               │ │Connector      │ │Connector      │ │Connector│  │
│  │ • Entity Extr │ │ • Multi-source│ │ • Filing Parse│ │• Email  │  │
│  │ • Sentiment   │ │ • Validation  │ │ • XBRL Process│ │• OCR    │  │
│  └───────────────┘ └───────────────┘ └───────────────┘ └─────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────┐
│  Layer 3: DATA PROCESSING PIPELINE                                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │           Pipeline Orchestrator (ice_data_manager.py)           │ │
│  │                                                                 │ │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌───────────┐  │ │
│  │  │ Ingestion   │ │ Validation  │ │Transform-   │ │Quality    │  │ │
│  │  │ Queue       │ │ Engine      │ │ation Engine │ │Controller │  │ │
│  │  │             │ │             │ │             │ │           │  │ │
│  │  │ • Priority  │ │ • Schema    │ │ • Normalize │ │ • Scoring │  │ │
│  │  │ • Batching  │ │ • Business  │ │ • Enrich    │ │ • Monitor │  │ │
│  │  │ • Backpres  │ │ • Cross-val │ │ • Extract   │ │ • Alert   │  │ │
│  │  └─────────────┘ └─────────────┘ └─────────────┘ └───────────┘  │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────┐
│  Layer 4: DATA ROUTING & DISTRIBUTION                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │        Data Distribution Router (ice_data_router.py)            │ │
│  │                                                                 │ │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌───────────┐  │ │
│  │  │ LightRAG    │ │ Graph KG    │ │ Vector DB   │ │ Search    │  │ │
│  │  │ Pipeline    │ │ Pipeline    │ │ Pipeline    │ │ Index     │  │ │
│  │  │             │ │             │ │             │ │ Pipeline  │  │ │
│  │  │ • Embed     │ │ • Entity    │ │ • Chunk     │ │ • Index   │  │ │
│  │  │ • Index     │ │ • Relations │ │ • Vector    │ │ • Keywords│  │ │
│  │  │ • Store     │ │ • Edges     │ │ • Store     │ │ • Cache   │  │ │
│  │  └─────────────┘ └─────────────┘ └─────────────┘ └───────────┘  │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────┐
│  Layer 5: PERSISTENT STORAGE                                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │             Storage Management (ice_storage_manager.py)         │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐       │
│  │  Raw Data       │ │ Processed Data  │ │  Metadata &     │       │
│  │  Storage        │ │ Storage         │ │  Index Storage  │       │
│  │                 │ │                 │ │                 │       │
│  │ • JSON Files    │ │ • LightRAG DB   │ │ • Source Info   │       │
│  │ • Timestamped   │ │ • NetworkX Graph│ │ • Quality Flags │       │
│  │ • Compressed    │ │ • Vector Stores │ │ • Lineage Data  │       │
│  │ • Partitioned   │ │ • Search Indexes│ │ • Usage Stats   │       │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘       │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────┐
│  Layer 6: MONITORING & OBSERVABILITY                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │        Pipeline Monitor & Alerting (ice_monitor.py)             │ │
│  │                                                                 │ │
│  │ • Health Checks        • Performance Metrics                   │ │
│  │ • Quality Monitoring   • Cost Tracking                         │ │
│  │ • Error Tracking       • Usage Analytics                       │ │
│  │ • SLA Monitoring       • Capacity Planning                     │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.2 Core Architectural Principles

#### 1.2.1 Microservice-Oriented Design
- **Loosely Coupled Components**: Each layer communicates through well-defined interfaces
- **Single Responsibility**: Each component has one clear purpose
- **Independent Scaling**: Components can be scaled independently based on load
- **Failure Isolation**: Component failures don't cascade through the system

#### 1.2.2 Event-Driven Architecture
- **Asynchronous Processing**: Non-blocking data flow through queues and events
- **Event Sourcing**: All data changes captured as immutable events
- **Reactive Scaling**: System responds to load changes automatically
- **Temporal Decoupling**: Data producers and consumers operate independently

#### 1.2.3 Data-Centric Design
- **Schema Evolution**: Support for data format changes without system redesign
- **Version Management**: Multiple data format versions supported simultaneously
- **Quality-First**: Data quality validation at every processing stage
- **Lineage Tracking**: Complete data provenance from source to consumption

---

## 2. Component Specifications

### 2.1 Connection Pool Manager

**Purpose**: Centralized management of all external API connections with intelligent rate limiting and health monitoring.

#### 2.1.1 Core Functionality

```python
# ice_connection_manager.py
class ICEConnectionManager:
    """Centralized connection management for all external data sources"""
    
    def __init__(self):
        self.connection_pools = {}
        self.rate_limiters = {}
        self.circuit_breakers = {}
        self.health_monitors = {}
        self.auth_managers = {}
        
    def register_data_source(self, source_config: DataSourceConfig):
        """Register a new data source with connection management"""
        
        source_name = source_config.name
        
        # Create connection pool
        self.connection_pools[source_name] = aiohttp.TCPConnector(
            limit=source_config.max_connections,
            limit_per_host=source_config.max_connections_per_host,
            ttl_dns_cache=300,
            use_dns_cache=True
        )
        
        # Create rate limiter
        self.rate_limiters[source_name] = TokenBucketRateLimiter(
            rate=source_config.requests_per_second,
            burst=source_config.burst_capacity
        )
        
        # Create circuit breaker
        self.circuit_breakers[source_name] = CircuitBreaker(
            failure_threshold=source_config.failure_threshold,
            recovery_timeout=source_config.recovery_timeout,
            expected_exception=source_config.expected_exceptions
        )
        
        # Create health monitor
        self.health_monitors[source_name] = HealthMonitor(
            check_interval=source_config.health_check_interval,
            check_endpoint=source_config.health_check_endpoint
        )
        
        # Create auth manager
        self.auth_managers[source_name] = AuthenticationManager(
            auth_type=source_config.auth_type,
            credentials=source_config.credentials,
            refresh_threshold=source_config.auth_refresh_threshold
        )
```

#### 2.1.2 Rate Limiting Strategy

```python
class TokenBucketRateLimiter:
    """Token bucket implementation for smooth rate limiting"""
    
    def __init__(self, rate: float, burst: int):
        self.rate = rate  # tokens per second
        self.burst = burst  # maximum burst capacity
        self.tokens = burst
        self.last_update = time.time()
        self.lock = asyncio.Lock()
        
    async def acquire(self, tokens: int = 1) -> bool:
        """Acquire tokens for API request"""
        
        async with self.lock:
            now = time.time()
            elapsed = now - self.last_update
            
            # Add tokens based on elapsed time
            self.tokens = min(
                self.burst, 
                self.tokens + elapsed * self.rate
            )
            self.last_update = now
            
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
                
            return False
            
    async def acquire_with_wait(self, tokens: int = 1):
        """Acquire tokens, waiting if necessary"""
        
        while not await self.acquire(tokens):
            wait_time = tokens / self.rate
            await asyncio.sleep(wait_time)
```

#### 2.1.3 Circuit Breaker Pattern

```python
class CircuitBreaker:
    """Circuit breaker to handle API failures gracefully"""
    
    def __init__(self, failure_threshold: int, recovery_timeout: int, expected_exception: tuple):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
        
    async def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
            else:
                raise CircuitBreakerOpenException("Circuit breaker is OPEN")
                
        try:
            result = await func(*args, **kwargs)
            await self._on_success()
            return result
            
        except self.expected_exception as e:
            await self._on_failure()
            raise e
            
    async def _on_success(self):
        """Handle successful API call"""
        self.failure_count = 0
        self.state = CircuitState.CLOSED
        
    async def _on_failure(self):
        """Handle failed API call"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
```

### 2.2 Data Source Connectors

#### 2.2.1 News Connector Implementation

```python
# ice_news_connector.py
class NewsConnector(BaseDataConnector):
    """Specialized connector for financial news sources"""
    
    def __init__(self, source_config: NewsSourceConfig):
        super().__init__(source_config)
        self.entity_extractor = FinancialEntityExtractor()
        self.sentiment_analyzer = FinancialSentimentAnalyzer()
        self.relevance_scorer = NewsRelevanceScorer()
        
    async def fetch_breaking_news(self, lookback_minutes: int = 15) -> List[NewsArticle]:
        """Fetch breaking financial news"""
        
        query_params = {
            'q': '(stock OR market OR earnings OR SEC OR filing OR merger OR acquisition)',
            'language': 'en',
            'sortBy': 'publishedAt',
            'from': (datetime.utcnow() - timedelta(minutes=lookback_minutes)).isoformat(),
            'pageSize': 100
        }
        
        raw_articles = await self._fetch_raw_data(query_params)
        processed_articles = []
        
        for raw_article in raw_articles:
            # Extract financial entities
            entities = self.entity_extractor.extract(raw_article['title'] + ' ' + raw_article['description'])
            
            # Only process articles with financial relevance
            if entities['tickers'] or entities['financial_terms']:
                article = NewsArticle(
                    title=raw_article['title'],
                    content=raw_article['description'],
                    url=raw_article['url'],
                    published_at=self._parse_datetime(raw_article['publishedAt']),
                    source=raw_article['source']['name'],
                    entities=entities,
                    sentiment=self.sentiment_analyzer.analyze(raw_article['title'] + ' ' + raw_article['description']),
                    relevance_score=self.relevance_scorer.score(entities)
                )
                processed_articles.append(article)
                
        return processed_articles
        
    async def fetch_company_specific_news(self, tickers: List[str], days_back: int = 1) -> Dict[str, List[NewsArticle]]:
        """Fetch news specific to given tickers"""
        
        company_news = {}
        
        for ticker in tickers:
            query_params = {
                'q': f'{ticker} OR "{self._get_company_name(ticker)}"',
                'language': 'en', 
                'sortBy': 'publishedAt',
                'from': (datetime.utcnow() - timedelta(days=days_back)).isoformat(),
                'pageSize': 50
            }
            
            raw_articles = await self._fetch_raw_data(query_params)
            
            ticker_articles = []
            for raw_article in raw_articles:
                article = self._process_article(raw_article, focus_ticker=ticker)
                if article.relevance_score > 0.3:  # Filter for relevance
                    ticker_articles.append(article)
                    
            company_news[ticker] = ticker_articles
            
        return company_news
```

#### 2.2.2 Financial Data Connector

```python
# ice_financial_connector.py
class FinancialDataConnector(BaseDataConnector):
    """Multi-source financial data aggregation"""
    
    def __init__(self):
        self.sources = {
            'yfinance': YFinanceAPI(),
            'alpha_vantage': AlphaVantageAPI(),
            'financial_modeling_prep': FinancialModelingPrepAPI(),
            'quandl': QuandlAPI()
        }
        self.data_reconciler = FinancialDataReconciler()
        
    async def fetch_comprehensive_ticker_data(self, ticker: str) -> ComprehensiveTickerData:
        """Fetch data from all sources and reconcile differences"""
        
        source_data = {}
        fetch_tasks = []
        
        for source_name, api in self.sources.items():
            task = asyncio.create_task(
                self._safe_fetch(source_name, api.get_ticker_data, ticker)
            )
            fetch_tasks.append(task)
            
        results = await asyncio.gather(*fetch_tasks, return_exceptions=True)
        
        for i, result in enumerate(results):
            source_name = list(self.sources.keys())[i]
            if not isinstance(result, Exception):
                source_data[source_name] = result
                
        return self.data_reconciler.reconcile_ticker_data(ticker, source_data)
        
    async def _safe_fetch(self, source_name: str, fetch_func, *args):
        """Safely fetch data with error handling"""
        try:
            await self.connection_manager.rate_limiters[source_name].acquire()
            return await fetch_func(*args)
        except Exception as e:
            logger.warning(f"Failed to fetch from {source_name}: {e}")
            return None
```

### 2.3 Pipeline Orchestrator

#### 2.3.1 Main Pipeline Controller

```python
# ice_data_manager.py
class ICEDataManager:
    """Central orchestrator for all data processing pipelines"""
    
    def __init__(self):
        self.ingestion_queue = asyncio.PriorityQueue()
        self.processing_semaphore = asyncio.Semaphore(10)  # Limit concurrent processing
        
        # Processing engines
        self.validation_engine = DataValidationEngine()
        self.transformation_engine = DataTransformationEngine()
        self.quality_controller = DataQualityController()
        self.distribution_router = DataDistributionRouter()
        
        # Monitoring
        self.metrics_collector = MetricsCollector()
        self.alert_manager = AlertManager()
        
    async def start_pipeline_orchestration(self):
        """Start all pipeline components"""
        
        # Create processing tasks
        tasks = [
            asyncio.create_task(self._data_ingestion_coordinator()),
            asyncio.create_task(self._data_processing_worker()),
            asyncio.create_task(self._quality_monitoring_loop()),
            asyncio.create_task(self._metrics_collection_loop()),
            asyncio.create_task(self._health_check_loop())
        ]
        
        # Start pipeline schedulers
        scheduler_tasks = [
            asyncio.create_task(self._schedule_news_ingestion()),
            asyncio.create_task(self._schedule_earnings_ingestion()),
            asyncio.create_task(self._schedule_sec_filing_ingestion()),
            asyncio.create_task(self._schedule_market_data_ingestion())
        ]
        
        all_tasks = tasks + scheduler_tasks
        
        try:
            await asyncio.gather(*all_tasks)
        except Exception as e:
            logger.error(f"Pipeline orchestration failed: {e}")
            await self._graceful_shutdown(all_tasks)
            
    async def _data_processing_worker(self):
        """Main data processing worker loop"""
        
        while True:
            try:
                # Get next item from priority queue
                priority, data_item = await self.ingestion_queue.get()
                
                async with self.processing_semaphore:
                    await self._process_data_item(data_item)
                    
            except Exception as e:
                logger.error(f"Data processing error: {e}")
                await self.alert_manager.send_alert(
                    AlertType.PROCESSING_ERROR,
                    details={'error': str(e), 'data_item': data_item.id}
                )
                
    async def _process_data_item(self, data_item: DataItem):
        """Process individual data item through pipeline"""
        
        processing_context = ProcessingContext(
            item_id=data_item.id,
            source=data_item.source,
            start_time=datetime.utcnow()
        )
        
        try:
            # Step 1: Validation
            validation_result = await self.validation_engine.validate(data_item)
            if not validation_result.passed:
                await self._handle_validation_failure(data_item, validation_result)
                return
                
            # Step 2: Transformation
            transformed_data = await self.transformation_engine.transform(data_item)
            
            # Step 3: Quality Control
            quality_result = await self.quality_controller.assess_quality(transformed_data)
            if quality_result.score < 0.7:  # Quality threshold
                await self._handle_quality_failure(transformed_data, quality_result)
                return
                
            # Step 4: Distribution
            await self.distribution_router.route_data(transformed_data)
            
            # Step 5: Metrics Collection
            await self._record_processing_success(processing_context, transformed_data)
            
        except Exception as e:
            await self._handle_processing_failure(processing_context, e)
```

#### 2.3.2 Data Validation Engine

```python
# ice_data_validation.py
class DataValidationEngine:
    """Comprehensive data validation with business rule support"""
    
    def __init__(self):
        self.schema_validators = self._load_schema_validators()
        self.business_rule_validators = self._load_business_rules()
        self.cross_source_validator = CrossSourceValidator()
        
    async def validate(self, data_item: DataItem) -> ValidationResult:
        """Run comprehensive validation on data item"""
        
        validation_checks = []
        
        # Schema validation
        schema_check = await self._validate_schema(data_item)
        validation_checks.append(schema_check)
        
        # Business rule validation
        business_check = await self._validate_business_rules(data_item)
        validation_checks.append(business_check)
        
        # Cross-source consistency (if multiple sources available)
        if self._has_cross_source_data(data_item):
            consistency_check = await self.cross_source_validator.validate(data_item)
            validation_checks.append(consistency_check)
            
        # Content quality validation
        quality_check = await self._validate_content_quality(data_item)
        validation_checks.append(quality_check)
        
        # Calculate overall validation score
        overall_score = self._calculate_validation_score(validation_checks)
        
        return ValidationResult(
            item_id=data_item.id,
            passed=all(check.passed for check in validation_checks),
            checks=validation_checks,
            overall_score=overall_score,
            recommendation=self._get_validation_recommendation(validation_checks)
        )
        
    async def _validate_business_rules(self, data_item: DataItem) -> ValidationCheck:
        """Apply investment-specific business rules"""
        
        rule_results = []
        
        # Rule: Valid ticker symbols
        if data_item.type == DataType.FINANCIAL_DATA:
            ticker_result = self._validate_ticker_symbols(data_item)
            rule_results.append(ticker_result)
            
        # Rule: Reasonable financial metrics
        if hasattr(data_item, 'financial_metrics'):
            metrics_result = self._validate_financial_metric_ranges(data_item)
            rule_results.append(metrics_result)
            
        # Rule: Temporal consistency
        temporal_result = self._validate_temporal_consistency(data_item)
        rule_results.append(temporal_result)
        
        # Rule: Source credibility
        credibility_result = self._validate_source_credibility(data_item)
        rule_results.append(credibility_result)
        
        return ValidationCheck(
            name="business_rules",
            passed=all(result.passed for result in rule_results),
            score=np.mean([result.score for result in rule_results]),
            details=rule_results
        )
```

---

## 3. Data Flow Design

### 3.1 Data Flow Patterns

#### 3.1.1 Real-Time Stream Processing

```python
# Real-time data flow for time-sensitive information
class RealTimeDataFlow:
    """Handle time-sensitive data with minimal latency"""
    
    def __init__(self):
        self.stream_processors = {
            'breaking_news': BreakingNewsProcessor(),
            'market_alerts': MarketAlertProcessor(), 
            'regulatory_filings': RegulatoryFilingProcessor()
        }
        
    async def process_real_time_stream(self, data_stream):
        """Process real-time data stream with <5 minute latency"""
        
        async for data_item in data_stream:
            # Skip detailed validation for speed
            if self._quick_validation(data_item):
                # Direct routing to high-priority queue
                await self.distribution_router.route_high_priority(data_item)
                
                # Async background processing
                asyncio.create_task(
                    self._background_quality_assessment(data_item)
                )
```

#### 3.1.2 Batch Processing Pipeline

```python
# Batch processing for comprehensive analysis
class BatchDataFlow:
    """Handle large volume data with comprehensive processing"""
    
    def __init__(self):
        self.batch_size = 100
        self.processing_window = timedelta(hours=1)
        
    async def process_batch_data(self, data_batch: List[DataItem]):
        """Process batch data with full validation and enrichment"""
        
        # Group by data type for efficient processing
        grouped_data = self._group_by_type(data_batch)
        
        processing_tasks = []
        for data_type, items in grouped_data.items():
            task = asyncio.create_task(
                self._process_typed_batch(data_type, items)
            )
            processing_tasks.append(task)
            
        batch_results = await asyncio.gather(*processing_tasks)
        return self._consolidate_batch_results(batch_results)
```

### 3.2 Data Transformation Pipeline

#### 3.2.1 Standard Data Format

```python
# Standardized data format across all sources
@dataclass
class StandardDataRecord:
    # Universal identifiers
    record_id: str
    source: str
    data_type: DataType
    timestamp: datetime
    
    # Core content
    raw_data: Dict[str, Any]
    processed_data: Optional[Dict[str, Any]] = None
    
    # Extracted entities and relationships
    entities: Dict[str, List[str]] = field(default_factory=dict)
    relationships: List[Relationship] = field(default_factory=list)
    
    # Quality and confidence metrics
    quality_score: float = 0.0
    confidence_score: float = 0.0
    validation_status: ValidationStatus = ValidationStatus.PENDING
    
    # Processing metadata
    processing_stage: ProcessingStage = ProcessingStage.INGESTED
    processing_history: List[ProcessingEvent] = field(default_factory=list)
    
    # Business context
    investment_relevance: float = 0.0
    priority_level: PriorityLevel = PriorityLevel.NORMAL
    
    def add_processing_event(self, event: ProcessingEvent):
        """Add processing event to history"""
        self.processing_history.append(event)
        self.processing_stage = event.resulting_stage
```

#### 3.2.2 Data Transformation Rules

```python
# Data transformation engine with configurable rules
class DataTransformationEngine:
    """Transform raw data into standardized format"""
    
    def __init__(self):
        self.transformation_rules = self._load_transformation_rules()
        self.entity_extractors = self._initialize_entity_extractors()
        self.relationship_extractors = self._initialize_relationship_extractors()
        
    async def transform(self, data_item: DataItem) -> StandardDataRecord:
        """Apply transformation rules to convert raw data"""
        
        # Create standard record shell
        standard_record = StandardDataRecord(
            record_id=self._generate_record_id(data_item),
            source=data_item.source,
            data_type=data_item.type,
            timestamp=data_item.timestamp,
            raw_data=data_item.data
        )
        
        # Apply source-specific transformation rules
        transformation_rule = self.transformation_rules[data_item.source]
        processed_data = await transformation_rule.transform(data_item.data)
        standard_record.processed_data = processed_data
        
        # Extract entities
        entities = await self._extract_entities(processed_data)
        standard_record.entities = entities
        
        # Extract relationships
        relationships = await self._extract_relationships(processed_data, entities)
        standard_record.relationships = relationships
        
        # Calculate investment relevance
        relevance_score = self._calculate_investment_relevance(standard_record)
        standard_record.investment_relevance = relevance_score
        
        # Set priority based on content and source
        priority = self._determine_priority(standard_record)
        standard_record.priority_level = priority
        
        return standard_record
```

---

## 4. Integration Patterns

### 4.1 LightRAG Integration

```python
# Integration with existing LightRAG system
class LightRAGIntegration:
    """Bridge between data pipeline and LightRAG processing"""
    
    def __init__(self, lightrag_instance):
        self.lightrag = lightrag_instance
        self.document_formatter = LightRAGDocumentFormatter()
        
    async def process_for_lightrag(self, standard_record: StandardDataRecord):
        """Convert standard record for LightRAG processing"""
        
        # Format document for LightRAG consumption
        formatted_doc = self.document_formatter.format(standard_record)
        
        # Add to LightRAG with metadata
        result = await self.lightrag.add_document(
            text=formatted_doc.content,
            doc_type=formatted_doc.type,
            metadata=formatted_doc.metadata
        )
        
        # Track processing result
        if result["status"] == "success":
            standard_record.add_processing_event(
                ProcessingEvent(
                    stage=ProcessingStage.LIGHTRAG_PROCESSED,
                    timestamp=datetime.utcnow(),
                    details={"lightrag_doc_id": result.get("doc_id")}
                )
            )
        
        return result
```

### 4.2 Graph Database Integration

```python
# Integration with custom graph database
class GraphDatabaseIntegration:
    """Integration with NetworkX-based graph storage"""
    
    def __init__(self, graph_engine):
        self.graph_engine = graph_engine
        self.relationship_mapper = RelationshipMapper()
        
    async def update_graph_from_data(self, standard_record: StandardDataRecord):
        """Update graph database with extracted relationships"""
        
        graph_updates = []
        
        # Convert relationships to graph edges
        for relationship in standard_record.relationships:
            edge = self.relationship_mapper.to_graph_edge(
                relationship=relationship,
                source_record=standard_record
            )
            
            # Add edge to graph
            edge_id = await self.graph_engine.add_edge(
                source=edge.source_entity,
                target=edge.target_entity,
                edge_type=edge.relationship_type,
                confidence=edge.confidence,
                source_doc=standard_record.record_id,
                timestamp=standard_record.timestamp
            )
            
            graph_updates.append(edge_id)
            
        return graph_updates
```

### 4.3 Search Index Integration

```python
# Integration with search indexing system
class SearchIndexIntegration:
    """Integration with search indexing for fast lookups"""
    
    def __init__(self):
        self.text_index = TextSearchIndex()
        self.entity_index = EntitySearchIndex()
        self.temporal_index = TemporalSearchIndex()
        
    async def index_standard_record(self, standard_record: StandardDataRecord):
        """Index record across multiple search dimensions"""
        
        indexing_tasks = [
            # Full-text search indexing
            self.text_index.index_document(
                doc_id=standard_record.record_id,
                content=self._extract_searchable_text(standard_record),
                metadata=standard_record.processed_data
            ),
            
            # Entity-based indexing
            self.entity_index.index_entities(
                doc_id=standard_record.record_id,
                entities=standard_record.entities,
                relationships=standard_record.relationships
            ),
            
            # Temporal indexing for time-based queries
            self.temporal_index.index_by_time(
                doc_id=standard_record.record_id,
                timestamp=standard_record.timestamp,
                data_type=standard_record.data_type
            )
        ]
        
        await asyncio.gather(*indexing_tasks)
```

---

## 5. Scalability & Performance

### 5.1 Horizontal Scaling Architecture

```python
# Scalable processing architecture
class ScalableProcessingArchitecture:
    """Architecture supporting horizontal scaling"""
    
    def __init__(self):
        self.worker_pool = WorkerPool()
        self.load_balancer = LoadBalancer()
        self.resource_monitor = ResourceMonitor()
        
    async def scale_based_on_load(self):
        """Dynamically scale processing capacity"""
        
        current_load = await self.resource_monitor.get_current_load()
        
        if current_load.cpu_usage > 0.8 or current_load.queue_size > 1000:
            # Scale up
            await self.worker_pool.add_workers(2)
            logger.info("Scaled up processing capacity")
            
        elif current_load.cpu_usage < 0.3 and current_load.queue_size < 100:
            # Scale down
            await self.worker_pool.remove_workers(1)
            logger.info("Scaled down processing capacity")
```

### 5.2 Caching Strategy

```python
# Multi-level caching for performance
class MultiLevelCache:
    """Implement multi-level caching strategy"""
    
    def __init__(self):
        self.l1_cache = LRUCache(maxsize=1000)  # In-memory
        self.l2_cache = RedisCache()  # Distributed
        self.l3_cache = FileCache()   # Persistent
        
    async def get(self, key: str) -> Optional[Any]:
        """Get from cache with multi-level fallback"""
        
        # L1: In-memory cache (fastest)
        if key in self.l1_cache:
            return self.l1_cache[key]
            
        # L2: Distributed cache
        value = await self.l2_cache.get(key)
        if value:
            self.l1_cache[key] = value
            return value
            
        # L3: Persistent cache
        value = await self.l3_cache.get(key)
        if value:
            await self.l2_cache.set(key, value, ttl=3600)
            self.l1_cache[key] = value
            return value
            
        return None
        
    async def set(self, key: str, value: Any, ttl: int = 3600):
        """Set in all cache levels"""
        
        self.l1_cache[key] = value
        await self.l2_cache.set(key, value, ttl=ttl)
        await self.l3_cache.set(key, value)
```

---

## 6. Security Architecture

### 6.1 Authentication & Authorization

```python
# Secure API key management
class SecureAPIKeyManager:
    """Secure management of API keys and credentials"""
    
    def __init__(self):
        self.key_vault = KeyVault()
        self.encryption_service = EncryptionService()
        self.rotation_scheduler = KeyRotationScheduler()
        
    async def get_api_key(self, service_name: str) -> str:
        """Securely retrieve API key"""
        
        encrypted_key = await self.key_vault.get(f"{service_name}_api_key")
        decrypted_key = self.encryption_service.decrypt(encrypted_key)
        
        # Log access for audit
        await self._log_key_access(service_name)
        
        return decrypted_key
        
    async def rotate_api_keys(self):
        """Automatic API key rotation"""
        
        for service_name in self.managed_services:
            if await self.rotation_scheduler.should_rotate(service_name):
                await self._rotate_service_key(service_name)
```

### 6.2 Data Privacy & Compliance

```python
# Data privacy protection
class DataPrivacyManager:
    """Ensure data privacy and compliance"""
    
    def __init__(self):
        self.pii_detector = PIIDetector()
        self.anonymizer = DataAnonymizer()
        self.audit_logger = AuditLogger()
        
    async def process_with_privacy_protection(self, data_record: StandardDataRecord):
        """Process data with privacy protection"""
        
        # Detect sensitive information
        pii_detected = self.pii_detector.scan(data_record.raw_data)
        
        if pii_detected:
            # Anonymize sensitive data
            anonymized_data = self.anonymizer.anonymize(
                data_record.raw_data, pii_detected
            )
            data_record.processed_data = anonymized_data
            
            # Log privacy action
            await self.audit_logger.log_privacy_action(
                record_id=data_record.record_id,
                action="anonymization",
                pii_types=pii_detected
            )
```

---

## 7. Implementation Guidelines

### 7.1 Development Phases

#### Phase 1: Core Infrastructure (Weeks 1-2)
1. **Connection Manager**: Implement centralized connection management
2. **Base Connectors**: Create abstract base classes for data connectors  
3. **Pipeline Orchestrator**: Build core pipeline management framework
4. **Monitoring Foundation**: Set up basic monitoring and logging

#### Phase 2: Data Source Integration (Weeks 2-4)
1. **News Connector**: Implement NewsAPI and Benzinga integration
2. **Financial Connector**: Multi-source financial data aggregation
3. **SEC Filing Connector**: EDGAR API integration and XBRL processing
4. **Validation Engine**: Comprehensive data validation framework

#### Phase 3: Processing Pipeline (Weeks 4-6)
1. **Transformation Engine**: Standardized data transformation
2. **Quality Controller**: Data quality assessment and scoring
3. **Distribution Router**: Multi-destination data routing
4. **Cache Layer**: Multi-level caching implementation

#### Phase 4: Integration & Optimization (Weeks 6-8)
1. **LightRAG Integration**: Bridge with existing LightRAG system
2. **Graph Integration**: Connect with NetworkX graph database
3. **Search Integration**: Full-text and entity search indexing
4. **Performance Optimization**: Scaling and caching optimization

### 7.2 Testing Strategy

#### 7.2.1 Unit Testing Framework

```python
# Comprehensive unit testing approach
class TestDataPipeline:
    """Unit tests for data pipeline components"""
    
    @pytest.fixture
    def mock_data_source(self):
        """Create mock data source for testing"""
        return MockDataSource(
            response_data=self.load_test_data('sample_news_response.json'),
            response_delay=0.1,
            failure_rate=0.05
        )
        
    async def test_news_connector_entity_extraction(self, mock_data_source):
        """Test entity extraction from news articles"""
        
        connector = NewsConnector(self.get_test_config())
        articles = await connector.fetch_breaking_news(lookback_minutes=15)
        
        # Verify entity extraction
        for article in articles:
            assert article.entities is not None
            assert 'tickers' in article.entities
            assert 'financial_terms' in article.entities
            
        # Verify sentiment analysis
        assert all(hasattr(article, 'sentiment') for article in articles)
```

#### 7.2.2 Integration Testing

```python
# End-to-end integration testing
class TestPipelineIntegration:
    """Integration tests for complete pipeline"""
    
    async def test_end_to_end_news_processing(self):
        """Test complete news processing pipeline"""
        
        # Setup test data
        test_news_data = self.create_test_news_data()
        
        # Inject test data into pipeline
        data_manager = ICEDataManager()
        await data_manager.process_test_data(test_news_data)
        
        # Verify processing results
        processed_records = await self.get_processed_records()
        
        assert len(processed_records) == len(test_news_data)
        assert all(record.validation_status == ValidationStatus.PASSED 
                  for record in processed_records)
        assert all(record.quality_score > 0.7 
                  for record in processed_records)
```

### 7.3 Deployment Configuration

#### 7.3.1 Production Configuration

```yaml
# production_config.yaml
data_pipeline:
  connection_management:
    max_connections_per_source: 20
    connection_timeout: 30
    retry_attempts: 3
    circuit_breaker_threshold: 5
    
  rate_limiting:
    newsapi:
      requests_per_second: 0.5
      burst_capacity: 5
    benzinga:
      requests_per_second: 2.0
      burst_capacity: 10
      
  processing:
    max_concurrent_items: 50
    batch_size: 100
    processing_timeout: 300
    
  quality_control:
    min_quality_score: 0.7
    validation_timeout: 60
    cross_validation_threshold: 0.8
    
  monitoring:
    health_check_interval: 60
    metrics_collection_interval: 30
    alert_thresholds:
      error_rate: 0.05
      processing_latency: 300
      queue_size: 1000
```

#### 7.3.2 Infrastructure Requirements

```python
# Infrastructure specification
INFRASTRUCTURE_REQUIREMENTS = {
    'compute': {
        'cpu_cores': 8,
        'memory_gb': 32,
        'storage_gb': 500,
        'network_bandwidth_mbps': 1000
    },
    'external_services': {
        'redis': {
            'memory_gb': 8,
            'persistence': True
        },
        'monitoring': {
            'prometheus': True,
            'grafana': True,
            'alertmanager': True
        }
    },
    'api_quotas': {
        'newsapi': '1000 requests/hour',
        'benzinga': '120 requests/minute', 
        'sec_edgar': '10 requests/second',
        'alpha_vantage': '5 requests/minute'
    }
}
```

---

## Conclusion

This technical architecture specification provides a comprehensive blueprint for implementing a scalable, robust data ingestion pipeline for the Investment Context Engine. The architecture emphasizes:

- **Modularity**: Components can be developed and scaled independently
- **Reliability**: Circuit breakers, retries, and health monitoring ensure system resilience
- **Performance**: Multi-level caching and asynchronous processing optimize throughput
- **Quality**: Comprehensive validation and monitoring maintain data integrity
- **Security**: Secure credential management and privacy protection ensure compliance

The phased implementation approach allows for iterative development while ensuring each component delivers immediate business value. The architecture is designed to support the unique requirements of investment decision-making while providing a scalable foundation for future enhancements.

**Next Steps**: Begin Phase 1 implementation with connection manager and base connector development, following the detailed specifications provided in this document.

---

**Document Version**: 1.0  
**Last Updated**: August 2025  
**Review Cycle**: Bi-weekly during development phases  
**Approval Required**: Technical Architecture Review Board