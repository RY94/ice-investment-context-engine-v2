# setup/production_config.py
# Production configuration management and deployment utilities for ICE system
# Provides environment configuration, validation, and deployment patterns
# RELEVANT FILES: CLAUDE.md, check/health_checks.py, src/ice_lightrag/ice_rag.py

import os
import json
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any
from pathlib import Path


@dataclass
class ICEConfig:
    """Production configuration for ICE system"""
    
    # API Configuration
    openai_api_key: str
    openai_model: str = "gpt-4"
    openai_timeout: int = 30
    
    # Performance Tuning
    max_concurrent_queries: int = 5
    query_timeout_seconds: int = 120
    cache_ttl_hours: int = 24
    
    # Storage Configuration  
    working_dir: str = "./src/ice_lightrag/storage"
    backup_enabled: bool = True
    backup_interval_hours: int = 6
    
    # Security
    enable_query_logging: bool = True
    sanitize_logs: bool = True
    rate_limit_per_minute: int = 100
    
    # Local LLM Configuration
    local_llm_enabled: bool = False
    local_llm_fallback: bool = True
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3:8b"
    
    @classmethod
    def from_environment(cls) -> 'ICEConfig':
        """Create configuration from environment variables"""
        return cls(
            openai_api_key=os.getenv('OPENAI_API_KEY', ''),
            openai_model=os.getenv('ICE_MODEL', 'gpt-4'),
            openai_timeout=int(os.getenv('ICE_TIMEOUT', '30')),
            max_concurrent_queries=int(os.getenv('ICE_MAX_QUERIES', '5')),
            query_timeout_seconds=int(os.getenv('ICE_QUERY_TIMEOUT', '120')),
            cache_ttl_hours=int(os.getenv('ICE_CACHE_TTL', '24')),
            working_dir=os.getenv('ICE_STORAGE_DIR', './src/ice_lightrag/storage'),
            backup_enabled=os.getenv('ICE_BACKUP_ENABLED', 'true').lower() == 'true',
            backup_interval_hours=int(os.getenv('ICE_BACKUP_INTERVAL', '6')),
            enable_query_logging=os.getenv('ICE_ENABLE_LOGGING', 'true').lower() == 'true',
            sanitize_logs=os.getenv('ICE_SANITIZE_LOGS', 'true').lower() == 'true',
            rate_limit_per_minute=int(os.getenv('ICE_RATE_LIMIT', '100')),
            local_llm_enabled=os.getenv('ICE_LOCAL_LLM', 'false').lower() == 'true',
            local_llm_fallback=os.getenv('ICE_LOCAL_LLM_FALLBACK', 'true').lower() == 'true',
            ollama_base_url=os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434'),
            ollama_model=os.getenv('OLLAMA_MODEL', 'llama3:8b')
        )
    
    @classmethod
    def from_file(cls, config_path: str) -> 'ICEConfig':
        """Load configuration from JSON file"""
        try:
            with open(config_path, 'r') as f:
                config_data = json.load(f)
            return cls(**config_data)
        except FileNotFoundError:
            print(f"⚠️  Config file {config_path} not found, using defaults")
            return cls.from_environment()
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON in config file {config_path}: {e}")
            return cls.from_environment()
    
    def save_to_file(self, config_path: str) -> bool:
        """Save configuration to JSON file"""
        try:
            config_dict = asdict(self)
            # Don't save sensitive data
            config_dict.pop('openai_api_key', None)
            
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            with open(config_path, 'w') as f:
                json.dump(config_dict, f, indent=2)
            print(f"✅ Configuration saved to {config_path}")
            return True
        except Exception as e:
            print(f"❌ Failed to save configuration: {e}")
            return False
    
    def validate(self) -> None:
        """Validate configuration settings"""
        errors = []
        
        # Required settings
        if not self.openai_api_key:
            errors.append("OPENAI_API_KEY must be provided")
        
        # Directory validation
        working_dir_parent = os.path.dirname(self.working_dir)
        if working_dir_parent and not os.path.exists(working_dir_parent):
            errors.append(f"Storage directory parent does not exist: {working_dir_parent}")
        
        # Numeric validations
        if self.max_concurrent_queries <= 0:
            errors.append("max_concurrent_queries must be positive")
        
        if self.query_timeout_seconds <= 0:
            errors.append("query_timeout_seconds must be positive")
        
        if self.cache_ttl_hours <= 0:
            errors.append("cache_ttl_hours must be positive")
        
        if self.rate_limit_per_minute <= 0:
            errors.append("rate_limit_per_minute must be positive")
        
        # OpenAI API key format check (basic)
        if self.openai_api_key and not self.openai_api_key.startswith('sk-'):
            errors.append("OpenAI API key should start with 'sk-'")
        
        if errors:
            error_msg = "Configuration validation failed:\n" + "\n".join(f"  • {e}" for e in errors)
            raise ValueError(error_msg)
    
    def get_environment_setup(self) -> Dict[str, str]:
        """Get environment variables for this configuration"""
        return {
            'OPENAI_API_KEY': self.openai_api_key,
            'ICE_MODEL': self.openai_model,
            'ICE_TIMEOUT': str(self.openai_timeout),
            'ICE_MAX_QUERIES': str(self.max_concurrent_queries),
            'ICE_QUERY_TIMEOUT': str(self.query_timeout_seconds),
            'ICE_CACHE_TTL': str(self.cache_ttl_hours),
            'ICE_STORAGE_DIR': self.working_dir,
            'ICE_BACKUP_ENABLED': 'true' if self.backup_enabled else 'false',
            'ICE_BACKUP_INTERVAL': str(self.backup_interval_hours),
            'ICE_ENABLE_LOGGING': 'true' if self.enable_query_logging else 'false',
            'ICE_SANITIZE_LOGS': 'true' if self.sanitize_logs else 'false',
            'ICE_RATE_LIMIT': str(self.rate_limit_per_minute),
            'ICE_LOCAL_LLM': 'true' if self.local_llm_enabled else 'false',
            'ICE_LOCAL_LLM_FALLBACK': 'true' if self.local_llm_fallback else 'false',
            'OLLAMA_BASE_URL': self.ollama_base_url,
            'OLLAMA_MODEL': self.ollama_model
        }


