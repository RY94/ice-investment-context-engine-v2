# imap_email_ingestion_pipeline/quick_email_test.py
# Quick email connection test with command line password
# Usage: python quick_email_test.py YOUR_PASSWORD
# RELEVANT FILES: imap_connector.py, auto_detect_email.py

import sys
import os
import logging

# Add current directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from imap_connector import ResilientIMAPConnector

def test_connection_with_password(password: str):
    """Test email connection with provided password"""
    
    # Suppress verbose logging
    logging.getLogger().setLevel(logging.ERROR)
    
    print("🔍 Testing Email Connection for roy@agtpartners.com.sg")
    print("=" * 60)
    
    # Test configurations in order of preference
    configs = [
        ('mail.agtpartners.com.sg', 993, 'AGT Partners Mail Server'),
        ('outlook.office365.com', 993, 'Office365/Outlook'),
        ('imap-mail.outlook.com', 993, 'Outlook.com'),
    ]
    
    for server, port, name in configs:
        print(f"\\n🔄 Testing {name}: {server}:{port}")
        
        try:
            connector = ResilientIMAPConnector(
                email_address="roy@agtpartners.com.sg",
                password=password,
                server=server,
                port=port
            )
            
            if connector.connect():
                print(f"✅ Successfully connected to {name}!")
                
                # Get folder info
                folders = connector.get_folder_list()
                print(f"📁 Available folders ({len(folders)}): {', '.join(folders[:5])}...")
                
                # Get recent emails
                emails = connector.fetch_new_emails(folder='INBOX', limit=3)
                print(f"📧 Recent emails found: {len(emails)}")
                
                if emails:
                    print("\\n📬 Latest emails preview:")
                    for i, email in enumerate(emails, 1):
                        subject = email.get('subject', 'No Subject')[:50]
                        sender = email.get('from', 'Unknown')[:25]
                        date = email.get('date', '')[:16]  # Just date part
                        
                        print(f"  {i}. {subject}...")
                        print(f"     From: {sender}")
                        print(f"     Date: {date}")
                        
                        # Check if investment-related
                        investment_keywords = [
                            'earnings', 'portfolio', 'stock', 'equity', 'analysis',
                            'recommendation', 'rating', 'target', 'price', 'market'
                        ]
                        
                        content = (subject + ' ' + email.get('body', '')).lower()
                        is_investment = any(keyword in content for keyword in investment_keywords)
                        
                        if is_investment:
                            print(f"     🎯 Investment-related content detected")
                        
                        print()
                
                connector.close()
                
                print(f"\\n🎉 CONNECTION SUCCESSFUL with {name}!")
                print("✅ Your email is ready for pipeline processing")
                print("\\nNext steps:")
                print("1. Process recent emails through the pipeline")
                print("2. Extract investment entities and build knowledge graphs")
                print("3. Integrate with ICE system for querying")
                
                return True
                
            else:
                print(f"❌ Authentication failed for {name}")
                
        except Exception as e:
            print(f"❌ Connection failed for {name}: {type(e).__name__}")
            continue
    
    print("\\n❌ All connection attempts failed")
    print("\\n💡 Troubleshooting suggestions:")
    print("  - Verify the password is correct")
    print("  - If 2FA is enabled, use an app-specific password")
    print("  - Check if IMAP is enabled in your email settings")
    print("  - Contact IT support for server configuration")
    
    return False

def main():
    if len(sys.argv) != 2:
        print("Usage: python quick_email_test.py YOUR_PASSWORD")
        print("Example: python quick_email_test.py mypassword123")
        return
    
    password = sys.argv[1]
    
    if not password.strip():
        print("❌ Password cannot be empty")
        return
    
    success = test_connection_with_password(password)
    
    if success:
        print("\\n🚀 Ready to run the full pipeline!")
        print(f"Command: python process_emails.py {password}")

if __name__ == "__main__":
    main()