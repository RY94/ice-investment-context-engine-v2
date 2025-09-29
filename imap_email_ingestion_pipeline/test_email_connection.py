# imap_email_ingestion_pipeline/test_email_connection.py
# Simple email connection test for roy@agtpartners.com.sg
# Tests basic IMAP connectivity and shows recent emails
# RELEVANT FILES: imap_connector.py, connect_real_email.py

import sys
import os
import logging

# Add current directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from imap_connector import ResilientIMAPConnector

def test_email_connection():
    print("🔍 Testing Email Connection for roy@agtpartners.com.sg")
    print("=" * 60)
    
    # Set up logging
    logging.basicConfig(level=logging.WARNING)  # Reduce noise
    
    # Get password input
    print("Please enter your email password:")
    password = input("Password: ")
    
    if not password.strip():
        print("❌ Password cannot be empty")
        return False
    
    print("\n🔄 Testing connection...")
    
    # Test Office365 connection
    try:
        connector = ResilientIMAPConnector(
            email_address="roy@agtpartners.com.sg",
            password=password,
            server="outlook.office365.com",
            port=993
        )
        
        if connector.connect():
            print("✅ Successfully connected to Office365 server!")
            
            # Get folder list
            folders = connector.get_folder_list()
            print(f"📁 Available folders: {folders[:5]}...")
            
            # Get recent emails
            print("\n📧 Fetching recent emails...")
            emails = connector.fetch_new_emails(folder='INBOX', limit=5)
            
            if emails:
                print(f"📬 Found {len(emails)} recent emails:")
                for i, email in enumerate(emails, 1):
                    subject = email.get('subject', 'No Subject')[:60]
                    sender = email.get('from', 'Unknown')[:30]
                    date = email.get('date', 'Unknown')
                    priority = email.get('priority', 0)
                    
                    print(f"  {i}. {subject}")
                    print(f"     From: {sender}")
                    print(f"     Date: {date}")
                    print(f"     Priority: {priority}")
                    print()
                
                # Show one email body sample
                if emails[0].get('body'):
                    body_preview = emails[0]['body'][:200].replace('\n', ' ')
                    print(f"📝 Sample email content: {body_preview}...")
                
            else:
                print("📭 No recent emails found")
            
            connector.close()
            return True
            
        else:
            print("❌ Failed to connect to email server")
            print("\n💡 Troubleshooting tips:")
            print("  - Check if password is correct")
            print("  - If you have 2FA, create an app-specific password")
            print("  - Ensure IMAP is enabled in your email settings")
            return False
            
    except Exception as e:
        print(f"❌ Connection error: {e}")
        print("\n💡 This might indicate:")
        print("  - Network connectivity issues")
        print("  - Email server configuration problems")
        print("  - Authentication method not supported")
        return False

def main():
    success = test_email_connection()
    
    if success:
        print("\n🎉 Connection test successful!")
        print("✅ Your email is ready for pipeline processing")
        print("\nNext steps:")
        print("  1. Run: python connect_real_email.py")
        print("  2. Or use: python pipeline_orchestrator.py --email roy@agtpartners.com.sg --password YOUR_PASSWORD --mode single")
    else:
        print("\n❌ Connection test failed")
        print("Please resolve the connection issues before proceeding")

if __name__ == "__main__":
    main()