class ICEDeployment:
    """Production deployment utilities for ICE system"""
    
    def __init__(self, config: ICEConfig):
        self.config = config
    
    def setup_production_environment(self) -> bool:
        """Setup production environment with proper directories and permissions"""
        try:
            # Create necessary directories
            os.makedirs(self.config.working_dir, exist_ok=True)
            os.makedirs("logs", exist_ok=True)
            os.makedirs("backups", exist_ok=True)
            
            # Set up logging configuration
            self._setup_logging()
            
            # Set up backup system if enabled
            if self.config.backup_enabled:
                self._setup_backup_system()
            
            print("✅ Production environment setup completed")
            return True
            
        except Exception as e:
            print(f"❌ Failed to setup production environment: {e}")
            return False
    
    def _setup_logging(self):
        """Configure production logging"""
        import logging
        
        log_level = logging.INFO if self.config.enable_query_logging else logging.WARNING
        
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/ice_system.log'),
                logging.StreamHandler()
            ]
        )
        
        # Create sanitized logger if needed
        if self.config.sanitize_logs:
            # Add log sanitization logic here
            pass
        
        print("📝 Logging configured")
    
    def _setup_backup_system(self):
        """Setup automated backup system"""
        backup_script = f"""#!/bin/bash
# ICE System Backup Script
# Generated automatically by production_config.py

BACKUP_DIR="backups"
STORAGE_DIR="{self.config.working_dir}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Create backup
tar -czf "$BACKUP_DIR/ice_backup_$TIMESTAMP.tar.gz" "$STORAGE_DIR"

# Keep only last 10 backups
ls -t "$BACKUP_DIR"/ice_backup_*.tar.gz | tail -n +11 | xargs -r rm

echo "Backup completed: ice_backup_$TIMESTAMP.tar.gz"
"""
        
        with open("scripts/backup.sh", "w") as f:
            f.write(backup_script)
        
        os.chmod("scripts/backup.sh", 0o755)
        print("💾 Backup system configured")
    
    def generate_systemd_service(self) -> str:
        """Generate systemd service file for ICE system"""
        service_content = f"""[Unit]
Description=ICE Investment Context Engine
After=network.target

[Service]
Type=simple
User=ice
Group=ice
WorkingDirectory=/opt/ice
Environment=OPENAI_API_KEY={self.config.openai_api_key}
Environment=ICE_STORAGE_DIR={self.config.working_dir}
Environment=ICE_MAX_QUERIES={self.config.max_concurrent_queries}
ExecStart=/opt/ice/venv/bin/python -m streamlit run UI/ice_ui_v17.py --server.port 8501
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
"""
        
        service_file = "ice-system.service"
        with open(service_file, "w") as f:
            f.write(service_content)
        
        print(f"🔧 SystemD service file generated: {service_file}")
        print("Install with: sudo cp ice-system.service /etc/systemd/system/")
        print("Enable with: sudo systemctl enable ice-system")
        
        return service_content
    
    def generate_docker_compose(self) -> str:
        """Generate Docker Compose configuration"""
        compose_content = f"""version: '3.8'

services:
  ice-system:
    build: .
    ports:
      - "8501:8501"
    environment:
      - OPENAI_API_KEY={self.config.openai_api_key}
      - ICE_STORAGE_DIR=/app/storage
      - ICE_MAX_QUERIES={self.config.max_concurrent_queries}
      - ICE_ENABLE_LOGGING=true
    volumes:
      - ./storage:/app/storage
      - ./logs:/app/logs
      - ./backups:/app/backups
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8501/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  ice-monitor:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
    depends_on:
      - ice-system
"""
        
        with open("docker-compose.yml", "w") as f:
            f.write(compose_content)
        
        print("🐳 Docker Compose file generated: docker-compose.yml")
        return compose_content


def main():
    """Configuration management CLI"""
    import argparse
    
    parser = argparse.ArgumentParser(description='ICE Production Configuration')
    parser.add_argument('command', choices=['validate', 'generate', 'setup', 'export'],
                       help='Configuration command')
    parser.add_argument('--config', default='config/production.json',
                       help='Configuration file path')
    parser.add_argument('--env-file', default='.env.production',
                       help='Environment file path')
    
    args = parser.parse_args()
    
    # Load configuration
    if os.path.exists(args.config):
        config = ICEConfig.from_file(args.config)
    else:
        config = ICEConfig.from_environment()
    
    if args.command == 'validate':
        try:
            config.validate()
            print("✅ Configuration is valid")
        except ValueError as e:
            print(f"❌ {e}")
    
    elif args.command == 'generate':
        config.save_to_file(args.config)
        
        deployment = ICEDeployment(config)
        deployment.generate_systemd_service()
        deployment.generate_docker_compose()
    
    elif args.command == 'setup':
        deployment = ICEDeployment(config)
        deployment.setup_production_environment()
    
    elif args.command == 'export':
        env_vars = config.get_environment_setup()
        with open(args.env_file, 'w') as f:
            for key, value in env_vars.items():
                if key != 'OPENAI_API_KEY':  # Don't export sensitive data
                    f.write(f'{key}={value}\n')
        print(f"📄 Environment variables exported to {args.env_file}")


if __name__ == "__main__":
    main()