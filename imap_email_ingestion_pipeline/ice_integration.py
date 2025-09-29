# imap_email_ingestion_pipeline/ice_integration.py
# Integration layer between email pipeline and ICE knowledge graph
# Feeds processed email content into LightRAG system
# RELEVANT FILES: ice_lightrag/ice_rag.py, email_processor.py

import os
import sys
from typing import Dict, Any
import logging

# Add parent directory to path to import ICE modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from ice_lightrag.ice_rag import ICELightRAG
except ImportError:
    logging.warning("ICELightRAG not available - using mock integration")
    ICELightRAG = None

class ICEEmailIntegrator:
    def __init__(self, working_dir="./ice_lightrag/storage"):
        self.logger = logging.getLogger(__name__)
        self.working_dir = working_dir
        
        if ICELightRAG:
            try:
                self.ice_rag = ICELightRAG(working_dir=working_dir)
                self.logger.info("ICE LightRAG integration initialized")
            except Exception as e:
                self.logger.warning(f"Failed to initialize ICE LightRAG: {e}")
                self.ice_rag = None
        else:
            self.ice_rag = None
    
    def ingest_email(self, processed_email: Dict[str, Any]) -> bool:
        """Ingest processed email into ICE knowledge graph"""
        try:
            if not processed_email or 'error' in processed_email:
                return False
            
            # Create document text for LightRAG
            email_doc = self._create_document(processed_email)
            
            if self.ice_rag:
                # Insert into LightRAG
                self.ice_rag.insert(email_doc)
                self.logger.info(f"Email {processed_email['id']} ingested into ICE")
                return True
            else:
                # Mock ingestion for testing
                self.logger.info(f"Mock ingestion: Email {processed_email['id']}")
                return True
                
        except Exception as e:
            self.logger.error(f"Ingestion failed for email {processed_email.get('id', 'unknown')}: {e}")
            return False
    
    def _create_document(self, processed_email: Dict[str, Any]) -> str:
        """Create formatted document for LightRAG ingestion"""
        metadata = processed_email['metadata']
        content = processed_email['content']
        entities = processed_email['entities']
        
        doc_lines = []
        doc_lines.append(f"EMAIL: {metadata['subject']}")
        doc_lines.append(f"FROM: {metadata['from']}")
        doc_lines.append(f"DATE: {metadata['date']}")
        doc_lines.append("")
        
        # Add entity context
        if entities['tickers']:
            doc_lines.append(f"TICKERS MENTIONED: {', '.join(entities['tickers'])}")
        
        if entities['prices']:
            doc_lines.append(f"PRICES: {', '.join(entities['prices'])}")
        
        if processed_email.get('topics'):
            doc_lines.append(f"TOPICS: {', '.join(processed_email['topics'])}")
        
        doc_lines.append("")
        doc_lines.append("CONTENT:")
        doc_lines.append(content['body'])
        
        return "\n".join(doc_lines)
    
    def query_emails(self, query: str) -> str:
        """Query the email knowledge base"""
        if self.ice_rag:
            try:
                result = self.ice_rag.query(query)
                return result
            except Exception as e:
                self.logger.error(f"Query failed: {e}")
                return f"Query failed: {e}"
        else:
            return "ICE LightRAG not available"