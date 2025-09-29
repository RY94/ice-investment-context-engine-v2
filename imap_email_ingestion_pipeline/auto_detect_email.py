# imap_email_ingestion_pipeline/auto_detect_email.py
# Auto-detect email server settings for roy@agtpartners.com.sg
# Tests multiple server configurations to find the working one
# RELEVANT FILES: imap_connector.py, test_email_connection.py

import sys
import os
import logging
from typing import Optional, Dict, Any

# Add current directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from imap_connector import ResilientIMAPConnector

def test_server_config(email: str, password: str, server: str, port: int, name: str) -> Optional[Dict[str, Any]]:
    """Test a specific server configuration"""
    print(f"🔍 Testing {name}: {server}:{port}")
    
    try:
        connector = ResilientIMAPConnector(
            email_address=email,
            password=password,
            server=server,
            port=port
        )
        
        if connector.connect():
            # Test basic operations
            folders = connector.get_folder_list()
            emails = connector.fetch_new_emails(folder='INBOX', limit=2)
            
            connector.close()
            
            result = {
                'server': server,
                'port': port,
                'name': name,
                'folders_count': len(folders),
                'recent_emails_count': len(emails),
                'sample_folders': folders[:3] if folders else [],
                'working': True
            }
            
            print(f"   ✅ SUCCESS - {len(folders)} folders, {len(emails)} recent emails")
            return result
        else:
            print(f"   ❌ Authentication failed")
            return None
            
    except Exception as e:
        print(f"   ❌ Connection error: {type(e).__name__}: {e}")
        return None

def auto_detect_email_settings(email: str, password: str) -> Optional[Dict[str, Any]]:
    """Auto-detect the correct email server settings"""
    
    # Server configurations to test
    server_configs = [
        # Office365/Outlook (most common for business emails)
        ('outlook.office365.com', 993, 'Office365/Outlook'),
        
        # AGT Partners direct mail server
        ('mail.agtpartners.com.sg', 993, 'AGT Partners Mail Server'),
        ('mail.agtpartners.com.sg', 143, 'AGT Partners Mail Server (STARTTLS)'),
        
        # Other common configurations
        ('imap-mail.outlook.com', 993, 'Outlook.com'),
        ('imap.gmail.com', 993, 'Gmail (if forwarded)'),
    ]
    
    print(f"🔍 Auto-detecting email settings for {email}")
    print("=" * 60)
    
    working_configs = []
    
    for server, port, name in server_configs:
        config = test_server_config(email, password, server, port, name)
        if config:
            working_configs.append(config)
            print(f"   📊 Folders: {config['sample_folders']}")
            print()
    
    if working_configs:
        print("✅ Found working email configurations:")
        for i, config in enumerate(working_configs, 1):
            print(f"  {i}. {config['name']} - {config['folders_count']} folders, {config['recent_emails_count']} emails")
        
        # Return the best configuration (most emails/folders)
        best_config = max(working_configs, key=lambda x: (x['recent_emails_count'], x['folders_count']))
        print(f"\n🎯 Recommended configuration: {best_config['name']}")
        return best_config
    else:
        print("❌ No working email configurations found")
        return None

def main():
    print("🚀 AUTO-DETECT EMAIL SETTINGS")
    print("=" * 40)
    print("This will test multiple server configurations for roy@agtpartners.com.sg")
    print()
    
    # Get password
    print("Please enter your email password:")
    password = input("Password for roy@agtpartners.com.sg: ")
    
    if not password.strip():
        print("❌ Password cannot be empty")
        return
    
    print()
    
    # Suppress verbose logging during tests
    logging.getLogger().setLevel(logging.ERROR)
    
    # Auto-detect settings
    best_config = auto_detect_email_settings("roy@agtpartners.com.sg", password)
    
    if best_config:
        print("\n" + "=" * 60)
        print("🎉 EMAIL CONFIGURATION DETECTED!")
        print("=" * 60)
        print(f"Server: {best_config['server']}")
        print(f"Port: {best_config['port']}")
        print(f"Type: {best_config['name']}")
        print(f"Folders: {best_config['folders_count']}")
        print(f"Recent emails: {best_config['recent_emails_count']}")
        
        print("\n📧 Ready to process your emails!")
        print("Next steps:")
        print(f"  1. Run the pipeline: python connect_real_email.py")
        print(f"  2. Or use orchestrator with detected settings")
        
        # Save configuration for later use
        config_file = "detected_email_config.json"
        import json
        with open(config_file, 'w') as f:
            json.dump(best_config, f, indent=2)
        print(f"\n💾 Configuration saved to: {config_file}")
        
    else:
        print("\n❌ Could not detect working email configuration")
        print("\n💡 Troubleshooting:")
        print("  - Verify your password is correct")
        print("  - Check if 2FA requires an app-specific password")
        print("  - Ensure IMAP is enabled in your email settings")
        print("  - Contact your IT admin for server settings")

if __name__ == "__main__":
    main()