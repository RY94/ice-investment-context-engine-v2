# tests/test_fixtures.py  
# Shared test fixtures and data for ICE RAG system testing
# Provides consistent test data across LightRAG and LazyGraphRAG tests
# Enables comprehensive validation of both systems with identical scenarios

import os
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json


class TestDataFixtures:
    """Comprehensive test data fixtures for RAG system testing"""
    
    def __init__(self):
        self.test_documents = self._create_test_documents()
        self.test_edges = self._create_test_edges()
        self.test_queries = self._create_test_queries()
        self.expected_results = self._create_expected_results()
    
    def _create_test_documents(self) -> List[Dict[str, str]]:
        """Create realistic financial document test data"""
        return [
            {
                "id": "nvda_q3_2024",
                "type": "earnings_transcript",
                "title": "NVIDIA Q3 2024 Earnings Call",
                "text": """
                NVIDIA Corporation (NVDA) reported exceptional Q3 2024 results with data center 
                revenue surging 206% year-over-year to $14.5 billion. CEO Jensen Huang highlighted 
                the company's leadership in AI infrastructure but noted supply chain dependencies 
                on TSMC for advanced 4nm and 3nm chip manufacturing. The company faces headwinds 
                from export restrictions limiting access to Chinese markets, which previously 
                represented 20-25% of data center sales. Management emphasized diversification 
                efforts but acknowledged TSMC remains critical for cutting-edge GPU production.
                Gaming revenue declined 33% to $2.9 billion due to crypto mining normalization.
                """,
                "entities": ["NVDA", "NVIDIA", "Jensen Huang", "TSMC", "China", "Data Center", "Gaming"],
                "date": "2024-02-21"
            },
            {
                "id": "tsmc_supply_analysis",
                "type": "industry_report", 
                "title": "TSMC Supply Chain Analysis 2024",
                "text": """
                Taiwan Semiconductor Manufacturing Company (TSMC) dominates advanced chip 
                manufacturing with over 70% market share in cutting-edge processes. The company's 
                facilities in Taiwan face increasing geopolitical risks amid US-China tensions. 
                TSMC's advanced 3nm and 4nm processes are critical for AI chips, with major 
                customers including NVIDIA, Apple, and AMD. Recent export control regulations 
                from the US government target advanced semiconductor manufacturing equipment, 
                potentially impacting TSMC's expansion plans. The company has committed to 
                building fabs in Arizona but timeline delays and cost overruns raise concerns 
                about near-term supply diversification.
                """,
                "entities": ["TSMC", "Taiwan", "NVIDIA", "Apple", "AMD", "US", "China", "Arizona"],
                "date": "2024-01-15"
            },
            {
                "id": "china_policy_update",
                "type": "policy_analysis",
                "title": "China Semiconductor Policy Update Q4 2024", 
                "text": """
                China's semiconductor self-sufficiency initiative accelerated in Q4 2024 with 
                new restrictions on rare earth materials exports essential for chip manufacturing. 
                The government imposed counter-sanctions targeting US semiconductor companies, 
                limiting their access to Chinese markets and supply chains. Beijing allocated 
                an additional $50 billion to domestic chip development through the National 
                Integrated Circuit Industry Investment Fund. Chinese companies are prohibited 
                from purchasing advanced AI chips from US suppliers, creating a bifurcated 
                global semiconductor market. This policy directly impacts NVIDIA's revenue 
                projections and forces supply chain restructuring across the industry.
                """,
                "entities": ["China", "US", "NVIDIA", "Rare Earth Materials", "Beijing"],
                "date": "2024-12-01"
            },
            {
                "id": "apple_supply_diversification",
                "type": "corporate_strategy",
                "title": "Apple Supply Chain Diversification Strategy",
                "text": """
                Apple Inc. (AAPL) announced strategic supply chain diversification to reduce 
                dependence on single suppliers and geographic concentrations. The company 
                plans to source advanced chips from multiple foundries including TSMC, Samsung, 
                and emerging players. Apple's chip design team is developing custom silicon 
                optimized for AI workloads, reducing reliance on NVIDIA's GPU architecture. 
                The move comes as geopolitical tensions threaten Taiwan-based manufacturing. 
                Apple allocated $10 billion for supply chain resilience initiatives including 
                alternative sourcing agreements and technology transfer partnerships. Management 
                expects 18-month transition period for critical component diversification.
                """,
                "entities": ["Apple", "AAPL", "TSMC", "Samsung", "NVIDIA", "Taiwan", "AI"],
                "date": "2024-03-10"
            },
            {
                "id": "export_controls_impact",
                "type": "regulatory_analysis",
                "title": "US Export Controls Impact on Semiconductor Industry",
                "text": """
                The Biden Administration's expanded export controls on advanced semiconductors 
                significantly reshape the global chip industry. New restrictions target AI-capable 
                chips with specific performance thresholds, directly affecting NVIDIA's H100 
                and A100 product lines. The controls extend to semiconductor manufacturing 
                equipment, impacting TSMC's capacity expansion plans. Industry estimates suggest 
                $15-20 billion in annual revenue at risk for US chip companies. Export licenses 
                now required for sales to China, creating compliance complexity and delivery delays. 
                The policy aims to prevent Chinese military applications of AI technology while 
                maintaining commercial relationships. Companies must redesign products to comply 
                with new specifications, increasing development costs and time-to-market.
                """,
                "entities": ["Biden Administration", "NVIDIA", "H100", "A100", "TSMC", "China", "AI"],
                "date": "2024-10-07"
            }
        ]
    
    def _create_test_edges(self) -> List[Dict[str, Any]]:
        """Create test edge data for graph construction"""
        return [
            # Core supply chain relationships
            {
                "source": "NVDA",
                "target": "TSMC", 
                "edge_type": "depends_on",
                "weight": 0.95,
                "confidence": 0.92,
                "days_ago": 1,
                "is_positive": False,
                "source_doc": "nvda_q3_2024"
            },
            {
                "source": "TSMC",
                "target": "Taiwan",
                "edge_type": "located_in", 
                "weight": 1.0,
                "confidence": 0.98,
                "days_ago": 0,
                "is_positive": True,
                "source_doc": "tsmc_supply_analysis"
            },
            {
                "source": "Taiwan", 
                "target": "China",
                "edge_type": "geopolitical_tension",
                "weight": 0.85,
                "confidence": 0.88,
                "days_ago": 0,
                "is_positive": False,
                "source_doc": "china_policy_update"
            },
            # Revenue and business relationships
            {
                "source": "NVDA",
                "target": "Data Center Revenue",
                "edge_type": "drives",
                "weight": 0.93,
                "confidence": 0.95,
                "days_ago": 1,
                "is_positive": True, 
                "source_doc": "nvda_q3_2024"
            },
            {
                "source": "Data Center Revenue",
                "target": "AI Infrastructure",
                "edge_type": "dependent_on",
                "weight": 0.88,
                "confidence": 0.87,
                "days_ago": 5,
                "is_positive": True,
                "source_doc": "industry_analysis"
            },
            # Policy and regulatory relationships
            {
                "source": "US",
                "target": "Export Controls",
                "edge_type": "enforces",
                "weight": 0.97,
                "confidence": 0.96,
                "days_ago": 30,
                "is_positive": False,
                "source_doc": "export_controls_impact"
            },
            {
                "source": "Export Controls", 
                "target": "NVDA",
                "edge_type": "restricts",
                "weight": 0.82,
                "confidence": 0.85,
                "days_ago": 30,
                "is_positive": False,
                "source_doc": "export_controls_impact"
            },
            {
                "source": "China",
                "target": "Export Controls",
                "edge_type": "affected_by",
                "weight": 0.90,
                "confidence": 0.89,
                "days_ago": 30,
                "is_positive": False,
                "source_doc": "export_controls_impact"
            },
            # Alternative supply chains
            {
                "source": "Apple",
                "target": "TSMC",
                "edge_type": "sources_from",
                "weight": 0.85,
                "confidence": 0.83,
                "days_ago": 10,
                "is_positive": True,
                "source_doc": "apple_supply_diversification"
            },
            {
                "source": "Apple",
                "target": "Samsung",
                "edge_type": "diversifies_to",
                "weight": 0.65,
                "confidence": 0.72,
                "days_ago": 10,
                "is_positive": True,
                "source_doc": "apple_supply_diversification"
            },
            # Competitive relationships
            {
                "source": "Apple",
                "target": "NVDA",
                "edge_type": "reduces_dependence_on",
                "weight": 0.70,
                "confidence": 0.75,
                "days_ago": 10,
                "is_positive": False,
                "source_doc": "apple_supply_diversification"
            }
        ]
    
    def _create_test_queries(self) -> List[Dict[str, Any]]:
        """Create test queries with different complexity levels"""
        return [
            # Simple entity queries
            {
                "query": "What are NVIDIA's main business risks?",
                "type": "entity_analysis",
                "expected_entities": ["NVDA", "NVIDIA"],
                "expected_hops": 1,
                "complexity": "simple"
            },
            {
                "query": "Tell me about TSMC's role in the semiconductor industry",
                "type": "entity_info",
                "expected_entities": ["TSMC"],
                "expected_hops": 1,
                "complexity": "simple"
            },
            
            # Causal relationship queries
            {
                "query": "How do US export controls affect NVIDIA?",
                "type": "causal_analysis", 
                "expected_entities": ["US", "Export Controls", "NVDA"],
                "expected_hops": 2,
                "complexity": "medium"
            },
            {
                "query": "What is the relationship between China and TSMC?",
                "type": "relationship_analysis",
                "expected_entities": ["China", "TSMC"],
                "expected_hops": 2,
                "complexity": "medium"
            },
            
            # Multi-hop reasoning queries
            {
                "query": "How does geopolitical tension between US and China impact NVIDIA's data center revenue?",
                "type": "multi_hop_analysis",
                "expected_entities": ["US", "China", "NVDA", "Data Center Revenue"],
                "expected_hops": 3,
                "complexity": "complex"
            },
            {
                "query": "What are the supply chain risks for NVIDIA through its TSMC dependency?",
                "type": "risk_propagation",
                "expected_entities": ["NVDA", "TSMC", "Taiwan", "China"],
                "expected_hops": 3,
                "complexity": "complex"
            },
            
            # Pathway finding queries
            {
                "query": "Find connections between Apple and China policy",
                "type": "pathway_discovery",
                "expected_entities": ["Apple", "China"],
                "expected_hops": 4,
                "complexity": "complex"
            },
            
            # Investment-specific queries
            {
                "query": "Which companies are most exposed to Taiwan supply chain risks?",
                "type": "exposure_analysis",
                "expected_entities": ["Taiwan", "TSMC"],
                "expected_hops": 2,
                "complexity": "medium"
            },
            
            # Competitive intelligence queries
            {
                "query": "How is Apple reducing its semiconductor supply chain dependencies?",
                "type": "strategy_analysis", 
                "expected_entities": ["Apple", "TSMC", "Samsung"],
                "expected_hops": 2,
                "complexity": "medium"
            }
        ]
    
    def _create_expected_results(self) -> Dict[str, Any]:
        """Create expected result patterns for validation"""
        return {
            # Response quality metrics
            "min_response_length": 50,
            "max_response_time": 10.0,  # seconds
            "min_confidence_score": 0.3,
            
            # Entity extraction expectations
            "min_entities_found": 1,
            "max_entities_found": 10,
            
            # Graph structure expectations
            "min_nodes_in_subgraph": 2,
            "min_edges_in_subgraph": 1,
            "max_subgraph_size": 50,
            
            # Path finding expectations
            "max_path_length": 5,
            "min_path_confidence": 0.1,
            
            # Performance benchmarks
            "acceptable_query_time": 5.0,
            "cache_hit_improvement": 0.5,  # 50% faster on cache hit
            
            # Content quality patterns
            "required_keywords": {
                "risk_analysis": ["risk", "impact", "concern", "challenge"],
                "causal_analysis": ["because", "due to", "causes", "leads to", "results in"],
                "relationship": ["connected", "related", "linked", "associated"],
                "supply_chain": ["supply", "manufacturing", "production", "dependency"]
            }
        }
    
    def get_sample_document(self, doc_type: Optional[str] = None) -> Dict[str, str]:
        """Get a sample document for testing"""
        if doc_type:
            docs = [d for d in self.test_documents if d["type"] == doc_type]
            return docs[0] if docs else self.test_documents[0]
        return self.test_documents[0]
    
    def get_sample_edges(self, count: int = 5) -> List[Dict[str, Any]]:
        """Get sample edges for testing"""
        return self.test_edges[:count]
    
    def get_test_query(self, complexity: str = "simple") -> Dict[str, Any]:
        """Get a test query by complexity level"""
        queries = [q for q in self.test_queries if q["complexity"] == complexity]
        return queries[0] if queries else self.test_queries[0]
    
    def validate_response(self, response: Dict[str, Any], query_type: str) -> List[str]:
        """Validate response quality against expected patterns"""
        issues = []
        
        # Basic structure validation
        if "result" not in response:
            issues.append("Missing 'result' field")
        elif len(response["result"]) < self.expected_results["min_response_length"]:
            issues.append("Response too short")
        
        # Content quality validation
        if query_type in self.expected_results["required_keywords"]:
            keywords = self.expected_results["required_keywords"][query_type]
            result_text = str(response.get("result", "")).lower()
            found_keywords = [kw for kw in keywords if kw in result_text]
            if not found_keywords:
                issues.append(f"Missing expected keywords for {query_type}: {keywords}")
        
        return issues


