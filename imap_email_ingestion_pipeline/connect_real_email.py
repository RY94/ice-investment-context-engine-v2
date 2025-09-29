# imap_email_ingestion_pipeline/connect_real_email.py
# Secure connection script for real email processing roy@agtpartners.com.sg
# Interactive email processing with security best practices
# RELEVANT FILES: imap_connector.py, pipeline_orchestrator.py, entity_extractor.py

import getpass
import logging
import sys
import os
import tempfile
from datetime import datetime, timedelta
from typing import List, Dict, Any
import json

# Add current directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from imap_connector import ResilientIMAPConnector
from state_manager import StateManager
from entity_extractor import EntityExtractor
from graph_builder import GraphBuilder
from ice_integrator import ICEEmailIntegrator

class RealEmailProcessor:
    def __init__(self, email_address: str):
        self.email_address = email_address
        self.password = None
        self.imap_connector = None
        self.logger = self._setup_logging()
        
        # Initialize pipeline components
        self.demo_dir = tempfile.mkdtemp(prefix="real_email_")
        self.state_manager = StateManager(os.path.join(self.demo_dir, "email_state.db"))
        self.entity_extractor = EntityExtractor(os.path.join(self.demo_dir, "config"))
        self.graph_builder = GraphBuilder()
        self.ice_integrator = ICEEmailIntegrator(os.path.join(self.demo_dir, "ice_storage"))
        
        print(f"🔧 Initialized pipeline components in: {self.demo_dir}")
        
    def _setup_logging(self):
        """Setup logging for email processing"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)
    
    def get_credentials(self):
        """Securely get email credentials"""
        print(f"📧 Connecting to: {self.email_address}")
        print("🔒 Please enter your email password securely")
        print("💡 Tip: If you have 2FA enabled, you may need an app-specific password")
        print()
        
        self.password = getpass.getpass(f"Password for {self.email_address}: ")
        
        if not self.password.strip():
            print("❌ Password cannot be empty")
            return False
            
        return True
    
    def test_connection(self) -> bool:
        """Test IMAP connection to email server"""
        print("🔍 Testing connection to email server...")
        
        try:
            # Try Office365 settings first
            self.imap_connector = ResilientIMAPConnector(
                email_address=self.email_address,
                password=self.password,
                server="outlook.office365.com",
                port=993
            )
            
            if self.imap_connector.connect():
                print("✅ Successfully connected to Office365/Outlook server")
                return True
            else:
                print("❌ Failed to connect to Office365 server")
                print("💡 This might be due to:")
                print("   - Incorrect password")
                print("   - 2FA requiring app-specific password")
                print("   - IMAP not enabled in email settings")
                print("   - Different email server configuration")
                return False
                
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return False
    
    def get_mailbox_info(self) -> Dict[str, Any]:
        """Get information about the mailbox"""
        print("📊 Retrieving mailbox information...")
        
        try:
            folders = self.imap_connector.get_folder_list()
            print(f"📁 Available folders: {folders[:5]}..." if len(folders) > 5 else f"📁 Available folders: {folders}")
            
            # Get inbox info
            inbox_emails = self.imap_connector.fetch_new_emails(
                folder='INBOX', 
                limit=5  # Just get a few for testing
            )
            
            print(f"📬 Recent emails in INBOX: {len(inbox_emails)}")
            
            if inbox_emails:
                print("📋 Latest emails preview:")
                for i, email in enumerate(inbox_emails[:3], 1):
                    subject = email.get('subject', 'No Subject')[:50]
                    sender = email.get('from', 'Unknown')[:30]
                    date = email.get('date', 'Unknown')
                    print(f"   {i}. {subject}... | From: {sender} | {date}")
            
            return {
                'folders': folders,
                'recent_emails_count': len(inbox_emails),
                'preview_emails': inbox_emails[:3]
            }
            
        except Exception as e:
            print(f"❌ Error getting mailbox info: {e}")
            return {}
    
    def fetch_investment_emails(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Fetch recent emails and filter for investment-related content"""
        print(f"📧 Fetching last {limit} emails for investment analysis...")
        
        try:
            # Fetch recent emails
            all_emails = self.imap_connector.fetch_new_emails(
                folder='INBOX',
                limit=limit
            )
            
            print(f"📬 Retrieved {len(all_emails)} emails")
            
            # Filter for investment-related emails
            investment_keywords = [
                'earnings', 'portfolio', 'stock', 'equity', 'analysis',
                'recommendation', 'rating', 'target', 'price', 'market',
                'research', 'analyst', 'financial', 'investment', 'fund',
                'ticker', 'trading', 'shares', 'dividend', 'merger',
                'acquisition', 'guidance', 'outlook'
            ]
            
            investment_emails = []
            for email in all_emails:
                subject = email.get('subject', '').lower()
                body = email.get('body', '').lower()
                sender = email.get('from', '').lower()
                
                # Check if email contains investment-related content
                is_investment_related = any(
                    keyword in subject or keyword in body or keyword in sender
                    for keyword in investment_keywords
                )
                
                # Also check sender domains for financial institutions
                financial_domains = [
                    'bloomberg', 'reuters', 'marketwatch', 'cnbc', 'wsj', 'ft.com',
                    'research', 'analyst', 'investment', 'capital', 'securities',
                    'fund', 'equity', 'agtpartners'
                ]
                
                is_financial_sender = any(
                    domain in sender for domain in financial_domains
                )
                
                if is_investment_related or is_financial_sender or email.get('priority', 0) > 20:
                    investment_emails.append(email)
            
            print(f"📈 Found {len(investment_emails)} investment-related emails")
            
            if investment_emails:
                print("🎯 Investment emails found:")
                for i, email in enumerate(investment_emails[:5], 1):
                    subject = email.get('subject', 'No Subject')[:60]
                    sender = email.get('from', 'Unknown')[:25]
                    priority = email.get('priority', 0)
                    print(f"   {i}. {subject}... | {sender} | Priority: {priority}")
            
            return investment_emails
            
        except Exception as e:
            print(f"❌ Error fetching emails: {e}")
            return []
    
    def process_emails(self, emails: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process emails through the full pipeline"""
        print("🔄 Processing emails through extraction pipeline...")
        
        results = {
            'processed_count': 0,
            'entities_extracted': [],
            'graphs_built': [],
            'ice_integrated': 0,
            'errors': []
        }
        
        for i, email in enumerate(emails, 1):
            try:
                print(f"\n📧 Processing email {i}/{len(emails)}: {email.get('subject', 'No Subject')[:50]}...")
                
                # Extract entities
                entities = self.entity_extractor.extract_entities(
                    email.get('body', ''),
                    metadata={
                        'sender': email.get('from', ''),
                        'subject': email.get('subject', ''),
                        'date': email.get('date', '')
                    }
                )
                entities['email_uid'] = email.get('uid', f'email_{i}')
                
                # Display extraction results
                tickers = entities.get('tickers', [])
                companies = entities.get('companies', [])
                people = entities.get('people', [])
                
                print(f"   ✅ Extracted: {len(tickers)} tickers, {len(companies)} companies, {len(people)} people")
                
                if tickers:
                    ticker_list = [t['ticker'] for t in tickers[:5]]
                    print(f"   📈 Tickers: {', '.join(ticker_list)}")
                
                if entities.get('sentiment'):
                    sentiment = entities['sentiment']
                    print(f"   💭 Sentiment: {sentiment.get('sentiment', 'neutral')} ({sentiment.get('confidence', 0):.2f})")
                
                # Build knowledge graph
                graph_data = self.graph_builder.build_email_graph(email, entities, [])
                validation = self.graph_builder.validate_graph_structure(graph_data)
                
                print(f"   🕸️ Graph: {len(graph_data.get('nodes', []))} nodes, {len(graph_data.get('edges', []))} edges")
                
                # Integrate with ICE
                integration_result = self.ice_integrator.integrate_email_data(
                    email, entities, graph_data, []
                )
                
                if integration_result.get('success'):
                    print(f"   ✅ ICE integration successful")
                    results['ice_integrated'] += 1
                
                # Store results
                results['entities_extracted'].append(entities)
                results['graphs_built'].append(graph_data)
                results['processed_count'] += 1
                
            except Exception as e:
                error_msg = f"Error processing email {i}: {e}"
                print(f"   ❌ {error_msg}")
                results['errors'].append(error_msg)
                continue
        
        return results
    
    def generate_analysis_report(self, results: Dict[str, Any]):
        """Generate analysis report from processed emails"""
        print("\n" + "="*60)
        print("📊 EMAIL ANALYSIS REPORT")
        print("="*60)
        
        print(f"📧 Emails processed: {results['processed_count']}")
        print(f"🔗 ICE integrations: {results['ice_integrated']}")
        print(f"❌ Errors encountered: {len(results['errors'])}")
        
        if results['errors']:
            print("\n⚠️ Errors:")
            for error in results['errors'][:3]:
                print(f"   - {error}")
        
        # Aggregate entity statistics
        all_tickers = []
        all_companies = []
        all_people = []
        sentiment_scores = []
        
        for entities in results['entities_extracted']:
            all_tickers.extend([t['ticker'] for t in entities.get('tickers', [])])
            all_companies.extend([c['name'] for c in entities.get('companies', [])])
            all_people.extend([p['name'] for p in entities.get('people', [])])
            
            if entities.get('sentiment'):
                sentiment_scores.append(entities['sentiment'].get('confidence', 0))
        
        print(f"\n📈 ENTITIES DISCOVERED:")
        if all_tickers:
            unique_tickers = list(set(all_tickers))
            print(f"   Tickers: {', '.join(unique_tickers[:10])}")
            if len(unique_tickers) > 10:
                print(f"   ... and {len(unique_tickers) - 10} more")
        
        if all_companies:
            unique_companies = list(set(all_companies))
            print(f"   Companies: {', '.join(unique_companies[:5])}")
            if len(unique_companies) > 5:
                print(f"   ... and {len(unique_companies) - 5} more")
        
        if all_people:
            unique_people = list(set(all_people))
            print(f"   People: {', '.join(unique_people[:5])}")
        
        # Knowledge graph statistics
        total_nodes = sum(len(g.get('nodes', [])) for g in results['graphs_built'])
        total_edges = sum(len(g.get('edges', [])) for g in results['graphs_built'])
        
        print(f"\n🕸️ KNOWLEDGE GRAPH:")
        print(f"   Total nodes: {total_nodes}")
        print(f"   Total edges: {total_edges}")
        print(f"   Average nodes per email: {total_nodes / max(results['processed_count'], 1):.1f}")
        
        # Sentiment analysis
        if sentiment_scores:
            avg_confidence = sum(sentiment_scores) / len(sentiment_scores)
            print(f"\n💭 SENTIMENT ANALYSIS:")
            print(f"   Average confidence: {avg_confidence:.2f}")
        
        print(f"\n🎉 Analysis complete! Your investment emails have been processed and integrated into ICE.")
        print(f"💾 Data stored in: {self.demo_dir}")
    
    def cleanup(self):
        """Clean up resources"""
        try:
            if self.imap_connector:
                self.imap_connector.close()
            
            self.state_manager.close()
            self.ice_integrator.close()
            
            print("✅ Resources cleaned up successfully")
        except Exception as e:
            print(f"⚠️ Cleanup warning: {e}")

def main():
    print("🚀 REAL EMAIL PROCESSING FOR ICE")
    print("="*50)
    print("This will connect to roy@agtpartners.com.sg and process actual emails")
    print("through the investment analysis pipeline.\n")
    
    # Initialize processor
    processor = RealEmailProcessor("roy@agtpartners.com.sg")
    
    try:
        # Step 1: Get credentials
        if not processor.get_credentials():
            return
        
        # Step 2: Test connection
        if not processor.test_connection():
            return
        
        # Step 3: Get mailbox info
        mailbox_info = processor.get_mailbox_info()
        
        # Step 4: Fetch investment emails
        investment_emails = processor.fetch_investment_emails(limit=20)
        
        if not investment_emails:
            print("📭 No investment-related emails found in recent messages.")
            print("💡 Try increasing the limit or check different folders.")
            return
        
        # Confirm processing
        print(f"\n🔍 Found {len(investment_emails)} investment-related emails to process.")
        confirm = input("Continue with processing? (y/N): ").lower().strip()
        
        if confirm != 'y':
            print("⏹️ Processing cancelled by user.")
            return
        
        # Step 5: Process emails
        results = processor.process_emails(investment_emails)
        
        # Step 6: Generate report
        processor.generate_analysis_report(results)
        
        # Step 7: Query demonstration
        print("\n🔍 You can now query your processed emails!")
        print("Examples:")
        print("- What stocks were mentioned in my recent emails?")
        print("- What's the sentiment around NVDA?")
        print("- Who are the key analysts mentioned?")
        
    except KeyboardInterrupt:
        print("\n⏹️ Processing interrupted by user.")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    finally:
        processor.cleanup()

if __name__ == "__main__":
    main()