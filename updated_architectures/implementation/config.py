# config.py
"""
ICE Configuration - Basic configuration and logging setup
Simple, direct configuration management without complex hierarchies
Provides sensible defaults and environment variable integration
Relevant files: ice_simplified.py, ice_core.py, data_ingestion.py, query_engine.py
"""

import os
import logging
import sys
from pathlib import Path
from typing import Dict, Optional, Any, List
from datetime import datetime


# ========== CONFIDENCE CENTRALIZATION (Phase 2.8 - 2025-11-25) ==========
# All confidence values centralized here for consistency and tuning
# Organized by category for easy discovery and modification

CONFIDENCE_DEFAULTS: Dict[str, float] = {
    # === Source-specific defaults (used when source doesn't provide confidence) ===
    'source_default': 0.5,           # Unknown or unspecified sources
    'source_api': 0.85,              # API-provided data (FMP, Alpha Vantage, etc.)
    'source_email': 0.90,            # Email-sourced documents (research reports)
    'source_sec_filing': 0.95,       # SEC EDGAR filings (regulatory, verified)
    'source_news': 0.70,             # News articles (variable quality)
    'source_pattern': 0.70,          # Pattern-extracted data (regex matches)

    # === Node type defaults (for graph nodes without confidence) ===
    'node_email': 1.0,               # EMAIL nodes (existence is certain)
    'node_sender': 1.0,              # SENDER nodes (existence is certain)
    'node_ticker': 0.98,             # Validated ticker symbols
    'node_entity': 0.80,             # General extracted entities
    'node_relationship': 0.80,       # Graph edges/relationships

    # === Extraction defaults (for entity/relationship extraction) ===
    'extraction_high': 0.95,         # High confidence extraction (exact match)
    'extraction_medium': 0.85,       # Medium confidence (strong pattern)
    'extraction_low': 0.75,          # Low confidence (weak pattern)
    'extraction_minimal': 0.60,      # Minimal confidence (uncertain)
    'extraction_failed': 0.0,        # Failed extraction

    # === Query thresholds (filtering in query processing) ===
    'threshold_high': 0.80,          # High quality filter
    'threshold_medium': 0.70,        # Medium quality filter
    'threshold_default': 0.60,       # Default quality filter
    'threshold_low': 0.50,           # Low quality filter (more results)

    # === Confidence boosts/adjustments ===
    'boost_financial_term': 0.05,    # Per financial term found
    'boost_source_verified': 0.10,   # Source verification passed
    'boost_cross_referenced': 0.15,  # Cross-reference validation
    'penalty_ambiguous': 0.10,       # Penalty for ambiguous data

    # === Financial metrics defaults ===
    'metric_default': 0.80,          # Default for financial metrics
    'metric_rating': 0.85,           # Analyst ratings
    'metric_price_target': 0.92,     # Price targets
    'metric_fundamental': 0.87,      # Fundamental data (P/E, revenue, etc.)

    # === Scoring weights (for composite scores) ===
    'weight_confidence': 0.30,       # Confidence weight in ranking
    'weight_freshness': 0.30,        # Freshness weight in ranking
    'weight_relevance': 0.40,        # Relevance weight in ranking

    # === Relationship extraction defaults (Phase 2.8 Core Path) ===
    'relationship_base': 0.5,        # Base confidence for relationships
    'relationship_competitive': 0.8, # Competitive relationship confidence
    'relationship_supplier': 0.75,   # Supplier/vendor relationship
    'relationship_employment': 0.85, # Employment/executive relationship
    'relationship_portfolio': 0.8,   # Portfolio holding relationship
    'relationship_event_close': 0.7, # Event within 30 days
    'relationship_event_distant': 0.5, # Event beyond 30 days
    'relationship_category': 0.5,    # Category/sector relationship

    # === Query processing defaults (Phase 2.8 Core Path) ===
    'lightrag_base': 0.7,            # Base confidence for LightRAG results
    'query_min_threshold': 0.6,      # Minimum threshold for query results
    'confidence_cap': 0.95,          # Maximum confidence ceiling
    'confidence_floor': 0.1,         # Minimum confidence floor
    'no_sources': 0.0,               # No source attribution available
    'single_source': 0.7,            # Single source confidence
    'chunk_default': 0.7,            # Default chunk confidence
    'path_default': 0.7,             # Default path confidence

    # === Graph building defaults (Phase 2.8 Core Path) ===
    'edge_default': 0.5,             # Default edge/relationship confidence
    'ui_min_threshold': 0.6,         # UI display minimum threshold

    # === Relationship pattern confidences (Phase 2.8 Core Path) ===
    'pattern_depends_on': 0.8,       # Dependency relationship
    'pattern_supplies': 0.75,        # Supply chain relationship
    'pattern_exposed_to': 0.85,      # Risk exposure relationship
    'pattern_drives': 0.8,           # Driver relationship
    'pattern_impacts': 0.7,          # Impact relationship
    'pattern_competes_with': 0.75,   # Competitive relationship
    'pattern_owns': 0.9,             # Ownership relationship
    'pattern_operates_in': 0.7,      # Operational geography
    'pattern_manufactures_in': 0.8,  # Manufacturing geography
}


