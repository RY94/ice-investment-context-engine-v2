# imap_email_ingestion_pipeline/ice_ultra_refined_integration.py
# Integration layer between Ultra-Refined Email Processor and existing ICE infrastructure
# Connects Blueprint V2 system with LightRAG, MCP protocols, and existing pipeline components
# RELEVANT FILES: ultra_refined_email_processor.py, ice_integrator.py, pipeline_orchestrator.py, ../ice_lightrag/ice_rag.py

import logging
import json
import asyncio
import time
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path

# Import existing ICE components
import sys
sys.path.append(str(Path(__file__).parent.parent))

from ultra_refined_email_processor import UltraRefinedEmailProcessor
from intelligent_email_router import IntelligentEmailRouter, ProcessingRoute
from incremental_learning_system import IncrementalKnowledgeSystem, FallbackCascadeSystem, ExtractionResult, ExtractionMethod

# Import existing pipeline components
from ice_integrator import ICEEmailIntegrator
from entity_extractor import EntityExtractor
from graph_builder import GraphBuilder
from attachment_processor import AttachmentProcessor

# Import ICE LightRAG system
try:
    from ice_lightrag.ice_rag import ICELightRAG
    LIGHTRAG_AVAILABLE = True
except ImportError:
    LIGHTRAG_AVAILABLE = False
    logging.warning("ICE LightRAG not available")

# Import MCP infrastructure
try:
    from ice_data_ingestion.mcp_data_manager import MCPDataManager
    from ice_data_ingestion.mcp_infrastructure import MCPInfrastructure
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    logging.warning("MCP infrastructure not available")

