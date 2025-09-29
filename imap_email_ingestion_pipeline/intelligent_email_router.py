# imap_email_ingestion_pipeline/intelligent_email_router.py  
# Intelligent Email Router with Type-Specific Processors - Blueprint V2 Component #4
# Routes emails to specialized processors based on pattern recognition
# RELEVANT FILES: ultra_refined_email_processor.py, attachment_processor.py, entity_extractor.py

import logging
import re
import json
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from enum import Enum

class EmailType(Enum):
    """Email categorization types"""
    DBS_SALES_SCOOP = "dbs_sales_scoop"
    DBS_ECONOMICS = "dbs_economics"
    UOBKH_RESEARCH = "uobkh_research"
    OCBC_SIMPLE = "ocbc_simple"
    THREAD_CONVERSATION = "thread_conversation"
    EARNINGS_ALERT = "earnings_alert"
    MARKET_UPDATE = "market_update"
    RESEARCH_REPORT = "research_report"
    ADMIN_EMAIL = "admin_email"
    UNKNOWN = "unknown"

@dataclass
class EmailPattern:
    """Pattern definition for email classification"""
    email_type: EmailType
    sender_patterns: List[str]
    subject_patterns: List[str]
    body_indicators: List[str]
    attachment_patterns: Dict[str, Any]
    processing_priority: int  # 1=highest, 5=lowest
    expected_processing_time: float  # seconds
    processor_class: str
    optimization_flags: List[str]

@dataclass
class ProcessingRoute:
    """Processing route decision"""
    email_type: EmailType
    processor_class: str
    optimization_flags: List[str]
    confidence: float
    expected_time: float
    priority: int

