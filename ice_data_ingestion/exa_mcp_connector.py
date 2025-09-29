# ice_data_ingestion/exa_mcp_connector.py
"""
Exa MCP Server Connector for ICE Investment Context Engine
Integrates Exa's advanced web search capabilities into the ICE knowledge graph
Provides intelligent web search, company research, and competitive intelligence
Relevant files: mcp_infrastructure.py, mcp_data_manager.py, ice_rag.py
"""

import os
import json
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ExaSearchType(Enum):
    WEB_SEARCH = "web_search_exa"
    RESEARCH_PAPERS = "research_paper_search"
    COMPANY_RESEARCH = "company_research"
    CRAWLING = "crawling"
    COMPETITOR_FINDER = "competitor_finder"
    LINKEDIN_SEARCH = "linkedin_search"
    WIKIPEDIA_SEARCH = "wikipedia_search_exa"
    GITHUB_SEARCH = "github_search"


@dataclass
class ExaSearchQuery:
    """Query specification for Exa search operations"""
    query: str
    search_type: ExaSearchType
    num_results: int = 10
    use_autoprompt: bool = True
    include_domains: Optional[List[str]] = None
    exclude_domains: Optional[List[str]] = None
    start_crawl_date: Optional[datetime] = None
    end_crawl_date: Optional[datetime] = None
    include_text: bool = True
    include_highlights: bool = True
    
    def to_mcp_params(self) -> Dict[str, Any]:
        """Convert to MCP parameters"""
        params = {
            "query": self.query,
            "numResults": self.num_results,
            "useAutoprompt": self.use_autoprompt,
            "includeText": self.include_text,
            "includeHighlights": self.include_highlights
        }
        
        if self.include_domains:
            params["includeDomains"] = self.include_domains
            
        if self.exclude_domains:
            params["excludeDomains"] = self.exclude_domains
            
        if self.start_crawl_date:
            params["startCrawlDate"] = self.start_crawl_date.isoformat()
            
        if self.end_crawl_date:
            params["endCrawlDate"] = self.end_crawl_date.isoformat()
            
        return params