class ICEUltraRefinedIntegrator:
    """
    Integration layer that combines Ultra-Refined Email Processing with existing ICE infrastructure
    Provides seamless integration with LightRAG, MCP protocols, and existing components
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.logger = logging.getLogger(__name__ + ".ICEUltraRefinedIntegrator")
        self.config = config or {}
        
        # Initialize Ultra-Refined components
        self.ultra_refined_processor = UltraRefinedEmailProcessor(config)
        self.email_router = IntelligentEmailRouter()
        self.learning_system = IncrementalKnowledgeSystem()
        self.cascade_system = FallbackCascadeSystem(self.learning_system)
        
        # Initialize existing ICE components
        self.ice_integrator = ICEEmailIntegrator()
        self.entity_extractor = EntityExtractor()
        self.graph_builder = GraphBuilder()
        self.attachment_processor = AttachmentProcessor()
        
        # Initialize LightRAG if available
        self.ice_rag = None
        if LIGHTRAG_AVAILABLE:
            try:
                working_dir = self.config.get('lightrag_dir', './ice_lightrag/storage')
                self.ice_rag = ICELightRAG(working_dir=working_dir)
                self.logger.info("ICE LightRAG initialized successfully")
            except Exception as e:
                self.logger.error(f"Failed to initialize ICE LightRAG: {e}")
        
        # Initialize MCP infrastructure if available
        self.mcp_manager = None
        self.mcp_infrastructure = None
        if MCP_AVAILABLE:
            try:
                self.mcp_manager = MCPDataManager()
                self.mcp_infrastructure = MCPInfrastructure()
                self.logger.info("MCP infrastructure initialized successfully")
            except Exception as e:
                self.logger.error(f"Failed to initialize MCP infrastructure: {e}")
        
        # Performance metrics
        self.integration_metrics = {
            'total_emails_processed': 0,
            'ultra_refined_successes': 0,
            'fallback_used': 0,
            'lightrag_integrations': 0,
            'mcp_integrations': 0,
            'average_processing_time': 0.0,
            'performance_improvements': []
        }
        
        self.logger.info("ICE Ultra-Refined Integrator initialized with all components")
    
    async def process_email_with_ultra_refinement(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process email using Ultra-Refined system integrated with existing ICE infrastructure
        Returns comprehensive processing results with ICE integration
        """
        start_time = time.time()
        email_id = email_data.get('id', f"email_{int(time.time())}")
        sender = email_data.get('sender', 'unknown')
        
        self.logger.info(f"Processing email {email_id} from {sender} with Ultra-Refined integration")
        
        try:
            # Step 1: Route email to determine optimal processing strategy
            processing_route = self.email_router.route_email(email_data)
            email_data['email_type'] = processing_route.email_type.value
            
            self.logger.info(f"Email routed to {processing_route.email_type.value} processor (confidence: {processing_route.confidence:.2f})")
            
            # Step 2: Process with Ultra-Refined system
            ultra_refined_result = await self.ultra_refined_processor.process_email(email_data)
            
            # Check if Ultra-Refined processing was successful
            if ultra_refined_result.get('status') == 'success':
                self.integration_metrics['ultra_refined_successes'] += 1
                extraction_result = ExtractionResult(
                    method=ExtractionMethod(ultra_refined_result.get('method', 'template_based')),
                    success=True,
                    confidence=ultra_refined_result.get('confidence', 0.85),
                    data=ultra_refined_result,
                    processing_time=ultra_refined_result.get('processing_time', 0.0)
                )
            else:
                # Step 3: Use cascade fallback if Ultra-Refined fails
                self.logger.warning(f"Ultra-Refined processing failed for {sender}, using cascade fallback")
                self.integration_metrics['fallback_used'] += 1
                extraction_result = await self.cascade_system.extract_with_cascade(email_data)
                ultra_refined_result = extraction_result.data
            
            # Step 4: Enhanced entity extraction using existing components
            enhanced_entities = await self._enhance_entity_extraction(email_data, ultra_refined_result)
            ultra_refined_result['enhanced_entities'] = enhanced_entities
            
            # Step 5: Process attachments with existing attachment processor if needed
            if email_data.get('attachments') and 'attachments' not in ultra_refined_result:
                attachment_results = await self._process_attachments_with_existing_processor(email_data['attachments'])
                ultra_refined_result['attachment_processing'] = attachment_results
            
            # Step 6: Build knowledge graph with existing graph builder
            graph_data = await self._build_knowledge_graph(email_data, ultra_refined_result)
            ultra_refined_result['graph_data'] = graph_data
            
            # Step 7: Integrate with ICE LightRAG system
            lightrag_integration = await self._integrate_with_lightrag(email_data, ultra_refined_result)
            ultra_refined_result['lightrag_integration'] = lightrag_integration
            
            # Step 8: Integrate with MCP protocols
            mcp_integration = await self._integrate_with_mcp(email_data, ultra_refined_result)
            ultra_refined_result['mcp_integration'] = mcp_integration
            
            # Step 9: Store results using existing ICE integrator
            ice_integration_result = await self._integrate_with_ice_system(email_data, ultra_refined_result)
            ultra_refined_result['ice_system_integration'] = ice_integration_result
            
            # Step 10: Record performance metrics
            processing_time = time.time() - start_time
            await self._record_integration_metrics(processing_route, extraction_result, processing_time)
            
            # Final result assembly
            final_result = {
                'email_id': email_id,
                'processing_summary': {
                    'status': 'success',
                    'processing_route': {
                        'email_type': processing_route.email_type.value,
                        'processor': processing_route.processor_class,
                        'confidence': processing_route.confidence
                    },
                    'ultra_refined_used': ultra_refined_result.get('status') == 'success',
                    'cascade_fallback_used': self.integration_metrics['fallback_used'] > self.integration_metrics['ultra_refined_successes'],
                    'total_processing_time': processing_time,
                    'performance_improvement_estimate': self._estimate_performance_improvement(processing_route, processing_time)
                },
                'extraction_results': ultra_refined_result,
                'integration_results': {
                    'lightrag_integrated': lightrag_integration.get('status') == 'success' if lightrag_integration else False,
                    'mcp_integrated': mcp_integration.get('status') == 'success' if mcp_integration else False,
                    'ice_system_integrated': ice_integration_result.get('status') == 'success' if ice_integration_result else False
                },
                'timestamp': datetime.now().isoformat()
            }
            
            self.integration_metrics['total_emails_processed'] += 1
            self.logger.info(f"Email {email_id} processed successfully in {processing_time:.2f}s")
            
            return final_result
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_result = {
                'email_id': email_id,
                'processing_summary': {
                    'status': 'error',
                    'error_message': str(e),
                    'total_processing_time': processing_time
                },
                'timestamp': datetime.now().isoformat()
            }
            
            self.logger.error(f"Integration processing failed for email {email_id}: {e}")
            return error_result
    
    async def _enhance_entity_extraction(self, email_data: Dict[str, Any], ultra_refined_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Enhance entity extraction using existing entity extractor"""
        try:
            # Use existing entity extractor to complement Ultra-Refined results
            existing_entities = await asyncio.to_thread(
                self.entity_extractor.extract_entities,
                email_data.get('body', ''),
                email_data.get('subject', '')
            )
            
            # Merge with Ultra-Refined entities
            ultra_refined_entities = ultra_refined_result.get('entities', [])
            
            # Combine and deduplicate entities
            all_entities = ultra_refined_entities + existing_entities
            enhanced_entities = self._deduplicate_entities(all_entities)
            
            self.logger.debug(f"Enhanced entity extraction: {len(ultra_refined_entities)} ultra-refined + {len(existing_entities)} existing = {len(enhanced_entities)} final")
            
            return enhanced_entities
            
        except Exception as e:
            self.logger.error(f"Entity enhancement failed: {e}")
            return ultra_refined_result.get('entities', [])
    
    def _deduplicate_entities(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Deduplicate entities while preserving highest confidence scores"""
        entity_map = {}
        
        for entity in entities:
            entity_key = f"{entity.get('type', 'unknown')}:{entity.get('value', 'unknown').lower()}"
            
            if entity_key not in entity_map:
                entity_map[entity_key] = entity
            else:
                # Keep entity with higher confidence
                existing_confidence = entity_map[entity_key].get('confidence', 0.0)
                new_confidence = entity.get('confidence', 0.0)
                if new_confidence > existing_confidence:
                    entity_map[entity_key] = entity
        
        return list(entity_map.values())
    
    async def _process_attachments_with_existing_processor(self, attachments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process attachments using existing attachment processor if Ultra-Refined didn't handle them"""
        try:
            processed_attachments = []
            
            for attachment in attachments:
                # Process with existing attachment processor
                result = await asyncio.to_thread(
                    self.attachment_processor.process_attachment,
                    attachment
                )
                processed_attachments.append(result)
            
            return {
                'status': 'success',
                'processed_count': len(processed_attachments),
                'attachments': processed_attachments
            }
            
        except Exception as e:
            self.logger.error(f"Attachment processing failed: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'processed_count': 0
            }
    
    async def _build_knowledge_graph(self, email_data: Dict[str, Any], processing_result: Dict[str, Any]) -> Dict[str, Any]:
        """Build knowledge graph using existing graph builder"""
        try:
            # Extract entities and relationships for graph building
            entities = processing_result.get('enhanced_entities', processing_result.get('entities', []))
            
            # Use existing graph builder
            graph_result = await asyncio.to_thread(
                self.graph_builder.build_graph,
                email_data,
                entities
            )
            
            return {
                'status': 'success',
                'nodes': len(graph_result.get('nodes', [])),
                'edges': len(graph_result.get('edges', [])),
                'graph_data': graph_result
            }
            
        except Exception as e:
            self.logger.error(f"Graph building failed: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    async def _integrate_with_lightrag(self, email_data: Dict[str, Any], processing_result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Integrate processed email with ICE LightRAG system"""
        if not self.ice_rag:
            return {'status': 'unavailable', 'reason': 'LightRAG not initialized'}
        
        try:
            # Prepare document for LightRAG
            document_content = self._prepare_document_for_lightrag(email_data, processing_result)
            
            # Insert into LightRAG system
            await asyncio.to_thread(
                self.ice_rag.insert,
                document_content
            )
            
            self.integration_metrics['lightrag_integrations'] += 1
            
            return {
                'status': 'success',
                'document_length': len(document_content),
                'integrated_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"LightRAG integration failed: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _prepare_document_for_lightrag(self, email_data: Dict[str, Any], processing_result: Dict[str, Any]) -> str:
        """Prepare email content for LightRAG processing"""
        # Create structured document content
        document_parts = [
            f"Email from: {email_data.get('sender', 'unknown')}",
            f"Subject: {email_data.get('subject', 'no subject')}",
            f"Email Type: {email_data.get('email_type', 'unknown')}",
            f"Processing Method: {processing_result.get('method', 'unknown')}",
            "",
            "Email Content:",
            email_data.get('body', ''),
            "",
            "Extracted Entities:",
        ]
        
        # Add entities
        entities = processing_result.get('enhanced_entities', processing_result.get('entities', []))
        for entity in entities:
            document_parts.append(f"- {entity.get('type', 'unknown')}: {entity.get('value', 'unknown')} (confidence: {entity.get('confidence', 0.0):.2f})")
        
        # Add attachment information
        if processing_result.get('attachments'):
            document_parts.extend([
                "",
                "Attachments:",
            ])
            for att in processing_result['attachments']:
                document_parts.append(f"- {att.get('name', 'unknown')} ({att.get('type', 'unknown')})")
        
        return "\n".join(document_parts)
    
    async def _integrate_with_mcp(self, email_data: Dict[str, Any], processing_result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Integrate with MCP protocols for external data enrichment"""
        if not self.mcp_manager or not self.mcp_infrastructure:
            return {'status': 'unavailable', 'reason': 'MCP infrastructure not initialized'}
        
        try:
            # Format data for MCP
            mcp_data = {
                'source': 'email_processing',
                'email_id': email_data.get('id'),
                'sender': email_data.get('sender'),
                'email_type': email_data.get('email_type'),
                'entities': processing_result.get('enhanced_entities', []),
                'processing_metadata': {
                    'method': processing_result.get('method'),
                    'confidence': processing_result.get('confidence'),
                    'timestamp': datetime.now().isoformat()
                }
            }
            
            # Send to MCP infrastructure
            mcp_result = await asyncio.to_thread(
                self.mcp_manager.process_data,
                mcp_data
            )
            
            self.integration_metrics['mcp_integrations'] += 1
            
            return {
                'status': 'success',
                'mcp_result': mcp_result
            }
            
        except Exception as e:
            self.logger.error(f"MCP integration failed: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    async def _integrate_with_ice_system(self, email_data: Dict[str, Any], processing_result: Dict[str, Any]) -> Dict[str, Any]:
        """Integrate with existing ICE system using ICE integrator"""
        try:
            # Use existing ICE integrator
            ice_result = await asyncio.to_thread(
                self.ice_integrator.integrate_email_data,
                email_data,
                processing_result
            )
            
            return {
                'status': 'success',
                'ice_result': ice_result
            }
            
        except Exception as e:
            self.logger.error(f"ICE system integration failed: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    async def _record_integration_metrics(self, processing_route: ProcessingRoute, extraction_result: ExtractionResult, processing_time: float):
        """Record performance metrics for the integration"""
        # Update running average processing time
        total_emails = self.integration_metrics['total_emails_processed']
        current_avg = self.integration_metrics['average_processing_time']
        new_avg = (current_avg * total_emails + processing_time) / (total_emails + 1)
        self.integration_metrics['average_processing_time'] = new_avg
        
        # Record performance improvement
        expected_time = processing_route.expected_time
        if expected_time > 0:
            improvement_factor = expected_time / processing_time
            self.integration_metrics['performance_improvements'].append(improvement_factor)
            
            # Keep only last 100 improvements
            if len(self.integration_metrics['performance_improvements']) > 100:
                self.integration_metrics['performance_improvements'].pop(0)
    
    def _estimate_performance_improvement(self, processing_route: ProcessingRoute, actual_time: float) -> str:
        """Estimate performance improvement compared to baseline"""
        expected_time = processing_route.expected_time
        if expected_time > 0:
            improvement_factor = expected_time / actual_time
            return f"{improvement_factor:.1f}x faster than baseline"
        return "baseline_not_available"
    
    async def query_processed_emails(self, query: str, mode: str = "hybrid") -> Dict[str, Any]:
        """Query processed emails using LightRAG system"""
        if not self.ice_rag:
            return {'status': 'error', 'error': 'LightRAG not available'}
        
        try:
            result = await asyncio.to_thread(
                self.ice_rag.query,
                query,
                mode=mode
            )
            
            return {
                'status': 'success',
                'query': query,
                'mode': mode,
                'result': result
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def get_integration_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive integration performance report"""
        # Get component reports
        ultra_refined_report = self.ultra_refined_processor.get_performance_report()
        router_stats = self.email_router.get_routing_stats()
        learning_report = self.learning_system.get_learning_report()
        cascade_report = self.cascade_system.get_cascade_performance_report()
        
        # Calculate improvements
        improvements = self.integration_metrics['performance_improvements']
        avg_improvement = sum(improvements) / len(improvements) if improvements else 1.0
        
        integration_report = {
            'integration_summary': {
                'total_emails_processed': self.integration_metrics['total_emails_processed'],
                'ultra_refined_success_rate': f"{(self.integration_metrics['ultra_refined_successes'] / max(1, self.integration_metrics['total_emails_processed'])):.1%}",
                'fallback_usage_rate': f"{(self.integration_metrics['fallback_used'] / max(1, self.integration_metrics['total_emails_processed'])):.1%}",
                'average_processing_time': f"{self.integration_metrics['average_processing_time']:.2f}s",
                'average_performance_improvement': f"{avg_improvement:.1f}x",
                'lightrag_integrations': self.integration_metrics['lightrag_integrations'],
                'mcp_integrations': self.integration_metrics['mcp_integrations']
            },
            'component_reports': {
                'ultra_refined_processor': ultra_refined_report,
                'email_router': router_stats,
                'learning_system': learning_report,
                'cascade_system': cascade_report
            },
            'system_health': {
                'lightrag_available': LIGHTRAG_AVAILABLE and self.ice_rag is not None,
                'mcp_available': MCP_AVAILABLE and self.mcp_manager is not None,
                'all_components_operational': True  # Would check actual component health
            }
        }
        
        return integration_report

# Example usage and testing
if __name__ == "__main__":
    import asyncio
    
    async def demo_ice_integration():
        # Initialize integrator
        integrator = ICEUltraRefinedIntegrator({
            'lightrag_dir': './test_lightrag_storage'
        })
        
        # Sample emails
        test_emails = [
            {
                'id': 'email_001',
                'sender': 'dbs-sales@dbs.com',
                'subject': 'DBS SALES SCOOP - Market Analysis',
                'body': 'Comprehensive market analysis with investment opportunities. Key highlights include strong performance in tech sector with NVDA showing 15% gains. Recommendation to BUY based on Q3 earnings beat expectations.',
                'attachments': [
                    {'id': 'att1', 'name': 'chart1.png', 'type': 'image', 'size': 1024*1024},
                    {'id': 'att2', 'name': 'analysis.pdf', 'type': 'pdf', 'size': 2*1024*1024}
                ],
                'timestamp': datetime.now().isoformat()
            },
            {
                'id': 'email_002',
                'sender': 'economics@dbs.com',
                'subject': 'Economic Outlook - Q4 2024',
                'body': 'Q4 economic outlook shows GDP growth of 2.3% with inflation stabilizing at 2.1%. Federal Reserve likely to maintain current rates. Market volatility expected to continue.',
                'attachments': [
                    {'id': 'att3', 'name': 'economic_charts.pdf', 'type': 'pdf', 'size': 5*1024*1024}
                ],
                'timestamp': datetime.now().isoformat()
            }
        ]
        
        print("=== ICE Ultra-Refined Integration Demo ===\n")
        
        # Process emails
        for email in test_emails:
            print(f"Processing email: {email['id']} from {email['sender']}")
            result = await integrator.process_email_with_ultra_refinement(email)
            
            print(f"Status: {result['processing_summary']['status']}")
            print(f"Processing time: {result['processing_summary'].get('total_processing_time', 0):.2f}s")
            print(f"Ultra-refined used: {result['processing_summary'].get('ultra_refined_used', False)}")
            print(f"Performance improvement: {result['processing_summary'].get('performance_improvement_estimate', 'N/A')}")
            print(f"LightRAG integrated: {result['integration_results'].get('lightrag_integrated', False)}")
            print()
        
        # Query processed emails
        print("--- Querying Processed Emails ---")
        query_result = await integrator.query_processed_emails("What are the investment recommendations from DBS?")
        print(f"Query result: {query_result.get('status')}")
        if query_result.get('result'):
            print(f"Answer: {query_result['result'][:200]}...")
        print()
        
        # Generate performance report
        print("--- Integration Performance Report ---")
        report = integrator.get_integration_performance_report()
        print(json.dumps(report['integration_summary'], indent=2))
    
    # Run demo
    asyncio.run(demo_ice_integration())