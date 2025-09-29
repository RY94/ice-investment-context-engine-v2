# imap_email_ingestion_pipeline/graph_builder.py
# Knowledge graph builder for email entities and relationships
# Creates timestamped edges with source attribution for ICE integration
# RELEVANT FILES: entity_extractor.py, ice_integrator.py, state_manager.py

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import hashlib
import json

class GraphBuilder:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Edge types for ICE knowledge graph
        self.edge_types = {
            # Email-specific edges
            'sent_by': {'weight': 1.0, 'bidirectional': False},
            'received_by': {'weight': 1.0, 'bidirectional': False},
            'mentions': {'weight': 0.8, 'bidirectional': False},
            'discusses': {'weight': 0.7, 'bidirectional': False},
            'attaches': {'weight': 0.9, 'bidirectional': False},
            'replies_to': {'weight': 0.6, 'bidirectional': False},
            
            # Financial relationship edges
            'recommends': {'weight': 0.9, 'bidirectional': False},
            'rates': {'weight': 0.8, 'bidirectional': False},
            'price_targets': {'weight': 0.9, 'bidirectional': False},
            'covers': {'weight': 0.7, 'bidirectional': False},
            'analyzes': {'weight': 0.7, 'bidirectional': False},
            
            # Market relationship edges
            'competes_with': {'weight': 0.6, 'bidirectional': True},
            'supplies_to': {'weight': 0.7, 'bidirectional': False},
            'depends_on': {'weight': 0.8, 'bidirectional': False},
            'exposed_to': {'weight': 0.7, 'bidirectional': False},
            
            # Temporal edges
            'precedes': {'weight': 0.5, 'bidirectional': False},
            'correlates_with': {'weight': 0.6, 'bidirectional': True}
        }
        
        # Node types
        self.node_types = {
            'email', 'attachment', 'sender', 'company', 'ticker', 
            'person', 'topic', 'metric', 'date', 'event'
        }
        
        # Confidence thresholds
        self.min_confidence = 0.5
        self.high_confidence = 0.8
    
    def build_email_graph(self, email_data: Dict[str, Any], 
                         extracted_entities: Dict[str, Any],
                         attachments_data: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Build knowledge graph structure from email and entities"""
        try:
            graph_data = {
                'nodes': [],
                'edges': [],
                'metadata': {
                    'email_uid': email_data.get('uid'),
                    'processed_at': datetime.now().isoformat(),
                    'confidence': extracted_entities.get('confidence', 0.0)
                }
            }
            
            # Create email node
            email_node = self._create_email_node(email_data)
            graph_data['nodes'].append(email_node)
            
            # Create sender node and edge
            sender_data = self._create_sender_relationship(email_data, email_node['id'])
            if sender_data:
                graph_data['nodes'].append(sender_data['node'])
                graph_data['edges'].append(sender_data['edge'])
            
            # Process extracted entities
            entity_nodes_edges = self._process_entities(
                extracted_entities, email_node['id'], email_data
            )
            graph_data['nodes'].extend(entity_nodes_edges['nodes'])
            graph_data['edges'].extend(entity_nodes_edges['edges'])
            
            # Process attachments if provided
            if attachments_data:
                attachment_nodes_edges = self._process_attachments(
                    attachments_data, email_node['id'], email_data
                )
                graph_data['nodes'].extend(attachment_nodes_edges['nodes'])
                graph_data['edges'].extend(attachment_nodes_edges['edges'])
            
            # Add thread relationships
            thread_edges = self._create_thread_relationships(email_data, email_node['id'])
            graph_data['edges'].extend(thread_edges)
            
            self.logger.info(f"Built graph with {len(graph_data['nodes'])} nodes and {len(graph_data['edges'])} edges")
            
            return graph_data
            
        except Exception as e:
            self.logger.error(f"Error building email graph: {e}")
            return {'nodes': [], 'edges': [], 'error': str(e)}
    
    def _create_email_node(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create email node with metadata"""
        email_id = f"email_{email_data.get('uid', 'unknown')}"
        
        return {
            'id': email_id,
            'type': 'email',
            'properties': {
                'uid': email_data.get('uid'),
                'subject': email_data.get('subject', ''),
                'date': email_data.get('date', ''),
                'message_id': email_data.get('message_id', ''),
                'body_length': len(email_data.get('body', '')),
                'priority': email_data.get('priority', 0),
                'has_attachments': len(email_data.get('attachments', [])) > 0
            },
            'created_at': datetime.now().isoformat()
        }
    
    def _create_sender_relationship(self, email_data: Dict[str, Any], 
                                  email_node_id: str) -> Optional[Dict[str, Any]]:
        """Create sender node and sent_by relationship"""
        try:
            sender = email_data.get('from', '').strip()
            if not sender:
                return None
            
            # Extract email address and name
            sender_email, sender_name = self._parse_sender(sender)
            sender_id = f"sender_{hashlib.md5(sender_email.encode()).hexdigest()[:8]}"
            
            sender_node = {
                'id': sender_id,
                'type': 'sender',
                'properties': {
                    'email': sender_email,
                    'name': sender_name,
                    'domain': sender_email.split('@')[-1] if '@' in sender_email else '',
                    'first_seen': datetime.now().isoformat()
                },
                'created_at': datetime.now().isoformat()
            }
            
            sent_by_edge = self._create_edge(
                source_id=sender_id,
                target_id=email_node_id,
                edge_type='sent_by',
                confidence=1.0,
                properties={
                    'timestamp': email_data.get('date', ''),
                    'source': 'email_header'
                }
            )
            
            return {
                'node': sender_node,
                'edge': sent_by_edge
            }
            
        except Exception as e:
            self.logger.warning(f"Failed to create sender relationship: {e}")
            return None
    
    def _parse_sender(self, sender_str: str) -> Tuple[str, str]:
        """Parse sender string to extract email and name"""
        import re
        
        # Pattern: "Name <email@domain.com>" or "email@domain.com"
        email_pattern = r'<([^>]+)>|([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
        name_pattern = r'^([^<]+)<'
        
        email_match = re.search(email_pattern, sender_str)
        name_match = re.search(name_pattern, sender_str)
        
        email = email_match.group(1) or email_match.group(2) if email_match else sender_str
        name = name_match.group(1).strip() if name_match else email.split('@')[0]
        
        return email, name
    
    def _process_entities(self, entities: Dict[str, Any], 
                         email_node_id: str, email_data: Dict[str, Any]) -> Dict[str, List[Dict]]:
        """Process extracted entities and create nodes/edges"""
        nodes = []
        edges = []
        
        try:
            # Process tickers
            for ticker_data in entities.get('tickers', []):
                ticker_nodes_edges = self._create_ticker_relationship(
                    ticker_data, email_node_id, email_data
                )
                if ticker_nodes_edges:
                    nodes.append(ticker_nodes_edges['node'])
                    edges.append(ticker_nodes_edges['edge'])
            
            # Process companies
            for company_data in entities.get('companies', []):
                company_nodes_edges = self._create_company_relationship(
                    company_data, email_node_id, email_data
                )
                if company_nodes_edges:
                    nodes.append(company_nodes_edges['node'])
                    edges.append(company_nodes_edges['edge'])
            
            # Process people
            for person_data in entities.get('people', []):
                person_nodes_edges = self._create_person_relationship(
                    person_data, email_node_id, email_data
                )
                if person_nodes_edges:
                    nodes.append(person_nodes_edges['node'])
                    edges.append(person_nodes_edges['edge'])
            
            # Process financial metrics
            metrics_nodes_edges = self._process_financial_metrics(
                entities.get('financial_metrics', {}), email_node_id, email_data
            )
            nodes.extend(metrics_nodes_edges['nodes'])
            edges.extend(metrics_nodes_edges['edges'])
            
            # Process topics
            for topic in entities.get('topics', []):
                topic_nodes_edges = self._create_topic_relationship(
                    topic, email_node_id, email_data
                )
                if topic_nodes_edges:
                    nodes.append(topic_nodes_edges['node'])
                    edges.append(topic_nodes_edges['edge'])
            
            # Process sentiment as edge properties
            sentiment = entities.get('sentiment', {})
            if sentiment.get('confidence', 0) > self.min_confidence:
                # Add sentiment as properties to ticker/company edges
                self._add_sentiment_to_edges(edges, sentiment)
            
        except Exception as e:
            self.logger.error(f"Error processing entities: {e}")
        
        return {'nodes': nodes, 'edges': edges}
    
    def _create_ticker_relationship(self, ticker_data: Dict[str, Any],
                                  email_node_id: str, email_data: Dict[str, Any]) -> Optional[Dict]:
        """Create ticker node and mentions relationship"""
        try:
            if ticker_data.get('confidence', 0) < self.min_confidence:
                return None
            
            ticker = ticker_data['ticker']
            ticker_id = f"ticker_{ticker}"
            
            ticker_node = {
                'id': ticker_id,
                'type': 'ticker',
                'properties': {
                    'symbol': ticker,
                    'first_mentioned': datetime.now().isoformat()
                },
                'created_at': datetime.now().isoformat()
            }
            
            mentions_edge = self._create_edge(
                source_id=email_node_id,
                target_id=ticker_id,
                edge_type='mentions',
                confidence=ticker_data['confidence'],
                properties={
                    'context': ticker_data.get('context', ''),
                    'source_method': ticker_data.get('source', 'unknown'),
                    'timestamp': email_data.get('date', '')
                }
            )
            
            return {'node': ticker_node, 'edge': mentions_edge}
            
        except Exception as e:
            self.logger.warning(f"Failed to create ticker relationship: {e}")
            return None
    
    def _create_company_relationship(self, company_data: Dict[str, Any],
                                   email_node_id: str, email_data: Dict[str, Any]) -> Optional[Dict]:
        """Create company node and discusses relationship"""
        try:
            if company_data.get('confidence', 0) < self.min_confidence:
                return None
            
            company = company_data['company']
            company_id = f"company_{hashlib.md5(company.lower().encode()).hexdigest()[:8]}"
            
            company_node = {
                'id': company_id,
                'type': 'company',
                'properties': {
                    'name': company,
                    'ticker': company_data.get('ticker'),
                    'first_mentioned': datetime.now().isoformat()
                },
                'created_at': datetime.now().isoformat()
            }
            
            discusses_edge = self._create_edge(
                source_id=email_node_id,
                target_id=company_id,
                edge_type='discusses',
                confidence=company_data['confidence'],
                properties={
                    'context': company_data.get('context', ''),
                    'source_method': company_data.get('source', 'unknown'),
                    'timestamp': email_data.get('date', '')
                }
            )
            
            return {'node': company_node, 'edge': discusses_edge}
            
        except Exception as e:
            self.logger.warning(f"Failed to create company relationship: {e}")
            return None
    
    def _create_person_relationship(self, person_data: Dict[str, Any],
                                  email_node_id: str, email_data: Dict[str, Any]) -> Optional[Dict]:
        """Create person node and mentions relationship"""
        try:
            if person_data.get('confidence', 0) < self.min_confidence:
                return None
            
            name = person_data['name']
            person_id = f"person_{hashlib.md5(name.lower().encode()).hexdigest()[:8]}"
            
            person_node = {
                'id': person_id,
                'type': 'person',
                'properties': {
                    'name': name,
                    'first_mentioned': datetime.now().isoformat()
                },
                'created_at': datetime.now().isoformat()
            }
            
            mentions_edge = self._create_edge(
                source_id=email_node_id,
                target_id=person_id,
                edge_type='mentions',
                confidence=person_data['confidence'],
                properties={
                    'context': person_data.get('context', ''),
                    'timestamp': email_data.get('date', '')
                }
            )
            
            return {'node': person_node, 'edge': mentions_edge}
            
        except Exception as e:
            self.logger.warning(f"Failed to create person relationship: {e}")
            return None
    
    def _process_financial_metrics(self, metrics: Dict[str, List[Dict]], 
                                 email_node_id: str, email_data: Dict[str, Any]) -> Dict[str, List]:
        """Process financial metrics and create specialized relationships"""
        nodes = []
        edges = []
        
        try:
            for metric_type, metric_list in metrics.items():
                for metric_data in metric_list:
                    if metric_data.get('confidence', 0) < self.min_confidence:
                        continue
                    
                    metric_id = f"metric_{hashlib.md5((metric_type + metric_data['value']).encode()).hexdigest()[:8]}"
                    
                    metric_node = {
                        'id': metric_id,
                        'type': 'metric',
                        'properties': {
                            'metric_type': metric_type,
                            'value': metric_data['value'],
                            'full_match': metric_data.get('full_match', ''),
                            'first_mentioned': datetime.now().isoformat()
                        },
                        'created_at': datetime.now().isoformat()
                    }
                    
                    # Choose appropriate edge type based on metric
                    if metric_type == 'price_targets':
                        edge_type = 'price_targets'
                    elif metric_type == 'ratings':
                        edge_type = 'rates'
                    else:
                        edge_type = 'discusses'
                    
                    metric_edge = self._create_edge(
                        source_id=email_node_id,
                        target_id=metric_id,
                        edge_type=edge_type,
                        confidence=metric_data['confidence'],
                        properties={
                            'context': metric_data.get('context', ''),
                            'metric_type': metric_type,
                            'timestamp': email_data.get('date', '')
                        }
                    )
                    
                    nodes.append(metric_node)
                    edges.append(metric_edge)
        
        except Exception as e:
            self.logger.error(f"Error processing financial metrics: {e}")
        
        return {'nodes': nodes, 'edges': edges}
    
    def _create_topic_relationship(self, topic: str, email_node_id: str, 
                                 email_data: Dict[str, Any]) -> Optional[Dict]:
        """Create topic node and discusses relationship"""
        try:
            topic_id = f"topic_{topic}"
            
            topic_node = {
                'id': topic_id,
                'type': 'topic',
                'properties': {
                    'topic': topic,
                    'first_mentioned': datetime.now().isoformat()
                },
                'created_at': datetime.now().isoformat()
            }
            
            discusses_edge = self._create_edge(
                source_id=email_node_id,
                target_id=topic_id,
                edge_type='discusses',
                confidence=0.7,  # Default confidence for topic extraction
                properties={
                    'topic_type': topic,
                    'timestamp': email_data.get('date', '')
                }
            )
            
            return {'node': topic_node, 'edge': discusses_edge}
            
        except Exception as e:
            self.logger.warning(f"Failed to create topic relationship: {e}")
            return None
    
    def _process_attachments(self, attachments_data: List[Dict[str, Any]], 
                           email_node_id: str, email_data: Dict[str, Any]) -> Dict[str, List]:
        """Process email attachments and create nodes/edges"""
        nodes = []
        edges = []
        
        try:
            for attachment in attachments_data:
                if attachment.get('error'):
                    continue
                
                attachment_id = f"attachment_{attachment['file_hash'][:8]}"
                
                attachment_node = {
                    'id': attachment_id,
                    'type': 'attachment',
                    'properties': {
                        'filename': attachment['filename'],
                        'file_hash': attachment['file_hash'],
                        'mime_type': attachment.get('mime_type', ''),
                        'file_size': attachment.get('file_size', 0),
                        'extraction_method': attachment.get('extraction_method', ''),
                        'ocr_confidence': attachment.get('ocr_confidence', 0.0),
                        'text_length': len(attachment.get('extracted_text', '')),
                        'processing_status': attachment.get('processing_status', 'unknown')
                    },
                    'created_at': datetime.now().isoformat()
                }
                
                attaches_edge = self._create_edge(
                    source_id=email_node_id,
                    target_id=attachment_id,
                    edge_type='attaches',
                    confidence=0.95,  # High confidence for attachment relationships
                    properties={
                        'filename': attachment['filename'],
                        'file_type': attachment.get('mime_type', ''),
                        'timestamp': email_data.get('date', '')
                    }
                )
                
                nodes.append(attachment_node)
                edges.append(attaches_edge)
        
        except Exception as e:
            self.logger.error(f"Error processing attachments: {e}")
        
        return {'nodes': nodes, 'edges': edges}
    
    def _create_thread_relationships(self, email_data: Dict[str, Any], 
                                   email_node_id: str) -> List[Dict[str, Any]]:
        """Create email thread relationships"""
        edges = []
        
        try:
            thread_info = email_data.get('thread_info', {})
            in_reply_to = thread_info.get('in_reply_to', '')
            
            if in_reply_to:
                # Create replies_to relationship
                parent_email_id = f"email_{hashlib.md5(in_reply_to.encode()).hexdigest()[:8]}"
                
                replies_edge = self._create_edge(
                    source_id=email_node_id,
                    target_id=parent_email_id,
                    edge_type='replies_to',
                    confidence=0.9,
                    properties={
                        'parent_message_id': in_reply_to,
                        'thread_topic': thread_info.get('thread_topic', ''),
                        'timestamp': email_data.get('date', '')
                    }
                )
                
                edges.append(replies_edge)
        
        except Exception as e:
            self.logger.warning(f"Failed to create thread relationships: {e}")
        
        return edges
    
    def _create_edge(self, source_id: str, target_id: str, edge_type: str,
                    confidence: float, properties: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create standardized edge structure"""
        edge_config = self.edge_types.get(edge_type, {'weight': 0.5, 'bidirectional': False})
        
        edge = {
            'id': f"{source_id}_{edge_type}_{target_id}",
            'source': source_id,
            'target': target_id,
            'type': edge_type,
            'weight': edge_config['weight'] * confidence,
            'confidence': confidence,
            'bidirectional': edge_config['bidirectional'],
            'properties': properties or {},
            'created_at': datetime.now().isoformat()
        }
        
        # Add temporal metadata
        edge['properties']['days_ago'] = 0  # Will be updated based on email date
        edge['properties']['is_recent'] = True
        
        return edge
    
    def _add_sentiment_to_edges(self, edges: List[Dict[str, Any]], 
                               sentiment: Dict[str, Any]):
        """Add sentiment information to relevant edges"""
        try:
            sentiment_data = {
                'sentiment': sentiment.get('sentiment', 'neutral'),
                'sentiment_confidence': sentiment.get('confidence', 0.0),
                'bullish_score': sentiment.get('bullish_score', 0),
                'bearish_score': sentiment.get('bearish_score', 0)
            }
            
            # Add sentiment to ticker and company edges
            for edge in edges:
                if edge['type'] in ['mentions', 'discusses', 'rates', 'price_targets']:
                    edge['properties'].update(sentiment_data)
        
        except Exception as e:
            self.logger.warning(f"Failed to add sentiment to edges: {e}")
    
    def validate_graph_structure(self, graph_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate graph structure and return validation results"""
        validation_results = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'stats': {
                'nodes': len(graph_data.get('nodes', [])),
                'edges': len(graph_data.get('edges', [])),
                'node_types': {},
                'edge_types': {}
            }
        }
        
        try:
            nodes = graph_data.get('nodes', [])
            edges = graph_data.get('edges', [])
            node_ids = set()
            
            # Validate nodes
            for node in nodes:
                if 'id' not in node or 'type' not in node:
                    validation_results['errors'].append(f"Node missing required fields: {node}")
                    validation_results['valid'] = False
                    continue
                
                node_ids.add(node['id'])
                node_type = node['type']
                validation_results['stats']['node_types'][node_type] = \
                    validation_results['stats']['node_types'].get(node_type, 0) + 1
                
                if node_type not in self.node_types:
                    validation_results['warnings'].append(f"Unknown node type: {node_type}")
            
            # Validate edges
            for edge in edges:
                required_fields = ['id', 'source', 'target', 'type', 'confidence']
                for field in required_fields:
                    if field not in edge:
                        validation_results['errors'].append(f"Edge missing {field}: {edge}")
                        validation_results['valid'] = False
                        continue
                
                # Check if referenced nodes exist
                if edge['source'] not in node_ids:
                    validation_results['errors'].append(f"Edge references non-existent source node: {edge['source']}")
                    validation_results['valid'] = False
                
                if edge['target'] not in node_ids:
                    validation_results['errors'].append(f"Edge references non-existent target node: {edge['target']}")
                    validation_results['valid'] = False
                
                edge_type = edge['type']
                validation_results['stats']['edge_types'][edge_type] = \
                    validation_results['stats']['edge_types'].get(edge_type, 0) + 1
                
                if edge_type not in self.edge_types:
                    validation_results['warnings'].append(f"Unknown edge type: {edge_type}")
                
                # Validate confidence
                confidence = edge.get('confidence', 0)
                if not (0 <= confidence <= 1):
                    validation_results['warnings'].append(f"Edge confidence out of range [0,1]: {confidence}")
        
        except Exception as e:
            validation_results['errors'].append(f"Validation error: {e}")
            validation_results['valid'] = False
        
        return validation_results
    
    def get_graph_statistics(self, graph_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get comprehensive statistics about the graph"""
        try:
            nodes = graph_data.get('nodes', [])
            edges = graph_data.get('edges', [])
            
            stats = {
                'total_nodes': len(nodes),
                'total_edges': len(edges),
                'node_types': {},
                'edge_types': {},
                'confidence_distribution': {
                    'high': 0,  # > 0.8
                    'medium': 0,  # 0.5-0.8
                    'low': 0  # < 0.5
                },
                'created_at': datetime.now().isoformat()
            }
            
            # Count node types
            for node in nodes:
                node_type = node.get('type', 'unknown')
                stats['node_types'][node_type] = stats['node_types'].get(node_type, 0) + 1
            
            # Count edge types and analyze confidence
            for edge in edges:
                edge_type = edge.get('type', 'unknown')
                stats['edge_types'][edge_type] = stats['edge_types'].get(edge_type, 0) + 1
                
                confidence = edge.get('confidence', 0)
                if confidence > 0.8:
                    stats['confidence_distribution']['high'] += 1
                elif confidence >= 0.5:
                    stats['confidence_distribution']['medium'] += 1
                else:
                    stats['confidence_distribution']['low'] += 1
            
            return stats
        
        except Exception as e:
            self.logger.error(f"Error calculating graph statistics: {e}")
            return {'error': str(e)}