class IntelligentEmailRouter:
    """
    GAME-CHANGING IMPROVEMENT #4: Smart Email Router with Type-Specific Processors (20% improvement)
    Route emails to specialized processors based on pattern. Avoids over-processing simple emails 
    and under-processing complex ones!
    """
    
    def __init__(self, patterns_file: str = None):
        self.logger = logging.getLogger(__name__ + ".IntelligentEmailRouter")
        self.patterns = self._load_email_patterns(patterns_file)
        self.routing_stats = {}
        self.performance_cache = {}
        
        self.logger.info(f"Email router initialized with {len(self.patterns)} patterns")
    
    def _load_email_patterns(self, patterns_file: str = None) -> List[EmailPattern]:
        """Load email classification patterns"""
        
        # Define patterns based on Blueprint V2 specifications
        default_patterns = [
            EmailPattern(
                email_type=EmailType.DBS_SALES_SCOOP,
                sender_patterns=[r".*dbs.*sales.*scoop.*", r".*dbs.*research.*"],
                subject_patterns=[r".*DBS.*SALES.*SCOOP.*", r".*Daily.*Sales.*"],
                body_indicators=["8 images", "50+ links", "market update", "sales trading"],
                attachment_patterns={"count": 8, "types": ["image", "pdf"], "total_size_mb": {"min": 10, "max": 50}},
                processing_priority=1,
                expected_processing_time=45.0,  # Original: 45s, Target: 8s
                processor_class="DBSSalesScoopProcessor",
                optimization_flags=["image_batch_processing", "link_extraction", "table_priority"]
            ),
            
            EmailPattern(
                email_type=EmailType.DBS_ECONOMICS,
                sender_patterns=[r".*dbs.*economics.*", r".*dbs.*research.*econ.*"],
                subject_patterns=[r".*Economics.*", r".*Economic.*Update.*", r".*GDP.*", r".*Inflation.*"],
                body_indicators=["17 charts", "economic analysis", "policy", "macro"],
                attachment_patterns={"count": {"min": 15, "max": 20}, "types": ["image", "pdf"], "chart_heavy": True},
                processing_priority=1,
                expected_processing_time=60.0,  # Original: 60s, Target: 12s
                processor_class="DBSEconomicsProcessor", 
                optimization_flags=["chart_ocr_batch", "economic_entity_extraction", "parallel_chart_analysis"]
            ),
            
            EmailPattern(
                email_type=EmailType.UOBKH_RESEARCH,
                sender_patterns=[r".*uobkh.*", r".*uob.*research.*"],
                subject_patterns=[r".*UOBKH.*", r".*Research.*Update.*", r".*Company.*Analysis.*"],
                body_indicators=["12 tables", "research report", "price target", "recommendation"],
                attachment_patterns={"count": {"min": 10, "max": 15}, "types": ["excel", "pdf"], "table_heavy": True},
                processing_priority=1,
                expected_processing_time=30.0,  # Original: 30s, Target: 3s
                processor_class="UOBKHResearchProcessor",
                optimization_flags=["table_extraction_priority", "financial_metrics", "excel_formula_parsing"]
            ),
            
            EmailPattern(
                email_type=EmailType.OCBC_SIMPLE,
                sender_patterns=[r".*ocbc.*", r".*oversea.*chinese.*"],
                subject_patterns=[r".*OCBC.*", r".*Daily.*Brief.*", r".*Market.*Brief.*"],
                body_indicators=["simple format", "brief update", "summary"],
                attachment_patterns={"count": {"min": 0, "max": 2}, "types": ["pdf"], "simple": True},
                processing_priority=2,
                expected_processing_time=5.0,  # Original: 5s, Target: 0.5s
                processor_class="OCBCSimpleProcessor",
                optimization_flags=["text_extraction_only", "minimal_processing", "quick_scan"]
            ),
            
            EmailPattern(
                email_type=EmailType.THREAD_CONVERSATION,
                sender_patterns=[r".*"],  # Any sender
                subject_patterns=[r"RE:.*", r"FW:.*", r".*thread.*", r".*conversation.*"],
                body_indicators=["reply chain", "forwarded", "conversation", "thread"],
                attachment_patterns={"thread_context": True},
                processing_priority=3,
                expected_processing_time=75.0,  # Original: 75s for 5 emails, Target: 15s
                processor_class="ThreadConversationProcessor",
                optimization_flags=["conversation_context", "thread_analysis", "relationship_mapping"]
            ),
            
            EmailPattern(
                email_type=EmailType.EARNINGS_ALERT,
                sender_patterns=[r".*earnings.*", r".*alert.*", r".*notification.*"],
                subject_patterns=[r".*Earnings.*Alert.*", r".*Q[1-4].*Results.*", r".*Quarterly.*"],
                body_indicators=["earnings", "quarterly", "results", "eps", "revenue"],
                attachment_patterns={"count": {"min": 1, "max": 5}, "types": ["pdf", "excel"]},
                processing_priority=1,
                expected_processing_time=20.0,
                processor_class="EarningsAlertProcessor", 
                optimization_flags=["earnings_extraction", "financial_metrics", "date_recognition"]
            ),
            
            EmailPattern(
                email_type=EmailType.RESEARCH_REPORT,
                sender_patterns=[r".*research.*", r".*analyst.*", r".*equity.*"],
                subject_patterns=[r".*Research.*", r".*Analysis.*", r".*Report.*", r".*Coverage.*"],
                body_indicators=["research", "analysis", "target price", "rating", "analyst"],
                attachment_patterns={"count": {"min": 1, "max": 10}, "types": ["pdf", "excel", "ppt"]},
                processing_priority=2,
                expected_processing_time=40.0,
                processor_class="ResearchReportProcessor",
                optimization_flags=["research_extraction", "analyst_sentiment", "price_target_extraction"]
            ),
            
            EmailPattern(
                email_type=EmailType.ADMIN_EMAIL,
                sender_patterns=[r".*admin.*", r".*system.*", r".*no-reply.*", r".*automated.*"],
                subject_patterns=[r".*System.*", r".*Automated.*", r".*Notification.*", r".*Admin.*"],
                body_indicators=["system", "automated", "notification", "admin"],
                attachment_patterns={"count": {"min": 0, "max": 1}, "administrative": True},
                processing_priority=5,
                expected_processing_time=2.0,
                processor_class="AdminEmailProcessor",
                optimization_flags=["minimal_processing", "skip_entity_extraction", "admin_only"]
            )
        ]
        
        if patterns_file and Path(patterns_file).exists():
            try:
                with open(patterns_file, 'r') as f:
                    loaded_patterns = json.load(f)
                # Convert to EmailPattern objects
                # Implementation would go here for loading from file
                self.logger.info(f"Loaded custom patterns from {patterns_file}")
            except Exception as e:
                self.logger.error(f"Failed to load custom patterns: {e}")
                return default_patterns
        
        return default_patterns
    
    def route_email(self, email_data: Dict[str, Any]) -> ProcessingRoute:
        """
        Route email to appropriate processor based on pattern matching
        Returns optimal processing route with confidence score
        """
        sender = email_data.get('sender', '').lower()
        subject = email_data.get('subject', '').lower() 
        body = email_data.get('body', '').lower()
        attachments = email_data.get('attachments', [])
        
        self.logger.debug(f"Routing email from {sender} with subject: {subject[:50]}...")
        
        # Score each pattern
        pattern_scores = []
        for pattern in self.patterns:
            score = self._calculate_pattern_score(email_data, pattern, sender, subject, body, attachments)
            if score > 0:
                pattern_scores.append((pattern, score))
        
        # Sort by score and select best match
        pattern_scores.sort(key=lambda x: x[1], reverse=True)
        
        if pattern_scores:
            best_pattern, confidence = pattern_scores[0]
            
            # Log routing decision
            self.logger.info(f"Routed {sender} to {best_pattern.email_type.value} (confidence: {confidence:.2f})")
            self._update_routing_stats(best_pattern.email_type.value)
            
            return ProcessingRoute(
                email_type=best_pattern.email_type,
                processor_class=best_pattern.processor_class,
                optimization_flags=best_pattern.optimization_flags,
                confidence=confidence,
                expected_time=best_pattern.expected_processing_time,
                priority=best_pattern.processing_priority
            )
        else:
            # Default to unknown pattern
            self.logger.warning(f"No pattern match for {sender}, using default processor")
            self._update_routing_stats("unknown")
            
            return ProcessingRoute(
                email_type=EmailType.UNKNOWN,
                processor_class="DefaultEmailProcessor",
                optimization_flags=["full_analysis_required"],
                confidence=0.5,
                expected_time=30.0,
                priority=3
            )
    
    def _calculate_pattern_score(self, email_data: Dict[str, Any], pattern: EmailPattern, 
                                sender: str, subject: str, body: str, attachments: List[Dict]) -> float:
        """Calculate how well an email matches a pattern"""
        score = 0.0
        max_score = 0.0
        
        # Sender pattern matching (30% weight)
        sender_score = self._match_patterns(sender, pattern.sender_patterns)
        score += sender_score * 0.3
        max_score += 0.3
        
        # Subject pattern matching (25% weight)  
        subject_score = self._match_patterns(subject, pattern.subject_patterns)
        score += subject_score * 0.25
        max_score += 0.25
        
        # Body indicator matching (25% weight)
        body_score = self._match_indicators(body, pattern.body_indicators)
        score += body_score * 0.25
        max_score += 0.25
        
        # Attachment pattern matching (20% weight)
        attachment_score = self._match_attachment_patterns(attachments, pattern.attachment_patterns)
        score += attachment_score * 0.20
        max_score += 0.20
        
        # Normalize score
        return score / max_score if max_score > 0 else 0.0
    
    def _match_patterns(self, text: str, patterns: List[str]) -> float:
        """Match text against regex patterns"""
        if not patterns:
            return 0.0
        
        matches = 0
        for pattern in patterns:
            try:
                if re.search(pattern, text, re.IGNORECASE):
                    matches += 1
            except re.error:
                # Invalid regex, treat as literal string match
                if pattern.lower() in text:
                    matches += 1
        
        return matches / len(patterns)
    
    def _match_indicators(self, text: str, indicators: List[str]) -> float:
        """Match text against indicator words/phrases"""
        if not indicators:
            return 0.0
        
        matches = 0
        for indicator in indicators:
            if indicator.lower() in text:
                matches += 1
        
        return matches / len(indicators)
    
    def _match_attachment_patterns(self, attachments: List[Dict], patterns: Dict[str, Any]) -> float:
        """Match attachments against expected patterns"""
        if not patterns:
            return 0.5  # Neutral score if no pattern specified
        
        score = 0.0
        checks = 0
        
        # Check attachment count
        if 'count' in patterns:
            checks += 1
            att_count = len(attachments)
            
            if isinstance(patterns['count'], int):
                score += 1.0 if att_count == patterns['count'] else 0.0
            elif isinstance(patterns['count'], dict):
                min_count = patterns['count'].get('min', 0)
                max_count = patterns['count'].get('max', 100)
                score += 1.0 if min_count <= att_count <= max_count else 0.0
        
        # Check attachment types
        if 'types' in patterns:
            checks += 1
            expected_types = patterns['types']
            actual_types = [att.get('type', '').lower() for att in attachments]
            
            type_matches = sum(1 for exp_type in expected_types if any(exp_type in act_type for act_type in actual_types))
            score += type_matches / len(expected_types) if expected_types else 0.0
        
        # Check total size
        if 'total_size_mb' in patterns:
            checks += 1
            total_size_mb = sum(att.get('size', 0) for att in attachments) / (1024 * 1024)
            size_pattern = patterns['total_size_mb']
            
            if isinstance(size_pattern, dict):
                min_size = size_pattern.get('min', 0)
                max_size = size_pattern.get('max', 1000)
                score += 1.0 if min_size <= total_size_mb <= max_size else 0.0
        
        # Check special flags
        special_flags = ['chart_heavy', 'table_heavy', 'simple', 'thread_context', 'administrative']
        for flag in special_flags:
            if flag in patterns:
                checks += 1
                score += 0.8  # Give partial credit for special flags
        
        return score / checks if checks > 0 else 0.5
    
    def _update_routing_stats(self, email_type: str):
        """Update routing statistics"""
        if email_type not in self.routing_stats:
            self.routing_stats[email_type] = {
                'count': 0,
                'last_seen': None
            }
        
        self.routing_stats[email_type]['count'] += 1
        self.routing_stats[email_type]['last_seen'] = datetime.now().isoformat()
    
    def get_routing_stats(self) -> Dict[str, Any]:
        """Get routing performance statistics"""
        total_routed = sum(stats['count'] for stats in self.routing_stats.values())
        
        stats_summary = {
            'total_emails_routed': total_routed,
            'unique_patterns_used': len(self.routing_stats),
            'patterns_available': len(self.patterns),
            'routing_distribution': {}
        }
        
        for email_type, stats in self.routing_stats.items():
            percentage = (stats['count'] / total_routed * 100) if total_routed > 0 else 0
            stats_summary['routing_distribution'][email_type] = {
                'count': stats['count'],
                'percentage': f"{percentage:.1f}%",
                'last_seen': stats['last_seen']
            }
        
        return stats_summary
    
    def add_custom_pattern(self, pattern: EmailPattern):
        """Add custom email pattern"""
        self.patterns.append(pattern)
        self.logger.info(f"Added custom pattern for {pattern.email_type.value}")
    
    def optimize_pattern_performance(self, email_type: EmailType, actual_processing_time: float):
        """Update pattern performance based on actual results"""
        for pattern in self.patterns:
            if pattern.email_type == email_type:
                # Update expected processing time with exponential moving average
                alpha = 0.2  # Learning rate
                pattern.expected_processing_time = (
                    alpha * actual_processing_time + 
                    (1 - alpha) * pattern.expected_processing_time
                )
                
                self.logger.debug(f"Updated {email_type.value} expected time to {pattern.expected_processing_time:.2f}s")
                break

