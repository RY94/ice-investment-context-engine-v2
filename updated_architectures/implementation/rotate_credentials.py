# Location: /updated_architectures/implementation/rotate_credentials.py
# Purpose: API key rotation utility for Week 3 credential management
# Why: Simplify API key rotation process with security best practices
# Relevant Files: ice_simplified.py, ice_data_ingestion/secure_config.py

"""
ICE Credential Rotation Utility (Week 3)

Features:
- Interactive API key rotation
- Batch rotation for multiple services
- Rotation status checking
- Secure key validation
- Audit log review

Usage:
    python rotate_credentials.py                    # Interactive mode
    python rotate_credentials.py --service OPENAI   # Rotate specific service
    python rotate_credentials.py --check            # Check rotation status
    python rotate_credentials.py --status           # Show status report
"""

import sys
import os
import argparse
from pathlib import Path
from datetime import datetime
import getpass

# Add project root to path
project_root = Path(__file__).parents[2]
sys.path.insert(0, str(project_root))

from ice_data_ingestion.secure_config import get_secure_config

def rotate_single_service(secure_config, service: str, interactive: bool = True):
    """
    Rotate API key for a single service

    Args:
        secure_config: SecureConfig instance
        service: Service name (e.g., 'OPENAI', 'FINNHUB')
        interactive: Whether to prompt for key input
    """
    print(f"\n{'=' * 60}")
    print(f"Rotating API Key: {service}")
    print(f"{'=' * 60}")

    # Check current key status
    current_key = secure_config.get_api_key(service, fallback_to_env=False)

    if current_key:
        print(f"✅ Current key exists: {current_key[:8]}...")

        # Check rotation history
        if service in secure_config.key_metadata:
            metadata = secure_config.key_metadata[service]
            days_since_rotation = (datetime.now() - metadata.last_rotated).days
            print(f"📅 Last rotated: {days_since_rotation} days ago")
            print(f"📊 Usage count: {metadata.usage_count} calls")

            if days_since_rotation < 30:
                print(f"⚠️  Warning: Key was rotated recently ({days_since_rotation} days ago)")
                if interactive:
                    confirm = input("Continue with rotation? (y/N): ").strip().lower()
                    if confirm != 'y':
                        print("❌ Rotation cancelled")
                        return False
    else:
        print(f"⚠️  No existing key found for {service}")

    # Get new API key
    if interactive:
        print(f"\nEnter new API key for {service}:")
        print(f"(Input will be hidden for security)")
        new_key = getpass.getpass("API Key: ").strip()

        if not new_key:
            print("❌ No key provided, rotation cancelled")
            return False

        # Confirm
        print(f"\nNew key preview: {new_key[:8]}...")
        confirm = input("Confirm rotation? (y/N): ").strip().lower()

        if confirm != 'y':
            print("❌ Rotation cancelled")
            return False
    else:
        print("❌ Non-interactive mode requires key via environment variable")
        return False

    # Perform rotation
    tier = secure_config.service_configs.get(service, {}).get('tier', 'free')
    success = secure_config.set_api_key(service, new_key, tier)

    if success:
        print(f"✅ API key rotated successfully for {service}")
        print(f"🔐 Key encrypted and stored securely")
        print(f"📝 Rotation logged in audit trail")
        return True
    else:
        print(f"❌ Failed to rotate API key for {service}")
        return False

def check_rotation_status(secure_config, rotation_days: int = 90):
    """Check which keys need rotation"""
    print(f"\n{'=' * 60}")
    print(f"API Key Rotation Status")
    print(f"{'=' * 60}")
    print(f"Rotation threshold: {rotation_days} days\n")

    needs_rotation = secure_config.check_rotation_needed(rotation_days)

    if needs_rotation:
        print(f"⚠️  {len(needs_rotation)} services need rotation:\n")
        for service in needs_rotation:
            metadata = secure_config.key_metadata[service]
            days_old = (datetime.now() - metadata.last_rotated).days
            print(f"   🔴 {service:15s} - {days_old} days old (Last: {metadata.last_rotated.strftime('%Y-%m-%d')})")
    else:
        print(f"✅ All API keys are up to date (< {rotation_days} days old)")

    # Show all services with rotation dates
    print(f"\n{'=' * 60}")
    print(f"All Configured Services:")
    print(f"{'=' * 60}\n")

    for service, metadata in sorted(secure_config.key_metadata.items(), key=lambda x: x[1].last_rotated):
        days_old = (datetime.now() - metadata.last_rotated).days
        status_icon = "🔴" if days_old > rotation_days else "🟢"
        print(f"   {status_icon} {service:15s} - {days_old:3d} days old (Usage: {metadata.usage_count:4d} calls)")

