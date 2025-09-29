# ice_data_ingestion/secure_config.py
"""
Secure Configuration Management for ICE Data Ingestion
Handles API key encryption, rotation, and secure access with audit logging
Implements best practices for credential management in financial systems
Relevant files: config.py, mcp_client_manager.py, financial_news_connectors.py
"""

import os
import json
import hashlib
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, List
from dataclasses import dataclass, asdict
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)


@dataclass
class APIKeyMetadata:
    """Metadata for API key management"""
    service: str
    created_at: datetime
    last_rotated: datetime
    last_used: Optional[datetime] = None
    usage_count: int = 0
    rate_limit_hits: int = 0
    is_active: bool = True
    expires_at: Optional[datetime] = None
    tier: str = "free"  # free, premium, enterprise


class SecureConfigManager:
    """
    Secure configuration management with encryption and audit logging

    Features:
    - Encryption at rest for API keys
    - Key rotation tracking
    - Usage analytics
    - Audit logging
    - Environment-based configuration
    """

    def __init__(self, config_dir: Optional[str] = None):
        """Initialize secure configuration manager"""
        self.config_dir = Path(config_dir or os.path.expanduser("~/.ice/config"))
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # Secure files
        self.keys_file = self.config_dir / "encrypted_keys.json"
        self.metadata_file = self.config_dir / "key_metadata.json"
        self.audit_log = self.config_dir / "audit.log"

        # Initialize encryption
        self.cipher = self._initialize_encryption()

        # Load existing configuration
        self.encrypted_keys: Dict[str, str] = {}
        self.key_metadata: Dict[str, APIKeyMetadata] = {}
        self._load_configuration()

        # Service configurations with fallback patterns
        self.service_configs = {
            "OPENAI": {
                "env_vars": ["OPENAI_API_KEY"],
                "required": True,
                "tier": "paid"
            },
            "EXA": {
                "env_vars": ["EXA_API_KEY"],
                "required": False,
                "tier": "freemium"
            },
            "FINNHUB": {
                "env_vars": ["FINNHUB_API_KEY", "FINNHUB_TOKEN"],
                "required": False,
                "tier": "free"
            },
            "MARKETAUX": {
                "env_vars": ["MARKETAUX_API_KEY", "MARKETAUX_API_TOKEN", "MARKETAUX_TOKEN"],
                "required": False,
                "tier": "free"
            },
            "POLYGON": {
                "env_vars": ["POLYGON_API_KEY", "POLYGON_IO_API_KEY"],
                "required": False,
                "tier": "free"
            },
            "OPENBB": {
                "env_vars": ["OPENBB_API_KEY", "OPENBB_TOKEN"],
                "required": False,
                "tier": "freemium"
            },
            "BENZINGA": {
                "env_vars": ["BENZINGA_API_KEY", "BENZINGA_API_TOKEN", "BENZINGA_TOKEN"],
                "required": False,
                "tier": "paid"
            },
            "NEWSAPI": {
                "env_vars": ["NEWSAPI_API_KEY", "NEWS_API_KEY", "NEWSAPI_ORG_API_KEY"],
                "required": False,
                "tier": "free"
            },
            "ALPHAVANTAGE": {
                "env_vars": ["ALPHAVANTAGE_API_KEY", "ALPHA_VANTAGE_API_KEY"],
                "required": False,
                "tier": "free"
            }
        }

    def _initialize_encryption(self) -> Fernet:
        """Initialize or load encryption key"""
        key_file = self.config_dir / ".encryption_key"

        if key_file.exists():
            # Load existing key
            with open(key_file, 'rb') as f:
                key = f.read()
        else:
            # Generate new key from environment or random
            master_key = os.getenv('ICE_MASTER_KEY', '').encode()

            if master_key:
                # Derive key from master password
                kdf = PBKDF2HMAC(
                    algorithm=hashes.SHA256(),
                    length=32,
                    salt=b'ice-data-ingestion-2024',
                    iterations=100000,
                )
                key = base64.urlsafe_b64encode(kdf.derive(master_key))
            else:
                # Generate random key
                key = Fernet.generate_key()
                logger.warning("Generated random encryption key. Set ICE_MASTER_KEY for consistent encryption.")

            # Save key securely (600 permissions)
            with open(key_file, 'wb') as f:
                f.write(key)
            os.chmod(key_file, 0o600)

        return Fernet(key)

    def _load_configuration(self) -> None:
        """Load encrypted keys and metadata"""
        # Load encrypted keys
        if self.keys_file.exists():
            try:
                with open(self.keys_file, 'r') as f:
                    self.encrypted_keys = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load encrypted keys: {e}")
                self.encrypted_keys = {}

        # Load metadata
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r') as f:
                    metadata_dict = json.load(f)
                    self.key_metadata = {
                        service: APIKeyMetadata(
                            service=meta['service'],
                            created_at=datetime.fromisoformat(meta['created_at']),
                            last_rotated=datetime.fromisoformat(meta['last_rotated']),
                            last_used=datetime.fromisoformat(meta['last_used']) if meta.get('last_used') else None,
                            usage_count=meta.get('usage_count', 0),
                            rate_limit_hits=meta.get('rate_limit_hits', 0),
                            is_active=meta.get('is_active', True),
                            expires_at=datetime.fromisoformat(meta['expires_at']) if meta.get('expires_at') else None,
                            tier=meta.get('tier', 'free')
                        )
                        for service, meta in metadata_dict.items()
                    }
            except Exception as e:
                logger.error(f"Failed to load metadata: {e}")
                self.key_metadata = {}

    def _save_configuration(self) -> None:
        """Save encrypted keys and metadata"""
        # Save encrypted keys
        with open(self.keys_file, 'w') as f:
            json.dump(self.encrypted_keys, f, indent=2)
        os.chmod(self.keys_file, 0o600)

        # Save metadata
        metadata_dict = {
            service: {
                'service': meta.service,
                'created_at': meta.created_at.isoformat(),
                'last_rotated': meta.last_rotated.isoformat(),
                'last_used': meta.last_used.isoformat() if meta.last_used else None,
                'usage_count': meta.usage_count,
                'rate_limit_hits': meta.rate_limit_hits,
                'is_active': meta.is_active,
                'expires_at': meta.expires_at.isoformat() if meta.expires_at else None,
                'tier': meta.tier
            }
            for service, meta in self.key_metadata.items()
        }

        with open(self.metadata_file, 'w') as f:
            json.dump(metadata_dict, f, indent=2)

    def _audit_log_entry(self, action: str, service: str, details: Dict[str, Any]) -> None:
        """Log audit entry for key access"""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'service': service,
            'details': details
        }

        with open(self.audit_log, 'a') as f:
            f.write(json.dumps(entry) + '\n')

    def set_api_key(self, service: str, api_key: str, tier: str = "free") -> bool:
        """
        Store an encrypted API key

        Args:
            service: Service name (e.g., 'OPENAI', 'POLYGON')
            api_key: The API key to encrypt and store
            tier: Service tier (free, freemium, paid, enterprise)

        Returns:
            bool: Success status
        """
        try:
            # Encrypt the key
            encrypted = self.cipher.encrypt(api_key.encode()).decode()
            self.encrypted_keys[service] = encrypted

            # Update metadata
            now = datetime.now()
            if service in self.key_metadata:
                self.key_metadata[service].last_rotated = now
            else:
                self.key_metadata[service] = APIKeyMetadata(
                    service=service,
                    created_at=now,
                    last_rotated=now,
                    tier=tier
                )

            # Save configuration
            self._save_configuration()

            # Audit log
            self._audit_log_entry("SET_KEY", service, {
                'tier': tier,
                'key_length': len(api_key),
                'key_hash': hashlib.sha256(api_key.encode()).hexdigest()[:8]
            })

            logger.info(f"Successfully stored API key for {service}")
            return True

        except Exception as e:
            logger.error(f"Failed to store API key for {service}: {e}")
            return False

    def get_api_key(self, service: str, fallback_to_env: bool = True) -> Optional[str]:
        """
        Retrieve and decrypt an API key

        Args:
            service: Service name
            fallback_to_env: Whether to check environment variables if not found

        Returns:
            Decrypted API key or None
        """
        try:
            # Try encrypted storage first
            if service in self.encrypted_keys:
                encrypted = self.encrypted_keys[service]
                api_key = self.cipher.decrypt(encrypted.encode()).decode()

                # Update usage metadata
                if service in self.key_metadata:
                    self.key_metadata[service].last_used = datetime.now()
                    self.key_metadata[service].usage_count += 1
                    self._save_configuration()

                # Audit log
                self._audit_log_entry("GET_KEY", service, {'source': 'encrypted_storage'})

                return api_key

            # Fallback to environment variables
            if fallback_to_env and service in self.service_configs:
                for env_var in self.service_configs[service]["env_vars"]:
                    api_key = os.getenv(env_var)
                    if api_key:
                        # Optionally store it encrypted for next time
                        self.set_api_key(service, api_key, self.service_configs[service].get('tier', 'free'))

                        # Audit log
                        self._audit_log_entry("GET_KEY", service, {
                            'source': 'environment',
                            'env_var': env_var
                        })

                        return api_key

            # Not found
            self._audit_log_entry("GET_KEY_FAILED", service, {'reason': 'not_found'})
            return None

        except Exception as e:
            logger.error(f"Failed to retrieve API key for {service}: {e}")
            self._audit_log_entry("GET_KEY_FAILED", service, {'error': str(e)})
            return None

    def validate_all_keys(self) -> Dict[str, Dict[str, Any]]:
        """
        Validate all configured API keys

        Returns:
            Dictionary with validation status for each service
        """
        results = {}

        for service in self.service_configs:
            api_key = self.get_api_key(service)

            results[service] = {
                'configured': api_key is not None,
                'tier': self.service_configs[service].get('tier', 'unknown'),
                'required': self.service_configs[service].get('required', False),
                'key_length': len(api_key) if api_key else 0,
                'key_prefix': api_key[:4] + '...' if api_key and len(api_key) > 4 else None
            }

            # Add metadata if available
            if service in self.key_metadata:
                meta = self.key_metadata[service]
                results[service].update({
                    'last_used': meta.last_used.isoformat() if meta.last_used else None,
                    'usage_count': meta.usage_count,
                    'rate_limit_hits': meta.rate_limit_hits,
                    'days_since_rotation': (datetime.now() - meta.last_rotated).days
                })

        return results

    def check_rotation_needed(self, rotation_days: int = 90) -> List[str]:
        """
        Check which keys need rotation

        Args:
            rotation_days: Days before rotation is recommended

        Returns:
            List of services needing rotation
        """
        services_needing_rotation = []
        cutoff_date = datetime.now() - timedelta(days=rotation_days)

        for service, metadata in self.key_metadata.items():
            if metadata.last_rotated < cutoff_date and metadata.is_active:
                services_needing_rotation.append(service)

        return services_needing_rotation

    def export_config_template(self) -> Dict[str, str]:
        """
        Export a template for environment variables

        Returns:
            Template dictionary for .env file
        """
        template = {}

        for service, config in self.service_configs.items():
            primary_var = config["env_vars"][0]
            api_key = self.get_api_key(service, fallback_to_env=False)

            if api_key:
                # Mask the key for template
                masked = api_key[:4] + '*' * (len(api_key) - 8) + api_key[-4:] if len(api_key) > 8 else '***'
                template[primary_var] = f"# {service} API Key ({config['tier']} tier) - Replace with actual key\n{primary_var}={masked}"
            else:
                template[primary_var] = f"# {service} API Key ({config['tier']} tier) - Not configured\n# {primary_var}=your_key_here"

        return template

    def generate_status_report(self) -> str:
        """Generate comprehensive status report"""
        report = []
        report.append("=" * 60)
        report.append("ICE DATA INGESTION - API KEY STATUS REPORT")
        report.append("=" * 60)
        report.append(f"Generated: {datetime.now().isoformat()}")
        report.append("")

        validation = self.validate_all_keys()

        # Group by tier
        tiers = {'paid': [], 'freemium': [], 'free': []}
        for service, status in validation.items():
            tiers[status['tier']].append((service, status))

        for tier_name, services in tiers.items():
            if services:
                report.append(f"\n{tier_name.upper()} TIER SERVICES:")
                report.append("-" * 40)

                for service, status in services:
                    icon = "✅" if status['configured'] else "❌"
                    req = " (REQUIRED)" if status['required'] else ""
                    report.append(f"{icon} {service}{req}")

                    if status['configured']:
                        report.append(f"   Key: {status.get('key_prefix', 'N/A')}")
                        if 'usage_count' in status:
                            report.append(f"   Usage: {status['usage_count']} calls")
                        if 'days_since_rotation' in status:
                            days = status['days_since_rotation']
                            warn = " ⚠️" if days > 90 else ""
                            report.append(f"   Last rotated: {days} days ago{warn}")

        # Rotation warnings
        needs_rotation = self.check_rotation_needed()
        if needs_rotation:
            report.append("\n⚠️  KEYS NEEDING ROTATION:")
            for service in needs_rotation:
                report.append(f"   - {service}")

        report.append("\n" + "=" * 60)
        return "\n".join(report)


# Singleton instance
_secure_config = None

def get_secure_config() -> SecureConfigManager:
    """Get or create singleton secure config instance"""
    global _secure_config
    if _secure_config is None:
        _secure_config = SecureConfigManager()
    return _secure_config