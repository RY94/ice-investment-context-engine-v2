# imap_email_ingestion_pipeline/ice_integrator.py
# Enhanced ICE integration layer for email pipeline
# Feeds email content and graph data into LightRAG system with batch processing
# RELEVANT FILES: graph_builder.py, state_manager.py, entity_extractor.py, enhanced_doc_creator.py

import os
import sys
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

# Import enhanced document creator (Week 1.5 addition)
# Support both package import (relative) and direct import (absolute)
try:
    from .enhanced_doc_creator import create_enhanced_document
except ImportError:
    from enhanced_doc_creator import create_enhanced_document

# Add parent directory to path to import ICE modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from ice_lightrag.ice_rag import ICELightRAG
    ICE_LIGHTRAG_AVAILABLE = True
except ImportError:
    ICE_LIGHTRAG_AVAILABLE = False
    logging.warning("ICE LightRAG not available - using mock integration")

class ICEEmailIntegrator:
    def __init__(self, working_dir: str = "./ice_lightrag/storage", batch_size: int = 10):
        self.logger = logging.getLogger(__name__)
        self.working_dir = Path(working_dir)
        self.batch_size = batch_size
        
        # Initialize ICE LightRAG
        self.ice_rag = None
        if ICE_LIGHTRAG_AVAILABLE:
            try:
                self.working_dir.mkdir(parents=True, exist_ok=True)
                self.ice_rag = ICELightRAG(working_dir=str(self.working_dir))
                self.logger.info("ICE LightRAG integration initialized")
            except Exception as e:
                self.logger.error(f"Failed to initialize ICE LightRAG: {e}")
                self.ice_rag = None
        
        # Batch processing
        self.document_batch = []
        self.graph_batch = []
        
        # Statistics
        self.stats = {
            'documents_processed': 0,
            'graphs_processed': 0,
            'batch_operations': 0,
            'errors': 0,
            'last_processed': None
        }
    
    def integrate_email_data(self, email_data: Dict[str, Any],
                           extracted_entities: Dict[str, Any],
                           graph_data: Dict[str, Any],
                           attachments_data: List[Dict[str, Any]] = None,
                           use_enhanced: bool = True,
                           save_graph_json: bool = False) -> Dict[str, Any]:
        """
        Integrate complete email data into ICE system

        Args:
            email_data: Email metadata and content
            extracted_entities: EntityExtractor output with confidence scores
            graph_data: GraphBuilder output
            attachments_data: List of attachment data (optional)
            use_enhanced: If True, use enhanced documents with inline markup (Week 1.5 feature)
            save_graph_json: If True, save graph data as JSON files (legacy feature, defaults to False)

        Returns:
            Integration result dictionary with success status and component results
        """
        try:
            integration_result = {
                'email_uid': email_data.get('uid'),
                'processed_at': datetime.now().isoformat(),
                'success': False,
                'components': {
                    'document_integration': False,
                    'graph_integration': False,
                    'attachment_integration': False
                },
                'errors': []
            }
            
            # 1. Create document for LightRAG (enhanced or plain)
            if use_enhanced:
                # Week 1.5: Use enhanced documents with inline markup
                email_document = self._create_enhanced_document(
                    email_data, extracted_entities, graph_data
                )
            else:
                # Legacy: Use plain comprehensive documents
                email_document = self._create_comprehensive_document(
                    email_data, extracted_entities, attachments_data
                )

            if email_document:
                doc_result = self._integrate_document(email_document)
                integration_result['components']['document_integration'] = doc_result['success']
                if not doc_result['success']:
                    integration_result['errors'].append(f"Document integration failed: {doc_result.get('error')}")

            # 2. Integrate graph structure (optional - Week 1.5: defaults to False)
            if save_graph_json and graph_data and graph_data.get('nodes'):
                graph_result = self._integrate_graph_data(graph_data)
                integration_result['components']['graph_integration'] = graph_result['success']
                if not graph_result['success']:
                    integration_result['errors'].append(f"Graph integration failed: {graph_result.get('error')}")
            
            # 3. Integrate attachment content separately
            if attachments_data:
                attachment_result = self._integrate_attachments(attachments_data, email_data.get('uid'))
                integration_result['components']['attachment_integration'] = attachment_result['success']
                if not attachment_result['success']:
                    integration_result['errors'].append(f"Attachment integration failed: {attachment_result.get('error')}")
            
            # Update statistics
            integration_result['success'] = any(integration_result['components'].values())
            if integration_result['success']:
                self.stats['documents_processed'] += 1
                self.stats['last_processed'] = datetime.now().isoformat()
            else:
                self.stats['errors'] += 1
            
            self.logger.info(f"Integrated email {email_data.get('uid')}: {integration_result['success']}")
            return integration_result
            
        except Exception as e:
            error_msg = f"Integration failed for email {email_data.get('uid', 'unknown')}: {e}"
            self.logger.error(error_msg)
            self.stats['errors'] += 1
            return {
                'success': False,
                'error': error_msg,
                'email_uid': email_data.get('uid')
            }
    
    def _create_comprehensive_document(self, email_data: Dict[str, Any],
                                     entities: Dict[str, Any],
                                     attachments_data: List[Dict[str, Any]] = None) -> Optional[str]:
        """Create comprehensive document structure for LightRAG"""
        try:
            doc_sections = []
            
            # Email metadata section
            doc_sections.append("=== EMAIL METADATA ===")
            doc_sections.append(f"Subject: {email_data.get('subject', '')}")
            doc_sections.append(f"From: {email_data.get('from', '')}")
            doc_sections.append(f"Date: {email_data.get('date', '')}")
            doc_sections.append(f"Message ID: {email_data.get('message_id', '')}")
            doc_sections.append(f"Priority: {email_data.get('priority', 0)}")
            doc_sections.append("")
            
            # Extracted entities section
            if entities:
                doc_sections.append("=== EXTRACTED ENTITIES ===")
                
                # Tickers
                tickers = entities.get('tickers', [])
                if tickers:
                    ticker_list = [t['ticker'] for t in tickers if t.get('confidence', 0) > 0.5]
                    doc_sections.append(f"Tickers Mentioned: {', '.join(ticker_list)}")
                
                # Companies
                companies = entities.get('companies', [])
                if companies:
                    company_list = [c['company'] for c in companies if c.get('confidence', 0) > 0.5]
                    doc_sections.append(f"Companies Discussed: {', '.join(company_list)}")
                
                # People
                people = entities.get('people', [])
                if people:
                    people_list = [p['name'] for p in people if p.get('confidence', 0) > 0.5]
                    doc_sections.append(f"People Mentioned: {', '.join(people_list)}")
                
                # Topics
                topics = entities.get('topics', [])
                if topics:
                    doc_sections.append(f"Topics: {', '.join(topics)}")
                
                # Sentiment
                sentiment = entities.get('sentiment', {})
                if sentiment and sentiment.get('confidence', 0) > 0.5:
                    doc_sections.append(f"Sentiment: {sentiment['sentiment']} (confidence: {sentiment['confidence']:.2f})")
                
                # Financial metrics
                metrics = entities.get('financial_metrics', {})
                if metrics:
                    for metric_type, metric_list in metrics.items():
                        values = [m['value'] for m in metric_list if m.get('confidence', 0) > 0.5]
                        if values:
                            doc_sections.append(f"{metric_type.title()}: {', '.join(values)}")
                
                doc_sections.append("")
            
            # Email body section
            if email_data.get('body'):
                doc_sections.append("=== EMAIL CONTENT ===")
                doc_sections.append(email_data['body'])
                doc_sections.append("")
            
            # Attachments section
            if attachments_data:
                doc_sections.append("=== ATTACHMENTS ===")
                for attachment in attachments_data:
                    if not attachment.get('error'):
                        doc_sections.append(f"File: {attachment.get('filename', 'unknown')}")
                        doc_sections.append(f"Type: {attachment.get('mime_type', 'unknown')}")
                        doc_sections.append(f"Size: {attachment.get('file_size', 0)} bytes")
                        
                        # Include extracted text if available and not too long
                        extracted_text = attachment.get('extracted_text', '')
                        if extracted_text and len(extracted_text) < 5000:  # Limit to prevent huge docs
                            doc_sections.append("Content:")
                            doc_sections.append(extracted_text[:2000])  # Truncate if very long
                            if len(extracted_text) > 2000:
                                doc_sections.append("... [content truncated] ...")
                        
                        doc_sections.append("")
            
            # Investment context section
            doc_sections.append("=== INVESTMENT CONTEXT ===")
            doc_sections.append(f"Source: Email from {email_data.get('from', 'unknown sender')}")
            doc_sections.append(f"Received: {email_data.get('date', 'unknown date')}")
            doc_sections.append(f"Analysis Confidence: {entities.get('confidence', 0.0):.2f}")
            
            # Create final document
            comprehensive_doc = "\n".join(doc_sections)

            return comprehensive_doc
            
        except Exception as e:
            self.logger.error(f"Error creating comprehensive document: {e}")
            return None

    def _create_enhanced_document(self, email_data: Dict[str, Any],
                                  entities: Dict[str, Any],
                                  graph_data: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        Create enhanced document with inline metadata markup for LightRAG.

        Week 1.5 Addition: Wrapper around enhanced_doc_creator.create_enhanced_document()
        that preserves EntityExtractor precision while using single LightRAG graph.

        This method replaces the dual-graph approach by injecting custom extractions
        as structured markup within the document text before LightRAG ingestion.

        Args:
            email_data: Email metadata (uid, from, date, subject, body, attachments, etc.)
            entities: EntityExtractor output with confidence scores
            graph_data: Optional GraphBuilder output (for future use)

        Returns:
            Enhanced document string with inline markup, or None if creation fails

        Example markup in output:
            [SOURCE_EMAIL:12345|sender:analyst@gs.com|date:2024-01-15]
            [TICKER:NVDA|confidence:0.95] [RATING:BUY|confidence:0.87]
            Original email body text...
        """
        try:
            # Use the enhanced_doc_creator module function
            enhanced_doc = create_enhanced_document(email_data, entities, graph_data)

            if enhanced_doc:
                self.logger.info(
                    f"Created enhanced document for email {email_data.get('uid')}: "
                    f"{len(enhanced_doc)} bytes with inline markup"
                )
            else:
                self.logger.warning(f"Failed to create enhanced document for email {email_data.get('uid')}")

            return enhanced_doc

        except Exception as e:
            self.logger.error(f"Error creating enhanced document: {e}", exc_info=True)
            return None

    def _integrate_document(self, document: str) -> Dict[str, Any]:
        """Integrate document into LightRAG"""
        try:
            if not self.ice_rag:
                # Mock integration for testing
                return {
                    'success': True,
                    'method': 'mock',
                    'document_length': len(document)
                }
            
            # Insert document into LightRAG
            self.ice_rag.insert(document)
            
            return {
                'success': True,
                'method': 'lightrag_insert',
                'document_length': len(document)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'method': 'lightrag_insert_failed'
            }
    
    def _integrate_graph_data(self, graph_data: Dict[str, Any]) -> Dict[str, Any]:
        """Integrate graph structure (for future graph-aware queries)"""
        try:
            # For now, store graph data as metadata
            # In future, this could integrate with NetworkX or other graph databases
            
            graph_storage_dir = self.working_dir / "graphs"
            graph_storage_dir.mkdir(exist_ok=True)
            
            email_uid = graph_data.get('metadata', {}).get('email_uid', 'unknown')
            graph_file = graph_storage_dir / f"email_{email_uid}_graph.json"
            
            with open(graph_file, 'w') as f:
                json.dump(graph_data, f, indent=2, default=str)
            
            return {
                'success': True,
                'method': 'json_storage',
                'graph_file': str(graph_file),
                'nodes': len(graph_data.get('nodes', [])),
                'edges': len(graph_data.get('edges', []))
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'method': 'graph_integration_failed'
            }
    
    def _integrate_attachments(self, attachments_data: List[Dict[str, Any]], 
                             email_uid: str) -> Dict[str, Any]:
        """Integrate attachment content separately"""
        try:
            integrated_count = 0
            total_attachments = len(attachments_data)
            
            for attachment in attachments_data:
                if attachment.get('error'):
                    continue
                
                # Create separate document for each significant attachment
                extracted_text = attachment.get('extracted_text', '')
                if len(extracted_text) > 100:  # Only process attachments with meaningful content
                    
                    attachment_doc = self._create_attachment_document(attachment, email_uid)
                    
                    if attachment_doc:
                        doc_result = self._integrate_document(attachment_doc)
                        if doc_result['success']:
                            integrated_count += 1
            
            return {
                'success': integrated_count > 0,
                'method': 'attachment_documents',
                'integrated': integrated_count,
                'total': total_attachments
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'method': 'attachment_integration_failed'
            }
    
    def _create_attachment_document(self, attachment: Dict[str, Any], email_uid: str) -> Optional[str]:
        """Create document structure for attachment content"""
        try:
            doc_sections = []
            
            # Attachment metadata
            doc_sections.append("=== ATTACHMENT DOCUMENT ===")
            doc_sections.append(f"Source Email UID: {email_uid}")
            doc_sections.append(f"Filename: {attachment.get('filename', 'unknown')}")
            doc_sections.append(f"File Type: {attachment.get('mime_type', 'unknown')}")
            doc_sections.append(f"File Size: {attachment.get('file_size', 0)} bytes")
            doc_sections.append(f"Extraction Method: {attachment.get('extraction_method', 'unknown')}")
            
            ocr_confidence = attachment.get('ocr_confidence', 0)
            if ocr_confidence > 0:
                doc_sections.append(f"OCR Confidence: {ocr_confidence:.2f}")
            
            doc_sections.append("")
            
            # Extracted content
            extracted_text = attachment.get('extracted_text', '')
            if extracted_text:
                doc_sections.append("=== EXTRACTED CONTENT ===")
                doc_sections.append(extracted_text)
            
            return "\n".join(doc_sections)
            
        except Exception as e:
            self.logger.warning(f"Error creating attachment document: {e}")
            return None
    
    def batch_integrate_emails(self, email_batch: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process multiple emails in batch for efficiency"""
        try:
            batch_results = {
                'total_emails': len(email_batch),
                'successful': 0,
                'failed': 0,
                'errors': [],
                'processed_at': datetime.now().isoformat()
            }
            
            batch_documents = []
            
            for email_package in email_batch:
                try:
                    # Each email package contains email_data, entities, graph_data, attachments
                    email_data = email_package['email_data']
                    entities = email_package.get('entities', {})
                    attachments = email_package.get('attachments', [])
                    
                    # Create document
                    doc = self._create_comprehensive_document(email_data, entities, attachments)
                    if doc:
                        batch_documents.append(doc)
                        batch_results['successful'] += 1
                    else:
                        batch_results['failed'] += 1
                        batch_results['errors'].append(f"Failed to create document for {email_data.get('uid')}")
                        
                except Exception as e:
                    batch_results['failed'] += 1
                    batch_results['errors'].append(f"Error processing email: {e}")
            
            # Batch insert documents
            if batch_documents and self.ice_rag:
                try:
                    for doc in batch_documents:
                        self.ice_rag.insert(doc)
                    
                    self.stats['batch_operations'] += 1
                    self.logger.info(f"Batch processed {len(batch_documents)} email documents")
                    
                except Exception as e:
                    self.logger.error(f"Batch insertion failed: {e}")
                    batch_results['errors'].append(f"Batch insertion failed: {e}")
            
            return batch_results
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'total_emails': len(email_batch) if email_batch else 0
            }
    
    def query_email_content(self, query: str, mode: str = "hybrid") -> Dict[str, Any]:
        """Query the integrated email content"""
        try:
            if not self.ice_rag:
                return {
                    'success': False,
                    'error': 'ICE LightRAG not available',
                    'query': query
                }
            
            # Query LightRAG
            result = self.ice_rag.query(query, mode=mode)
            
            return {
                'success': True,
                'query': query,
                'mode': mode,
                'result': result,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'query': query
            }
    
    def get_integration_statistics(self) -> Dict[str, Any]:
        """Get comprehensive integration statistics"""
        try:
            # Calculate storage usage
            storage_stats = self._calculate_storage_usage()
            
            # Get LightRAG stats if available
            lightrag_stats = {}
            if self.ice_rag:
                try:
                    # This would depend on LightRAG's internal stats methods
                    lightrag_stats = {'status': 'available'}
                except:
                    lightrag_stats = {'status': 'limited_access'}
            
            return {
                'processing_stats': self.stats.copy(),
                'storage_stats': storage_stats,
                'lightrag_stats': lightrag_stats,
                'batch_size': self.batch_size,
                'working_directory': str(self.working_dir),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _calculate_storage_usage(self) -> Dict[str, Any]:
        """Calculate storage usage statistics"""
        try:
            total_size = 0
            file_count = 0
            
            if self.working_dir.exists():
                for file_path in self.working_dir.rglob('*'):
                    if file_path.is_file():
                        file_count += 1
                        total_size += file_path.stat().st_size
            
            return {
                'total_size_mb': total_size / (1024 * 1024),
                'file_count': file_count,
                'working_directory': str(self.working_dir)
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def cleanup_old_data(self, days_old: int = 90):
        """Clean up old graph data files"""
        try:
            from datetime import timedelta
            
            cutoff_date = datetime.now() - timedelta(days=days_old)
            cleaned_count = 0
            
            graph_dir = self.working_dir / "graphs"
            if graph_dir.exists():
                for graph_file in graph_dir.glob("email_*_graph.json"):
                    file_mtime = datetime.fromtimestamp(graph_file.stat().st_mtime)
                    if file_mtime < cutoff_date:
                        graph_file.unlink()
                        cleaned_count += 1
            
            self.logger.info(f"Cleaned up {cleaned_count} old graph files")
            
        except Exception as e:
            self.logger.error(f"Error cleaning up old data: {e}")
    
    def flush_batch(self):
        """Flush any pending batch operations"""
        try:
            if self.document_batch:
                self.logger.info(f"Flushing {len(self.document_batch)} pending documents")
                self.document_batch.clear()
            
            if self.graph_batch:
                self.logger.info(f"Flushing {len(self.graph_batch)} pending graphs")  
                self.graph_batch.clear()
                
        except Exception as e:
            self.logger.error(f"Error flushing batch: {e}")
    
    def close(self):
        """Close integrator and clean up resources"""
        try:
            self.flush_batch()
            self.logger.info("ICE Email Integrator closed")
        except Exception as e:
            self.logger.error(f"Error closing integrator: {e}")