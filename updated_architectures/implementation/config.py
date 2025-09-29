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

    def is_api_available(self, service: str) -> bool:
        """Check if specific API service is configured"""
        return service in self.api_keys and bool(self.api_keys[service])

    def get_available_services(self) -> List[str]:
        """Get list of configured API services"""
        return list(self.api_keys.keys())

    def get_service_count(self) -> int:
        """Get count of configured API services"""
        return len(self.api_keys)

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