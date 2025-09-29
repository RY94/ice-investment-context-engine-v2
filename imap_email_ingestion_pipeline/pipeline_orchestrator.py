# imap_email_ingestion_pipeline/pipeline_orchestrator.py
# Main orchestrator for the email ingestion pipeline with monitoring and health checks
# Coordinates all components with parallel processing and error recovery
# RELEVANT FILES: All pipeline components - this is the main controller

import logging
import time
import asyncio
import signal
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from pathlib import Path
import multiprocessing as mp

# Import pipeline components
from state_manager import StateManager
from imap_connector import ResilientIMAPConnector
from attachment_processor import AttachmentProcessor
from entity_extractor import EntityExtractor
from graph_builder import GraphBuilder
from ice_integrator import ICEEmailIntegrator

# Import monitoring
import json
import traceback

class PipelineOrchestrator:
    def __init__(self, config_path: str = "./config/pipeline_config.json"):
        self.logger = logging.getLogger(__name__)
        self.config_path = Path(config_path)
        self.config = self._load_config()
        
        # Initialize components
        self.state_manager = StateManager()
        self.imap_connector = None
        self.attachment_processor = AttachmentProcessor()
        self.entity_extractor = EntityExtractor()
        self.graph_builder = GraphBuilder()
        self.ice_integrator = ICEEmailIntegrator()
        
        # Pipeline state
        self.running = False
        self.shutdown_requested = False
        self.last_health_check = None
        
        # Performance metrics
        self.metrics = {
            'emails_processed': 0,
            'attachments_processed': 0,
            'errors_encountered': 0,
            'processing_rate': 0.0,
            'last_run': None,
            'average_processing_time': 0.0,
            'uptime_start': datetime.now()
        }
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        self.logger.info("Pipeline orchestrator initialized")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load pipeline configuration"""
        default_config = {
            'email': {
                'server': 'outlook.office365.com',
                'port': 993,
                'folder': 'INBOX',
                'batch_size': 10,
                'max_emails_per_run': 100
            },
            'processing': {
                'max_workers': 4,
                'use_process_pool': False,
                'timeout_seconds': 300,
                'retry_attempts': 3,
                'retry_delay': 5
            },
            'scheduling': {
                'run_interval_minutes': 15,
                'market_hours_only': False,
                'max_runtime_hours': 2
            },
            'storage': {
                'cleanup_days': 90,
                'max_attachment_size_mb': 100
            },
            'monitoring': {
                'health_check_interval': 60,
                'alert_thresholds': {
                    'error_rate': 0.1,
                    'processing_time': 300
                }
            }
        }
        
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    user_config = json.load(f)
                # Merge with defaults
                return self._deep_merge(default_config, user_config)
            except Exception as e:
                self.logger.warning(f"Failed to load config, using defaults: {e}")
        
        # Create default config file
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(default_config, f, indent=2)
        except Exception as e:
            self.logger.warning(f"Failed to save default config: {e}")
        
        return default_config
    
    def _deep_merge(self, base: Dict, update: Dict) -> Dict:
        """Deep merge two dictionaries"""
        result = base.copy()
        for key, value in update.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result
    
    def initialize_email_connection(self, email: str, password: str) -> bool:
        """Initialize IMAP connection"""
        try:
            self.imap_connector = ResilientIMAPConnector(
                email, password,
                server=self.config['email']['server'],
                port=self.config['email']['port']
            )
            
            if self.imap_connector.connect():
                self.logger.info(f"Email connection initialized for {email}")
                return True
            else:
                self.logger.error("Failed to establish email connection")
                return False
                
        except Exception as e:
            self.logger.error(f"Error initializing email connection: {e}")
            return False
    
    def run_single_cycle(self) -> Dict[str, Any]:
        """Run a single processing cycle"""
        cycle_start = time.time()
        
        try:
            self.logger.info("Starting pipeline cycle")
            
            # Health check
            if not self._perform_health_check():
                return {
                    'success': False,
                    'error': 'Health check failed',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Fetch new emails
            emails_result = self._fetch_new_emails()
            if not emails_result['success']:
                return emails_result
            
            emails = emails_result['emails']
            if not emails:
                self.logger.info("No new emails to process")
                return {
                    'success': True,
                    'processed': 0,
                    'message': 'No new emails',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Process emails in parallel
            processing_result = self._process_emails_batch(emails)
            
            # Update metrics
            cycle_time = time.time() - cycle_start
            self._update_metrics(processing_result, cycle_time)
            
            self.logger.info(f"Pipeline cycle completed in {cycle_time:.2f}s: "
                           f"{processing_result['successful']}/{processing_result['total']} emails processed")
            
            return {
                'success': True,
                'cycle_time': cycle_time,
                'result': processing_result,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            error_msg = f"Pipeline cycle failed: {e}"
            self.logger.error(error_msg)
            self.metrics['errors_encountered'] += 1
            
            return {
                'success': False,
                'error': error_msg,
                'timestamp': datetime.now().isoformat()
            }
    
    def _fetch_new_emails(self) -> Dict[str, Any]:
        """Fetch new emails from IMAP server"""
        try:
            if not self.imap_connector:
                return {'success': False, 'error': 'IMAP connector not initialized'}
            
            # Get last processed UID for incremental sync
            last_uid = self._get_last_processed_uid()
            
            # Fetch emails
            emails = self.imap_connector.fetch_new_emails(
                folder=self.config['email']['folder'],
                since_uid=last_uid,
                limit=self.config['email']['max_emails_per_run']
            )
            
            if not emails:
                return {'success': True, 'emails': [], 'message': 'No new emails'}
            
            # Filter already processed emails
            new_emails = []
            for email in emails:
                if not self.state_manager.is_email_processed(email['uid']):
                    new_emails.append(email)
            
            self.logger.info(f"Fetched {len(new_emails)} new emails (filtered from {len(emails)})")
            
            return {
                'success': True,
                'emails': new_emails,
                'total_fetched': len(emails),
                'new_emails': len(new_emails)
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _get_last_processed_uid(self) -> Optional[str]:
        """Get the highest processed UID for incremental sync"""
        try:
            # This would query the state database for the highest UID
            # For now, return None to fetch recent emails
            return None
        except Exception as e:
            self.logger.warning(f"Failed to get last processed UID: {e}")
            return None
    
    def _process_emails_batch(self, emails: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process emails in batch with parallel processing"""
        try:
            batch_size = self.config['processing']['batch_size']
            max_workers = self.config['processing']['max_workers']
            use_process_pool = self.config['processing']['use_process_pool']
            
            results = {
                'total': len(emails),
                'successful': 0,
                'failed': 0,
                'errors': [],
                'processing_times': []
            }
            
            # Process in batches
            for i in range(0, len(emails), batch_size):
                batch = emails[i:i + batch_size]
                self.logger.info(f"Processing batch {i//batch_size + 1}: {len(batch)} emails")
                
                if use_process_pool and len(batch) > 1:
                    batch_result = self._process_batch_parallel_processes(batch, max_workers)
                else:
                    batch_result = self._process_batch_parallel_threads(batch, max_workers)
                
                # Aggregate results
                results['successful'] += batch_result['successful']
                results['failed'] += batch_result['failed']
                results['errors'].extend(batch_result['errors'])
                results['processing_times'].extend(batch_result['processing_times'])
            
            return results
            
        except Exception as e:
            self.logger.error(f"Batch processing failed: {e}")
            return {
                'total': len(emails),
                'successful': 0,
                'failed': len(emails),
                'errors': [str(e)],
                'processing_times': []
            }
    
    def _process_batch_parallel_threads(self, emails: List[Dict[str, Any]], 
                                      max_workers: int) -> Dict[str, Any]:
        """Process email batch using thread pool"""
        results = {
            'successful': 0,
            'failed': 0,
            'errors': [],
            'processing_times': []
        }
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all emails for processing
            future_to_email = {
                executor.submit(self._process_single_email, email): email 
                for email in emails
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_email, 
                                     timeout=self.config['processing']['timeout_seconds']):
                email = future_to_email[future]
                
                try:
                    result = future.result()
                    if result['success']:
                        results['successful'] += 1
                    else:
                        results['failed'] += 1
                        results['errors'].append(f"Email {email['uid']}: {result.get('error', 'Unknown error')}")
                    
                    results['processing_times'].append(result.get('processing_time', 0))
                    
                except Exception as e:
                    results['failed'] += 1
                    results['errors'].append(f"Email {email['uid']}: {str(e)}")
        
        return results
    
    def _process_batch_parallel_processes(self, emails: List[Dict[str, Any]], 
                                        max_workers: int) -> Dict[str, Any]:
        """Process email batch using process pool for CPU-intensive tasks"""
        results = {
            'successful': 0,
            'failed': 0,
            'errors': [],
            'processing_times': []
        }
        
        try:
            with ProcessPoolExecutor(max_workers=max_workers) as executor:
                # Submit all emails for processing
                future_to_email = {
                    executor.submit(process_email_standalone, email): email 
                    for email in emails
                }
                
                # Collect results as they complete
                for future in as_completed(future_to_email,
                                         timeout=self.config['processing']['timeout_seconds']):
                    email = future_to_email[future]
                    
                    try:
                        result = future.result()
                        if result['success']:
                            results['successful'] += 1
                        else:
                            results['failed'] += 1
                            results['errors'].append(f"Email {email['uid']}: {result.get('error', 'Unknown error')}")
                        
                        results['processing_times'].append(result.get('processing_time', 0))
                        
                    except Exception as e:
                        results['failed'] += 1
                        results['errors'].append(f"Email {email['uid']}: {str(e)}")
        
        except Exception as e:
            self.logger.error(f"Process pool execution failed: {e}")
            results['failed'] = len(emails)
            results['errors'].append(str(e))
        
        return results
    
    def _process_single_email(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single email through the complete pipeline"""
        processing_start = time.time()
        email_uid = email_data.get('uid', 'unknown')
        
        try:
            # Mark email as processing
            if not self.state_manager.mark_email_processing(email_uid, email_data):
                return {'success': False, 'error': 'Failed to mark email as processing'}
            
            # Process attachments
            attachments_data = []
            if email_data.get('attachments'):
                for attachment in email_data['attachments']:
                    try:
                        attachment_result = self.attachment_processor.process_attachment(
                            attachment, email_uid
                        )
                        if not attachment_result.get('error'):
                            attachments_data.append(attachment_result)
                            self.metrics['attachments_processed'] += 1
                    except Exception as e:
                        self.logger.warning(f"Attachment processing failed: {e}")
            
            # Extract entities from email content and attachments
            all_text = email_data.get('body', '')
            for attachment in attachments_data:
                all_text += "\n" + attachment.get('extracted_text', '')
            
            extracted_entities = self.entity_extractor.extract_entities(
                all_text, metadata=email_data
            )
            
            # Build knowledge graph
            graph_data = self.graph_builder.build_email_graph(
                email_data, extracted_entities, attachments_data
            )
            
            # Integrate with ICE system
            integration_result = self.ice_integrator.integrate_email_data(
                email_data, extracted_entities, graph_data, attachments_data
            )
            
            processing_time = time.time() - processing_start
            
            if integration_result.get('success'):
                # Mark as completed
                self.state_manager.mark_email_completed(email_uid, int(processing_time * 1000))
                self.metrics['emails_processed'] += 1
                
                return {
                    'success': True,
                    'email_uid': email_uid,
                    'processing_time': processing_time,
                    'attachments_processed': len(attachments_data),
                    'entities_extracted': len(extracted_entities.get('tickers', [])),
                    'graph_nodes': len(graph_data.get('nodes', [])),
                    'integration': integration_result
                }
            else:
                # Mark as failed
                error_msg = f"Integration failed: {integration_result.get('error', 'Unknown error')}"
                self.state_manager.mark_email_failed(email_uid, error_msg)
                
                return {
                    'success': False,
                    'email_uid': email_uid,
                    'processing_time': processing_time,
                    'error': error_msg
                }
        
        except Exception as e:
            processing_time = time.time() - processing_start
            error_msg = f"Email processing failed: {str(e)}"
            
            # Mark as failed
            self.state_manager.mark_email_failed(email_uid, error_msg)
            
            self.logger.error(f"Error processing email {email_uid}: {e}")
            
            return {
                'success': False,
                'email_uid': email_uid,
                'processing_time': processing_time,
                'error': error_msg
            }
    
    def _perform_health_check(self) -> bool:
        """Perform comprehensive health check"""
        try:
            health_issues = []
            
            # Check IMAP connection
            if not self.imap_connector or not self.imap_connector.ensure_connection():
                health_issues.append("IMAP connection failed")
            
            # Check disk space
            storage_path = Path("./data")
            if storage_path.exists():
                import shutil
                disk_usage = shutil.disk_usage(storage_path)
                free_gb = disk_usage.free / (1024**3)
                if free_gb < 1.0:  # Less than 1GB free
                    health_issues.append(f"Low disk space: {free_gb:.1f}GB free")
            
            # Check component health
            components = [
                self.state_manager,
                self.attachment_processor,
                self.entity_extractor,
                self.graph_builder,
                self.ice_integrator
            ]
            
            for component in components:
                if hasattr(component, 'get_processing_stats'):
                    try:
                        stats = component.get_processing_stats()
                        if not stats or stats.get('error'):
                            health_issues.append(f"{component.__class__.__name__} health check failed")
                    except Exception as e:
                        health_issues.append(f"{component.__class__.__name__} health check error: {e}")
            
            self.last_health_check = datetime.now()
            
            if health_issues:
                self.logger.warning(f"Health check issues: {', '.join(health_issues)}")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return False
    
    def _update_metrics(self, processing_result: Dict[str, Any], cycle_time: float):
        """Update performance metrics"""
        try:
            total_processed = processing_result['successful'] + processing_result['failed']
            
            # Update processing rate (emails per minute)
            if cycle_time > 0:
                current_rate = (total_processed / cycle_time) * 60
                # Exponential moving average
                if self.metrics['processing_rate'] == 0:
                    self.metrics['processing_rate'] = current_rate
                else:
                    self.metrics['processing_rate'] = (0.7 * self.metrics['processing_rate'] + 
                                                     0.3 * current_rate)
            
            # Update average processing time
            processing_times = processing_result.get('processing_times', [])
            if processing_times:
                avg_time = sum(processing_times) / len(processing_times)
                if self.metrics['average_processing_time'] == 0:
                    self.metrics['average_processing_time'] = avg_time
                else:
                    self.metrics['average_processing_time'] = (0.7 * self.metrics['average_processing_time'] + 
                                                             0.3 * avg_time)
            
            # Update error count
            self.metrics['errors_encountered'] += processing_result['failed']
            self.metrics['last_run'] = datetime.now().isoformat()
            
            # Record metric in state manager
            self.state_manager.record_metric('processing_rate', self.metrics['processing_rate'])
            self.state_manager.record_metric('average_processing_time', self.metrics['average_processing_time'])
            
        except Exception as e:
            self.logger.warning(f"Failed to update metrics: {e}")
    
    def get_pipeline_status(self) -> Dict[str, Any]:
        """Get comprehensive pipeline status"""
        try:
            uptime = datetime.now() - self.metrics['uptime_start']
            
            status = {
                'running': self.running,
                'uptime_hours': uptime.total_seconds() / 3600,
                'last_health_check': self.last_health_check.isoformat() if self.last_health_check else None,
                'metrics': self.metrics.copy(),
                'component_status': {
                    'imap_connector': self.imap_connector is not None,
                    'state_manager': True,
                    'attachment_processor': True,
                    'entity_extractor': True,
                    'graph_builder': True,
                    'ice_integrator': True
                },
                'configuration': self.config,
                'timestamp': datetime.now().isoformat()
            }
            
            # Add state manager stats
            try:
                state_stats = self.state_manager.get_processing_stats()
                status['processing_stats'] = state_stats
            except:
                status['processing_stats'] = {'error': 'Failed to get state stats'}
            
            return status
            
        except Exception as e:
            return {
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        self.logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self.shutdown_requested = True
    
    def run_continuous(self, email: str, password: str) -> bool:
        """Run pipeline continuously with scheduling"""
        try:
            # Initialize email connection
            if not self.initialize_email_connection(email, password):
                return False
            
            self.running = True
            run_interval = self.config['scheduling']['run_interval_minutes'] * 60
            max_runtime = self.config['scheduling']['max_runtime_hours'] * 3600
            start_time = time.time()
            
            self.logger.info(f"Starting continuous pipeline (interval: {run_interval}s)")
            
            while self.running and not self.shutdown_requested:
                try:
                    # Check if we've exceeded max runtime
                    if time.time() - start_time > max_runtime:
                        self.logger.info("Maximum runtime reached, stopping")
                        break
                    
                    # Run single cycle
                    cycle_result = self.run_single_cycle()
                    
                    if not cycle_result['success']:
                        self.logger.error(f"Cycle failed: {cycle_result.get('error')}")
                        # Continue running but log the error
                    
                    # Wait before next cycle
                    self.logger.info(f"Waiting {run_interval}s before next cycle...")
                    time.sleep(run_interval)
                    
                except KeyboardInterrupt:
                    self.logger.info("Keyboard interrupt received, stopping...")
                    break
                except Exception as e:
                    self.logger.error(f"Unexpected error in continuous loop: {e}")
                    time.sleep(60)  # Wait before retrying
            
            self.running = False
            self._cleanup()
            return True
            
        except Exception as e:
            self.logger.error(f"Continuous run failed: {e}")
            self.running = False
            return False
    
    def _cleanup(self):
        """Clean up resources"""
        try:
            self.logger.info("Cleaning up pipeline resources...")
            
            if self.imap_connector:
                self.imap_connector.close()
            
            if self.ice_integrator:
                self.ice_integrator.close()
            
            if self.state_manager:
                self.state_manager.close()
            
            # Cleanup old data if configured
            cleanup_days = self.config['storage']['cleanup_days']
            if cleanup_days > 0:
                self.state_manager.cleanup_old_data(cleanup_days)
                self.attachment_processor.cleanup_old_files(cleanup_days)
                self.ice_integrator.cleanup_old_data(cleanup_days)
            
            self.logger.info("Pipeline cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")


def process_email_standalone(email_data: Dict[str, Any]) -> Dict[str, Any]:
    """Standalone email processing function for multiprocessing"""
    try:
        # This function runs in a separate process
        # It needs to initialize its own component instances
        
        # For now, return a mock result
        # In a full implementation, this would recreate the processing pipeline
        return {
            'success': True,
            'email_uid': email_data.get('uid'),
            'processing_time': 1.0,
            'method': 'multiprocess_mock'
        }
        
    except Exception as e:
        return {
            'success': False,
            'email_uid': email_data.get('uid', 'unknown'),
            'error': str(e),
            'method': 'multiprocess_failed'
        }


def main():
    """Main function for running the pipeline"""
    import argparse
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('./data/logs/pipeline.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Email Ingestion Pipeline')
    parser.add_argument('--email', required=True, help='Email address')
    parser.add_argument('--password', required=True, help='Email password')
    parser.add_argument('--mode', choices=['single', 'continuous'], default='single',
                       help='Run mode: single cycle or continuous')
    parser.add_argument('--config', help='Config file path')
    
    args = parser.parse_args()
    
    # Initialize orchestrator
    config_path = args.config or "./config/pipeline_config.json"
    orchestrator = PipelineOrchestrator(config_path)
    
    try:
        if args.mode == 'single':
            # Initialize connection
            if orchestrator.initialize_email_connection(args.email, args.password):
                result = orchestrator.run_single_cycle()
                print(json.dumps(result, indent=2))
                return 0 if result['success'] else 1
            else:
                print("Failed to initialize email connection")
                return 1
        
        elif args.mode == 'continuous':
            success = orchestrator.run_continuous(args.email, args.password)
            return 0 if success else 1
            
    except Exception as e:
        logging.error(f"Pipeline execution failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())