# Source-specific confidence multipliers (for relationship/entity weighting by source)
# Higher = more reliable source, used to weight extracted data
SOURCE_CONFIDENCE_MULTIPLIERS: Dict[str, float] = {
    'sec_edgar': 1.0,       # Regulatory filing (highest authority)
    'sec_facts': 0.95,      # XBRL data from SEC
    'yahoo': 0.85,          # Financial data provider
    'benzinga': 0.80,       # Premium financial news
    'newsapi': 0.75,        # Standard news aggregator
    'finnhub': 0.75,        # Market news provider
    'marketaux': 0.70,      # Alternative news source
    'email': 0.70,          # Analyst email/reports
    'exa': 0.65,            # Web search results
    'unknown': 0.50,        # Unknown/unspecified source
}


# Confidence weights for composite scoring (Phase 2.8 Core Path)
# Used in ice_query_processor and ice_graph_builder for weighted confidence calculation
CONFIDENCE_WEIGHTS: Dict[str, float] = {
    'source_reliability': 0.3,      # Weight for source quality in composite score
    'relationship_clarity': 0.4,    # Weight for relationship clarity
    'evidence_strength': 0.3,       # Weight for evidence strength
    'base_weight': 0.6,             # Weight for base confidence (vs path)
    'path_weight': 0.4,             # Weight for path-based confidence
}


def get_confidence_weight(key: str, default: float = 0.5) -> float:
    """
    Get weight value for composite confidence calculations.

    Args:
        key: Weight key (e.g., 'base_weight', 'path_weight')
        default: Fallback if key not found

    Returns:
        Weight value (0.0-1.0)
    """
    return CONFIDENCE_WEIGHTS.get(key, default)


def get_source_confidence(source: str) -> float:
    """
    Get confidence multiplier for a data source

    Args:
        source: Source identifier (e.g., 'sec_edgar', 'newsapi', 'email')

    Returns:
        Confidence multiplier (0.0-1.0)

    Example:
        >>> get_source_confidence('sec_edgar')
        1.0
        >>> get_source_confidence('unknown_source')
        0.5
    """
    return SOURCE_CONFIDENCE_MULTIPLIERS.get(source, SOURCE_CONFIDENCE_MULTIPLIERS['unknown'])


def get_confidence(key: str, default: Optional[float] = None) -> float:
    """
    Get confidence value from centralized defaults

    Args:
        key: Confidence key (e.g., 'source_api', 'threshold_default')
        default: Fallback if key not found (defaults to 'source_default')

    Returns:
        Confidence value (0.0-1.0)

    Example:
        >>> get_confidence('source_api')
        0.85
        >>> get_confidence('unknown_key', 0.5)
        0.5
    """
    if default is None:
        default = CONFIDENCE_DEFAULTS.get('source_default', 0.5)
    return CONFIDENCE_DEFAULTS.get(key, default)