def batch_rotate(secure_config, services: list):
    """Rotate multiple services in sequence"""
    print(f"\n{'=' * 60}")
    print(f"Batch API Key Rotation")
    print(f"{'=' * 60}")
    print(f"Services to rotate: {', '.join(services)}\n")

    results = {}

    for service in services:
        success = rotate_single_service(secure_config, service, interactive=True)
        results[service] = success
        print()

    # Summary
    print(f"\n{'=' * 60}")
    print(f"Batch Rotation Summary")
    print(f"{'=' * 60}")

    successful = sum(1 for success in results.values() if success)
    failed = len(results) - successful

    for service, success in results.items():
        icon = "✅" if success else "❌"
        status = "Success" if success else "Failed"
        print(f"   {icon} {service:15s} - {status}")

    print(f"\n📊 Total: {successful}/{len(results)} successful")

def main():
    """Main credential rotation utility"""
    parser = argparse.ArgumentParser(
        description="ICE API Key Rotation Utility (Week 3)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python rotate_credentials.py                      # Interactive mode
  python rotate_credentials.py --service OPENAI     # Rotate specific service
  python rotate_credentials.py --check              # Check rotation status
  python rotate_credentials.py --status             # Show detailed status report
  python rotate_credentials.py --batch OPENAI FINNHUB NEWSAPI  # Batch rotation
        """
    )

    parser.add_argument('--service', type=str, help='Service name to rotate (e.g., OPENAI, FINNHUB)')
    parser.add_argument('--check', action='store_true', help='Check rotation status')
    parser.add_argument('--status', action='store_true', help='Show detailed status report')
    parser.add_argument('--batch', nargs='+', help='Rotate multiple services')
    parser.add_argument('--rotation-days', type=int, default=90, help='Rotation threshold in days (default: 90)')

    args = parser.parse_args()

    # Initialize SecureConfig
    print("🔐 ICE Credential Rotation Utility")
    print("=" * 60)
    secure_config = get_secure_config()
    print(f"📁 Config directory: {secure_config.config_dir}\n")

    # Execute requested action
    if args.check:
        check_rotation_status(secure_config, args.rotation_days)

    elif args.status:
        print(secure_config.generate_status_report())

    elif args.batch:
        batch_rotate(secure_config, args.batch)

    elif args.service:
        rotate_single_service(secure_config, args.service.upper(), interactive=True)

    else:
        # Interactive mode
        print("Select an option:")
        print("  1. Rotate single API key")
        print("  2. Check rotation status")
        print("  3. Show status report")
        print("  4. Batch rotate multiple keys")
        print("  5. Exit")

        choice = input("\nEnter choice (1-5): ").strip()

        if choice == '1':
            available_services = list(secure_config.service_configs.keys())
            print(f"\nAvailable services: {', '.join(available_services)}")
            service = input("Enter service name (e.g., OPENAI): ").strip().upper()

            if service in available_services:
                rotate_single_service(secure_config, service, interactive=True)
            else:
                print(f"❌ Unknown service: {service}")

        elif choice == '2':
            check_rotation_status(secure_config, args.rotation_days)

        elif choice == '3':
            print(secure_config.generate_status_report())

        elif choice == '4':
            available_services = list(secure_config.service_configs.keys())
            print(f"\nAvailable services: {', '.join(available_services)}")
            services_input = input("Enter services to rotate (comma-separated): ").strip()
            services = [s.strip().upper() for s in services_input.split(',') if s.strip()]

            if services:
                batch_rotate(secure_config, services)
            else:
                print("❌ No services specified")

        elif choice == '5':
            print("👋 Goodbye!")

        else:
            print("❌ Invalid choice")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
