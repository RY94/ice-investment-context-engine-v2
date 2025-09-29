# imap_email_ingestion_pipeline/pipeline.py
# Main email ingestion pipeline orchestrator for ICE system
# Coordinates email fetching, processing, and knowledge graph integration
# RELEVANT FILES: email_connector.py, email_processor.py, ice_integration.py

import logging
from typing import List, Dict, Any
from email_connector import EmailConnector
from email_processor import EmailProcessor
from ice_integration import ICEEmailIntegrator

class EmailIngestionPipeline:
    def __init__(self, email: str, password: str):
        self.email = email
        self.password = password
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.connector = EmailConnector(email, password)
        self.processor = EmailProcessor()
        self.integrator = ICEEmailIntegrator()
        
        self.logger.info("Email ingestion pipeline initialized")
    
    def run_pipeline(self, limit: int = 10) -> Dict[str, Any]:
        """Run the complete email ingestion pipeline"""
        results = {
            'fetched': 0,
            'processed': 0,
            'ingested': 0,
            'errors': []
        }
        
        try:
            # Step 1: Fetch emails
            self.logger.info(f"Fetching {limit} recent emails...")
            emails = self.connector.fetch_recent_emails(limit=limit)
            results['fetched'] = len(emails)
            
            if not emails:
                self.logger.warning("No emails fetched")
                return results
            
            # Step 2: Process emails
            self.logger.info(f"Processing {len(emails)} emails...")
            for email_data in emails:
                try:
                    # Process email content
                    processed = self.processor.process_email(email_data)
                    
                    if 'error' not in processed:
                        results['processed'] += 1
                        
                        # Step 3: Ingest into ICE
                        if self.integrator.ingest_email(processed):
                            results['ingested'] += 1
                        else:
                            results['errors'].append(f"Failed to ingest email {email_data['id']}")
                    else:
                        results['errors'].append(f"Failed to process email {email_data['id']}: {processed['error']}")
                        
                except Exception as e:
                    error_msg = f"Pipeline error for email {email_data.get('id', 'unknown')}: {e}"
                    results['errors'].append(error_msg)
                    self.logger.error(error_msg)
            
            self.logger.info(f"Pipeline complete: {results['ingested']}/{results['fetched']} emails ingested")
            
        except Exception as e:
            error_msg = f"Pipeline failed: {e}"
            results['errors'].append(error_msg)
            self.logger.error(error_msg)
        
        finally:
            self.connector.close()
        
        return results
    
    def test_connection(self) -> bool:
        """Test email connection"""
        return self.connector.connect()

def main():
    """Main function for running the pipeline"""
    # Email credentials (should be environment variables in production)
    EMAIL = "roy@agtpartners.com.sg"
    PASSWORD = "01jan1994!"
    
    # Initialize and run pipeline
    pipeline = EmailIngestionPipeline(EMAIL, PASSWORD)
    
    # Test connection first
    if pipeline.test_connection():
        print("✓ Email connection successful")
        
        # Run pipeline
        results = pipeline.run_pipeline(limit=5)  # Start with 5 emails
        
        print(f"\nPipeline Results:")
        print(f"Emails fetched: {results['fetched']}")
        print(f"Emails processed: {results['processed']}")
        print(f"Emails ingested: {results['ingested']}")
        
        if results['errors']:
            print(f"\nErrors ({len(results['errors'])}):")
            for error in results['errors']:
                print(f"- {error}")
    else:
        print("✗ Email connection failed")

if __name__ == "__main__":
    main()