def validate_confidence_config() -> Dict[str, Any]:
    """
    Validate confidence configuration at startup

    Returns:
        Dict with validation results and any warnings

    Raises:
        ValueError: If critical confidence values are invalid
    """
    validation = {
        'valid': True,
        'warnings': [],
        'errors': []
    }

    for key, value in CONFIDENCE_DEFAULTS.items():
        # Check type
        if not isinstance(value, (int, float)):
            validation['errors'].append(f"'{key}': Expected float, got {type(value).__name__}")
            validation['valid'] = False
            continue

        # Check range (0.0-1.0 for most, can be negative for penalties)
        if key.startswith('penalty_'):
            if not 0.0 <= value <= 0.5:
                validation['warnings'].append(f"'{key}': {value} seems high for a penalty")
        elif key.startswith('boost_'):
            if not 0.0 <= value <= 0.3:
                validation['warnings'].append(f"'{key}': {value} seems high for a boost")
        elif key.startswith('weight_'):
            if not 0.0 <= value <= 1.0:
                validation['errors'].append(f"'{key}': Weight {value} must be 0.0-1.0")
                validation['valid'] = False
        else:
            if not 0.0 <= value <= 1.0:
                validation['errors'].append(f"'{key}': Confidence {value} must be 0.0-1.0")
                validation['valid'] = False

    # Check weights sum to 1.0 (or close)
    weights = {k: v for k, v in CONFIDENCE_DEFAULTS.items() if k.startswith('weight_')}
    if weights:
        weight_sum = sum(weights.values())
        if not 0.99 <= weight_sum <= 1.01:
            validation['warnings'].append(f"Scoring weights sum to {weight_sum:.2f}, expected ~1.0")

    if not validation['valid']:
        raise ValueError(f"Invalid confidence config: {validation['errors']}")

    return validation