@dataclass
class ExaSearchResult:
    """Result from Exa search operation"""
    title: str
    url: str
    text: Optional[str]
    highlights: Optional[List[str]]
    published_date: Optional[datetime]
    author: Optional[str]
    score: Optional[float]
    
    @classmethod
    def from_mcp_result(cls, mcp_result: Dict[str, Any]) -> 'ExaSearchResult':
        """Create from MCP result"""
        published_date = None
        if mcp_result.get('publishedDate'):
            try:
                published_date = datetime.fromisoformat(mcp_result['publishedDate'].replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                pass
                
        return cls(
            title=mcp_result.get('title', ''),
            url=mcp_result.get('url', ''),
            text=mcp_result.get('text'),
            highlights=mcp_result.get('highlights'),
            published_date=published_date,
            author=mcp_result.get('author'),
            score=mcp_result.get('score')
        )


class ExaMCPConnector:
    """Connector for Exa MCP server integration"""
    
    def __init__(self):
        """Initialize Exa MCP connector"""
        self.server_name = "exa"
        self.api_key = os.getenv("EXA_API_KEY")
        self.base_url = "https://mcp.exa.ai/mcp"
        self.is_configured = self.api_key is not None
        
        if not self.is_configured:
            logger.warning("EXA_API_KEY not found. Exa MCP functionality will be limited.")
    
    def get_mcp_server_config(self) -> Dict[str, Any]:
        """Get MCP server configuration for Claude Desktop"""
        if not self.is_configured:
            logger.error("Cannot generate MCP config without EXA_API_KEY")
            return {}
            
        # Remote MCP server configuration
        remote_config = {
            "command": "npx",
            "args": [
                "-y",
                "mcp-remote",
                f"https://mcp.exa.ai/mcp?exaApiKey={self.api_key}"
            ]
        }
        
        # Local MCP server configuration (alternative)
        local_config = {
            "command": "npx",
            "args": [
                "-y",
                "exa-mcp-server",
                f"--tools={','.join([tool.value for tool in ExaSearchType])}"
            ],
            "env": {
                "EXA_API_KEY": self.api_key
            }
        }
        
        return {
            "remote": remote_config,
            "local": local_config
        }
    
    async def search_web(self, query: str, num_results: int = 10, 
                        include_domains: Optional[List[str]] = None,
                        exclude_domains: Optional[List[str]] = None) -> List[ExaSearchResult]:
        """Perform general web search"""
        search_query = ExaSearchQuery(
            query=query,
            search_type=ExaSearchType.WEB_SEARCH,
            num_results=num_results,
            include_domains=include_domains,
            exclude_domains=exclude_domains
        )
        
        return await self._execute_search(search_query)
    
    async def research_company(self, company: str, topics: Optional[List[str]] = None) -> List[ExaSearchResult]:
        """Research specific company information"""
        query = f"{company}"
        if topics:
            query += f" {' '.join(topics)}"
            
        search_query = ExaSearchQuery(
            query=query,
            search_type=ExaSearchType.COMPANY_RESEARCH,
            num_results=15,
            include_domains=[
                "sec.gov",
                "investor.{}.com".format(company.lower().replace(' ', '')),
                "bloomberg.com",
                "reuters.com",
                "cnbc.com",
                "yahoo.com"
            ]
        )
        
        return await self._execute_search(search_query)
    
    async def find_competitors(self, company: str, industry: Optional[str] = None) -> List[ExaSearchResult]:
        """Find competitors for a given company"""
        query = f"{company} competitors"
        if industry:
            query += f" {industry} industry"
            
        search_query = ExaSearchQuery(
            query=query,
            search_type=ExaSearchType.COMPETITOR_FINDER,
            num_results=20
        )
        
        return await self._execute_search(search_query)
    
    async def search_research_papers(self, topic: str, num_results: int = 10) -> List[ExaSearchResult]:
        """Search academic research papers"""
        search_query = ExaSearchQuery(
            query=topic,
            search_type=ExaSearchType.RESEARCH_PAPERS,
            num_results=num_results,
            include_domains=[
                "arxiv.org",
                "ssrn.com",
                "scholar.google.com",
                "pubmed.ncbi.nlm.nih.gov",
                "ieee.org",
                "acm.org"
            ]
        )
        
        return await self._execute_search(search_query)
    
    async def search_linkedin(self, query: str, num_results: int = 10) -> List[ExaSearchResult]:
        """Search LinkedIn for professional information"""
        search_query = ExaSearchQuery(
            query=query,
            search_type=ExaSearchType.LINKEDIN_SEARCH,
            num_results=num_results,
            include_domains=["linkedin.com"]
        )
        
        return await self._execute_search(search_query)
    
    async def crawl_website(self, url: str, max_depth: int = 2) -> List[ExaSearchResult]:
        """Crawl specific website for content"""
        search_query = ExaSearchQuery(
            query=url,
            search_type=ExaSearchType.CRAWLING,
            num_results=50,
            include_text=True
        )
        
        return await self._execute_search(search_query)
    
    async def _execute_search(self, search_query: ExaSearchQuery) -> List[ExaSearchResult]:
        """Execute search using MCP client"""
        if not self.is_configured:
            logger.warning(f"Cannot execute {search_query.search_type.value} - EXA_API_KEY not configured")
            return []
        
        try:
            # Use MCP client manager to execute the search
            from .mcp_client_manager import mcp_client_manager
            
            # Prepare MCP tool call
            tool_name = search_query.search_type.value
            tool_params = search_query.to_mcp_params()
            
            # Execute via MCP
            result = await mcp_client_manager.call_tool(
                server_name=self.server_name,
                tool_name=tool_name,
                parameters=tool_params
            )
            
            if result.get("error"):
                logger.error(f"Exa search error: {result['error']}")
                return []
            
            # Parse results
            raw_results = result.get("results", [])
            search_results = []
            
            for raw_result in raw_results:
                try:
                    search_result = ExaSearchResult.from_mcp_result(raw_result)
                    search_results.append(search_result)
                except Exception as e:
                    logger.warning(f"Failed to parse search result: {e}")
                    continue
            
            logger.info(f"Exa search completed: {len(search_results)} results for query '{search_query.query}'")
            return search_results
            
        except Exception as e:
            logger.error(f"Exa search execution failed: {e}")
            return []
    
    async def get_financial_news(self, symbol: str, days_back: int = 7) -> List[ExaSearchResult]:
        """Get recent financial news for a symbol"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        query = f"{symbol} earnings revenue financial results stock"
        
        search_query = ExaSearchQuery(
            query=query,
            search_type=ExaSearchType.WEB_SEARCH,
            num_results=20,
            start_crawl_date=start_date,
            end_crawl_date=end_date,
            include_domains=[
                "bloomberg.com",
                "reuters.com",
                "cnbc.com",
                "marketwatch.com",
                "yahoo.com",
                "sec.gov"
            ]
        )
        
        return await self._execute_search(search_query)
    
    async def get_industry_insights(self, industry: str, topics: Optional[List[str]] = None) -> List[ExaSearchResult]:
        """Get industry-specific insights and trends"""
        query = f"{industry} industry trends outlook"
        if topics:
            query += f" {' '.join(topics)}"
            
        search_query = ExaSearchQuery(
            query=query,
            search_type=ExaSearchType.WEB_SEARCH,
            num_results=15,
            include_domains=[
                "mckinsey.com",
                "bcg.com",
                "pwc.com",
                "deloitte.com",
                "bloomberg.com",
                "reuters.com"
            ]
        )
        
        return await self._execute_search(search_query)
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get connector health status"""
        return {
            "configured": self.is_configured,
            "api_key_present": bool(self.api_key),
            "server_name": self.server_name,
            "available_tools": [tool.value for tool in ExaSearchType],
            "last_check": datetime.now().isoformat()
        }


# Singleton instance for global access
exa_connector = ExaMCPConnector()


async def test_exa_integration():
    """Test Exa integration with sample queries"""
    if not exa_connector.is_configured:
        print("❌ Exa API key not configured. Please set EXA_API_KEY environment variable.")
        return False
    
    try:
        print("🔍 Testing Exa web search...")
        results = await exa_connector.search_web("NVIDIA Q3 2024 earnings", num_results=3)
        print(f"✅ Web search: {len(results)} results")
        
        print("🏢 Testing company research...")
        results = await exa_connector.research_company("NVIDIA", topics=["earnings", "AI"])
        print(f"✅ Company research: {len(results)} results")
        
        print("🆚 Testing competitor finder...")
        results = await exa_connector.find_competitors("NVIDIA", "semiconductors")
        print(f"✅ Competitor finder: {len(results)} results")
        
        print("✅ Exa integration test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Exa integration test failed: {e}")
        return False


if __name__ == "__main__":
    # Quick test
    asyncio.run(test_exa_integration())