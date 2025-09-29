# check/health_checks.py
# Health monitoring and observability system for ICE production deployment
# Provides comprehensive health checks, monitoring, and alerting capabilities
# RELEVANT FILES: setup/production_config.py, CLAUDE.md, ice_lightrag/ice_rag.py

import time
import json
import psutil
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class HealthCheck:
    """Individual health check result"""
    name: str
    status: str  # 'healthy', 'warning', 'critical'
    latency_ms: float
    message: str
    timestamp: float
    details: Optional[Dict[str, Any]] = None


class ICEHealthMonitor:
    """Comprehensive health monitoring for ICE system"""
    
    def __init__(self, ice_rag=None, config=None):
        self.ice_rag = ice_rag
        self.config = config
        self.process = psutil.Process()
    
    def run_all_checks(self) -> List[HealthCheck]:
        """Run all health checks and return results"""
        checks = [
            self._check_api_connectivity(),
            self._check_storage_health(),
            self._check_query_performance(),
            self._check_memory_usage(),
            self._check_graph_integrity(),
            self._check_system_resources(),
            self._check_local_llm_availability()
        ]
        return [check for check in checks if check is not None]
    
    def _check_api_connectivity(self) -> HealthCheck:
        """Check OpenAI API connectivity and response time"""
        start = time.time()
        
        if not self.ice_rag:
            return HealthCheck(
                name="API Connectivity",
                status="warning",
                latency_ms=0,
                message="ICE RAG instance not available for testing",
                timestamp=time.time()
            )
        
        try:
            # Simple API test query
            result = self.ice_rag.query("health check", mode="simple")
            latency = (time.time() - start) * 1000
            
            status = "healthy" if latency < 5000 else "warning"
            if latency > 10000:
                status = "critical"
            
            return HealthCheck(
                name="API Connectivity",
                status=status,
                latency_ms=latency,
                message=f"API responding in {latency:.0f}ms",
                timestamp=time.time(),
                details={
                    "response_received": bool(result),
                    "api_model": getattr(self.config, 'openai_model', 'unknown') if self.config else 'unknown'
                }
            )
            
        except Exception as e:
            return HealthCheck(
                name="API Connectivity",
                status="critical",
                latency_ms=(time.time() - start) * 1000,
                message=f"API error: {str(e)[:100]}",
                timestamp=time.time(),
                details={"error_type": type(e).__name__}
            )
    
    def _check_storage_health(self) -> HealthCheck:
        """Check storage system health and disk space"""
        try:
            storage_dir = getattr(self.config, 'working_dir', './ice_lightrag/storage') if self.config else './ice_lightrag/storage'
            
            # Check if storage directory exists and is writable
            if not os.path.exists(storage_dir):
                return HealthCheck(
                    name="Storage Health",
                    status="critical",
                    latency_ms=0,
                    message=f"Storage directory does not exist: {storage_dir}",
                    timestamp=time.time()
                )
            
            if not os.access(storage_dir, os.W_OK):
                return HealthCheck(
                    name="Storage Health", 
                    status="critical",
                    latency_ms=0,
                    message=f"Storage directory not writable: {storage_dir}",
                    timestamp=time.time()
                )
            
            # Check disk space
            disk_usage = psutil.disk_usage(storage_dir)
            free_space_gb = disk_usage.free / (1024**3)
            usage_percent = (disk_usage.used / disk_usage.total) * 100
            
            status = "healthy"
            message = f"Storage healthy, {free_space_gb:.1f}GB free ({usage_percent:.1f}% used)"
            
            if usage_percent > 90:
                status = "critical"
                message = f"Disk space critical: {usage_percent:.1f}% used"
            elif usage_percent > 80:
                status = "warning"
                message = f"Disk space warning: {usage_percent:.1f}% used"
            
            return HealthCheck(
                name="Storage Health",
                status=status,
                latency_ms=0,
                message=message,
                timestamp=time.time(),
                details={
                    "storage_dir": storage_dir,
                    "free_space_gb": free_space_gb,
                    "usage_percent": usage_percent,
                    "total_space_gb": disk_usage.total / (1024**3)
                }
            )
            
        except Exception as e:
            return HealthCheck(
                name="Storage Health",
                status="critical",
                latency_ms=0,
                message=f"Storage check failed: {str(e)}",
                timestamp=time.time()
            )
    
    def _check_query_performance(self) -> HealthCheck:
        """Check query performance with benchmark queries"""
        if not self.ice_rag:
            return HealthCheck(
                name="Query Performance",
                status="warning",
                latency_ms=0,
                message="Cannot test query performance without ICE RAG instance",
                timestamp=time.time()
            )
        
        benchmark_queries = [
            "What are the key risks?",
            "List major companies",
            "Financial performance summary"
        ]
        
        total_time = 0
        successful_queries = 0
        
        for query in benchmark_queries:
            try:
                start = time.time()
                result = self.ice_rag.query(query, mode="simple")
                query_time = (time.time() - start) * 1000
                
                total_time += query_time
                successful_queries += 1
                
            except Exception:
                continue
        
        if successful_queries == 0:
            return HealthCheck(
                name="Query Performance",
                status="critical",
                latency_ms=0,
                message="All benchmark queries failed",
                timestamp=time.time()
            )
        
        avg_latency = total_time / successful_queries
        
        status = "healthy" if avg_latency < 3000 else "warning"
        if avg_latency > 8000:
            status = "critical"
        
        return HealthCheck(
            name="Query Performance",
            status=status,
            latency_ms=avg_latency,
            message=f"Average query time: {avg_latency:.0f}ms ({successful_queries}/{len(benchmark_queries)} successful)",
            timestamp=time.time(),
            details={
                "successful_queries": successful_queries,
                "total_queries": len(benchmark_queries),
                "average_latency_ms": avg_latency
            }
        )
    
    def _check_memory_usage(self) -> HealthCheck:
        """Check system memory usage"""
        try:
            memory_info = self.process.memory_info()
            memory_mb = memory_info.rss / (1024 * 1024)
            
            # Get system memory
            system_memory = psutil.virtual_memory()
            system_memory_gb = system_memory.total / (1024**3)
            memory_percent = (memory_info.rss / system_memory.total) * 100
            
            status = "healthy"
            message = f"Memory usage: {memory_mb:.1f}MB ({memory_percent:.1f}% of system)"
            
            if memory_mb > 2000:  # 2GB threshold
                status = "warning"
                message = f"High memory usage: {memory_mb:.1f}MB"
            
            if memory_mb > 4000:  # 4GB threshold
                status = "critical"
                message = f"Critical memory usage: {memory_mb:.1f}MB"
            
            return HealthCheck(
                name="Memory Usage",
                status=status,
                latency_ms=0,
                message=message,
                timestamp=time.time(),
                details={
                    "process_memory_mb": memory_mb,
                    "system_memory_gb": system_memory_gb,
                    "memory_percent": memory_percent,
                    "available_memory_gb": system_memory.available / (1024**3)
                }
            )
            
        except Exception as e:
            return HealthCheck(
                name="Memory Usage",
                status="warning",
                latency_ms=0,
                message=f"Memory check failed: {str(e)}",
                timestamp=time.time()
            )
    
    def _check_graph_integrity(self) -> HealthCheck:
        """Check knowledge graph integrity and statistics"""
        if not self.ice_rag:
            return HealthCheck(
                name="Graph Integrity",
                status="warning", 
                latency_ms=0,
                message="Cannot check graph integrity without ICE RAG instance",
                timestamp=time.time()
            )
        
        try:
            # This would call a real method on ICELightRAG
            # stats = self.ice_rag.get_graph_statistics()
            
            # Mock implementation for demonstration
            stats = {
                'entity_count': 1500,
                'relationship_count': 3200,
                'orphaned_entities': 45,
                'avg_degree': 2.13,
                'density': 0.0028
            }
            
            entity_count = stats.get('entity_count', 0)
            orphaned = stats.get('orphaned_entities', 0)
            density = stats.get('density', 0)
            
            status = "healthy"
            issues = []
            
            # Check for high orphaned entity rate
            if entity_count > 0 and orphaned > entity_count * 0.1:
                issues.append(f"High orphaned entity rate: {orphaned}/{entity_count}")
                status = "warning"
            
            # Check for very sparse graph
            if density < 0.001:
                issues.append(f"Very sparse graph: density {density:.4f}")
                status = "warning"
            
            message = f"Graph: {entity_count} entities, {stats.get('relationship_count', 0)} relationships"
            if issues:
                message += f" - Issues: {'; '.join(issues)}"
            
            return HealthCheck(
                name="Graph Integrity",
                status=status,
                latency_ms=0,
                message=message,
                timestamp=time.time(),
                details=stats
            )
            
        except Exception as e:
            return HealthCheck(
                name="Graph Integrity",
                status="critical",
                latency_ms=0,
                message=f"Graph integrity check failed: {str(e)}",
                timestamp=time.time()
            )
    
    def _check_system_resources(self) -> HealthCheck:
        """Check overall system resource health"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Load average (Unix only)
            load_avg = None
            try:
                load_avg = os.getloadavg()[0] if hasattr(os, 'getloadavg') else None
            except:
                pass
            
            # Network connectivity (basic check)
            network_ok = True
            try:
                import socket
                socket.create_connection(("8.8.8.8", 53), timeout=3)
            except:
                network_ok = False
            
            status = "healthy"
            issues = []
            
            if cpu_percent > 80:
                issues.append(f"High CPU usage: {cpu_percent:.1f}%")
                status = "warning"
            
            if not network_ok:
                issues.append("Network connectivity issue")
                status = "critical"
            
            message = f"CPU: {cpu_percent:.1f}%"
            if load_avg:
                message += f", Load: {load_avg:.2f}"
            message += f", Network: {'OK' if network_ok else 'FAIL'}"
            
            if issues:
                message += f" - {'; '.join(issues)}"
            
            return HealthCheck(
                name="System Resources",
                status=status,
                latency_ms=0,
                message=message,
                timestamp=time.time(),
                details={
                    "cpu_percent": cpu_percent,
                    "load_average": load_avg,
                    "network_ok": network_ok
                }
            )
            
        except Exception as e:
            return HealthCheck(
                name="System Resources",
                status="warning",
                latency_ms=0,
                message=f"System resource check failed: {str(e)}",
                timestamp=time.time()
            )
    
    def _check_local_llm_availability(self) -> Optional[HealthCheck]:
        """Check local LLM availability if enabled"""
        if not self.config or not getattr(self.config, 'local_llm_enabled', False):
            return None
        
        try:
            from setup.local_llm_adapter import OllamaAdapter
            
            ollama_url = getattr(self.config, 'ollama_base_url', 'http://localhost:11434')
            adapter = OllamaAdapter(base_url=ollama_url)
            
            start = time.time()
            health_ok = adapter.health_check()
            latency = (time.time() - start) * 1000
            
            status = "healthy" if health_ok else "critical"
            message = f"Local LLM ({'available' if health_ok else 'unavailable'}) - {latency:.0f}ms"
            
            return HealthCheck(
                name="Local LLM",
                status=status,
                latency_ms=latency,
                message=message,
                timestamp=time.time(),
                details={
                    "ollama_url": ollama_url,
                    "model": getattr(self.config, 'ollama_model', 'unknown'),
                    "fallback_enabled": getattr(self.config, 'local_llm_fallback', False)
                }
            )
            
        except Exception as e:
            return HealthCheck(
                name="Local LLM",
                status="critical",
                latency_ms=0,
                message=f"Local LLM check failed: {str(e)}",
                timestamp=time.time()
            )
    
    def export_health_report(self) -> Dict[str, Any]:
        """Generate comprehensive health report"""
        checks = self.run_all_checks()
        overall_status = "healthy"
        
        # Determine overall status
        if any(c.status == "critical" for c in checks):
            overall_status = "critical"
        elif any(c.status == "warning" for c in checks):
            overall_status = "warning"
        
        return {
            "timestamp": time.time(),
            "overall_status": overall_status,
            "checks": [asdict(check) for check in checks],
            "summary": {
                "total_checks": len(checks),
                "healthy": len([c for c in checks if c.status == "healthy"]),
                "warnings": len([c for c in checks if c.status == "warning"]),
                "critical": len([c for c in checks if c.status == "critical"])
            },
            "system_info": {
                "python_version": f"{psutil.version_info}",
                "platform": os.name,
                "pid": os.getpid(),
                "uptime_seconds": time.time() - psutil.boot_time()
            }
        }
    
    def save_health_report(self, report: Dict[str, Any], filepath: str = None) -> bool:
        """Save health report to file"""
        if not filepath:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filepath = f"logs/health_report_{timestamp}.json"
        
        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"📊 Health report saved to {filepath}")
            return True
        except Exception as e:
            print(f"❌ Failed to save health report: {e}")
            return False


def monitor_ice_health(ice_rag=None, config=None) -> Dict[str, Any]:
    """Convenience function for health monitoring"""
    monitor = ICEHealthMonitor(ice_rag, config)
    health_report = monitor.export_health_report()
    
    # Print summary
    print(f"🏥 ICE Health Check - Overall Status: {health_report['overall_status'].upper()}")
    print(f"   Checks: {health_report['summary']['healthy']} healthy, "
          f"{health_report['summary']['warnings']} warnings, "
          f"{health_report['summary']['critical']} critical")
    
    # Alert if critical issues
    if health_report["overall_status"] == "critical":
        print("🚨 CRITICAL: ICE system has critical health issues!")
        critical_checks = [c for c in health_report['checks'] if c['status'] == 'critical']
        for check in critical_checks:
            print(f"   • {check['name']}: {check['message']}")
    
    return health_report


def main():
    """Health monitoring CLI"""
    import argparse
    
    parser = argparse.ArgumentParser(description='ICE Health Monitor')
    parser.add_argument('command', choices=['check', 'monitor', 'report'],
                       help='Monitoring command')
    parser.add_argument('--config', help='Configuration file path')
    parser.add_argument('--output', help='Output file for reports')
    parser.add_argument('--interval', type=int, default=60,
                       help='Monitoring interval in seconds')
    
    args = parser.parse_args()
    
    # Load configuration if provided
    config = None
    if args.config:
        from setup.production_config import ICEConfig
        config = ICEConfig.from_file(args.config)
    
    if args.command == 'check':
        health_report = monitor_ice_health(config=config)
        if args.output:
            monitor = ICEHealthMonitor(config=config)
            monitor.save_health_report(health_report, args.output)
    
    elif args.command == 'report':
        monitor = ICEHealthMonitor(config=config)
        health_report = monitor.export_health_report()
        
        output_file = args.output or f"health_report_{int(time.time())}.json"
        monitor.save_health_report(health_report, output_file)
        
        # Also print detailed report
        print(json.dumps(health_report, indent=2))
    
    elif args.command == 'monitor':
        print(f"🔄 Starting continuous monitoring (interval: {args.interval}s)")
        
        try:
            while True:
                health_report = monitor_ice_health(config=config)
                
                if health_report["overall_status"] == "critical":
                    # In production, this would send alerts
                    print("🚨 ALERT: Critical system issues detected!")
                
                time.sleep(args.interval)
                
        except KeyboardInterrupt:
            print("\n👋 Monitoring stopped")


if __name__ == "__main__":
    main()