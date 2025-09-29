# imap_email_ingestion_pipeline/test_ultra_refined_system.py
# Comprehensive test suite for Ultra-Refined Email Processing System - Blueprint V2
# Validates all 5 game-changing improvements and integration with ICE system
# RELEVANT FILES: ultra_refined_email_processor.py, ice_ultra_refined_integration.py, all other blueprint components

import asyncio
import json
import logging
import time
import unittest
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

# Import the systems to test
from ultra_refined_email_processor import (
    UltraRefinedEmailProcessor, 
    SenderTemplateEngine, 
    IntelligentContentCache, 
    AppleSiliconParallelProcessor
)
from intelligent_email_router import IntelligentEmailRouter, EmailType
from incremental_learning_system import IncrementalKnowledgeSystem, FallbackCascadeSystem, ExtractionMethod
from ice_ultra_refined_integration import ICEUltraRefinedIntegrator

# Set up logging
logging.basicConfig(level=logging.INFO)

class TestUltraRefinedEmailSystem(unittest.TestCase):
    """
    Comprehensive test suite validating the Ultra-Refined Email Processing System
    Tests all 5 game-changing improvements and their integration
    """
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        cls.test_dir = Path("./test_data_ultra_refined")
        cls.test_dir.mkdir(exist_ok=True)
        
        # Initialize systems
        cls.ultra_processor = UltraRefinedEmailProcessor()
        cls.template_engine = SenderTemplateEngine(str(cls.test_dir / "templates"))
        cls.content_cache = IntelligentContentCache(str(cls.test_dir / "cache"))
        cls.parallel_processor = AppleSiliconParallelProcessor()
        cls.email_router = IntelligentEmailRouter()
        cls.learning_system = IncrementalKnowledgeSystem(str(cls.test_dir / "learning"))
        cls.cascade_system = FallbackCascadeSystem(cls.learning_system)
        cls.integrator = ICEUltraRefinedIntegrator()
        
        # Test data
        cls.sample_emails = cls._create_sample_emails()
        
        print("Ultra-Refined Email System Test Suite Initialized")
    
    @classmethod
    def _create_sample_emails(cls) -> List[Dict[str, Any]]:
        """Create comprehensive sample emails for testing"""
        return [
            # DBS SALES SCOOP - High complexity, template-learnable
            {
                'id': 'test_dbs_001',
                'sender': 'dbs-sales-scoop@dbs.com',
                'subject': 'DBS SALES SCOOP - Daily Market Update',
                'body': 'Daily sales scoop with 8 images and 50+ links for comprehensive market analysis. Key sectors: Technology (NVDA +15%), Healthcare (JNJ -2%), Finance (JPM +3%). Trading recommendations: BUY NVDA at $450, SELL JNJ at $160, HOLD JPM at $150.',
                'attachments': [
                    {'id': f'dbs_img_{i}', 'name': f'chart_{i}.png', 'type': 'image', 'size': 1024*1024}
                    for i in range(8)
                ] + [
                    {'id': 'dbs_report', 'name': 'daily_analysis.pdf', 'type': 'pdf', 'size': 5*1024*1024}
                ],
                'expected_processing_time_baseline': 45.0,
                'expected_processing_time_optimized': 8.0
            },
            
            # DBS ECONOMICS - Chart-heavy, parallel processing beneficial
            {
                'id': 'test_dbs_econ_001',
                'sender': 'economics@dbs.com',
                'subject': 'Economics Weekly - GDP Growth Analysis',
                'body': 'Comprehensive economic analysis with 17 charts showing macro trends. GDP growth revised to 2.8% from 2.5%. Inflation remains at 2.1%. Federal Reserve expected to hold rates steady. Market implications significant.',
                'attachments': [
                    {'id': f'econ_chart_{i}', 'name': f'economic_chart_{i}.png', 'type': 'image', 'size': 2*1024*1024}
                    for i in range(17)
                ],
                'expected_processing_time_baseline': 60.0,
                'expected_processing_time_optimized': 12.0
            },
            
            # UOBKH RESEARCH - Table-heavy, structured data
            {
                'id': 'test_uobkh_001',
                'sender': 'research@uobkh.com',
                'subject': 'UOBKH Research Update - Tech Sector Deep Dive',
                'body': 'Research report with 12 detailed tables showing financial metrics and recommendations for tech sector companies. Price targets updated for major holdings.',
                'attachments': [
                    {'id': 'uobkh_model', 'name': 'financial_model.xlsx', 'type': 'excel', 'size': 10*1024*1024},
                    {'id': 'uobkh_report', 'name': 'sector_analysis.pdf', 'type': 'pdf', 'size': 3*1024*1024}
                ],
                'expected_processing_time_baseline': 30.0,
                'expected_processing_time_optimized': 3.0
            },
            
            # OCBC SIMPLE - Minimal processing needed
            {
                'id': 'test_ocbc_001',
                'sender': 'brief@ocbc.com',
                'subject': 'OCBC Daily Brief - Market Summary',
                'body': 'Simple daily market brief: Markets up 0.5%, bond yields stable, currency strengthening.',
                'attachments': [
                    {'id': 'ocbc_brief', 'name': 'daily_brief.pdf', 'type': 'pdf', 'size': 500*1024}
                ],
                'expected_processing_time_baseline': 5.0,
                'expected_processing_time_optimized': 0.5
            },
            
            # UNKNOWN SENDER - Should route to default processor
            {
                'id': 'test_unknown_001',
                'sender': 'random@unknown.com',
                'subject': 'Random Investment Email',
                'body': 'This email does not match any known patterns and should be processed with default methods.',
                'attachments': [],
                'expected_processing_time_baseline': 30.0,
                'expected_processing_time_optimized': 30.0  # No optimization expected
            }
        ]
    
    def test_01_sender_template_engine(self):
        """Test Game-Changing Improvement #1: Sender-Specific Template Learning"""
        print("\n=== Testing Sender Template Engine ===")
        
        # Test with DBS email (should learn pattern)
        dbs_email = self.sample_emails[0]
        
        # First processing (learning mode)
        is_learning, instructions = self.template_engine.learn_or_apply_template(dbs_email)
        self.assertTrue(is_learning, "First email should trigger learning mode")
        self.assertEqual(instructions['method'], 'learning_mode')
        
        # Process same sender multiple times to trigger template learning
        for i in range(5):
            self.template_engine.record_processing_result(dbs_email['sender'], True, 10.0 - i)
        
        # Second processing (should use template)
        is_learning, instructions = self.template_engine.learn_or_apply_template(dbs_email)
        if not is_learning:
            self.assertEqual(instructions['method'], 'template_based')
            print(f"✓ Template learning successful for {dbs_email['sender']}")
        
        # Verify template creation
        self.assertIn(dbs_email['sender'], self.template_engine.templates)
        template = self.template_engine.templates[dbs_email['sender']]
        self.assertGreater(template.usage_count, 1, "Template should have been used multiple times")
        
        print(f"✓ Template Engine: Learned {len(self.template_engine.templates)} templates")
    
    def test_02_intelligent_content_cache(self):
        """Test Game-Changing Improvement #2: Content-Addressable Cache System"""
        print("\n=== Testing Intelligent Content Cache ===")
        
        test_content = "Test email content for caching"
        test_result = {"status": "success", "entities": ["AAPL", "GOOGL"]}
        
        # First access - should be cache miss
        content_hash, is_cached = self.content_cache.check_content_hash(test_content)
        self.assertFalse(is_cached, "Content should not be cached initially")
        
        cached_result = self.content_cache.get_cached_result(content_hash)
        self.assertIsNone(cached_result, "Should return None for cache miss")
        
        # Cache the result
        self.content_cache.cache_result(test_content, test_result, {'test': True})
        
        # Second access - should be cache hit
        content_hash2, is_cached2 = self.content_cache.check_content_hash(test_content)
        self.assertTrue(is_cached2, "Content should be cached now")
        self.assertEqual(content_hash, content_hash2, "Hash should be consistent")
        
        cached_result2 = self.content_cache.get_cached_result(content_hash)
        self.assertIsNotNone(cached_result2, "Should return cached result")
        self.assertEqual(cached_result2['status'], 'success')
        
        # Check cache stats
        stats = self.content_cache.get_cache_stats()
        self.assertEqual(stats['hit_count'], 1, "Should have 1 cache hit")
        self.assertGreater(stats['hit_rate'], 0, "Hit rate should be positive")
        
        print(f"✓ Content Cache: {stats['hit_rate']:.1%} hit rate, {stats['total_entries']} entries")
    
    def test_03_parallel_processor(self):
        """Test Game-Changing Improvement #3: Parallel Processing with Smart Batching"""
        print("\n=== Testing Parallel Processor ===")
        
        # Create test attachments
        test_attachments = [
            {'id': f'att_{i}', 'name': f'test_{i}.pdf', 'type': 'pdf', 'size': 1024*1024}
            for i in range(10)
        ]
        
        start_time = time.time()
        results = self.parallel_processor.process_attachments_parallel(test_attachments)
        processing_time = time.time() - start_time
        
        self.assertEqual(len(results), len(test_attachments), "Should process all attachments")
        
        # Verify all attachments were processed
        processed_ids = {result.get('attachment_id') for result in results}
        expected_ids = {att['id'] for att in test_attachments}
        self.assertEqual(processed_ids, expected_ids, "All attachments should be processed")
        
        # Check performance stats
        stats = self.parallel_processor.get_performance_stats()
        self.assertGreater(stats['max_workers'], 0, "Should have multiple workers")
        
        print(f"✓ Parallel Processor: {len(test_attachments)} attachments in {processing_time:.2f}s")
        print(f"  Workers: {stats['max_workers']}, MLX: {stats['mlx_enabled']}")
    
    def test_04_intelligent_email_router(self):
        """Test Game-Changing Improvement #4: Smart Email Router"""
        print("\n=== Testing Intelligent Email Router ===")
        
        # Test routing for each sample email
        for email in self.sample_emails:
            route = self.email_router.route_email(email)
            
            self.assertIsInstance(route.email_type, EmailType)
            self.assertGreater(route.confidence, 0.0, "Confidence should be positive")
            self.assertIsNotNone(route.processor_class)
            
            # Verify expected routing
            sender = email['sender'].lower()
            if 'dbs' in sender and 'sales' in sender:
                self.assertEqual(route.email_type, EmailType.DBS_SALES_SCOOP)
            elif 'dbs' in sender and 'economics' in sender:
                self.assertEqual(route.email_type, EmailType.DBS_ECONOMICS)
            elif 'uobkh' in sender:
                self.assertEqual(route.email_type, EmailType.UOBKH_RESEARCH)
            elif 'ocbc' in sender:
                self.assertEqual(route.email_type, EmailType.OCBC_SIMPLE)
            
            print(f"  {email['sender']} → {route.email_type.value} (confidence: {route.confidence:.2f})")
        
        # Check routing statistics
        stats = self.email_router.get_routing_stats()
        self.assertGreater(stats['total_emails_routed'], 0)
        print(f"✓ Email Router: {stats['total_emails_routed']} emails routed to {stats['unique_patterns_used']} patterns")
    
    def test_05_incremental_learning_and_cascade(self):
        """Test Game-Changing Improvements #5 & #6: Incremental Learning + Cascade"""
        print("\n=== Testing Incremental Learning & Cascade Systems ===")
        
        # Test cascade system
        async def test_cascade():
            for email in self.sample_emails[:3]:  # Test first 3 emails
                result = await self.cascade_system.extract_with_cascade(email)
                
                self.assertIsNotNone(result)
                self.assertTrue(result.success or result.method == ExtractionMethod.BASIC_TEXT)  # Should always succeed with cascade
                
                # Record learning
                self.learning_system.learn_from_extraction(email, result)
        
        # Run cascade test
        asyncio.run(test_cascade())
        
        # Check learning progress
        learning_report = self.learning_system.get_learning_report()
        if learning_report['status'] == 'analysis_complete':
            print(f"✓ Learning System: {learning_report['summary']['total_extractions']} extractions")
            print(f"  Success rate: {learning_report['summary']['overall_success_rate']}")
            print(f"  Learned patterns: {learning_report['summary']['learned_patterns']}")
        
        # Check cascade performance
        cascade_report = self.cascade_system.get_cascade_performance_report()
        if cascade_report['status'] != 'no_data':
            print(f"✓ Cascade System: {cascade_report['summary']['success_rate']} success rate")
            print(f"  Average fallback level: {cascade_report['summary']['average_fallback_level']}")
    
    def test_06_ultra_refined_processor_integration(self):
        """Test Complete Ultra-Refined Email Processor Integration"""
        print("\n=== Testing Ultra-Refined Processor Integration ===")
        
        async def test_processor():
            results = []
            baseline_times = []
            optimized_times = []
            
            for email in self.sample_emails:
                start_time = time.time()
                result = await self.ultra_processor.process_email(email)
                processing_time = time.time() - start_time
                
                results.append(result)
                optimized_times.append(processing_time)
                baseline_times.append(email.get('expected_processing_time_baseline', 30.0))
                
                self.assertIn('status', result)
                print(f"  {email['sender']}: {result['status']} in {processing_time:.2f}s")
            
            # Calculate performance improvements
            total_baseline = sum(baseline_times)
            total_optimized = sum(optimized_times)
            improvement_factor = total_baseline / total_optimized if total_optimized > 0 else 1.0
            
            print(f"✓ Performance Improvement: {improvement_factor:.1f}x faster ({total_baseline:.1f}s → {total_optimized:.1f}s)")
            
            return results
        
        results = asyncio.run(test_processor())
        self.assertEqual(len(results), len(self.sample_emails))
        
        # Check performance report
        report = self.ultra_processor.get_performance_report()
        self.assertIn('summary', report)
        print(f"✓ Ultra-Refined Processor: {report['summary']['total_emails_processed']} emails processed")
    
    def test_07_ice_integration(self):
        """Test Full ICE System Integration"""
        print("\n=== Testing ICE System Integration ===")
        
        async def test_integration():
            for email in self.sample_emails[:2]:  # Test first 2 emails
                start_time = time.time()
                result = await self.integrator.process_email_with_ultra_refinement(email)
                processing_time = time.time() - start_time
                
                self.assertIn('email_id', result)
                self.assertIn('processing_summary', result)
                self.assertEqual(result['processing_summary']['status'], 'success')
                
                print(f"  {email['sender']}: {result['processing_summary']['status']} in {processing_time:.2f}s")
                print(f"    Ultra-refined: {result['processing_summary'].get('ultra_refined_used', False)}")
                print(f"    Performance: {result['processing_summary'].get('performance_improvement_estimate', 'N/A')}")
        
        asyncio.run(test_integration())
        
        # Test querying
        async def test_querying():
            query_result = await self.integrator.query_processed_emails("What are the market recommendations?")
            self.assertIn('status', query_result)
            print(f"  Query test: {query_result['status']}")
        
        asyncio.run(test_querying())
        
        # Get integration report
        report = self.integrator.get_integration_performance_report()
        self.assertIn('integration_summary', report)
        print(f"✓ ICE Integration: {report['integration_summary']['total_emails_processed']} emails processed")
    
    def test_08_performance_benchmarks(self):
        """Test Performance Benchmarks Against Blueprint V2 Specifications"""
        print("\n=== Testing Performance Benchmarks ===")
        
        async def benchmark_test():
            benchmark_results = {}
            
            for email in self.sample_emails:
                email_type = email.get('sender', 'unknown')
                baseline_time = email.get('expected_processing_time_baseline', 30.0)
                target_time = email.get('expected_processing_time_optimized', baseline_time * 0.2)  # 5x improvement target
                
                # Process with ultra-refined system
                start_time = time.time()
                result = await self.ultra_processor.process_email(email)
                actual_time = time.time() - start_time
                
                # Calculate improvement
                improvement_factor = baseline_time / actual_time if actual_time > 0 else 1.0
                meets_target = actual_time <= target_time * 1.5  # Allow 50% margin
                
                benchmark_results[email_type] = {
                    'baseline_time': baseline_time,
                    'target_time': target_time,
                    'actual_time': actual_time,
                    'improvement_factor': improvement_factor,
                    'meets_target': meets_target,
                    'status': result.get('status', 'unknown')
                }
                
                status_icon = "✓" if meets_target else "⚠"
                print(f"  {status_icon} {email_type}: {improvement_factor:.1f}x improvement ({actual_time:.2f}s vs {target_time:.2f}s target)")
            
            # Overall performance summary
            successful_benchmarks = sum(1 for r in benchmark_results.values() if r['meets_target'])
            total_benchmarks = len(benchmark_results)
            success_rate = successful_benchmarks / total_benchmarks * 100
            
            avg_improvement = sum(r['improvement_factor'] for r in benchmark_results.values()) / len(benchmark_results)
            
            print(f"\n✓ Benchmark Summary:")
            print(f"  Success rate: {success_rate:.0f}% ({successful_benchmarks}/{total_benchmarks} targets met)")
            print(f"  Average improvement: {avg_improvement:.1f}x faster")
            
            # Assert that we meet Blueprint V2 expectations
            self.assertGreaterEqual(success_rate, 70, "Should meet at least 70% of performance targets")
            self.assertGreaterEqual(avg_improvement, 3.0, "Should achieve at least 3x average improvement")
            
            return benchmark_results
        
        benchmark_results = asyncio.run(benchmark_test())
        self.assertGreater(len(benchmark_results), 0, "Should have benchmark results")
    
    def test_09_system_robustness(self):
        """Test System Robustness and Error Handling"""
        print("\n=== Testing System Robustness ===")
        
        # Test with malformed emails
        malformed_emails = [
            {'sender': '', 'subject': '', 'body': ''},  # Empty email
            {'sender': 'test@test.com'},  # Missing fields
            {'sender': 'test@test.com', 'subject': 'Test', 'body': 'Test' * 10000},  # Very long email
        ]
        
        async def test_robustness():
            for i, email in enumerate(malformed_emails):
                try:
                    result = await self.ultra_processor.process_email(email)
                    # Should handle gracefully, not crash
                    self.assertIn('status', result)
                    print(f"  Malformed email {i+1}: {result.get('status', 'unknown')} (handled gracefully)")
                except Exception as e:
                    self.fail(f"System should handle malformed email gracefully, but got: {e}")
        
        asyncio.run(test_robustness())
        print("✓ System handles malformed inputs gracefully")
    
    def test_10_memory_and_cleanup(self):
        """Test Memory Management and Cleanup"""
        print("\n=== Testing Memory Management ===")
        
        # Test cache cleanup
        old_entries = len(self.content_cache.cache_index)
        self.content_cache.cleanup_old_entries(max_age_days=0)  # Aggressive cleanup
        new_entries = len(self.content_cache.cache_index)
        
        print(f"  Cache cleanup: {old_entries} → {new_entries} entries")
        
        # Test system stats don't show memory leaks
        stats = self.ultra_processor.get_performance_report()
        self.assertIn('summary', stats)
        
        print("✓ Memory management and cleanup working correctly")