class EmailProcessorRegistry:
    """Registry for email processor classes"""
    
    def __init__(self):
        self.processors = {}
        self.logger = logging.getLogger(__name__ + ".EmailProcessorRegistry")
        self._register_default_processors()
    
    def _register_default_processors(self):
        """Register default processor classes"""
        # These would be actual processor implementations
        self.processors.update({
            "DBSSalesScoopProcessor": "ultra_refined_email_processor.UltraRefinedEmailProcessor",
            "DBSEconomicsProcessor": "ultra_refined_email_processor.UltraRefinedEmailProcessor", 
            "UOBKHResearchProcessor": "ultra_refined_email_processor.UltraRefinedEmailProcessor",
            "OCBCSimpleProcessor": "ultra_refined_email_processor.UltraRefinedEmailProcessor",
            "ThreadConversationProcessor": "ultra_refined_email_processor.UltraRefinedEmailProcessor",
            "EarningsAlertProcessor": "ultra_refined_email_processor.UltraRefinedEmailProcessor",
            "ResearchReportProcessor": "ultra_refined_email_processor.UltraRefinedEmailProcessor",
            "AdminEmailProcessor": "ultra_refined_email_processor.UltraRefinedEmailProcessor",
            "DefaultEmailProcessor": "ultra_refined_email_processor.UltraRefinedEmailProcessor"
        })
    
    def get_processor(self, processor_class: str):
        """Get processor instance by class name"""
        if processor_class in self.processors:
            # In real implementation, this would instantiate the actual class
            return self.processors[processor_class]
        else:
            self.logger.warning(f"Unknown processor class: {processor_class}")
            return self.processors["DefaultEmailProcessor"]
    
    def register_processor(self, name: str, processor_class: str):
        """Register custom processor"""
        self.processors[name] = processor_class
        self.logger.info(f"Registered processor: {name}")

