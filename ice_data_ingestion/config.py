# /Users/royyeo/Library/CloudStorage/OneDrive-NationalUniversityofSingapore/Capstone Project/ice_data_ingestion/config.py
# Configuration management for ICE news API integration
# Handles API key management, client initialization, and configuration settings
# RELEVANT FILES: __init__.py, news_apis.py, alpha_vantage_client.py, fmp_client.py, marketaux_client.py

"""
ICE News API Configuration Manager

This module handles configuration and initialization for the ICE news data ingestion system.
It provides secure API key management, client factory methods, and configuration validation.

Key Features:
- Environment variable-based API key management
- Automatic client initialization with sensible defaults
- Configuration validation and error handling
- Support for multiple deployment environments (dev, staging, prod)
- Fallback configuration for missing API keys

Supported Environment Variables:
- ALPHA_VANTAGE_API_KEY: Alpha Vantage API key (recommended primary)
- FMP_API_KEY: Financial Modeling Prep API key
- MARKETAUX_API_TOKEN: MarketAux API token
- POLYGON_API_KEY: Polygon.io API key
- NEWSAPI_ORG_KEY: NewsAPI.org API key
- BENZINGA_API_TOKEN: Benzinga API token
- FINNHUB_API_TOKEN: Finnhub API token (future)

Configuration Priority:
1. Environment variables
2. Configuration file (ice_config.json)
3. Default/demo configuration

Usage:
    from ice_data_ingestion.config import ICEConfig
    
    config = ICEConfig()
    manager = config.create_news_manager()
    news = manager.get_financial_news("NVDA", limit=10)
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass, field

from .news_apis import NewsAPIManager, NewsCache, RateLimiter, NewsAPIProvider
from .alpha_vantage_client import AlphaVantageClient
from .fmp_client import FMPClient
from .marketaux_client import MarketAuxClient
from .newsapi_org_client import NewsAPIClient_Org
from .benzinga_client import BenzingaClient
from .polygon_client import PolygonClient

logger = logging.getLogger(__name__)

@dataclass
class APIKeyConfig:
    """Configuration for individual API keys"""
    key: Optional[str] = None
    enabled: bool = True
    is_primary: bool = False
    rate_limit_per_minute: int = 60
    cache_ttl_hours: int = 6
    priority: int = 10  # Lower numbers = higher priority
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ICENewsConfig:
    """Complete configuration for ICE news system"""
    alpha_vantage: APIKeyConfig = field(default_factory=lambda: APIKeyConfig(priority=1, rate_limit_per_minute=5))
    fmp: APIKeyConfig = field(default_factory=lambda: APIKeyConfig(priority=2, rate_limit_per_minute=10))
    marketaux: APIKeyConfig = field(default_factory=lambda: APIKeyConfig(priority=3, rate_limit_per_minute=30))
    polygon: APIKeyConfig = field(default_factory=lambda: APIKeyConfig(priority=4, rate_limit_per_minute=5, enabled=False))
    benzinga: APIKeyConfig = field(default_factory=lambda: APIKeyConfig(priority=5, rate_limit_per_minute=10, enabled=False))
    newsapi_org: APIKeyConfig = field(default_factory=lambda: APIKeyConfig(priority=6, rate_limit_per_minute=60, enabled=False))
    finnhub: APIKeyConfig = field(default_factory=lambda: APIKeyConfig(priority=7, enabled=False))
    
    # Global settings
    cache_directory: str = "storage/cache/news_cache"
    default_cache_ttl: int = 6
    max_articles_per_request: int = 100
    enable_fallback: bool = True
    log_level: str = "INFO"

class ICEConfig:
    """Main configuration manager for ICE news system"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or "ice_config.json"
        self.config = self._load_configuration()
        self._setup_logging()
    
    def _load_configuration(self) -> ICENewsConfig:
        """Load configuration from environment variables and config file"""
        # Start with defaults
        config = ICENewsConfig()
        
        # Load from config file if it exists
        if Path(self.config_file).exists():
            try:
                with open(self.config_file, 'r') as f:
                    file_config = json.load(f)
                config = self._merge_config_from_dict(config, file_config)
                logger.info(f"Loaded configuration from {self.config_file}")
            except Exception as e:
                logger.warning(f"Failed to load config file {self.config_file}: {e}")
        
        # Override with environment variables
        config = self._load_from_environment(config)
        
        return config
    
    def _merge_config_from_dict(self, config: ICENewsConfig, data: Dict[str, Any]) -> ICENewsConfig:
        """Merge configuration from dictionary"""
        # Update API configurations
        if 'alpha_vantage' in data:
            av_config = data['alpha_vantage']
            config.alpha_vantage.key = av_config.get('key', config.alpha_vantage.key)
            config.alpha_vantage.enabled = av_config.get('enabled', config.alpha_vantage.enabled)
            config.alpha_vantage.is_primary = av_config.get('is_primary', config.alpha_vantage.is_primary)
        
        if 'fmp' in data:
            fmp_config = data['fmp']
            config.fmp.key = fmp_config.get('key', config.fmp.key)
            config.fmp.enabled = fmp_config.get('enabled', config.fmp.enabled)
            config.fmp.is_primary = fmp_config.get('is_primary', config.fmp.is_primary)
        
        if 'marketaux' in data:
            ma_config = data['marketaux']
            config.marketaux.key = ma_config.get('key', config.marketaux.key)
            config.marketaux.enabled = ma_config.get('enabled', config.marketaux.enabled)
            config.marketaux.is_primary = ma_config.get('is_primary', config.marketaux.is_primary)
        
        # Update global settings
        if 'cache_directory' in data:
            config.cache_directory = data['cache_directory']
        if 'max_articles_per_request' in data:
            config.max_articles_per_request = data['max_articles_per_request']
        if 'enable_fallback' in data:
            config.enable_fallback = data['enable_fallback']
        if 'log_level' in data:
            config.log_level = data['log_level']
        
        return config
    
    def _load_from_environment(self, config: ICENewsConfig) -> ICENewsConfig:
        """Load configuration from environment variables"""
        # Alpha Vantage
        if os.getenv('ALPHA_VANTAGE_API_KEY'):
            config.alpha_vantage.key = os.getenv('ALPHA_VANTAGE_API_KEY')
            config.alpha_vantage.enabled = True
            config.alpha_vantage.is_primary = True  # Alpha Vantage is recommended primary
        
        # Financial Modeling Prep  
        if os.getenv('FMP_API_KEY'):
            config.fmp.key = os.getenv('FMP_API_KEY')
            config.fmp.enabled = True
        
        # MarketAux
        if os.getenv('MARKETAUX_API_TOKEN'):
            config.marketaux.key = os.getenv('MARKETAUX_API_TOKEN')
            config.marketaux.enabled = True
        
        # Polygon.io
        if os.getenv('POLYGON_API_KEY'):
            config.polygon.key = os.getenv('POLYGON_API_KEY')
            config.polygon.enabled = True
        
        # Benzinga
        if os.getenv('BENZINGA_API_TOKEN'):
            config.benzinga.key = os.getenv('BENZINGA_API_TOKEN')
            config.benzinga.enabled = True
        
        # NewsAPI.org
        if os.getenv('NEWSAPI_ORG_KEY'):
            config.newsapi_org.key = os.getenv('NEWSAPI_ORG_KEY')
            config.newsapi_org.enabled = True
        
        # Global settings from environment
        if os.getenv('ICE_CACHE_DIR'):
            config.cache_directory = os.getenv('ICE_CACHE_DIR')
        
        if os.getenv('ICE_LOG_LEVEL'):
            config.log_level = os.getenv('ICE_LOG_LEVEL')
        
        return config
    
    def _setup_logging(self):
        """Setup logging based on configuration"""
        log_level = getattr(logging, self.config.log_level.upper(), logging.INFO)
        
        # Configure ice_data_ingestion logger
        ice_logger = logging.getLogger('ice_data_ingestion')
        ice_logger.setLevel(log_level)
        
        # Create console handler if none exists
        if not ice_logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            ice_logger.addHandler(handler)
    
    def create_news_manager(self) -> NewsAPIManager:
        """Create and configure NewsAPIManager with available clients"""
        # Create shared cache
        cache = NewsCache(cache_dir=self.config.cache_directory, ttl_hours=self.config.default_cache_ttl)
        
        # Create manager
        manager = NewsAPIManager(cache=cache)
        
        # Collect enabled clients with their priorities
        enabled_clients = []
        
        # Alpha Vantage
        if self.config.alpha_vantage.enabled and self.config.alpha_vantage.key:
            try:
                rate_limiter = RateLimiter(requests_per_minute=self.config.alpha_vantage.rate_limit_per_minute)
                client = AlphaVantageClient(
                    api_key=self.config.alpha_vantage.key,
                    rate_limiter=rate_limiter,
                    cache=cache
                )
                enabled_clients.append((self.config.alpha_vantage.priority, client, self.config.alpha_vantage.is_primary))
                logger.info("Alpha Vantage client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Alpha Vantage client: {e}")
        
        # Financial Modeling Prep
        if self.config.fmp.enabled and self.config.fmp.key:
            try:
                rate_limiter = RateLimiter(requests_per_minute=self.config.fmp.rate_limit_per_minute)
                client = FMPClient(
                    api_key=self.config.fmp.key,
                    rate_limiter=rate_limiter,
                    cache=cache
                )
                enabled_clients.append((self.config.fmp.priority, client, self.config.fmp.is_primary))
                logger.info("Financial Modeling Prep client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize FMP client: {e}")
        
        # MarketAux
        if self.config.marketaux.enabled and self.config.marketaux.key:
            try:
                rate_limiter = RateLimiter(requests_per_minute=self.config.marketaux.rate_limit_per_minute)
                client = MarketAuxClient(
                    api_token=self.config.marketaux.key,
                    rate_limiter=rate_limiter,
                    cache=cache
                )
                enabled_clients.append((self.config.marketaux.priority, client, self.config.marketaux.is_primary))
                logger.info("MarketAux client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize MarketAux client: {e}")
        
        # Polygon.io
        if self.config.polygon.enabled and self.config.polygon.key:
            try:
                rate_limiter = RateLimiter(requests_per_minute=self.config.polygon.rate_limit_per_minute)
                client = PolygonClient(
                    api_key=self.config.polygon.key,
                    rate_limiter=rate_limiter,
                    cache=cache
                )
                enabled_clients.append((self.config.polygon.priority, client, self.config.polygon.is_primary))
                logger.info("Polygon.io client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Polygon.io client: {e}")
        
        # Benzinga
        if self.config.benzinga.enabled and self.config.benzinga.key:
            try:
                rate_limiter = RateLimiter(requests_per_minute=self.config.benzinga.rate_limit_per_minute)
                client = BenzingaClient(
                    api_token=self.config.benzinga.key,
                    rate_limiter=rate_limiter,
                    cache=cache
                )
                enabled_clients.append((self.config.benzinga.priority, client, self.config.benzinga.is_primary))
                logger.info("Benzinga client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Benzinga client: {e}")
        
        # NewsAPI.org
        if self.config.newsapi_org.enabled and self.config.newsapi_org.key:
            try:
                rate_limiter = RateLimiter(requests_per_minute=self.config.newsapi_org.rate_limit_per_minute)
                client = NewsAPIClient_Org(
                    api_key=self.config.newsapi_org.key,
                    rate_limiter=rate_limiter,
                    cache=cache
                )
                enabled_clients.append((self.config.newsapi_org.priority, client, self.config.newsapi_org.is_primary))
                logger.info("NewsAPI.org client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize NewsAPI.org client: {e}")
        
        # Register clients in priority order
        enabled_clients.sort(key=lambda x: x[0])  # Sort by priority
        primary_set = False
        
        for priority, client, is_primary in enabled_clients:
            should_be_primary = is_primary or (not primary_set and priority == enabled_clients[0][0])
            manager.register_client(client, set_as_primary=should_be_primary)
            if should_be_primary:
                primary_set = True
        
        if not enabled_clients:
            logger.warning("No news API clients were successfully initialized. Check your API keys.")
        else:
            logger.info(f"NewsAPIManager initialized with {len(enabled_clients)} clients")
        
        return manager
    
    def validate_configuration(self) -> Dict[str, Any]:
        """Validate current configuration and return status"""
        validation = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'enabled_apis': [],
            'primary_api': None
        }
        
        enabled_count = 0
        
        # Check Alpha Vantage
        if self.config.alpha_vantage.enabled:
            if not self.config.alpha_vantage.key:
                validation['errors'].append("Alpha Vantage enabled but no API key provided")
                validation['valid'] = False
            else:
                validation['enabled_apis'].append('alpha_vantage')
                enabled_count += 1
                if self.config.alpha_vantage.is_primary:
                    validation['primary_api'] = 'alpha_vantage'
        
        # Check FMP
        if self.config.fmp.enabled:
            if not self.config.fmp.key:
                validation['errors'].append("FMP enabled but no API key provided")
                validation['valid'] = False
            else:
                validation['enabled_apis'].append('fmp')
                enabled_count += 1
                if self.config.fmp.is_primary:
                    validation['primary_api'] = 'fmp'
        
        # Check MarketAux
        if self.config.marketaux.enabled:
            if not self.config.marketaux.key:
                validation['errors'].append("MarketAux enabled but no API key provided")
                validation['valid'] = False
            else:
                validation['enabled_apis'].append('marketaux')
                enabled_count += 1
                if self.config.marketaux.is_primary:
                    validation['primary_api'] = 'marketaux'
        
        # Check if at least one API is enabled
        if enabled_count == 0:
            validation['errors'].append("No news APIs are enabled or configured")
            validation['valid'] = False
        
        # Set default primary if none specified
        if not validation['primary_api'] and validation['enabled_apis']:
            validation['primary_api'] = validation['enabled_apis'][0]
            validation['warnings'].append(f"No primary API specified, using {validation['primary_api']} as default")
        
        # Check cache directory
        cache_path = Path(self.config.cache_directory)
        try:
            cache_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            validation['warnings'].append(f"Cannot create cache directory {cache_path}: {e}")
        
        return validation
    
    def save_configuration(self):
        """Save current configuration to file"""
        config_data = {
            'alpha_vantage': {
                'key': self.config.alpha_vantage.key,
                'enabled': self.config.alpha_vantage.enabled,
                'is_primary': self.config.alpha_vantage.is_primary
            },
            'fmp': {
                'key': self.config.fmp.key,
                'enabled': self.config.fmp.enabled,
                'is_primary': self.config.fmp.is_primary
            },
            'marketaux': {
                'key': self.config.marketaux.key,
                'enabled': self.config.marketaux.enabled,
                'is_primary': self.config.marketaux.is_primary
            },
            'cache_directory': self.config.cache_directory,
            'max_articles_per_request': self.config.max_articles_per_request,
            'enable_fallback': self.config.enable_fallback,
            'log_level': self.config.log_level
        }
        
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
            logger.info(f"Configuration saved to {self.config_file}")
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
    
    def get_api_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all configured APIs"""
        status = {}
        
        # Check each API configuration
        apis = [
            ('alpha_vantage', self.config.alpha_vantage),
            ('fmp', self.config.fmp),
            ('marketaux', self.config.marketaux)
        ]
        
        for name, config in apis:
            status[name] = {
                'enabled': config.enabled,
                'has_key': bool(config.key),
                'is_primary': config.is_primary,
                'priority': config.priority,
                'rate_limit': config.rate_limit_per_minute
            }
        
        return status
    
    def create_demo_config(self) -> 'ICEConfig':
        """Create a demo configuration for testing without API keys"""
        logger.warning("Creating demo configuration - limited functionality without API keys")
        
        # Create minimal working configuration
        demo_config = ICENewsConfig()
        demo_config.alpha_vantage.enabled = False
        demo_config.fmp.enabled = False
        demo_config.marketaux.enabled = False
        
        self.config = demo_config
        return self

def get_default_config() -> ICEConfig:
    """Get default ICE configuration"""
    return ICEConfig()

def setup_api_keys_interactive():
    """Interactive setup for API keys (for CLI usage)"""
    print("ICE News API Configuration Setup")
    print("=" * 40)
    
    config = ICEConfig()
    
    # Alpha Vantage setup
    print("\n1. Alpha Vantage (Recommended - 500 req/day free)")
    av_key = input("Enter Alpha Vantage API key (or press Enter to skip): ").strip()
    if av_key:
        config.config.alpha_vantage.key = av_key
        config.config.alpha_vantage.enabled = True
        config.config.alpha_vantage.is_primary = True
        print("✓ Alpha Vantage configured as primary provider")
    
    # FMP setup
    print("\n2. Financial Modeling Prep (250 req/day free)")
    fmp_key = input("Enter FMP API key (or press Enter to skip): ").strip()
    if fmp_key:
        config.config.fmp.key = fmp_key
        config.config.fmp.enabled = True
        if not av_key:  # Set as primary if Alpha Vantage not configured
            config.config.fmp.is_primary = True
        print("✓ FMP configured")
    
    # MarketAux setup
    print("\n3. MarketAux (Free tier available)")
    ma_token = input("Enter MarketAux API token (or press Enter to skip): ").strip()
    if ma_token:
        config.config.marketaux.key = ma_token
        config.config.marketaux.enabled = True
        if not av_key and not fmp_key:  # Set as primary if others not configured
            config.config.marketaux.is_primary = True
        print("✓ MarketAux configured")
    
    # Save configuration
    save_config = input("\nSave configuration to ice_config.json? (y/N): ").strip().lower()
    if save_config == 'y':
        config.save_configuration()
        print("✓ Configuration saved")
    
    # Validate
    validation = config.validate_configuration()
    if validation['valid']:
        print(f"\n✓ Configuration valid. Enabled APIs: {', '.join(validation['enabled_apis'])}")
        if validation['primary_api']:
            print(f"✓ Primary API: {validation['primary_api']}")
    else:
        print(f"\n✗ Configuration errors: {', '.join(validation['errors'])}")
    
    return config