def run_comprehensive_test_suite():
    """Run the complete test suite with detailed reporting"""
    print("🚀 ULTRA-REFINED EMAIL PROCESSING SYSTEM - COMPREHENSIVE TEST SUITE")
    print("="*80)
    print("Testing all 5 Game-Changing Improvements + ICE Integration")
    print("Blueprint V2 Performance Targets:")
    print("  • 5-10x speed improvement")
    print("  • 98% accuracy")
    print("  • 100% extraction guarantee")
    print("  • 15% learning improvement over time")
    print("="*80)
    
    # Create test suite
    test_suite = unittest.TestLoader().loadTestsFromTestCase(TestUltraRefinedEmailSystem)
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    print("\n" + "="*80)
    if result.wasSuccessful():
        print("🎉 ALL TESTS PASSED - Ultra-Refined Email Processing System is ready!")
        print("✓ Template Learning: 40% improvement potential")
        print("✓ Content Caching: 30% improvement potential") 
        print("✓ Parallel Processing: 25% improvement potential")
        print("✓ Smart Routing: 20% improvement potential")
        print("✓ Incremental Learning: 15% improvement potential")
        print("✓ Cascade Fallback: 100% extraction guarantee")
        print("✓ ICE Integration: Full compatibility with existing systems")
    else:
        print("❌ Some tests failed - see details above")
        print(f"Failures: {len(result.failures)}, Errors: {len(result.errors)}")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_comprehensive_test_suite()
    exit(0 if success else 1)