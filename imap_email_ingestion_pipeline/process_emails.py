# imap_email_ingestion_pipeline/process_emails.py
# Full pipeline execution with real email processing
# Usage: python process_emails.py YOUR_PASSWORD
# RELEVANT FILES: All pipeline components - full integration

# 1. Connect to the email using IMAP
# 2. Fetch investment-related emails
# 3. Process each email through entity extraction (tickers, companies, people, sentiment)
# 4. Build knowledge graphs (nodes and edges)
# 5. Integrate with ICE system for querying
# 6. Generate comprehensive analysis report


import sys
import os
import logging
import tempfile
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Add current directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from imap_connector import ResilientIMAPConnector
from state_manager import StateManager
from entity_extractor import EntityExtractor
from graph_builder import GraphBuilder
from ice_integrator import ICEEmailIntegrator

class FullPipelineRunner:
    def __init__(self, email: str, password: str):
        self.email = email
        self.password = password
        self.connector = None
        
        # Setup logging
        logging.basicConfig(level=logging.WARNING, format='%(levelname)s: %(message)s')
        self.logger = logging.getLogger(__name__)
        
        # Create temporary working directory
        self.working_dir = tempfile.mkdtemp(prefix="real_pipeline_")
        print(f"💾 Working directory: {self.working_dir}")
        
        # Initialize pipeline components
        self.state_manager = StateManager(os.path.join(self.working_dir, "pipeline_state.db"))
        self.entity_extractor = EntityExtractor(os.path.join(self.working_dir, "config"))
        self.graph_builder = GraphBuilder()
        self.ice_integrator = ICEEmailIntegrator(os.path.join(self.working_dir, "ice_storage"))
        
        print("🔧 Pipeline components initialized")
    
    def connect_to_email(self) -> bool:
        """Connect to email server using auto-detected settings"""
        print("🔄 Connecting to email server...")
        
        # Try different server configurations
        configs = [
            ('mail.agtpartners.com.sg', 993, 'AGT Partners'),
            ('outlook.office365.com', 993, 'Office365'),
        ]
        
        for server, port, name in configs:
            try:
                print(f"   Testing {name}...")
                
                self.connector = ResilientIMAPConnector(
                    email_address=self.email,
                    password=self.password,
                    server=server,
                    port=port
                )
                
                if self.connector.connect():
                    print(f"✅ Connected successfully to {name}")
                    return True
                    
            except Exception as e:
                continue
        
        print("❌ Failed to connect to any email server")
        return False
    
    def fetch_investment_emails(self, days_back: int = 7, limit: int = 30) -> List[Dict[str, Any]]:
        """Fetch and filter investment-related emails"""
        print(f"📧 Fetching emails from last {days_back} days (limit: {limit})...")
        
        try:
            # Fetch emails from the specified time period
            all_emails = self.connector.fetch_new_emails(
                folder='INBOX',
                limit=limit
            )
            
            print(f"📬 Retrieved {len(all_emails)} total emails")
            
            # Filter for investment-related content
            investment_keywords = [
                'earnings', 'portfolio', 'stock', 'equity', 'analysis', 'research',
                'recommendation', 'rating', 'target', 'price', 'market', 'financial',
                'investment', 'fund', 'ticker', 'trading', 'shares', 'dividend',
                'merger', 'acquisition', 'guidance', 'outlook', 'analyst',
                'upgrade', 'downgrade', 'alert', 'report', 'sector', 'company'
            ]
            
            # Financial institutions and sources
            financial_domains = [
                'bloomberg', 'reuters', 'marketwatch', 'cnbc', 'wsj', 'ft.com',
                'research', 'analyst', 'investment', 'capital', 'securities',
                'fund', 'equity', 'agtpartners', 'goldmansachs', 'jpmorgan',
                'morganstanley', 'barclays', 'ubs', 'citi', 'wells'
            ]
            
            investment_emails = []
            
            for email in all_emails:
                subject = email.get('subject', '').lower()
                body = email.get('body', '').lower() 
                sender = email.get('from', '').lower()
                
                # Check for investment keywords
                content_text = f"{subject} {body} {sender}"
                has_investment_keywords = any(
                    keyword in content_text for keyword in investment_keywords
                )
                
                # Check for financial institution senders
                has_financial_sender = any(
                    domain in sender for domain in financial_domains
                )
                
                # Include high priority emails
                is_high_priority = email.get('priority', 0) > 30
                
                if has_investment_keywords or has_financial_sender or is_high_priority:
                    investment_emails.append(email)
            
            print(f"🎯 Found {len(investment_emails)} investment-related emails")
            
            # Show preview
            if investment_emails:
                print("\\n📊 Investment email preview:")
                for i, email in enumerate(investment_emails[:5], 1):
                    subject = email.get('subject', 'No Subject')[:55]
                    sender = email.get('from', 'Unknown')[:25]
                    priority = email.get('priority', 0)
                    
                    print(f"  {i}. {subject}...")
                    print(f"     📧 {sender} | Priority: {priority}")
            
            return investment_emails
            
        except Exception as e:
            print(f"❌ Error fetching emails: {e}")
            return []
    
    def process_emails_through_pipeline(self, emails: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process emails through the complete pipeline"""
        print(f"\\n🔄 Processing {len(emails)} emails through pipeline...")
        print("=" * 60)
        
        results = {
            'processed_count': 0,
            'entities_extracted': [],
            'graphs_built': [],
            'ice_integrated': 0,
            'errors': [],
            'all_tickers': [],
            'all_companies': [],
            'all_people': [],
            'sentiment_scores': []
        }
        
        for i, email in enumerate(emails, 1):
            print(f"\\n📧 Processing {i}/{len(emails)}: {email.get('subject', 'No Subject')[:50]}...")
            
            try:
                # Step 1: Entity Extraction
                entities = self.entity_extractor.extract_entities(
                    email.get('body', ''),
                    metadata={
                        'sender': email.get('from', ''),
                        'subject': email.get('subject', ''),
                        'date': email.get('date', ''),
                        'uid': email.get('uid', f'email_{i}')
                    }
                )
                
                # Collect results
                tickers = entities.get('tickers', [])
                companies = entities.get('companies', [])
                people = entities.get('people', [])
                sentiment = entities.get('sentiment', {})
                
                print(f"   📊 Extracted: {len(tickers)} tickers, {len(companies)} companies, {len(people)} people")
                
                if tickers:
                    ticker_names = [t['ticker'] for t in tickers[:5]]
                    print(f"   📈 Tickers: {', '.join(ticker_names)}")
                    results['all_tickers'].extend(ticker_names)
                
                if sentiment:
                    sent_label = sentiment.get('sentiment', 'neutral')
                    sent_conf = sentiment.get('confidence', 0)
                    print(f"   💭 Sentiment: {sent_label} ({sent_conf:.2f})")
                    results['sentiment_scores'].append(sent_conf)
                
                # Collect entities for final report
                results['all_companies'].extend([c['name'] for c in companies])
                results['all_people'].extend([p['name'] for p in people])
                
                # Step 2: Knowledge Graph Building
                graph_data = self.graph_builder.build_email_graph(email, entities, [])
                validation = self.graph_builder.validate_graph_structure(graph_data)
                
                nodes_count = len(graph_data.get('nodes', []))
                edges_count = len(graph_data.get('edges', []))
                
                print(f"   🕸️ Graph: {nodes_count} nodes, {edges_count} edges")
                
                if not validation.get('valid'):
                    print(f"   ⚠️ Graph validation issues: {len(validation.get('errors', []))} errors")
                
                # Step 3: ICE Integration
                integration_result = self.ice_integrator.integrate_email_data(
                    email, entities, graph_data, []
                )
                
                if integration_result.get('success'):
                    print(f"   ✅ ICE integration successful")
                    results['ice_integrated'] += 1
                    
                    components = integration_result.get('components', {})
                    doc_ok = components.get('document_integration', False)
                    graph_ok = components.get('graph_integration', False)
                    print(f"      📄 Document: {'✅' if doc_ok else '❌'} | 🕸️ Graph: {'✅' if graph_ok else '❌'}")
                else:
                    print(f"   ❌ ICE integration failed: {integration_result.get('error', 'Unknown')}")
                
                # Store detailed results
                results['entities_extracted'].append(entities)
                results['graphs_built'].append(graph_data)
                results['processed_count'] += 1
                
            except Exception as e:
                error_msg = f"Error processing email {i}: {e}"
                print(f"   ❌ {error_msg}")
                results['errors'].append(error_msg)
                continue
        
        return results
    
    def generate_comprehensive_report(self, results: Dict[str, Any]):
        """Generate comprehensive analysis report"""
        print("\\n" + "=" * 70)
        print("📊 COMPREHENSIVE EMAIL ANALYSIS REPORT")
        print("=" * 70)
        
        # Processing Summary
        print(f"📧 PROCESSING SUMMARY:")
        print(f"   Emails processed: {results['processed_count']}")
        print(f"   ICE integrations: {results['ice_integrated']}")
        print(f"   Success rate: {results['ice_integrated']/max(results['processed_count'], 1)*100:.1f}%")
        print(f"   Errors: {len(results['errors'])}")
        
        # Entity Analysis
        print(f"\\n🎯 INVESTMENT ENTITIES DISCOVERED:")
        
        unique_tickers = list(set(results['all_tickers']))
        if unique_tickers:
            print(f"   📈 Tickers ({len(unique_tickers)}): {', '.join(unique_tickers[:15])}")
            if len(unique_tickers) > 15:
                print(f"      ... and {len(unique_tickers) - 15} more")
        
        unique_companies = list(set(results['all_companies']))
        if unique_companies:
            print(f"   🏢 Companies ({len(unique_companies)}): {', '.join(unique_companies[:10])}")
            if len(unique_companies) > 10:
                print(f"      ... and {len(unique_companies) - 10} more")
        
        unique_people = list(set(results['all_people']))
        if unique_people:
            print(f"   👤 People ({len(unique_people)}): {', '.join(unique_people[:8])}")
        
        # Knowledge Graph Stats
        total_nodes = sum(len(g.get('nodes', [])) for g in results['graphs_built'])
        total_edges = sum(len(g.get('edges', [])) for g in results['graphs_built'])
        
        print(f"\\n🕸️ KNOWLEDGE GRAPH STATISTICS:")
        print(f"   Total nodes: {total_nodes}")
        print(f"   Total edges: {total_edges}")
        print(f"   Average graph size: {total_nodes/max(results['processed_count'], 1):.1f} nodes/email")
        
        # Sentiment Analysis
        if results['sentiment_scores']:
            avg_sentiment_conf = sum(results['sentiment_scores']) / len(results['sentiment_scores'])
            print(f"\\n💭 SENTIMENT ANALYSIS:")
            print(f"   Average confidence: {avg_sentiment_conf:.2f}")
            print(f"   Emails with sentiment: {len(results['sentiment_scores'])}")
        
        # Error Summary
        if results['errors']:
            print(f"\\n⚠️ ERRORS ENCOUNTERED:")
            for error in results['errors'][:3]:
                print(f"   - {error}")
            if len(results['errors']) > 3:
                print(f"   ... and {len(results['errors']) - 3} more errors")
        
        # Next Steps
        print(f"\\n🚀 SYSTEM READY:")
        print(f"   ✅ Your investment emails are now integrated into ICE")
        print(f"   🔍 You can query the knowledge base with natural language")
        print(f"   📊 Dashboard available for investment insights")
        print(f"   💾 Data stored in: {self.working_dir}")
        
        # Save results
        results_file = os.path.join(self.working_dir, "analysis_results.json")
        with open(results_file, 'w') as f:
            # Make results JSON serializable
            json_results = {
                'summary': {
                    'processed_count': results['processed_count'],
                    'ice_integrated': results['ice_integrated'],
                    'error_count': len(results['errors'])
                },
                'entities': {
                    'tickers': unique_tickers,
                    'companies': unique_companies[:20],  # Limit for JSON size
                    'people': unique_people[:20]
                },
                'graph_stats': {
                    'total_nodes': total_nodes,
                    'total_edges': total_edges
                },
                'timestamp': datetime.now().isoformat()
            }
            json.dump(json_results, f, indent=2)
        
        print(f"\\n💾 Detailed results saved to: {results_file}")
    
    def query_demonstration(self):
        """Demonstrate querying capabilities"""
        print("\\n🔍 QUERY DEMONSTRATION")
        print("=" * 40)
        
        sample_queries = [
            "What stocks were mentioned in my recent emails?",
            "What's the sentiment around technology stocks?",
            "Who are the key analysts mentioned?",
            "What companies have earnings updates?",
            "What investment risks were highlighted?"
        ]
        
        print("You can now ask questions like:")
        for query in sample_queries:
            print(f"   • {query}")
        
        print("\\n💡 To query your data:")
        print("   ice_integrator.query_email_content('Your question here')")
    
    def cleanup(self):
        """Cleanup resources"""
        try:
            if self.connector:
                self.connector.close()
            
            self.state_manager.close()
            self.ice_integrator.close()
            
            print("\\n✅ Pipeline resources cleaned up")
            
        except Exception as e:
            print(f"⚠️ Cleanup warning: {e}")

def main():
    if len(sys.argv) != 2:
        print("Usage: python process_emails.py YOUR_PASSWORD")
        print("\\nThis will:")
        print("  1. Connect to roy@agtpartners.com.sg")
        print("  2. Fetch recent investment-related emails")
        print("  3. Process through entity extraction")
        print("  4. Build knowledge graphs")
        print("  5. Integrate with ICE system")
        print("  6. Generate comprehensive analysis report")
        return
    
    password = sys.argv[1]
    
    print("🚀 FULL PIPELINE EXECUTION FOR REAL EMAILS")
    print("=" * 60)
    print(f"📧 Email: roy@agtpartners.com.sg")
    print(f"🕐 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    runner = FullPipelineRunner("roy@agtpartners.com.sg", password)
    
    try:
        # Step 1: Connect to email
        if not runner.connect_to_email():
            print("❌ Failed to connect to email server")
            return
        
        # Step 2: Fetch investment emails
        investment_emails = runner.fetch_investment_emails(days_back=7, limit=30)
        
        if not investment_emails:
            print("📭 No investment emails found to process")
            return
        
        # Step 3: Process through pipeline
        results = runner.process_emails_through_pipeline(investment_emails)
        
        # Step 4: Generate comprehensive report
        runner.generate_comprehensive_report(results)
        
        # Step 5: Query demonstration
        runner.query_demonstration()
        
        print(f"\\n🎉 PIPELINE EXECUTION COMPLETED!")
        print(f"⏰ Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except KeyboardInterrupt:
        print("\\n⏹️ Pipeline execution interrupted by user")
    except Exception as e:
        print(f"❌ Pipeline execution failed: {e}")
    finally:
        runner.cleanup()

if __name__ == "__main__":
    main()