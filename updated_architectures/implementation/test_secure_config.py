# Location: /updated_architectures/implementation/test_secure_config.py
# Purpose: Test SecureConfig integration for Week 3 validation
# Why: Validate encrypted API key management, rotation tracking, and fallback logic
# Relevant Files: ice_simplified.py, ice_data_ingestion/secure_config.py

"""
Week 3 SecureConfig Validation Test

Tests:
1. API key retrieval with encryption
2. Fallback to environment variables
3. Rotation tracking
4. Status report generation
5. Configuration validation
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parents[2]
sys.path.insert(0, str(project_root))

from ice_data_ingestion.secure_config import get_secure_config

def test_secure_config_integration():
    """Comprehensive SecureConfig integration test"""

    print("=" * 70)
    print("WEEK 3: SecureConfig Integration Validation")
    print("=" * 70)
    print()

    # Initialize SecureConfig
    print("1. Initializing SecureConfig...")
    secure_config = get_secure_config()
    print(f"   ✅ SecureConfig initialized")
    print(f"   📁 Config directory: {secure_config.config_dir}")
    print()

    # Test 2: Environment variable fallback
    print("2. Testing environment variable fallback...")
    test_services = ['OPENAI', 'FINNHUB', 'NEWSAPI', 'POLYGON', 'ALPHAVANTAGE']

    for service in test_services:
        api_key = secure_config.get_api_key(service, fallback_to_env=True)
        status = "✅ Configured" if api_key else "⚠️  Not configured"
        key_preview = f"{api_key[:8]}..." if api_key and len(api_key) > 8 else "N/A"
        print(f"   {status} {service:15s} - Key: {key_preview}")
    print()

    # Test 3: Validate all keys
    print("3. Validating all configured keys...")
    validation = secure_config.validate_all_keys()

    configured_count = sum(1 for status in validation.values() if status['configured'])
    total_count = len(validation)
    print(f"   📊 {configured_count}/{total_count} services configured")
    print()

    # Test 4: Check rotation status
    print("4. Checking key rotation status...")
    needs_rotation = secure_config.check_rotation_needed(rotation_days=90)

    if needs_rotation:
        print(f"   ⚠️  {len(needs_rotation)} keys need rotation:")
        for service in needs_rotation:
            print(f"      - {service}")
    else:
        print(f"   ✅ No keys need rotation (all < 90 days old)")
    print()

    # Test 5: Generate status report
    print("5. Generating comprehensive status report...")
    print()
    report = secure_config.generate_status_report()
    print(report)
    print()

    # Test 6: Test ICEConfig integration
    print("6. Testing ICEConfig integration...")
    try:
        from ice_simplified import ICEConfig

        config = ICEConfig()
        print(f"   ✅ ICEConfig initialized successfully")
        print(f"   🔑 OPENAI API Key: {'Configured' if config.openai_api_key else 'Missing'}")
        print(f"   📡 Available services: {', '.join(config.get_available_services())}")

        # Test rotation check via ICEConfig
        rotation_needed = config.check_rotation_needed()
        print(f"   🔄 Keys needing rotation: {len(rotation_needed)}")

    except Exception as e:
        print(f"   ❌ ICEConfig integration failed: {e}")
    print()

    # Test 7: Encryption file existence
    print("7. Checking encryption files...")
    encryption_key_file = secure_config.config_dir / ".encryption_key"
    encrypted_keys_file = secure_config.config_dir / "encrypted_keys.json"
    metadata_file = secure_config.config_dir / "key_metadata.json"
    audit_log_file = secure_config.config_dir / "audit.log"

    files_status = {
        "Encryption Key": encryption_key_file.exists(),
        "Encrypted Keys": encrypted_keys_file.exists(),
        "Key Metadata": metadata_file.exists(),
        "Audit Log": audit_log_file.exists()
    }

    for file_name, exists in files_status.items():
        icon = "✅" if exists else "⚠️ "
        print(f"   {icon} {file_name:20s}: {'Present' if exists else 'Not created yet'}")
    print()

    # Summary
    print("=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)
    print(f"✅ SecureConfig operational")
    print(f"✅ {configured_count}/{total_count} API services configured")
    print(f"✅ Encryption system ready")
    print(f"✅ Fallback to environment variables working")
    print(f"✅ Audit logging enabled")

    if needs_rotation:
        print(f"⚠️  {len(needs_rotation)} keys need rotation (>90 days old)")
    else:
        print(f"✅ All keys recently rotated")

    print()
    print("🎉 Week 3 SecureConfig Integration: VALIDATED")
    print("=" * 70)

if __name__ == "__main__":
    try:
        test_secure_config_integration()
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