class ICEConfig:
    """
    Simple configuration management for ICE simplified architecture

    Key principles:
    1. Environment variables with sensible defaults
    2. No complex configuration hierarchies or validation layers
    3. Direct attribute access for simplicity
    4. Optional validation only where critical
    """

    def __init__(self):
        """Initialize configuration from environment variables with defaults"""

        # Core LightRAG configuration
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.working_dir = os.getenv('ICE_WORKING_DIR', './src/ice_lightrag/storage')
        self.batch_size = int(os.getenv('ICE_BATCH_SIZE', '5'))
        self.timeout = int(os.getenv('ICE_TIMEOUT', '30'))
        self.log_level = os.getenv('ICE_LOG_LEVEL', 'INFO')

        # Data ingestion API keys
        self.api_keys = {
            'newsapi': os.getenv('NEWSAPI_ORG_API_KEY'),
            'alpha_vantage': os.getenv('ALPHA_VANTAGE_API_KEY'),
            'fmp': os.getenv('FMP_API_KEY'),
            'polygon': os.getenv('POLYGON_API_KEY'),
            'finnhub': os.getenv('FINNHUB_API_KEY'),
            'benzinga': os.getenv('BENZINGA_API_TOKEN'),
            'marketaux': os.getenv('MARKETAUX_API_KEY'),
            'exa': os.getenv('EXA_API_KEY')
        }

        # Filter out None values
        self.api_keys = {k: v for k, v in self.api_keys.items() if v}

        # Query engine settings
        self.default_query_mode = os.getenv('ICE_QUERY_MODE', 'hybrid')
        self.query_timeout = int(os.getenv('ICE_QUERY_TIMEOUT', '60'))

        # Logging configuration
        self.log_to_file = os.getenv('ICE_LOG_TO_FILE', 'false').lower() == 'true'
        self.log_file = os.getenv('ICE_LOG_FILE', 'ice.log')

        # Performance settings
        self.max_concurrent_queries = int(os.getenv('ICE_MAX_CONCURRENT_QUERIES', '3'))
        self.cache_enabled = os.getenv('ICE_CACHE_ENABLED', 'true').lower() == 'true'

        # Docling Integration Feature Flags (Switchable Architecture)
        # Environment variables: USE_DOCLING_SEC, USE_DOCLING_EMAIL, etc.

        # CRITICAL: SEC Filing Content Extraction
        # Current: Metadata only (0% content)
        # Docling: Full content + tables (97.9% accuracy)
        # Default: true (enable docling for SEC)
        self.use_docling_sec = os.getenv('USE_DOCLING_SEC', 'true').lower() == 'true'

        # Email Attachment Processing
        # Current: PyPDF2/openpyxl (42% table accuracy)
        # Docling: 97.9% table accuracy
        # Default: true (enable docling for email)
        self.use_docling_email = os.getenv('USE_DOCLING_EMAIL', 'true').lower() == 'true'

        # URL PDF Processing (Phase 2 - 2025-11-04)
        # Current: pdfplumber (42% table accuracy)
        # Docling: 97.9% table accuracy
        # Default: true (enable docling for URL PDFs)
        self.use_docling_urls = os.getenv('USE_DOCLING_URLS', 'true').lower() == 'true'

        # Future Features (document only, default false)
        self.use_docling_uploads = os.getenv('USE_DOCLING_UPLOADS', 'false').lower() == 'true'
        self.use_docling_archives = os.getenv('USE_DOCLING_ARCHIVES', 'false').lower() == 'true'
        self.use_docling_news = os.getenv('USE_DOCLING_NEWS', 'false').lower() == 'true'

        # Docling Configuration
        self.docling_cache_dir = os.getenv('DOCLING_CACHE_DIR', str(Path.home() / '.ice' / 'docling_cache'))
        self.docling_log_conversions = os.getenv('DOCLING_LOG_CONVERSIONS', 'false').lower() == 'true'

        # Crawl4AI Integration Feature Flags (Switchable Architecture)
        # Environment variables: USE_CRAWL4AI_LINKS, CRAWL4AI_TIMEOUT, CRAWL4AI_HEADLESS

        # URL Fetching Strategy
        # Current: Simple HTTP only (fast, free, but fails on JS-heavy sites)
        # Crawl4AI: Browser automation (slower, CPU cost, handles JS/auth)
        # Default: false (use simple HTTP, enable when needed)
        self.use_crawl4ai_links = os.getenv('USE_CRAWL4AI_LINKS', 'false').lower() == 'true'

        # URL Processing Master Switch
        # Controls whether to process URLs in emails at all
        # true: Extract and download URLs from emails
        # false: Skip all URL processing (faster, attachment-only builds)
        # Default: true (process URLs normally)
        self.process_urls = os.getenv('ICE_PROCESS_URLS', 'true').lower() == 'true'

        # Crawl4AI timeout (seconds)
        # Balance between waiting for slow pages vs failing fast
        # Default: 60s (reasonable for most pages)
        self.crawl4ai_timeout = int(os.getenv('CRAWL4AI_TIMEOUT', '60'))

        # Crawl4AI headless mode
        # true: faster, no browser window (production)
        # false: debugging, see what's happening
        self.crawl4ai_headless = os.getenv('CRAWL4AI_HEADLESS', 'true').lower() == 'true'

        # Signal Store (Dual-Layer Architecture) Feature Flags
        # Environment variables: USE_SIGNAL_STORE, SIGNAL_STORE_PATH, SIGNAL_STORE_TIMEOUT

        # Signal Store enables fast (<1s) structured queries
        # Current: LightRAG only (~12s for all queries)
        # Signal Store: SQL lookups for "What/Which/Show" queries (<1s) + LightRAG for "Why/How" queries (~12s)
        # Default: true (enable dual-layer architecture)
        self.use_signal_store = os.getenv('USE_SIGNAL_STORE', 'true').lower() == 'true'

        # Signal Store database path
        # Default: data/signal_store/signal_store.db
        self.signal_store_path = os.getenv('SIGNAL_STORE_PATH', 'data/signal_store/signal_store.db')

        # Signal Store query timeout (milliseconds)
        # Balance between waiting for slow queries vs failing fast
        # Default: 5000ms (5 seconds)
        self.signal_store_timeout = int(os.getenv('SIGNAL_STORE_TIMEOUT', '5000'))

        # Signal Store debug mode
        # true: log all queries and performance metrics
        # false: minimal logging (production)
        self.signal_store_debug = os.getenv('SIGNAL_STORE_DEBUG', 'false').lower() == 'true'

        # ========== TEMPORAL CONFIGURATION (2025-11-18) ==========
        # Data ingestion lookback windows (how far back to fetch historical data)

        # News API lookback period (days)
        # How many days of historical news to fetch per ticker
        # Default: 7 days (NewsAPI free tier limit)
        # Range: 1-30 days (NewsAPI free tier supports up to 30 days)
        self.news_lookback_days = int(os.getenv('ICE_NEWS_LOOKBACK_DAYS', '7'))

        # Financial data lookback period (days)
        # How far back to fetch market data, financial metrics
        # Default: 90 days (~1 quarter)
        # Range: 30-365 days
        self.financial_lookback_days = int(os.getenv('ICE_FINANCIAL_LOOKBACK_DAYS', '90'))

        # Freshness scoring configuration
        # Half-life for exponential decay (days)
        # Determines how quickly information is considered stale
        # Default: 30 days (score drops to 0.5 after 30 days)
        # Lower = more aggressive decay (value recent info more)
        # Higher = slower decay (value historical info more)
        self.freshness_half_life_days = int(os.getenv('ICE_FRESHNESS_HALF_LIFE_DAYS', '30'))

        # Stale threshold (days)
        # Data older than this is categorized as "very_stale"
        # Default: 365 days (1 year)
        # Use for filtering out very old data in queries
        self.stale_threshold_days = int(os.getenv('ICE_STALE_THRESHOLD_DAYS', '365'))

        # Recency ranking weight (for get_latest_signals_ranked)
        # Balance between freshness and confidence in ranking
        # Default: 0.5 (50% freshness, 50% confidence)
        # 0.0 = pure confidence ranking (ignore recency)
        # 0.5 = balanced (recommended for investment decisions)
        # 1.0 = pure recency ranking (ignore confidence)
        self.recency_ranking_weight = float(os.getenv('ICE_RECENCY_RANKING_WEIGHT', '0.5'))

        # ========== SEC COMPANY FACTS CONFIGURATION (2025-11-22) ==========
        # Free financial metrics from SEC XBRL Company Facts API

        # Enable/disable SEC Company Facts fetching
        # Default: true (use free SEC data for financial metrics)
        self.sec_facts_enabled = os.getenv('ICE_SEC_FACTS_ENABLED', 'true').lower() == 'true'

        # Number of recent quarters to fetch (default: 8 = 2 years)
        # Limits memory usage (full history can be 10+ years, 5-10MB per company)
        # Range: 4-12 quarters (1-3 years)
        self.sec_facts_lookback_quarters = int(os.getenv('ICE_SEC_FACTS_LOOKBACK_QUARTERS', '8'))

        # ========== RELATIONSHIP EXTRACTION CONFIGURATION (2025-11-24) ==========
        # Cross-company relationship extraction for multi-hop intelligence

        # Enable/disable relationship extraction
        # Default: true (extract competitors, suppliers, customers, executives, partnerships)
        self.relationship_extraction_enabled = os.getenv(
            'ICE_RELATIONSHIP_EXTRACTION', 'true'
        ).lower() == 'true'

        # Minimum confidence threshold for relationships (0.0-1.0)
        # Lower = more relationships but potentially more false positives
        # Higher = fewer but higher quality relationships
        # Default: 0.5 (balanced - recommended for investment decisions)
        self.relationship_confidence_threshold = float(os.getenv(
            'ICE_RELATIONSHIP_CONFIDENCE_THRESHOLD', '0.5'
        ))

        # Maximum relationships to extract per document
        # Prevents memory explosion on relationship-dense documents
        # Default: 50 (typical documents have 5-15 relationships)
        self.max_relationships_per_doc = int(os.getenv(
            'ICE_MAX_RELATIONSHIPS_PER_DOC', '50'
        ))

        # Relationship cache size (number of documents)
        # Content-based caching prevents redundant extraction
        # Default: 1000 (sufficient for typical portfolios)
        self.relationship_cache_size = int(os.getenv(
            'ICE_RELATIONSHIP_CACHE_SIZE', '1000'
        ))

        # ===== Event Extraction Configuration (Phase 2.7B - Option 1) =====
        # Enable/disable event extraction from documents
        # Events include: earnings, M&A, management changes, scandals, etc.
        # Default: False (opt-in for gradual rollout)
        self.event_extraction_enabled = os.getenv(
            'ICE_EVENT_EXTRACTION_ENABLED', 'false'
        ).lower() == 'true'

        # Confidence threshold for event extraction (0.0-1.0)
        # Higher threshold = fewer but more reliable events
        # Default: 0.8 (high confidence only)
        self.event_confidence_threshold = float(os.getenv(
            'ICE_EVENT_CONFIDENCE_THRESHOLD', '0.8'
        ))

        # Maximum events to extract per document
        # Prevents noise from event-dense documents
        # Default: 10 (typical documents have 1-3 events)
        self.max_events_per_doc = int(os.getenv(
            'ICE_MAX_EVENTS_PER_DOC', '10'
        ))

        # Event cache size (number of documents)
        # Content-based caching prevents redundant extraction
        # Default: 500 (smaller than relationships, events less common)
        self.event_cache_size = int(os.getenv(
            'ICE_EVENT_CACHE_SIZE', '500'
        ))

        # Validate critical configuration
        self._validate_critical_config()

    def _validate_critical_config(self):
        """Validate critical configuration that would prevent system operation"""
        if not self.openai_api_key:
            raise ValueError(
                "OPENAI_API_KEY is required for LightRAG operations. "
                "Please set the environment variable or provide it in configuration."
            )

        if not self.openai_api_key.startswith('sk-'):
            raise ValueError(
                "OPENAI_API_KEY appears to be invalid. "
                "OpenAI API keys should start with 'sk-'."
            )

        # Validate confidence configuration (Phase 2.8)
        validate_confidence_config()

    def is_api_available(self, service: str) -> bool:
        """Check if specific API service is configured"""
        return service in self.api_keys and bool(self.api_keys[service])

    def get_available_services(self) -> List[str]:
        """Get list of configured API services"""
        return list(self.api_keys.keys())

    def get_service_count(self) -> int:
        """Get count of configured API services"""
        return len(self.api_keys)

    def get_docling_status(self) -> Dict[str, Any]:
        """Get docling integration status for diagnostics"""
        return {
            'sec_filings': self.use_docling_sec,
            'email_attachments': self.use_docling_email,
            'url_pdfs': self.use_docling_urls,
            'user_uploads': self.use_docling_uploads,
            'archives': self.use_docling_archives,
            'news_pdfs': self.use_docling_news
        }

    def get_signal_store_status(self) -> Dict[str, Any]:
        """Get Signal Store integration status for diagnostics"""
        return {
            'enabled': self.use_signal_store,
            'db_path': self.signal_store_path,
            'timeout_ms': self.signal_store_timeout,
            'debug_mode': self.signal_store_debug
        }

    def get_temporal_config_status(self) -> Dict[str, Any]:
        """Get temporal configuration status for diagnostics"""
        return {
            'news_lookback_days': self.news_lookback_days,
            'financial_lookback_days': self.financial_lookback_days,
            'freshness_half_life_days': self.freshness_half_life_days,
            'stale_threshold_days': self.stale_threshold_days,
            'recency_ranking_weight': self.recency_ranking_weight
        }

    def ensure_working_dir(self):
        """Ensure working directory exists"""
        Path(self.working_dir).mkdir(parents=True, exist_ok=True)

    def get_status(self) -> Dict[str, Any]:
        """Get configuration status for diagnostics"""
        return {
            'openai_configured': bool(self.openai_api_key),
            'working_dir': self.working_dir,
            'working_dir_exists': Path(self.working_dir).exists(),
            'api_services_configured': len(self.api_keys),
            'available_services': list(self.api_keys.keys()),
            'batch_size': self.batch_size,
            'timeout': self.timeout,
            'log_level': self.log_level,
            'default_query_mode': self.default_query_mode
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary (without sensitive data)"""
        return {
            'working_dir': self.working_dir,
            'batch_size': self.batch_size,
            'timeout': self.timeout,
            'log_level': self.log_level,
            'api_services_configured': len(self.api_keys),
            'available_services': list(self.api_keys.keys()),
            'default_query_mode': self.default_query_mode,
            'query_timeout': self.query_timeout,
            'max_concurrent_queries': self.max_concurrent_queries,
            'cache_enabled': self.cache_enabled,
            'log_to_file': self.log_to_file,
            'log_file': self.log_file
        }

    @classmethod
    def from_env_file(cls, env_file: str = '.env') -> 'ICEConfig':
        """
        Load configuration from .env file

        Args:
            env_file: Path to .env file

        Returns:
            ICEConfig instance with loaded configuration
        """
        if Path(env_file).exists():
            from dotenv import load_dotenv
            load_dotenv(env_file)

        return cls()

    def __str__(self) -> str:
        """String representation of configuration (without sensitive data)"""
        status = self.get_status()
        return f"ICEConfig(services={status['api_services_configured']}, mode={self.default_query_mode})"


def setup_logging(config: Optional[ICEConfig] = None) -> logging.Logger:
    """
    Setup logging configuration for ICE system

    Args:
        config: ICEConfig instance (will create default if not provided)

    Returns:
        Configured logger instance
    """
    if config is None:
        config = ICEConfig()

    # Convert log level string to logging constant
    log_level = getattr(logging, config.log_level.upper(), logging.INFO)

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Clear any existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler if requested
    if config.log_to_file:
        try:
            file_handler = logging.FileHandler(config.log_file)
            file_handler.setLevel(log_level)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
        except Exception as e:
            logging.warning(f"Failed to setup file logging: {e}")

    # Get ICE-specific logger
    ice_logger = logging.getLogger('ice')
    ice_logger.info(f"Logging configured: level={config.log_level}, file={config.log_to_file}")

    return ice_logger


def create_default_config() -> ICEConfig:
    """
    Create default ICE configuration

    Returns:
        ICEConfig instance with default settings
    """
    try:
        config = ICEConfig()
        return config
    except ValueError as e:
        # If critical configuration is missing, provide helpful guidance
        print(f"❌ Configuration Error: {e}")
        print("\n🔧 Configuration Help:")
        print("Required environment variables:")
        print("  OPENAI_API_KEY=sk-your-openai-api-key")
        print("\nOptional environment variables:")
        print("  ICE_WORKING_DIR=./storage")
        print("  ICE_BATCH_SIZE=5")
        print("  ICE_TIMEOUT=30")
        print("  ICE_LOG_LEVEL=INFO")
        print("  NEWSAPI_ORG_API_KEY=your-newsapi-key")
        print("  ALPHA_VANTAGE_API_KEY=your-alphavantage-key")
        print("  FMP_API_KEY=your-fmp-key")
        print("  FINNHUB_API_KEY=your-finnhub-key")
        print("  POLYGON_API_KEY=your-polygon-key")
        raise


def validate_environment() -> Dict[str, Any]:
    """
    Validate environment configuration and return status

    Returns:
        Dictionary with validation results and recommendations
    """
    validation = {
        'timestamp': datetime.now().isoformat(),
        'critical_check': {},
        'optional_check': {},
        'recommendations': []
    }

    # Critical checks
    openai_key = os.getenv('OPENAI_API_KEY')
    validation['critical_check']['openai_api_key'] = {
        'configured': bool(openai_key),
        'valid_format': openai_key.startswith('sk-') if openai_key else False,
        'status': 'pass' if openai_key and openai_key.startswith('sk-') else 'fail'
    }

    # Optional API service checks
    optional_services = {
        'newsapi': 'NEWSAPI_ORG_API_KEY',
        'alpha_vantage': 'ALPHA_VANTAGE_API_KEY',
        'fmp': 'FMP_API_KEY',
        'finnhub': 'FINNHUB_API_KEY',
        'polygon': 'POLYGON_API_KEY'
    }

    configured_services = 0
    for service, env_var in optional_services.items():
        key = os.getenv(env_var)
        is_configured = bool(key)
        validation['optional_check'][service] = {
            'configured': is_configured,
            'env_var': env_var
        }
        if is_configured:
            configured_services += 1

    validation['optional_check']['summary'] = {
        'configured_services': configured_services,
        'total_services': len(optional_services),
        'coverage_percentage': (configured_services / len(optional_services)) * 100
    }

    # Generate recommendations
    if not validation['critical_check']['openai_api_key']['configured']:
        validation['recommendations'].append("Set OPENAI_API_KEY environment variable")

    if not validation['critical_check']['openai_api_key']['valid_format']:
        validation['recommendations'].append("Verify OPENAI_API_KEY starts with 'sk-'")

    if configured_services == 0:
        validation['recommendations'].append("Configure at least one data API service for comprehensive analysis")
    elif configured_services < 3:
        validation['recommendations'].append("Configure additional API services for better data coverage")

    # Working directory check
    working_dir = os.getenv('ICE_WORKING_DIR', './src/ice_lightrag/storage')
    working_dir_exists = Path(working_dir).exists()
    validation['optional_check']['working_directory'] = {
        'path': working_dir,
        'exists': working_dir_exists,
        'writable': os.access(Path(working_dir).parent, os.W_OK) if not working_dir_exists else os.access(working_dir, os.W_OK)
    }

    if not validation['optional_check']['working_directory']['writable']:
        validation['recommendations'].append("Ensure working directory is writable")

    # Overall status
    validation['overall_status'] = 'ready' if (
        validation['critical_check']['openai_api_key']['status'] == 'pass' and
        configured_services > 0
    ) else 'needs_configuration'

    return validation


def print_environment_status():
    """Print formatted environment status to console"""
    validation = validate_environment()

    print("🔧 ICE Environment Validation")
    print("=" * 50)

    # Critical requirements
    print("\n🚨 Critical Requirements:")
    openai_check = validation['critical_check']['openai_api_key']
    status_icon = "✅" if openai_check['status'] == 'pass' else "❌"
    print(f"  {status_icon} OpenAI API Key: {'Configured' if openai_check['configured'] else 'Missing'}")

    # Optional services
    print("\n📡 Data API Services:")
    summary = validation['optional_check']['summary']
    print(f"  📊 Coverage: {summary['configured_services']}/{summary['total_services']} ({summary['coverage_percentage']:.0f}%)")

    for service, details in validation['optional_check'].items():
        if service != 'summary' and service != 'working_directory':
            status_icon = "✅" if details['configured'] else "⚪"
            print(f"  {status_icon} {service.title()}: {'Configured' if details['configured'] else 'Not configured'}")

    # Working directory
    print("\n📂 Storage:")
    wd_check = validation['optional_check']['working_directory']
    wd_icon = "✅" if wd_check['exists'] and wd_check['writable'] else "⚠️"
    print(f"  {wd_icon} Working Directory: {wd_check['path']} {'(Ready)' if wd_check['writable'] else '(Check permissions)'}")

    # Recommendations
    if validation['recommendations']:
        print("\n💡 Recommendations:")
        for rec in validation['recommendations']:
            print(f"  • {rec}")

    # Overall status
    overall_icon = "🚀" if validation['overall_status'] == 'ready' else "⚠️"
    status_text = "Ready for operation" if validation['overall_status'] == 'ready' else "Needs configuration"
    print(f"\n{overall_icon} Overall Status: {status_text}")


# Convenience functions
def load_config(env_file: Optional[str] = None) -> ICEConfig:
    """
    Load ICE configuration with optional .env file

    Args:
        env_file: Path to .env file (optional)

    Returns:
        ICEConfig instance
    """
    if env_file:
        return ICEConfig.from_env_file(env_file)
    else:
        return create_default_config()


def setup_ice_environment(config: Optional[ICEConfig] = None) -> tuple[ICEConfig, logging.Logger]:
    """
    Setup complete ICE environment with configuration and logging

    Args:
        config: Optional pre-configured ICEConfig instance

    Returns:
        Tuple of (config, logger)
    """
    if config is None:
        config = create_default_config()

    logger = setup_logging(config)
    config.ensure_working_dir()

    logger.info("ICE environment setup completed")
    logger.info(f"Configuration: {config}")

    return config, logger


if __name__ == "__main__":
    # Demo configuration and validation
    print("🚀 ICE Configuration Demo")

    try:
        # Print environment status
        print_environment_status()

        print("\n" + "=" * 50)

        # Create configuration
        config = create_default_config()
        print(f"\n✅ Configuration created: {config}")

        # Setup logging
        logger = setup_logging(config)
        logger.info("Configuration demo completed successfully")

        # Show configuration details
        print(f"\n📋 Configuration Details:")
        config_dict = config.to_dict()
        for key, value in config_dict.items():
            print(f"  {key}: {value}")

    except Exception as e:
        print(f"\n❌ Configuration demo failed: {e}")
        print("\nPlease check your environment variables and try again.")