class TestEnvironmentManager:
    """Manages test environments for consistent testing"""
    
    def __init__(self):
        self.temp_dirs = []
        self.active_environments = {}
    
    def create_test_environment(self, name: str) -> str:
        """Create isolated test environment"""
        temp_dir = tempfile.mkdtemp(prefix=f"ice_test_{name}_")
        self.temp_dirs.append(temp_dir)
        self.active_environments[name] = temp_dir
        
        # Create directory structure
        Path(temp_dir).mkdir(exist_ok=True)
        (Path(temp_dir) / "storage").mkdir(exist_ok=True)
        (Path(temp_dir) / "cache").mkdir(exist_ok=True)
        
        return temp_dir
    
    def get_environment_path(self, name: str) -> Optional[str]:
        """Get path to named test environment"""
        return self.active_environments.get(name)
    
    def cleanup_environment(self, name: str):
        """Clean up specific test environment"""
        if name in self.active_environments:
            temp_dir = self.active_environments[name]
            if Path(temp_dir).exists():
                shutil.rmtree(temp_dir)
            del self.active_environments[name]
            if temp_dir in self.temp_dirs:
                self.temp_dirs.remove(temp_dir)
    
    def cleanup_all_environments(self):
        """Clean up all test environments"""
        for temp_dir in self.temp_dirs:
            if Path(temp_dir).exists():
                shutil.rmtree(temp_dir)
        self.temp_dirs = []
        self.active_environments = {}
    
    def __del__(self):
        """Cleanup on destruction"""
        self.cleanup_all_environments()


def create_test_config() -> Dict[str, Any]:
    """Create test configuration"""
    return {
        "openai_api_key": os.getenv("OPENAI_API_KEY"),
        "test_timeout": 30.0,
        "max_retries": 3,
        "enable_caching": True,
        "log_level": "INFO",
        "performance_benchmarks": {
            "max_query_time": 10.0,
            "max_document_processing_time": 5.0,
            "max_edge_addition_time": 1.0
        }
    }


# Global fixtures for easy access
TEST_FIXTURES = TestDataFixtures()
TEST_CONFIG = create_test_config()