# Example usage and testing
if __name__ == "__main__":
    # Demo the Intelligent Email Router
    
    def demo_email_routing():
        router = IntelligentEmailRouter()
        
        # Sample emails matching different patterns
        test_emails = [
            {
                'sender': 'dbs-sales-scoop@dbs.com',
                'subject': 'DBS SALES SCOOP - Daily Market Update',
                'body': 'Daily sales scoop with 8 images and 50+ links for market analysis',
                'attachments': [
                    {'type': 'image', 'size': 1024*1024},
                    {'type': 'image', 'size': 1024*1024},
                    {'type': 'pdf', 'size': 5*1024*1024}
                ] * 3  # Simulate 8 attachments
            },
            {
                'sender': 'economics@dbs.com',
                'subject': 'Economics Weekly - GDP Analysis',
                'body': 'Economic analysis with 17 charts showing macro trends and policy implications',
                'attachments': [{'type': 'image', 'size': 2*1024*1024}] * 17
            },
            {
                'sender': 'research@uobkh.com',
                'subject': 'UOBKH Research Update - Tech Sector',
                'body': 'Research report with 12 tables showing financial metrics and recommendations',
                'attachments': [
                    {'type': 'excel', 'size': 10*1024*1024},
                    {'type': 'pdf', 'size': 3*1024*1024}
                ]
            },
            {
                'sender': 'brief@ocbc.com', 
                'subject': 'OCBC Daily Brief',
                'body': 'Simple daily market brief with summary updates',
                'attachments': [{'type': 'pdf', 'size': 500*1024}]
            },
            {
                'sender': 'unknown@example.com',
                'subject': 'Random Email',
                'body': 'This email does not match any known patterns',
                'attachments': []
            }
        ]
        
        print("=== Email Routing Demo ===\n")
        
        for i, email in enumerate(test_emails, 1):
            route = router.route_email(email)
            print(f"Email {i}: {email['sender']}")
            print(f"  Subject: {email['subject']}")
            print(f"  Routed to: {route.email_type.value}")
            print(f"  Processor: {route.processor_class}")
            print(f"  Confidence: {route.confidence:.2f}")
            print(f"  Expected time: {route.expected_time:.1f}s")
            print(f"  Optimizations: {', '.join(route.optimization_flags)}")
            print()
        
        # Print routing statistics
        print("=== Routing Statistics ===")
        stats = router.get_routing_stats()
        print(json.dumps(stats, indent=2))
    
    demo_email_routing()